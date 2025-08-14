import tkinter as tk
from tkinter import messagebox
import time
import sys
import threading
import importlib
from PIL import Image, ImageTk
import pymongo
from pymongo import MongoClient
import os
from dotenv import load_dotenv
from register import check_student_exists, is_valid_access_code

# Load environment variables
load_dotenv()

# MongoDB connection
try:
    MONGODB_URI = os.getenv("MONGODB_URI")
    if not MONGODB_URI:
        raise ValueError("MONGODB_URI not set in environment variables")
    
    # Configure MongoDB client
    client = MongoClient(
        MONGODB_URI,
        tls=True,
        tlsAllowInvalidCertificates=False,
        serverSelectionTimeoutMS=5000,
        connectTimeoutMS=10000,
        socketTimeoutMS=10000
    )
    # Test the connection
    client.admin.command('ping')
    db = client["beyond_the_brush"]
    print("MongoDB connection successful")
except Exception as e:
    print(f"MongoDB connection failed: {str(e)}")
    db = None

# Preload modules in background
def preload_modules():
    try:
        # Remove VirtualPainter from preload
        import cv2
        import numpy as np
        import HandTrackingModule
        import KeyboardInput
    except Exception as e:
        print(f"Preloading error: {e}")

# --- VERIFICATION LOGIC ---
def verify_code(code, role, name):
    if db is None:
        messagebox.showerror("Error", "Database connection not available")
        return False
    
    try:
        if role == "student":
            # For students, check if they exist with the given name and access code
            if check_student_exists(name, code):
                return True, "student", name
            else:
                return False, None, None
        elif role == "educator":
            # For educators, check if the access code is valid
            if is_valid_access_code(code):
                return True, "educator", name
            else:
                return False, None, None
        else:
            return False, None, None
    except Exception as e:
        print(f"Verification error: {e}")
        return False, None, None

class Launcher:
    def __init__(self):
        self.CORRECT_CODE = "hYwfg"
        # Define global font settings
        self.title_font = ("Arial", 48, "bold")
        self.normal_font = ("Arial", 18)
        self.loading_font = ("Arial", 24)
        self.small_font = ("Arial", 14)
        
        # Create a single root window to be reused
        self.root = tk.Tk()
        self.root.title("Beyond The Brush")
        self.root.geometry("1280x720")  # Exact size matching VirtualPainter
        self.root.resizable(False, False)  # Prevent resizing
        
        # Set the window icon
        try:
            # For Windows, use the .ico file directly with wm_iconbitmap
            if sys.platform == "win32":
                self.root.wm_iconbitmap("icon/app.ico")
            else:
                # For other platforms, use a PNG with PhotoImage
                icon_img = tk.PhotoImage(file="icon/app.ico")
                self.root.iconphoto(True, icon_img)
        except Exception as e:
            print(f"Could not set icon: {e}")
            # Fallback: try to load icon using PIL which has better format support
            try:
                from PIL import Image, ImageTk
                icon = Image.open("icon/app.ico")
                icon_photo = ImageTk.PhotoImage(icon)
                self.root.iconphoto(True, icon_photo)
            except Exception as e2:
                print(f"Fallback icon loading also failed: {e2}")
        
        # Set up protocol to force close when X button is clicked
        self.root.protocol("WM_DELETE_WINDOW", self.force_close)
        
        # Center the window on screen
        self.center_window()
        
        # Start preloading in background during loading screen
        self.preload_thread = threading.Thread(target=preload_modules)
        self.preload_thread.daemon = True
        self.preload_thread.start()
        
        self.show_loading_screen()
        
        # Only call mainloop once, at the end of initialization
        self.root.mainloop()

    def center_window(self):
        # Get screen width and height
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        # Calculate position coordinates
        x = (screen_width - 1280) // 2
        y = (screen_height - 720) // 2
        
        # Set the position
        self.root.geometry(f"1280x720+{x}+{y}")

    def show_loading_screen(self):
        # Clear any existing widgets
        for widget in self.root.winfo_children():
            widget.destroy()
        
        canvas = tk.Canvas(self.root, width=1280, height=720)
        canvas.pack()
        
        # Background - #383232 as requested
        bg_color = "#383232"
        canvas.create_rectangle(0, 0, 1280, 720, fill=bg_color, outline="")
        
        # Try to load logo image
        try:
            logo_img = Image.open("icon/logo.png")
            logo_img = logo_img.resize((200, 200))
            self.logo_photo = ImageTk.PhotoImage(logo_img)
            canvas.create_image(610, 150, image=self.logo_photo)
        except FileNotFoundError:
            print("Logo image not found, using text instead")
            canvas.create_text(610, 150, text="Beyond The Brush",
                               font=self.title_font, fill="white")

        # Loading text with loading font
        canvas.create_text(610, 360, text="Loading...",
                           font=self.loading_font, fill="white")

        # Progress bar
        progress = canvas.create_rectangle(410, 400, 410, 430, fill="#3498db", outline="")

        # Animate progress bar
        for i in range(1, 101):
            # Check if window still exists before updating
            try:
                canvas.coords(progress, 410, 400, 410 + (i * 4), 430)
                self.root.update()
                time.sleep(0.03)
            except tk.TclError:
                # Window was closed during loading
                return

        self.show_entry_page()

    def show_entry_page(self):
        # Clear any existing widgets
        for widget in self.root.winfo_children():
            widget.destroy()
        
        # Background - #383232
        bg_color = "#383232"
        canvas = tk.Canvas(self.root, width=1280, height=720, bg=bg_color)
        canvas.pack()

        # Center everything vertically with more spacing
        center_y = 360  # Middle of 720
        logo_spacing = 120   # Spacing for logo
        form_spacing = 80    # Spacing for form elements

        # Try to load logo image
        try:
            logo_img = Image.open("icon/app.ico")
            logo_img = logo_img.resize((150, 150))
            self.logo_photo = ImageTk.PhotoImage(logo_img)
            # Position logo higher up
            canvas.create_image(610, center_y - logo_spacing, image=self.logo_photo)
            
            # Show title text
            canvas.create_text(610, center_y - logo_spacing + 100, text="Beyond The Brush",
                              font=self.title_font, fill="white")
        except FileNotFoundError:
            print("Logo image not found, using text instead")
            canvas.create_text(610, center_y - logo_spacing + 100, text="Beyond The Brush",
                              font=self.title_font, fill="white")

        # Role selection
        self.role_var = tk.StringVar(value="student")
        
        # Role selection frame
        role_frame = tk.Frame(self.root, bg=bg_color)
        role_frame.place(x=460, y=center_y - 20, width=360, height=40)
        
        tk.Radiobutton(role_frame, text="Student", variable=self.role_var, value="student", 
                      font=self.small_font, bg=bg_color, fg="white", selectcolor="#666666",
                      activebackground=bg_color, activeforeground="white").pack(side=tk.LEFT, padx=20)
        tk.Radiobutton(role_frame, text="Educator", variable=self.role_var, value="educator", 
                      font=self.small_font, bg=bg_color, fg="white", selectcolor="#666666",
                      activebackground=bg_color, activeforeground="white").pack(side=tk.LEFT, padx=20)

        # Student name entry (only visible for student role)
        self.name_label = tk.Label(self.root, text="Student Name:", font=self.small_font, 
                                  bg=bg_color, fg="white")
        self.name_label.place(x=460, y=center_y + 20, width=120, height=25)
        
        self.name_entry = tk.Entry(self.root, font=self.small_font, width=25)
        self.name_entry.place(x=590, y=center_y + 20, width=200, height=25)

        # Access code entry
        self.code_label = tk.Label(self.root, text="Access Code:", font=self.small_font, 
                                  bg=bg_color, fg="white")
        self.code_label.place(x=460, y=center_y + 60, width=120, height=25)
        
        self.code_entry = tk.Entry(self.root, font=self.small_font, width=25, show="*")
        self.code_entry.place(x=590, y=center_y + 60, width=200, height=25)

        # Login button
        login_btn = tk.Button(self.root, text="LOGIN", font=self.normal_font,
                             command=self.verify_and_launch, bg="#ff00ff", fg="white",
                             activebackground="#cc00cc", activeforeground="white")
        login_btn.place(x=510, y=center_y + 120, width=200, height=60)
        
        # # Register button
        # register_btn = tk.Button(self.root, text="REGISTER", font=self.normal_font,
        #                         command=self.show_register_page, bg="#ff6600", fg="white",
        #                         activebackground="#cc5200", activeforeground="white")
        # register_btn.place(x=510, y=center_y + 200, width=200, height=60)
        
        # Exit button
        exit_btn = tk.Button(self.root, text="EXIT", font=self.normal_font,
                             command=self.force_close, bg="#00cc00", fg="white",
                             activebackground="#009900", activeforeground="white")
        exit_btn.place(x=510, y=center_y + 200, width=200, height=60)

        # Bind Enter key to login
        self.root.bind('<Return>', lambda event: self.verify_and_launch())
        
        # Update UI based on role selection
        self.role_var.trace('w', self.on_role_change)
        self.on_role_change()

    def on_role_change(self, *args):
        """Update UI elements based on selected role"""
        if self.role_var.get() == "student":
            self.name_label.config(text="Student Name:")
            self.name_entry.config(state="normal")
            self.name_entry.config(bg="white")
        else:
            self.name_label.config(text="Admin Name:")
            self.name_entry.config(state="normal")
            self.name_entry.config(bg="white")

    def show_register_page(self):
        """Show the student registration page"""
        # Clear any existing widgets
        for widget in self.root.winfo_children():
            widget.destroy()
        
        # Background - #383232
        bg_color = "#383232"
        canvas = tk.Canvas(self.root, width=1280, height=720, bg=bg_color)
        canvas.pack()

        # Center everything vertically
        center_y = 360

        # Title
        canvas.create_text(610, center_y - 200, text="Student Registration",
                          font=self.title_font, fill="white")

        # Username entry
        username_label = tk.Label(self.root, text="Username (8 characters):", font=self.small_font, 
                                 bg=bg_color, fg="white")
        username_label.place(x=460, y=center_y - 100, width=200, height=25)
        
        self.username_entry = tk.Entry(self.root, font=self.small_font, width=25)
        self.username_entry.place(x=590, y=center_y - 100, width=200, height=25)

        # Access code entry
        code_label = tk.Label(self.root, text="Access Code:", font=self.small_font, 
                             bg=bg_color, fg="white")
        code_label.place(x=460, y=center_y - 50, width=200, height=25)
        
        self.reg_code_entry = tk.Entry(self.root, font=self.small_font, width=25, show="*")
        self.reg_code_entry.place(x=590, y=center_y - 50, width=200, height=25)

        # Register button
        register_btn = tk.Button(self.root, text="REGISTER", font=self.normal_font,
                                command=self.register_student, bg="#ff6600", fg="white",
                                activebackground="#cc5200", activeforeground="white")
        register_btn.place(x=510, y=center_y + 20, width=200, height=60)
        
        # Back button
        back_btn = tk.Button(self.root, text="BACK", font=self.normal_font,
                            command=self.show_entry_page, bg="#666666", fg="white",
                            activebackground="#555555", activeforeground="white")
        back_btn.place(x=510, y=center_y + 100, width=200, height=60)
        
        # Add access code button (for educators)
        add_code_btn = tk.Button(self.root, text="ADD ACCESS CODE", font=self.small_font,
                                command=self.show_add_code_page, bg="#9933cc", fg="white",
                                activebackground="#7a2999", activeforeground="white")
        add_code_btn.place(x=510, y=center_y + 160, width=200, height=40)

    def register_student(self):
        """Register a new student"""
        username = self.username_entry.get().strip()
        access_code = self.reg_code_entry.get().strip()
        
        if not username or not access_code:
            messagebox.showerror("Error", "Please fill in all fields")
            return
        
        if len(username) != 8:
            messagebox.showerror("Error", "Username must be exactly 8 characters long")
            return
        
        try:
            # Check if username already exists
            if check_student_exists(username, access_code):
                messagebox.showerror("Error", "This username is already registered")
                return
            
            # Check if access code is valid
            if not is_valid_access_code(access_code):
                messagebox.showerror("Error", "Invalid access code")
                return
            
            # Register the student
            from register import students_collection
            student_data = {
                "name": username,
                "access_code": access_code,
                "registered_at": time.time()
            }
            students_collection.insert_one(student_data)
            
            messagebox.showinfo("Success", "Student registered successfully!")
            self.show_entry_page()
            
        except Exception as e:
            messagebox.showerror("Error", f"Registration failed: {str(e)}")

    def show_add_code_page(self):
        """Show the add access code page for educators"""
        # Clear any existing widgets
        for widget in self.root.winfo_children():
            widget.destroy()
        
        # Background - #383232
        bg_color = "#383232"
        canvas = tk.Canvas(self.root, width=1280, height=720, bg=bg_color)
        canvas.pack()

        # Center everything vertically
        center_y = 360

        # Title
        canvas.create_text(610, center_y - 200, text="Add Access Code",
                          font=self.title_font, fill="white")

        # Access code entry
        code_label = tk.Label(self.root, text="New Access Code:", font=self.small_font, 
                             bg=bg_color, fg="white")
        code_label.place(x=460, y=center_y - 100, width=200, height=25)
        
        self.new_code_entry = tk.Entry(self.root, font=self.small_font, width=25)
        self.new_code_entry.place(x=590, y=center_y - 100, width=200, height=25)

        # Educator ID entry
        educator_label = tk.Label(self.root, text="Educator ID (optional):", font=self.small_font, 
                                 bg=bg_color, fg="white")
        educator_label.place(x=460, y=center_y - 50, width=200, height=25)
        
        self.educator_entry = tk.Entry(self.root, font=self.small_font, width=25)
        self.educator_entry.place(x=590, y=center_y - 50, width=200, height=25)

        # Add button
        add_btn = tk.Button(self.root, text="ADD CODE", font=self.normal_font,
                           command=self.add_access_code, bg="#9933cc", fg="white",
                           activebackground="#7a2999", activeforeground="white")
        add_btn.place(x=510, y=center_y + 20, width=200, height=60)
        
        # Back button
        back_btn = tk.Button(self.root, text="BACK", font=self.normal_font,
                            command=self.show_register_page, bg="#666666", fg="white",
                            activebackground="#555555", activeforeground="white")
        back_btn.place(x=510, y=center_y + 100, width=200, height=60)

    def add_access_code(self):
        """Add a new access code"""
        code = self.new_code_entry.get().strip()
        educator_id = self.educator_entry.get().strip()
        
        if not code:
            messagebox.showerror("Error", "Please enter an access code")
            return
        
        try:
            from register import add_access_code
            if add_access_code(code, educator_id):
                messagebox.showinfo("Success", "Access code added successfully!")
                self.show_register_page()
            else:
                messagebox.showerror("Error", "Failed to add access code")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to add access code: {str(e)}")

    def verify_and_launch(self):
        """Verify credentials and launch application"""
        role = self.role_var.get()
        name = self.name_entry.get().strip()
        code = self.code_entry.get().strip()
        
        if not code:
            messagebox.showerror("Error", "Please enter an access code")
            return
            
        if role == "student" and not name:
            messagebox.showerror("Error", "Please enter your name")
            return
        
        # Verify the code
        success, user_type, username = verify_code(code, role, name)
        
        if success:
            messagebox.showinfo("Success", f"Access granted for {user_type}!")
            self.launch_application(user_type, username)
        else:
            if role == "student":
                messagebox.showerror("Error", "Invalid name or access code")
            else:
                messagebox.showerror("Error", "Invalid access code")

    def launch_application(self, user_type, username):
        # Close entry window and launch the application
        self.root.destroy()
        self.launch_VirtualPainter_program(user_type, username)

    def launch_VirtualPainter_program(self, user_type, username):
        """Launch VirtualPainter directly after successful login"""
        try:
            print(f"Launching VirtualPainter as {user_type}: {username}")
            
            # Safely destroy the root window if it exists
            try:
                if self.root and self.root.winfo_exists():
                    self.root.destroy()
            except Exception as e:
                print(f"Warning: Could not destroy root window: {e}")
            
            try:
                # Import VirtualPainter only when needed
                global VirtualPainter
                import VirtualPainter
                
                # Call the run_application function with user type and username
                VirtualPainter.run_application(user_type, username)
            except ImportError as ie:
                print(f"Failed to import VirtualPainter: {ie}")
                raise
            except Exception as e:
                print(f"Error in VirtualPainter: {e}")
                raise
            
        except Exception as e:
            print(f"Error launching VirtualPainter: {e}")
            import traceback
            traceback.print_exc()
            input("Press Enter to exit...")
            sys.exit(1)

    def force_close(self):
        """Force close the application when X button is clicked"""
        self.root.destroy()
        sys.exit(0)  # Force exit the program


if __name__ == "__main__":
    try:
        launcher = Launcher()
    except KeyboardInterrupt:
        print("Application terminated by user")
        sys.exit(0)
