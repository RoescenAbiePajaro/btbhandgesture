# -*- coding: utf-8 -*-
# main.py
import tkinter as tk
from tkinter import messagebox
import time
import sys
import threading
import socket
from PIL import Image, ImageTk
from pymongo import MongoClient
import os
from dotenv import load_dotenv
import gc
from datetime import datetime
import hashlib
import json
import base64

# ----------------------------------------------------------------------
# 1. Resource-path helper (works for dev & frozen one-file exe)
# ----------------------------------------------------------------------
def resource_path(relative_path: str) -> str:
    """Return absolute path to a bundled resource."""
    if getattr(sys, 'frozen', False):
        # PyInstaller extracts everything to sys._MEIPASS (in RAM for one-file)
        return os.path.join(sys._MEIPASS, relative_path)
    # Development mode – use the folder where the script lives
    return os.path.join(os.path.abspath(os.path.dirname(__file__)), relative_path)

# Load environment variables
load_dotenv()

class MongoDBHandler:
    """Handles MongoDB connection and user authentication"""
    def __init__(self):
        self.client = None
        self.db = None
        self.users_collection = None
        self.save_uploads_collection = None  # Collection for saved images
        self.connect()
    
    def connect(self):
        """Establish MongoDB connection"""
        try:
            mongodb_uri = os.getenv("MONGODB_URI", "mongodb+srv://202211504:APoiboNwZGFYm9cQ@cluster0.eeyewov.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
            self.client = MongoClient(mongodb_uri)
            
            # Connect to 'test' database
            database_name = "test"
            self.db = self.client[database_name]
            
            # Connect to 'users' collection
            self.users_collection = self.db.users
            
            # Connect to 'save_uploads' collection for saved images
            self.save_uploads_collection = self.db.save_uploads
            
            print(f"MongoDB Connected Successfully")
            print(f"Database: {database_name}")
            print(f"Users Collection: users")
            print(f"Uploads Collection: save_uploads")
            print(f"Total users: {self.users_collection.count_documents({})}")
            
            return True
        except Exception as e:
            print(f"MongoDB Connection Error: {e}")
            # Try to show what collections are available
            try:
                if self.client:
                    print("Available databases:", self.client.list_database_names())
            except:
                pass
            return False
    
    def authenticate_user(self, email: str, password: str):
        """Authenticate user with email and password"""
        try:
            print(f"Attempting to authenticate user: {email}")
            
            # Find user by email (case-insensitive)
            user = self.users_collection.find_one({"email": email.lower().strip()})
            
            if not user:
                print(f"No user found with email: {email}")
                return {"success": False, "message": "Invalid email or password"}
            
            print(f"User found: {user.get('fullName', 'No name')}")
            print(f"User role: {user.get('role', 'No role')}")
            
            # Check if user is active
            if 'isActive' in user and not user['isActive']:
                return {"success": False, "message": "Account is deactivated"}
            
            # Check password
            stored_password = user.get('password', '')
            
            # METHOD 1: Direct comparison (for plain text passwords in development)
            if stored_password == password:
                print("Password matched (plain text)")
                return self._create_auth_response(user)
            
            # METHOD 2: Try bcrypt if password looks like bcrypt hash
            if stored_password.startswith('$2'):
                try:
                    import bcrypt
                    if bcrypt.checkpw(password.encode('utf-8'), stored_password.encode('utf-8')):
                        print("Password matched (bcrypt)")
                        return self._create_auth_response(user)
                except Exception as bcrypt_error:
                    print(f"Bcrypt error: {bcrypt_error}")
            
            # METHOD 3: Try SHA256 if stored password is 64 chars (hex)
            if len(stored_password) == 64:
                try:
                    hashed_input = hashlib.sha256(password.encode()).hexdigest()
                    if hashed_input == stored_password:
                        print("Password matched (SHA256)")
                        return self._create_auth_response(user)
                except:
                    pass
            
            print("Password did not match any method")
            return {"success": False, "message": "Invalid email or password"}
            
        except Exception as e:
            print(f"Authentication Error: {e}")
            import traceback
            traceback.print_exc()
            return {"success": False, "message": "Authentication failed"}
    
    def _create_auth_response(self, user):
        """Create authentication response"""
        try:
            # Update last login
            self.users_collection.update_one(
                {"_id": user["_id"]},
                {"$set": {"lastLogin": datetime.utcnow()}}
            )
            
            # Prepare user data
            user_data = {
                "id": str(user["_id"]),
                "fullName": user.get("fullName", ""),
                "email": user.get("email", ""),
                "username": user.get("username", ""),
                "role": user.get("role", "student")
            }
            
            # Add role-specific data
            if user_data["role"] == "student":
                user_data.update({
                    "school": user.get("school", ""),
                    "course": user.get("course", ""),
                    "year": user.get("year", ""),
                    "block": user.get("block", ""),
                    "enrolledClass": str(user.get("enrolledClass", "")) if user.get("enrolledClass") else None
                })
            elif user_data["role"] == "educator":
                user_data.update({
                    "classes": [str(cls) for cls in user.get("classes", [])] if user.get("classes") else []
                })
            
            # Add other common fields
            user_data.update({
                "isActive": user.get("isActive", True),
                "createdAt": user.get("createdAt", ""),
                "updatedAt": user.get("updatedAt", "")
            })
            
            print(f"Authentication successful for: {user_data['fullName']}")
            
            return {
                "success": True,
                "message": "Login successful",
                "user": user_data,
                "token": self._generate_token(user_data["id"])
            }
        except Exception as e:
            print(f"Error creating auth response: {e}")
            return {"success": False, "message": "Error processing user data"}
    
    def save_image_to_db(self, user_email: str, user_role: str, image_path: str, image_data=None):
        """Save uploaded image to save_uploads collection"""
        try:
            print(f"Saving image to MongoDB for user: {user_email}")
            
            # Read image if data not provided
            if image_data is None:
                with open(image_path, 'rb') as f:
                    image_data = f.read()
            
            # Convert to base64
            image_base64 = base64.b64encode(image_data).decode('utf-8')
            
            # Get file info
            file_size = len(image_data)
            file_name = os.path.basename(image_path)
            
            # Create document
            upload_doc = {
                "user_email": user_email.lower().strip(),
                "user_role": user_role,
                "file_name": file_name,
                "file_path": image_path,
                "file_size": file_size,
                "image_data": image_base64,
                "upload_date": datetime.utcnow(),
                "timestamp": time.time()
            }
            
            # Insert into save_uploads collection
            result = self.save_uploads_collection.insert_one(upload_doc)
            
            print(f"Image saved to database. Document ID: {result.inserted_id}")
            return {
                "success": True,
                "message": "Image saved to database",
                "document_id": str(result.inserted_id)
            }
            
        except Exception as e:
            print(f"Error saving image to database: {e}")
            import traceback
            traceback.print_exc()
            return {"success": False, "message": f"Database save failed: {str(e)}"}
    
    def get_user_uploads(self, user_email: str):
        """Get all uploaded images for a user"""
        try:
            uploads = list(self.save_uploads_collection.find(
                {"user_email": user_email.lower().strip()},
                {"_id": 1, "file_name": 1, "upload_date": 1, "file_size": 1, "user_role": 1}
            ).sort("upload_date", -1))
            
            # Convert ObjectId to string and format date
            for upload in uploads:
                upload['_id'] = str(upload['_id'])
                if 'upload_date' in upload:
                    upload['upload_date'] = upload['upload_date'].isoformat()
            
            return uploads
        except Exception as e:
            print(f"Error fetching user uploads: {e}")
            return []
    
    def _generate_token(self, user_id: str) -> str:
        """Generate a simple token"""
        timestamp = str(int(time.time()))
        return hashlib.sha256(f"{user_id}{timestamp}".encode()).hexdigest()
    
    def close(self):
        """Close MongoDB connection"""
        if self.client:
            self.client.close()

class Launcher:
    def __init__(self):
        # Initialize MongoDB handler
        self.db_handler = MongoDBHandler()
        self.current_user = None
        
        # MEMORY OPTIMIZATION: Predefine fonts and sizes
        self.title_font = ("Arial", 48, "bold")
        self.normal_font = ("Arial", 18)
        self.loading_font = ("Arial", 24)
        self.small_font = ("Arial", 14)
        self.login_font = ("Arial", 16)

        # MEMORY OPTIMIZATION: Initialize variables
        self.root = None
        self.timeout_id = None
        self.process_alive = True
        self.animation_running = False
        self.loading_start_time = None
        self.last_width = 0
        self.dots_animation_id = None
        self.rectangle_animation_id = None
        self.canvas = None
        self.entry_canvas = None
        self.login_canvas = None
        self.vp_ready = False
        
        # Initialize as None, will set in initialize_ui()
        self.email_var = None
        self.password_var = None
        self.role_var = None

        self.initialize_ui()

    # ------------------------------------------------------------------
    # UI INITIALISATION
    # ------------------------------------------------------------------
    def initialize_ui(self):
        """Initialize UI components with memory optimization"""
        try:
            self.root = tk.Tk()
            self.root.title("Beyond The Brush")

            # Initialize Tkinter variables AFTER root window is created
            self.email_var = tk.StringVar()
            self.password_var = tk.StringVar()
            self.role_var = tk.StringVar(value="student")

            # Match VirtualPainter.py geometry
            self.root.geometry("1280x720")
            self.center_window()

            self.root.state('zoomed')               # maximise
            self.root.minsize(1024, 576)            # keep aspect ratio

            self.root.resizable(True, True)
            self.root.attributes('-toolwindow', 1)
            self.root.attributes('-toolwindow', 0)

            self.set_window_icon()
            self.root.protocol("WM_DELETE_WINDOW", self.force_close)

            # Start with entry page
            self.show_entry_page()

            self.root.mainloop()

        except Exception as e:
            print(f"UI initialization failed: {e}")
            import traceback
            traceback.print_exc()
            self.cleanup_resources()
            raise

    # ------------------------------------------------------------------
    # ICON / LOGO HELPERS
    # ------------------------------------------------------------------
    def set_window_icon(self):
        """Set window icon – works for .ico and fallback .png"""
        try:
            ico = resource_path(os.path.join("icon", "app.ico"))
            if os.path.exists(ico):
                self.root.iconbitmap(ico)
                return

            png = resource_path(os.path.join("icon", "logo.png"))
            if os.path.exists(png):
                img = Image.open(png)
                img.thumbnail((32, 32), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(img)
                self.root.iconphoto(True, photo)
                self._icon_photo = photo                     # keep reference
        except Exception as e:
            print(f"Icon setting failed: {e}")

    # ------------------------------------------------------------------
    # LAYOUT HELPERS
    # ------------------------------------------------------------------
    def center_window(self):
        """Center the 1280x720 window on the primary monitor."""
        try:
            sw = self.root.winfo_screenwidth()
            sh = self.root.winfo_screenheight()
            x = (sw - 1280) // 2
            y = (sh - 720) // 2
            self.root.geometry(f"1280x720+{x}+{y}")
        except Exception as e:
            print(f"Window centering failed: {e}")

    # ------------------------------------------------------------------
    # LOGIN PAGE
    # ------------------------------------------------------------------
    def show_login_page(self):
        """Show login page with email and password fields"""
        self.clear_widgets()
        
        # Create main canvas
        self.login_canvas = tk.Canvas(self.root, bg="#000000", highlightthickness=0)
        self.login_canvas.pack(fill=tk.BOTH, expand=True)
        
        # Create background
        bg_rect = self.login_canvas.create_rectangle(0, 0, 1280, 720, fill="#000000", outline="")
        
        # Load logo
        try:
            path = resource_path(os.path.join("icon", "logo.png"))
            if os.path.exists(path):
                img = Image.open(path)
                img.thumbnail((150, 150), Image.Resampling.LANCZOS)
                self.login_logo_img = ImageTk.PhotoImage(img)
                self.login_canvas.create_image(640, 120, image=self.login_logo_img)
            else:
                self.login_canvas.create_text(640, 120, text="Beyond The Brush", 
                                            font=self.title_font, fill="white")
        except Exception as e:
            print(f"Login logo error: {e}")
            self.login_canvas.create_text(640, 120, text="Beyond The Brush", 
                                        font=self.title_font, fill="white")
        
        # Create login frame
        login_frame = tk.Frame(self.login_canvas, bg="#1a1a1a", padx=40, pady=40)
        self.login_canvas.create_window(640, 400, window=login_frame)
        
        # Title
        tk.Label(login_frame, text="Login", font=("Arial", 32, "bold"), 
                bg="#1a1a1a", fg="white").pack(pady=(0, 30))
        
        # Email field
        email_frame = tk.Frame(login_frame, bg="#1a1a1a")
        email_frame.pack(fill=tk.X, pady=(0, 20))
        tk.Label(email_frame, text="Email:", font=self.login_font, 
                bg="#1a1a1a", fg="white", width=10, anchor="w").pack(side=tk.LEFT)
        email_entry = tk.Entry(email_frame, textvariable=self.email_var, 
                            font=self.login_font, width=30, bg="#333", fg="white",
                            insertbackground="white")
        email_entry.pack(side=tk.LEFT, padx=(10, 0))
        
        # Password field
        password_frame = tk.Frame(login_frame, bg="#1a1a1a")
        password_frame.pack(fill=tk.X, pady=(0, 30))
        tk.Label(password_frame, text="Password:", font=self.login_font, 
                bg="#1a1a1a", fg="white", width=10, anchor="w").pack(side=tk.LEFT)
        password_entry = tk.Entry(password_frame, textvariable=self.password_var, 
                                font=self.login_font, width=30, bg="#333", fg="white",
                                show="•", insertbackground="white")
        password_entry.pack(side=tk.LEFT, padx=(10, 0))
        
        # Role selection
        role_frame = tk.Frame(login_frame, bg="#1a1a1a")
        role_frame.pack(fill=tk.X, pady=(0, 30))
        tk.Label(role_frame, text="Role:", font=self.login_font, 
                bg="#1a1a1a", fg="white", width=10, anchor="w").pack(side=tk.LEFT)
        
        tk.Radiobutton(role_frame, text="Student", variable=self.role_var, 
                      value="student", font=self.login_font, bg="#1a1a1a", fg="white",
                      selectcolor="#333", activebackground="#1a1a1a",
                      activeforeground="white").pack(side=tk.LEFT, padx=(10, 20))
        tk.Radiobutton(role_frame, text="Educator", variable=self.role_var, 
                      value="educator", font=self.login_font, bg="#1a1a1a", fg="white",
                      selectcolor="#333", activebackground="#1a1a1a",
                      activeforeground="white").pack(side=tk.LEFT)
        
        # Buttons frame
        button_frame = tk.Frame(login_frame, bg="#1a1a1a")
        button_frame.pack(pady=(10, 0))
        
        tk.Button(button_frame, text="Login", font=self.login_font,
                 command=self.handle_login, bg="#2575fc", fg="white",
                 activebackground="#1a5dc2", activeforeground="white",
                 width=15, height=1, padx=20).pack(side=tk.LEFT, padx=(0, 20))
        
        tk.Button(button_frame, text="Back", font=self.login_font,
                 command=self.show_entry_page, bg="#666", fg="white",
                 activebackground="#555", activeforeground="white",
                 width=15, height=1, padx=20).pack(side=tk.LEFT)
        
        # Debug button (remove in production)
        tk.Button(button_frame, text="Debug Info", font=self.small_font,
                 command=self.show_debug_info, bg="#444", fg="white",
                 activebackground="#333", activeforeground="white",
                 width=12, height=1, padx=10).pack(side=tk.LEFT, padx=(20, 0))
        
        # Bind Enter key to login
        self.root.bind("<Return>", lambda e: self.handle_login())
        
        # Focus on email entry
        email_entry.focus_set()
        

    def show_debug_info(self):
        """Show debug information about MongoDB connection"""
        try:
            user_count = self.db_handler.users_collection.count_documents({})
            upload_count = self.db_handler.save_uploads_collection.count_documents({})
            collections = self.db_handler.db.list_collection_names()
            messagebox.showinfo("Debug Info", 
                              f"Database: test\n"
                              f"Collection: users (Total: {user_count})\n"
                              f"Collection: save_uploads (Total: {upload_count})\n"
                              f"All collections: {', '.join(collections)}")
        except Exception as e:
            messagebox.showerror("Debug Error", f"Error: {str(e)}")

    def handle_login(self):
        """Handle login authentication"""
        email = self.email_var.get().strip()
        password = self.password_var.get().strip()
        role = self.role_var.get()
        
        # Validation
        if not email or not password:
            messagebox.showwarning("Input Error", "Please enter both email and password")
            return
        
        # Check internet connection
        if not self.check_internet_connection():
            messagebox.showerror("Connection Error", 
                               "No internet connection. Please check your connection and try again.")
            return
        
        # Show loading
        self.show_background_loading_screen()
        
        # Authenticate in separate thread
        threading.Thread(target=self.authenticate_user_thread, 
                        args=(email, password, role), daemon=True).start()

    def authenticate_user_thread(self, email, password, role):
        """Authenticate user in background thread"""
        try:
            result = self.db_handler.authenticate_user(email, password)
            
            self.root.after(0, lambda: self.handle_auth_result(result, role))
            
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Error", f"Authentication failed: {str(e)}"))
            self.root.after(0, self.show_login_page)

    def handle_auth_result(self, result, expected_role):
        """Handle authentication result"""
        self.stop_loading_animations()
        
        if result["success"]:
            user = result["user"]
            
            # Check if user role matches selected role
            if user["role"] != expected_role:
                messagebox.showwarning("Role Mismatch", 
                                     f"Your account is registered as a {user['role']}, "
                                     f"but you selected {expected_role}. Please select the correct role.")
                self.show_login_page()
                return
            
            self.current_user = user
            messagebox.showinfo("Login Successful", 
                              f"Welcome, {user['fullName']}!\nRole: {user['role'].title()}")
            
            # Save user data to JSON file for VirtualPainter
            self.save_user_data(user)
            
            # Proceed to Virtual Painter
            self.launch_application()
        else:
            messagebox.showerror("Login Failed", result["message"])
            self.show_login_page()

    def save_user_data(self, user_data):
        """Save user data to JSON file for VirtualPainter"""
        try:
            with open("user_data.json", "w") as f:
                json.dump(user_data, f, indent=2, default=str)
            print(f"User data saved to user_data.json")
        except Exception as e:
            print(f"Error saving user data: {e}")

    # ------------------------------------------------------------------
    # LOADING SCREEN
    # ------------------------------------------------------------------
    def show_background_loading_screen(self):
        """Show a responsive loading screen."""
        self.clear_widgets()

        main_frame = tk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True)

        canvas = tk.Canvas(main_frame, width=1280, height=720)
        canvas.pack(fill=tk.BOTH, expand=True)
        self.canvas = canvas

        bg = "#000000"
        self.bg_rect = canvas.create_rectangle(0, 0, 1280, 720, fill=bg, outline="")

        self.load_logo_image(canvas, 640, 150)

        self.loading_text = canvas.create_text(
            640, 360, text="Loading Please Wait...", font=self.loading_font, fill="white"
        )
        self.loading_rect = canvas.create_rectangle(
            440, 400, 440, 430, fill="#2575fc", outline=""
        )

        canvas.bind("<Configure>", self.on_canvas_resize)
        self.start_loading_animations()

    def load_logo_image(self, canvas, x, y):
        """Load logo (PNG) – fallback to text."""
        try:
            path = resource_path(os.path.join("icon", "logo.png"))
            if not os.path.exists(path):
                raise FileNotFoundError

            img = Image.open(path)
            img.thumbnail((200, 200), Image.Resampling.LANCZOS)
            self.logo_photo = ImageTk.PhotoImage(img)
            self.logo_image = canvas.create_image(x, y, image=self.logo_photo)
            self._logo_photo_ref = self.logo_photo
        except Exception as e:
            print(f"Logo loading failed: {e}")
            self.logo_text = canvas.create_text(
                x, y, text="Beyond The Brush", font=self.title_font, fill="white"
            )

    def on_canvas_resize(self, event):
        """Keep everything centered when the window is resized."""
        try:
            self.canvas.coords(self.bg_rect, 0, 0, event.width, event.height)
            cx, cy = event.width // 2, event.height // 2

            if hasattr(self, "logo_image"):
                self.canvas.coords(self.logo_image, cx, cy - 200)
            elif hasattr(self, "logo_text"):
                self.canvas.coords(self.logo_text, cx, cy - 200)

            if hasattr(self, "loading_text"):
                self.canvas.coords(self.loading_text, cx, cy)

            if hasattr(self, "loading_rect"):
                bar_w = min(400, event.width - 200)
                bar_x = cx - bar_w // 2
                elapsed = time.time() - (self.loading_start_time or time.time())
                prog = min(elapsed / 30.0, 1.0)
                cur_w = int(bar_w * prog)
                self.canvas.coords(
                    self.loading_rect, bar_x, cy + 40, bar_x + cur_w, cy + 70
                )
        except Exception as e:
            print(f"Canvas resize failed: {e}")

    # ------------------------------------------------------------------
    # ANIMATIONS
    # ------------------------------------------------------------------
    def start_loading_animations(self):
        self.animation_running = True
        self.loading_start_time = time.time()
        self.last_width = 0
        self.animate_dots()
        self.animate_rectangle()

    def stop_loading_animations(self):
        self.animation_running = False
        for aid in (self.dots_animation_id, self.rectangle_animation_id):
            if aid:
                self.root.after_cancel(aid)
        self.dots_animation_id = self.rectangle_animation_id = None

    def animate_dots(self):
        if not self.animation_running or not hasattr(self, "canvas"):
            return
        try:
            txt = self.canvas.itemcget(self.loading_text, "text")
            new_txt = "Loading Please Wait" if txt.endswith("...") else txt + "."
            self.canvas.itemconfig(self.loading_text, text=new_txt)
            self.dots_animation_id = self.root.after(500, self.animate_dots)
        except tk.TclError:
            pass

    def animate_rectangle(self):
        if not self.animation_running or not hasattr(self, "canvas"):
            return
        try:
            if self.loading_start_time is None:
                self.loading_start_time = time.time()
                self.last_width = 0

            elapsed = time.time() - self.loading_start_time
            prog = min(elapsed / 3.0, 1.0)

            cw = self.canvas.winfo_width()
            max_w = min(400, cw - 200)
            target_w = int(max_w * prog)

            if target_w > self.last_width:
                cx, cy = cw // 2, self.canvas.winfo_height() // 2
                x0 = cx - max_w // 2
                self.canvas.coords(
                    self.loading_rect, x0, cy + 40, x0 + target_w, cy + 70
                )
                self.last_width = target_w

            if prog < 1.0:
                self.rectangle_animation_id = self.root.after(50, self.animate_rectangle)
            else:
                # loop forever
                self.loading_start_time = time.time()
                self.last_width = 0
                self.rectangle_animation_id = self.root.after(50, self.animate_rectangle)
        except tk.TclError:
            pass

    # ------------------------------------------------------------------
    # ENTRY PAGE
    # ------------------------------------------------------------------
    def show_entry_page(self):
        self.center_window()
        self.clear_widgets()

        main_frame = tk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True)

        canvas = tk.Canvas(main_frame, bg="#000000")
        canvas.pack(fill=tk.BOTH, expand=True)
        self.entry_canvas = canvas

        self.entry_bg_rect = canvas.create_rectangle(
            0, 0, 1280, 720, fill="#000000", outline=""
        )
        self.load_entry_logo(canvas, 640, 150)

        self.title_text = canvas.create_text(
            640, 300, text="Beyond The Brush", font=("Arial", 36), fill="white"
        )

        self.button_frame = tk.Frame(canvas, bg="#000000")
        self.button_frame_id = canvas.create_window(
            640, 450, window=self.button_frame, anchor="center"
        )
        self.create_entry_buttons()

        canvas.bind("<Configure>", self.on_entry_resize)

    def load_entry_logo(self, canvas, x, y):
        try:
            path = resource_path(os.path.join("icon", "logo.png"))
            if not os.path.exists(path):
                raise FileNotFoundError

            img = Image.open(path)
            img.thumbnail((200, 200), Image.Resampling.LANCZOS)
            self.entry_logo_photo = ImageTk.PhotoImage(img)
            self.entry_logo = canvas.create_image(x, y, image=self.entry_logo_photo)
            self._entry_logo_photo_ref = self.entry_logo_photo
        except Exception as e:
            print(f"Entry logo loading failed: {e}")
            self.entry_logo = canvas.create_text(
                x, y, text="Beyond The Brush", font=self.title_font, fill="white"
            )

    def create_entry_buttons(self):
        tk.Button(
            self.button_frame,
            text="Login",
            font=self.normal_font,
            command=self.show_login_page,
            bg="#2575fc",
            fg="white",
            activebackground="#1a5dc2",
            activeforeground="white",
            width=15,
            height=1,
        ).pack(pady=10)

        tk.Button(
            self.button_frame,
            text="Exit",
            font=self.normal_font,
            command=self.force_close,
            bg="#ff00ff",
            fg="white",
            activebackground="#cc00cc",
            activeforeground="white",
            width=15,
            height=1,
        ).pack(pady=10)

        tk.Label(
            self.button_frame,
            text="Warning: Please login with your credentials\nand select your correct role.",
            font=self.small_font,
            fg="gray",
            bg="#000000",
            justify="center",
        ).pack(pady=5)

    def on_entry_resize(self, event):
        try:
            self.entry_canvas.coords(self.entry_bg_rect, 0, 0, event.width, event.height)
            cx, cy = event.width // 2, event.height // 2

            if hasattr(self, "entry_logo"):
                self.entry_canvas.coords(self.entry_logo, cx, 150)

            if hasattr(self, "title_text"):
                self.entry_canvas.coords(self.title_text, cx, 300)

            if hasattr(self, "button_frame_id"):
                self.entry_canvas.coords(self.button_frame_id, cx, 450)
        except Exception as e:
            print(f"Entry resize failed: {e}")

    # ------------------------------------------------------------------
    # WIDGET CLEANUP
    # ------------------------------------------------------------------
    def clear_widgets(self):
        """Destroy every child widget – prevents leaks."""
        try:
            for w in self.root.winfo_children():
                w.destroy()
        except tk.TclError:
            pass

    # ------------------------------------------------------------------
    # NETWORK / LAUNCH LOGIC
    # ------------------------------------------------------------------
    def check_internet_connection(self, host="8.8.8.8", port=53, timeout=3):
        try:
            socket.setdefaulttimeout(timeout)
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            r = s.connect_ex((host, port))
            s.close()
            return r == 0
        except Exception:
            return False

    def launch_application(self):
        try:
            if not self.check_internet_connection():
                messagebox.showerror(
                    "Connection Error",
                    "Connection Lost, Please Try Again\n\n"
                    "Please check your internet connection and try again.",
                )
                return

            # 3-second safety timeout
            self.timeout_id = self.root.after(3000, self.close_main_window)
            
            self.show_background_loading_screen()
            self.vp_ready = False
            
            # Launch VirtualPainter
            threading.Thread(target=self.launch_VirtualPainter_program, daemon=True).start()
            self.check_vp_ready()
        except Exception as e:
            self.cancel_timeout()
            self.stop_loading_animations()
            messagebox.showerror("Error", f"Failed to launch application: {e}")
            self.show_entry_page()

    def check_vp_ready(self):
        if self.vp_ready:
            self.cancel_timeout()
            self.stop_loading_animations()
            self.root.destroy()
        else:
            self.root.after(100, self.check_vp_ready)

    def launch_VirtualPainter_program(self):
        try:
            print("Launching VirtualPainter")
            print(f"Current user: {self.current_user}")
            
            # Import and run VirtualPainter
            import VirtualPainter
            VirtualPainter.run_application()
            self.vp_ready = True
        except Exception as e:
            print(f"VirtualPainter error: {e}")
            import traceback
            traceback.print_exc()
            self.root.after(
                0,
                lambda: messagebox.showerror(
                    "Error", f"Could not start the painting application: {str(e)}"
                ),
            )
            self.root.after(0, self.show_entry_page)

    # ------------------------------------------------------------------
    # CLEANUP / CLOSE
    # ------------------------------------------------------------------
    def cancel_timeout(self):
        if self.timeout_id:
            self.root.after_cancel(self.timeout_id)
            self.timeout_id = None

    def close_main_window(self):
        self.cancel_timeout()
        self.stop_loading_animations()
        try:
            self.root.destroy()
        except tk.TclError:
            pass

    def force_close(self):
        self.cancel_timeout()
        self.stop_loading_animations()
        try:
            self.root.destroy()
        except tk.TclError:
            pass
        self.process_alive = False
        self.cleanup_resources()

    def cleanup_resources(self):
        self.stop_loading_animations()
        self.cancel_timeout()
        self.canvas = self.entry_canvas = self.login_canvas = None
        
        # Close MongoDB connection
        if self.db_handler:
            self.db_handler.close()
        
        gc.collect()
        print("Launcher cleanup completed")

    def __del__(self):
        self.cleanup_resources()


# ----------------------------------------------------------------------
# ENTRY POINT
# ----------------------------------------------------------------------
if __name__ == "__main__":
    launcher = None
    try:
        launcher = Launcher()
        while launcher and launcher.process_alive:
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("Terminated by user")
    except Exception as e:
        print(f"Fatal error: {e}")
        import traceback
        traceback.print_exc()
        messagebox.showerror("Error", "Application failed to start")
    finally:
        if launcher:
            launcher.cleanup_resources()