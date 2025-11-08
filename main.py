import tkinter as tk
from tkinter import messagebox
import time
import sys
import threading
import socket
import urllib.request
from PIL import Image, ImageTk
from pymongo import MongoClient
import os
from dotenv import load_dotenv

# Import click tracker
from track_click import tracker

# Load environment variables
load_dotenv()

# Get the base path for resources
if getattr(sys, 'frozen', False):
    basePath = sys._MEIPASS
else:
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

        self.set_window_icon()
        self.root.protocol("WM_DELETE_WINDOW", self.force_close)
        self.center_window()
        
        # Show entry page immediately instead of loading screen
        self.show_entry_page()
        
        self.timeout_id = None  # Store timeout ID for cancellation
        self.process_alive = True  # Flag to keep process running
        self.root.mainloop()

    def set_window_icon(self):
        try:
            icon_path = os.path.join(basePath, "icon", "app.ico")
            if os.path.exists(icon_path):
                self.root.iconbitmap(icon_path)
            else:
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

    def show_background_loading_screen(self):
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

        # Create loading text and animation
        self.loading_text = canvas.create_text(640, 360, text="Loading Please Wait...",
                                            font=self.loading_font, fill="white")
        
        # Create rectangular loading animation
        self.loading_rect = canvas.create_rectangle(440, 400, 440, 430, fill="#2575fc", outline="")
        self.canvas = canvas
        
        # Start both animations
        self.animate_dots()
        self.animate_rectangle()

    def animate_dots(self):
        try:
            current_text = self.canvas.itemcget(self.loading_text, "text")
            if current_text.endswith("..."):
                new_text = "Loading Please Wait"
            else:
                new_text = current_text + "."
            self.canvas.itemconfig(self.loading_text, text=new_text)
            self.root.after(500, self.animate_dots)
        except tk.TclError:
            return

    def animate_rectangle(self):
        """Animate the rectangular loading bar"""
        try:
            # Get current coordinates of the rectangle
            coords = self.canvas.coords(self.loading_rect)
            if len(coords) >= 4:
                current_width = coords[2] - coords[0]
                
                # Reset if full width (840 - 440 = 400)
                if current_width >= 400:
                    self.canvas.coords(self.loading_rect, 440, 400, 440, 430)
                else:
                    # Increase width by 20 pixels each step
                    new_width = current_width + 20
                    self.canvas.coords(self.loading_rect, 440, 400, 440 + new_width, 430)
            
            # Continue animation
            self.root.after(100, self.animate_rectangle)
        except tk.TclError:
            return

    def show_entry_page(self):
        self.center_window()
        for widget in self.root.winfo_children():
            widget.destroy()
        
        bg_color = "#000000"
        canvas = tk.Canvas(self.root, width=1280, height=720, bg=bg_color)
        canvas.pack()

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

        canvas.create_text(640, 325, text="Beyond The Brush",
                         font=("Arial", 36,), fill="white")
        
        button_frame = tk.Frame(self.root, bg=bg_color)
        button_frame.place(relx=0.5, rely=0.65, anchor='center')

        enter_btn = tk.Button(button_frame, text="Enter", font=self.normal_font,
                             command=self.on_enter_click, bg="#2575fc", fg="white",
                             activebackground="#1a5dc2", activeforeground="white",
                             width=15, height=1)
        enter_btn.pack(pady=10)
        
        exit_btn = tk.Button(button_frame, text="Exit", font=self.normal_font,
                             command=self.force_close, bg="#ff00ff", fg="white",
                             activebackground="#cc00cc", activeforeground="white",
                             width=15, height=1)
        exit_btn.pack(pady=10)

        warning_label = tk.Label(button_frame, 
                                 text="⚠ When you click Enter, please wait\nand do not turn off your computer.",
                                 font=self.small_font, fg="gray", bg=bg_color, justify="center")
        warning_label.pack(pady=5)

        self.root.bind('<Return>', lambda event: self.on_enter_click())

    def check_internet_connection(self, host="8.8.8.8", port=53, timeout=3):
        try:
            socket.setdefaulttimeout(timeout)
            socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
            return True
        except (socket.gaierror, socket.timeout, socket.error):
            return False

    def on_enter_click(self):
        tracker.track_click(button="btb_enter", page="beyondthebrush_app")
        if not self.check_internet_connection():
            
            messagebox.showerror("Connection Error", 
                              "Connection Lost, Please Try Again\n\n"
                              "Please check your internet connection and try again.")
            return
        # Start a 30-second timeout to close the main window
        self.timeout_id = self.root.after(30000, self.close_main_window)
        self.launch_application()

    def on_exit_click(self):
        tracker.track_click(button="btb_exit", page="beyondthebrush_app")
        self.force_close()

    def launch_application(self):
        try:
            if not self.check_internet_connection():
                # Cancel timeout if no internet
                if self.timeout_id:
                    self.root.after_cancel(self.timeout_id)
                    self.timeout_id = None
                messagebox.showerror("Connection Error",
                                  "Connection Lost, Please Try Again\n\n"
                                  "Please check your internet connection and try again.")
                return
                
            # Show loading screen with rectangular animation when Enter is clicked
            self.show_background_loading_screen()
            
            # Create a flag to track VirtualPainter readiness
            self.vp_ready = False
            threading.Thread(target=self.launch_VirtualPainter_program, daemon=True).start()
            
            # Check periodically if VirtualPainter is ready
            self.check_vp_ready()

        except Exception as e:
            # Cancel timeout if launch fails
            if self.timeout_id:
                self.root.after_cancel(self.timeout_id)
                self.timeout_id = None
            messagebox.showerror("Error", f"Failed to launch application: {str(e)}")
            self.show_entry_page()

    def check_vp_ready(self):
        """Periodically check if VirtualPainter is ready"""
        try:
            if self.vp_ready:
                # Cancel timeout when VirtualPainter is ready
                if self.timeout_id:
                    self.root.after_cancel(self.timeout_id)
                    self.timeout_id = None
                self.root.destroy()  # Close main window when VirtualPainter is ready
            else:
                self.root.after(100, self.check_vp_ready)  # Check again after 100ms
        except tk.TclError:
            return

    def launch_VirtualPainter_program(self):
        try:
            print("Launching VirtualPainter")
            import VirtualPainter
            
            # Run VirtualPainter (assuming it creates its own window)
            VirtualPainter.run_application()
            
            # Set flag to indicate VirtualPainter is ready
            self.vp_ready = True
            
        except ImportError as ie:
            print(f"Failed to import VirtualPainter: {ie}")
            self.root.after(0, lambda: messagebox.showerror("Error", "Could not start the painting application"))
            self.root.after(0, self.show_entry_page)
        except Exception as e:
            print(f"Error in VirtualPainter: {e}")
            self.root.after(0, lambda: messagebox.showerror("Error", "Application startup failed"))
            self.root.after(0, self.show_entry_page)

    def close_main_window(self):
        """Close the main window without terminating the process"""
        if self.timeout_id:
            self.root.after_cancel(self.timeout_id)
            self.timeout_id = None
        try:
            self.root.destroy()
        except tk.TclError:
            pass
        # Do not call sys.exit(0) to keep the process alive for VirtualPainter

    def force_close(self):
        """Handle manual closure (e.g., window close button or Exit button)"""
        if self.timeout_id:
            self.root.after_cancel(self.timeout_id)
            self.timeout_id = None
        try:
            self.root.destroy()
        except tk.TclError:
            pass
        # Do not call sys.exit(0) to allow VirtualPainter to continue
        self.process_alive = False

if __name__ == "__main__":
    try:
        launcher = Launcher()
        # Keep process alive after mainloop ends if VirtualPainter is running
        while launcher.process_alive:
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("Application terminated by user")
        sys.exit(0)
    except Exception as e:
        print(f"Fatal error: {e}")
        import traceback
        traceback.print_exc()
        messagebox.showerror("Error", "Application failed to start")
        sys.exit(1)