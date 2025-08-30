import tkinter as tk
from tkinter import messagebox
import time
import sys
import threading
from PIL import Image, ImageTk
from pymongo import MongoClient
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get the base path for resources
if getattr(sys, 'frozen', False):
    # Running as compiled executable
    basePath = sys._MEIPASS
else:
    # Running as normal Python script
    basePath = os.path.dirname(os.path.abspath(__file__))

# MongoDB connection - secure implementation
def get_db_connection():
    try:
        # Load from environment variable (secure)
        MONGODB_URI = os.getenv("MONGODB_URI")
        
        # Fallback: Try to read from .env file directly if not found in environment
        if not MONGODB_URI:
            env_path = os.path.join(basePath, '.env')
            if os.path.exists(env_path):
                print("Loading MongoDB URI from .env file...")
                with open(env_path, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#'):
                            if '=' in line:
                                key, value = line.split('=', 1)
                                if key.strip() == 'MONGODB_URI':
                                    MONGODB_URI = value.strip().strip('"\'')
                                    break
        
        if not MONGODB_URI:
            print("MongoDB URI not found in environment variables or .env file")
            return None
        
        # Security check - don't log full URI
        uri_prefix = MONGODB_URI.split('@')[0] if '@' in MONGODB_URI else MONGODB_URI[:20]
        print(f"Attempting MongoDB connection with: {uri_prefix}...")
        
        # Connection with secure settings
        client = MongoClient(
            MONGODB_URI,
            tls=True,
            tlsAllowInvalidCertificates=False,
            serverSelectionTimeoutMS=10000,
            connectTimeoutMS=15000,
            socketTimeoutMS=20000,
            retryWrites=True,
            w='majority',
            appName="BeyondTheBrushApp"
        )
        
        # Test connection with timeout
        client.admin.command('ping', serverSelectionTimeoutMS=5000)
        db = client["beyond_the_brush"]
        print("MongoDB connection successful")
        return db
        
    except Exception as e:
        print(f"MongoDB connection failed: {str(e)}")
        # Don't expose sensitive information in error messages
        error_msg = str(e)
        if "authentication" in error_msg.lower():
            error_msg = "Authentication failed - check credentials"
        elif "network" in error_msg.lower() or "timeout" in error_msg.lower():
            error_msg = "Network connection failed - check internet connection"
        
        print(f"Connection error: {error_msg}")
        return None

# Global db connection
db = get_db_connection()

class Launcher:
    def __init__(self):
        self.title_font = ("Arial", 48, "bold")
        self.normal_font = ("Arial", 18)
        self.loading_font = ("Arial", 24)
        self.small_font = ("Arial", 14)
        
        self.root = tk.Tk()
        self.root.title("Beyond The Brush")
        self.center_window()
        self.root.geometry("1280x720")
        self.root.resizable(False, False)

        # Set the window icon securely
        self.set_window_icon()
        
        self.root.protocol("WM_DELETE_WINDOW", self.force_close)
        self.center_window()
        self.show_loading_screen()
        self.root.mainloop()

    def set_window_icon(self):
        """Set window icon with secure error handling"""
        try:
            icon_path = os.path.join(basePath, "icon", "app.ico")
            if os.path.exists(icon_path):
                self.root.iconbitmap(icon_path)
            else:
                # Fallback to PNG
                png_path = os.path.join(basePath, "icon", "logo.png")
                if os.path.exists(png_path):
                    icon_img = Image.open(png_path)
                    icon_photo = ImageTk.PhotoImage(icon_img)
                    self.root.iconphoto(True, icon_photo)
        except Exception as e:
            print(f"Icon setting failed: {e}")

    def center_window(self):
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width - 1280) // 2
        y = (screen_height - 720) // 2
        self.root.geometry(f"1280x720+{x}+{y}")

    def show_loading_screen(self):
        for widget in self.root.winfo_children():
            widget.destroy()
        
        canvas = tk.Canvas(self.root, width=1280, height=720)
        canvas.pack()
        bg_color = "#000000"
        canvas.create_rectangle(0, 0, 1280, 720, fill=bg_color, outline="")
        
        try:
            logo_path = os.path.join(basePath, "icon", "logo.png")
            logo_img = Image.open(logo_path)
            logo_img = logo_img.resize((200, 200))
            self.logo_photo = ImageTk.PhotoImage(logo_img)
            canvas.create_image(640, 150, image=self.logo_photo)
        except Exception as e:
            print(f"Logo image not found: {e}, using text instead")
            canvas.create_text(640, 150, text="Beyond The Brush",
                             font=self.title_font, fill="white")

        canvas.create_text(640, 360, text="Loading...",
                         font=self.loading_font, fill="white")
        progress = canvas.create_rectangle(410, 400, 410, 430, fill="#2575fc", outline="")

        for i in range(1, 101):
            try:
                canvas.coords(progress, 410, 400, 410 + (i * 4), 430)
                self.root.update()
                time.sleep(0.03)
            except tk.TclError:
                return

        self.show_entry_page()

    def show_entry_page(self):
        self.center_window()
        for widget in self.root.winfo_children():
            widget.destroy()
        
        bg_color = "#000000"
        canvas = tk.Canvas(self.root, width=1280, height=720, bg=bg_color)
        canvas.pack()

        # Centered logo
        try:
            logo_path = os.path.join(basePath, "icon", "logo.png")
            logo_img = Image.open(logo_path)
            logo_img = logo_img.resize((200, 200))
            self.logo_photo = ImageTk.PhotoImage(logo_img)
            canvas.create_image(640, 120, image=self.logo_photo)
        except Exception as e:
            print(f"Logo image not found: {e}, using text instead")
            canvas.create_text(640, 120, text="Beyond The Brush",
                               font=self.title_font, fill="white")

        # Title text - centered
        canvas.create_text(640, 260, text="Beyond The Brush",
                         font=("Arial", 36,), fill="white")
        
        # Role selection
        role_frame = tk.Frame(self.root, bg=bg_color)
        role_frame.place(relx=0.5, rely=0.45, anchor='center')

        self.role_var = tk.StringVar(value="student")
        tk.Radiobutton(role_frame, text="Student", variable=self.role_var, value="student", 
                      font=("Arial", 14,), bg=bg_color, fg="white", selectcolor="#2575fc",
                      activebackground=bg_color, activeforeground="white").pack(side=tk.LEFT, padx=20)
        tk.Radiobutton(role_frame, text="Educator", variable=self.role_var, value="educator", 
                      font=("Arial", 14, ), bg=bg_color, fg="white", selectcolor="#2575fc",
                      activebackground=bg_color, activeforeground="white").pack(side=tk.LEFT, padx=20)

        # Form container for input fields
        form_frame = tk.Frame(self.root, bg='')
        form_frame.place(relx=0.5, rely=0.58, anchor='center')

        # Name field
        name_frame = tk.Frame(form_frame, bg=bg_color)
        name_frame.pack(pady=10, fill='x')
        
        self.name_label = tk.Label(name_frame, text="Enter your name:", font=self.small_font, 
                                 bg=bg_color, fg="white", width=15, anchor='e')
        self.name_label.pack(side=tk.LEFT, padx=5)
        
        self.name_entry = tk.Entry(name_frame, font=self.small_font, width=25)
        self.name_entry.pack(side=tk.LEFT, padx=5)

        # Code field
        code_frame = tk.Frame(form_frame, bg=bg_color)
        code_frame.pack(pady=10, fill='x')
        
        self.code_label = tk.Label(code_frame, text="Access code:", font=self.small_font, 
                                 bg=bg_color, fg="white", width=15, anchor='e')
        self.code_label.pack(side=tk.LEFT, padx=5)
        
        self.code_entry = tk.Entry(code_frame, font=self.small_font, width=25, show="*")
        self.code_entry.pack(side=tk.LEFT, padx=5)

        # Button container
        button_frame = tk.Frame(self.root, bg=bg_color)
        button_frame.place(relx=0.5, rely=0.75, anchor='center')

        # Buttons
        login_btn = tk.Button(button_frame, text="Enter", font=self.normal_font,
                             command=self.verify_and_launch, bg="#2575fc", fg="white",
                             activebackground="#1a5dc2", activeforeground="white",
                             width=15, height=1)
        login_btn.pack(pady=10)
        
        exit_btn = tk.Button(button_frame, text="Exit", font=self.normal_font,
                             command=self.force_close, bg="#ff00ff", fg="white",
                             activebackground="#cc00cc", activeforeground="white",
                             width=15, height=1)
        exit_btn.pack(pady=10)

        self.root.bind('<Return>', lambda event: self.verify_and_launch())
        self.role_var.trace('w', self.on_role_change)
        self.on_role_change()

    def on_role_change(self, *args):
        if self.role_var.get() == "student":
            self.name_label.config(text="Enter your name:")
            self.name_entry.config(state="normal")
            self.name_entry.config(bg="white")
            self.name_entry.delete(0, tk.END)
        else:
            self.name_label.config(text="Educator Name:")
            self.name_entry.config(state="disabled")
            self.name_entry.config(bg="light gray")
            self.name_entry.delete(0, tk.END)

    def verify_code(self, code, role, name):
        global db
        if db is None:
            db = get_db_connection()
            if db is None:
                # Offline mode - allow access with basic validation
                if len(code) >= 4 and (role == "educator" or (role == "student" and len(name) >= 3)):
                    return True, role, name
                messagebox.showerror("Error", "Database connection not available")
                return False, None, None
        
        try:
            access_codes_collection = db["access_codes"]
            students_collection = db["students"]
            
            code_data = access_codes_collection.find_one({"code": code, "is_active": True})
            
            if not code_data:
                messagebox.showerror("Error", "Invalid or inactive access code")
                return False, None, None
            
            is_admin_code = code_data.get('is_admin_code', False)
            
            if role == "student" and is_admin_code:
                messagebox.showerror("Error", "Students cannot use admin access codes")
                return False, None, None
                
            if role == "educator" and not is_admin_code:
                messagebox.showerror("Error", "Educators must use admin access codes")
                return False, None, None
                
            if role == "student":
                student_data = students_collection.find_one({"access_code": code, "name": name})
                
                if student_data:
                    return True, "student", name
                else:
                    if messagebox.askyesno("Student Not Found", "Student not found. Would you like to register?"):
                        return False, "register", name
                    return False, None, None
                    
            elif role == "educator":
                if code_data:
                    return True, "educator", name
                else:
                    return False, None, None
            else:
                return False, None, None
                
        except Exception as e:
            print(f"Database verification error: {e}")
            messagebox.showerror("Error", "Verification failed due to database error")
            return False, None, None

    def verify_and_launch(self):
        role = self.role_var.get()
        name = self.name_entry.get().strip()
        code = self.code_entry.get().strip()
        
        if not code:
            messagebox.showerror("Error", "Please enter an access code")
            return
            
        if role == "student" and not name:
            messagebox.showerror("Error", "Please enter your name")
            return
        
        success, user_type, username = self.verify_code(code, role, name)
        
        if success:
            messagebox.showinfo("Success", f"Access granted for {user_type}!")
            self.launch_application(user_type, username)
        elif user_type == "register":
            self.show_register_page(name, code)
        else:
            if role == "student":
                messagebox.showerror("Error", "Invalid name or access code")
            else:
                messagebox.showerror("Error", "Invalid access code")

    def show_register_page(self, name="", code=""):
        for widget in self.root.winfo_children():
            widget.destroy()
        
        bg_color = "#383232"
        canvas = tk.Canvas(self.root, width=1280, height=720, bg=bg_color)
        canvas.pack()

        center_x = 1280 // 2
        logo_y = 100
        title_y = 230
        form_y = 290
        
        try:
            logo_path = os.path.join(basePath, "icon", "logo.png")
            logo_img = Image.open(logo_path)
            logo_img = logo_img.resize((150, 150))
            self.logo_photo = ImageTk.PhotoImage(logo_img)
            canvas.create_image(center_x, logo_y, image=self.logo_photo)
        except Exception as e:
            print(f"Logo image not found: {e}, using text instead")
            canvas.create_text(center_x, logo_y, text="Beyond The Brush",
                             font=self.title_font, fill="white")

        canvas.create_text(center_x, title_y, text="Student Registration",
                         font=("Arial", 36, "bold"), fill="white")

        form_frame = tk.Frame(self.root, bg=bg_color)
        form_frame.place(relx=0.5, y=form_y, anchor='center')

        name_frame = tk.Frame(form_frame, bg=bg_color)
        name_frame.pack(pady=10, fill='x')
        
        name_label = tk.Label(name_frame, text="Full Name:", 
                            font=self.small_font, bg=bg_color, fg="white")
        name_label.pack(side='left', padx=10)
        
        self.reg_name_entry = tk.Entry(name_frame, font=self.small_font, width=25)
        self.reg_name_entry.insert(0, name)
        self.reg_name_entry.pack(side='left')

        code_frame = tk.Frame(form_frame, bg=bg_color)
        code_frame.pack(pady=10, fill='x')
        
        code_label = tk.Label(code_frame, text="Access Code:", 
                            font=self.small_font, bg=bg_color, fg="white")
        code_label.pack(side='left', padx=10)
        
        self.reg_code_entry = tk.Entry(code_frame, font=self.small_font, width=25, show="*")
        self.reg_code_entry.insert(0, code)
        self.reg_code_entry.pack(side='left')

        button_frame = tk.Frame(form_frame, bg=bg_color)
        button_frame.pack(pady=20)

        register_btn = tk.Button(button_frame, text="REGISTER", font=self.normal_font,
                               command=self.register_student, bg="#ff6600", fg="white",
                               activebackground="#cc5200", activeforeground="white",
                               width=15)
        register_btn.pack(pady=5)
        
        back_btn = tk.Button(button_frame, text="BACK", font=self.normal_font,
                           command=self.show_entry_page, bg="#666666", fg="white",
                           activebackground="#555555", activeforeground="white",
                           width=15)
        back_btn.pack(pady=5)

    def register_student(self):
        name = self.reg_name_entry.get().strip()
        code = self.reg_code_entry.get().strip()
        
        if not name or not code:
            messagebox.showerror("Error", "Please fill in all fields")
            return
        
        if len(name) < 3:
            messagebox.showerror("Error", "Name must be at least 3 characters")
            return
        
        try:
            global db
            if db is None:
                db = get_db_connection()
                if db is None:
                    messagebox.showerror("Error", "Database connection not available")
                    return
            
            access_codes_collection = db["access_codes"]
            students_collection = db["students"]
            
            code_data = access_codes_collection.find_one({"code": code, "is_active": True})
            if not code_data:
                messagebox.showerror("Error", "Invalid access code")
                return
                
            if code_data.get('is_admin_code', False):
                messagebox.showerror("Error", "Cannot register with admin code")
                return
                
            existing_student = students_collection.find_one({"name": name})
            if existing_student:
                messagebox.showerror("Error", "Student already exists")
                return
                
            students_collection.insert_one({
                "name": name,
                "access_code": code,
                "registered_at": time.time()
            })
            
            messagebox.showinfo("Success", "Registration successful!")
            self.launch_application("student", name)
            
        except Exception as e:
            print(f"Registration error: {e}")
            messagebox.showerror("Error", "Registration failed due to database error")

    def launch_application(self, user_type, username):
        self.root.destroy()
        self.launch_VirtualPainter_program(user_type, username)

    def launch_VirtualPainter_program(self, user_type, username):
        try:
            print(f"Launching VirtualPainter as {user_type}: {username}")
            
            try:
                if self.root and self.root.winfo_exists():
                    self.root.destroy()
            except Exception as e:
                print(f"Warning: Could not destroy root window: {e}")
            
            try:
                import VirtualPainter
                VirtualPainter.run_application(user_type, username)
            except ImportError as ie:
                print(f"Failed to import VirtualPainter: {ie}")
                messagebox.showerror("Error", "Could not start the painting application")
                sys.exit(1)
            except Exception as e:
                print(f"Error in VirtualPainter: {e}")
                messagebox.showerror("Error", "Application startup failed")
                sys.exit(1)
            
        except Exception as e:
            print(f"Error launching VirtualPainter: {e}")
            import traceback
            traceback.print_exc()
            messagebox.showerror("Error", "Failed to launch application")
            sys.exit(1)

    def force_close(self):
        self.root.destroy()
        sys.exit(0)

if __name__ == "__main__":
    try:
        launcher = Launcher()
    except KeyboardInterrupt:
        print("Application terminated by user")
        sys.exit(0)
    except Exception as e:
        print(f"Fatal error: {e}")
        import traceback
        traceback.print_exc()
        messagebox.showerror("Error", "Application failed to start")
        sys.exit(1)