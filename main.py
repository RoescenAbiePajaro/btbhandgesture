import tkinter as tk
from tkinter import messagebox
import time
import sys
import threading
from PIL import Image, ImageTk
from pymongo import MongoClient
import os
from dotenv import load_dotenv
import subprocess
from SizeAdjustmentWindow import SizeAdjustmentWindow
from VirtualPainter import run_application

# Load environment variables
load_dotenv()

# Get the base path for resources
if getattr(sys, 'frozen', False):
    # Running as compiled executable
    basePath = sys._MEIPASS
else:
    # Running as normal Python script
    basePath = os.path.dirname(os.path.abspath(__file__))

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
        
        # Show size adjustment window first
        self.show_size_adjustment()
        
        self.root.mainloop()
    
    def show_size_adjustment(self):
        """Show the size adjustment window first"""
        def on_size_adjustment_close():
            # This will be called when the size adjustment window is closed
            self.size_window.window.destroy()
            self.launch_virtual_painter()
        
        # Create and show size adjustment window
        self.size_window = SizeAdjustmentWindow()
        # Set up callback for when the window is closed
        self.size_window.window.protocol("WM_DELETE_WINDOW", on_size_adjustment_close)
        # Set focus to the size adjustment window
        self.size_window.window.focus_force()
        # Wait for the window to be closed
        self.root.wait_window(self.size_window.window)
    
    def launch_virtual_painter(self):
        """Launch VirtualPainter after size adjustment is done"""
        try:
            # Hide the launcher window
            self.root.withdraw()
            # Launch VirtualPainter in the same process
            from VirtualPainter import run_application
            run_application(self.root)  # Pass the root window to VirtualPainter
        except Exception as e:
            print(f"Error launching VirtualPainter: {e}")
            # If there's an error, show the launcher window again
            self.root.deiconify()

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
            canvas.create_image(640, 180, image=self.logo_photo)
        except Exception as e:
            print(f"Logo image not found: {e}, using text instead")
            canvas.create_text(640, text="Beyond The Brush",
                               font=self.title_font, fill="white")

        # Title text - centered
        canvas.create_text(640, 325, text="Beyond The Brush",
                         font=("Arial", 36,), fill="white")
        
        # Button container
        button_frame = tk.Frame(self.root, bg=bg_color)
        button_frame.place(relx=0.5, rely=0.65, anchor='center')

        # Buttons
        enter_btn = tk.Button(button_frame, text="Enter", font=self.normal_font,
                             command=self.launch_application, bg="#2575fc", fg="white",
                             activebackground="#1a5dc2", activeforeground="white",
                             width=15, height=1)
        enter_btn.pack(pady=10)
        
        exit_btn = tk.Button(button_frame, text="Exit", font=self.normal_font,
                             command=self.force_close, bg="#ff00ff", fg="white",
                             activebackground="#cc00cc", activeforeground="white",
                             width=15, height=1)
        exit_btn.pack(pady=10)

        self.root.bind('<Return>', lambda event: self.launch_application())

    def launch_application(self):
        self.root.destroy()
        self.launch_VirtualPainter_program()

    def launch_VirtualPainter_program(self):
        try:
            print("Launching VirtualPainter")
            
            try:
                if self.root and self.root.winfo_exists():
                    self.root.destroy()
            except Exception as e:
                print(f"Warning: Could not destroy root window: {e}")
            
            try:
                import VirtualPainter
                VirtualPainter.run_application()
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