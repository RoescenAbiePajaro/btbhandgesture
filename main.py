# main.py
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
        
        # Set window properties to match VirtualPainter.py
        self.root.geometry("1280x720")
        self.center_window()
        
        # Configure window properties
        self.root.state('zoomed')  # Maximize the window
        self.root.minsize(1024, 576)  # Set minimum size to maintain aspect ratio
        
        # Disable minimize button while keeping maximize and close buttons
        self.root.resizable(True, True)  # Allow resizing
        self.root.attributes('-toolwindow', 1)  # Removes minimize and maximize buttons
        self.root.attributes('-toolwindow', 0)  # Revert to normal window but keep the effect
        
        self.set_window_icon()
        self.root.protocol("WM_DELETE_WINDOW", self.force_close)
        self.center_window()
        
        # Show entry page immediately instead of loading screen
        self.show_entry_page()
        
        self.timeout_id = None  # Store timeout ID for cancellation
        self.process_alive = True  # Flag to keep process running
        self.animation_running = False  # Track if animation is running
        
        # Variables for loading animation
        self.loading_start_time = None
        self.last_width = 0
        self.dots_animation_id = None
        self.rectangle_animation_id = None
        
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
        
        # Create a frame that will handle resizing
        main_frame = tk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        canvas = tk.Canvas(main_frame, width=1280, height=720)
        canvas.pack(fill=tk.BOTH, expand=True)
        
        # Store canvas reference for resizing
        self.canvas = canvas
        
        bg_color = "#000000"
        self.bg_rect = canvas.create_rectangle(0, 0, 1280, 720, fill=bg_color, outline="")
        
        try:
            logo_path = os.path.join(basePath, "icon", "logo.png")
            logo_img = Image.open(logo_path)
            logo_img = logo_img.resize((200, 200))
            self.logo_photo = ImageTk.PhotoImage(logo_img)
            self.logo_image = canvas.create_image(640, 150, image=self.logo_photo)
        except Exception as e:
            print(f"Logo image not found: {e}, using text instead")
            self.logo_text = canvas.create_text(640, 150, text="Beyond The Brush",
                             font=self.title_font, fill="white")

        # Create loading text and animation
        self.loading_text = canvas.create_text(640, 360, text="Loading Please Wait...",
                                            font=self.loading_font, fill="white")
        
        # Create rectangular loading animation
        self.loading_rect = canvas.create_rectangle(440, 400, 440, 430, fill="#2575fc", outline="")
        
        # Bind resize event
        canvas.bind('<Configure>', self.on_canvas_resize)
        
        # Start animations
        self.start_loading_animations()

    def start_loading_animations(self):
        """Start both loading animations"""
        self.animation_running = True
        self.loading_start_time = time.time()
        self.last_width = 0
        
        # Start dots animation
        self.animate_dots()
        
        # Start rectangle animation
        self.animate_rectangle()

    def stop_loading_animations(self):
        """Stop all loading animations"""
        self.animation_running = False
        if self.dots_animation_id:
            self.root.after_cancel(self.dots_animation_id)
        if self.rectangle_animation_id:
            self.root.after_cancel(self.rectangle_animation_id)

    def on_canvas_resize(self, event):
        """Handle canvas resizing while maintaining aspect ratio"""
        if hasattr(self, 'canvas'):
            # Update background rectangle
            self.canvas.coords(self.bg_rect, 0, 0, event.width, event.height)
            
            # Update positions based on new size
            center_x = event.width // 2
            center_y = event.height // 2
            
            # Update logo position
            if hasattr(self, 'logo_image'):
                self.canvas.coords(self.logo_image, center_x, center_y - 200)
            elif hasattr(self, 'logo_text'):
                self.canvas.coords(self.logo_text, center_x, center_y - 200)
            
            # Update loading text position
            if hasattr(self, 'loading_text'):
                self.canvas.coords(self.loading_text, center_x, center_y)
            
            # Update loading bar position and width
            if hasattr(self, 'loading_rect'):
                bar_width = min(400, event.width - 200)  # Max 400 or screen width - 200
                bar_x = center_x - bar_width // 2
                # Get current progress to maintain loading bar position
                if self.loading_start_time:
                    elapsed = time.time() - self.loading_start_time
                    progress = min(elapsed / 30.0, 1.0)
                    current_width = int(bar_width * progress)
                    self.canvas.coords(self.loading_rect, bar_x, center_y + 40, bar_x + current_width, center_y + 70)
                else:
                    self.canvas.coords(self.loading_rect, bar_x, center_y + 40, bar_x, center_y + 70)

    def animate_dots(self):
        """Animate the loading dots - continues even when window is minimized"""
        if not self.animation_running:
            return
            
        try:
            current_text = self.canvas.itemcget(self.loading_text, "text")
            if current_text.endswith("..."):
                new_text = "Loading Please Wait"
            else:
                new_text = current_text + "."
            self.canvas.itemconfig(self.loading_text, text=new_text)
            self.dots_animation_id = self.root.after(500, self.animate_dots)
        except tk.TclError:
            return

    def animate_rectangle(self):
        """Animate the rectangular loading bar - continues even when window is minimized"""
        if not self.animation_running:
            return
            
        try:
            if self.loading_start_time is None:
                self.loading_start_time = time.time()
                self.last_width = 0
                
            # Calculate elapsed time and progress
            elapsed = time.time() - self.loading_start_time
            progress = min(elapsed / 3.0, 1.0)  # 3 seconds total duration
            
            # Get current canvas width for responsive sizing
            canvas_width = self.canvas.winfo_width()
            max_bar_width = min(400, canvas_width - 200)
            
            # Calculate target width based on progress
            target_width = int(max_bar_width * progress)
            
            # Only update if width has changed
            if target_width > self.last_width:
                center_x = canvas_width // 2
                center_y = self.canvas.winfo_height() // 2
                bar_x = center_x - max_bar_width // 2
                self.canvas.coords(self.loading_rect, bar_x, center_y + 40, bar_x + target_width, center_y + 70)
                self.last_width = target_width
            
            # Continue animation if not complete
            if progress < 1.0:
                self.rectangle_animation_id = self.root.after(50, self.animate_rectangle)
            else:
                # Restart animation if it completes (safety measure)
                self.loading_start_time = time.time()
                self.last_width = 0
                self.rectangle_animation_id = self.root.after(50, self.animate_rectangle)
                
        except tk.TclError:
            return

    def show_entry_page(self):
        self.center_window()
        for widget in self.root.winfo_children():
            widget.destroy()
        
        # Create a main frame that handles resizing
        main_frame = tk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        bg_color = "#000000"
        canvas = tk.Canvas(main_frame, width=1280, height=720, bg=bg_color)
        canvas.pack(fill=tk.BOTH, expand=True)
        
        # Store references for resizing
        self.entry_canvas = canvas
        
        # Create background rectangle for entry page
        self.entry_bg_rect = canvas.create_rectangle(0, 0, 1280, 720, fill=bg_color, outline="")
        
        try:
            logo_path = os.path.join(basePath, "icon", "logo.png")
            logo_img = Image.open(logo_path)
            logo_img = logo_img.resize((200, 200))
            self.logo_photo = ImageTk.PhotoImage(logo_img)
            self.entry_logo = canvas.create_image(640, 150, image=self.logo_photo)
        except Exception as e:
            print(f"Logo image not found: {e}, using text instead")
            self.entry_logo = canvas.create_text(640, 150, text="Beyond The Brush",
                               font=self.title_font, fill="white")

        self.title_text = canvas.create_text(640, 300, text="Beyond The Brush",
                         font=("Arial", 36,), fill="white")
        
        # Create button frame that centers properly
        self.button_frame = tk.Frame(canvas, bg=bg_color)
        self.button_frame_id = canvas.create_window(640, 450, window=self.button_frame, anchor='center')

        enter_btn = tk.Button(self.button_frame, text="Enter", font=self.normal_font,
                             command=self.on_enter_click, bg="#2575fc", fg="white",
                             activebackground="#1a5dc2", activeforeground="white",
                             width=15, height=1)
        enter_btn.pack(pady=10)
        
        exit_btn = tk.Button(self.button_frame, text="Exit", font=self.normal_font,
                             command=self.force_close, bg="#ff00ff", fg="white",
                             activebackground="#cc00cc", activeforeground="white",
                             width=15, height=1)
        exit_btn.pack(pady=10)

        warning_label = tk.Label(self.button_frame, 
                                 text="⚠ When you click Enter, please wait\nand do not turn off your computer.",
                                 font=self.small_font, fg="gray", bg=bg_color, justify="center")
        warning_label.pack(pady=5)

        # Bind resize event
        canvas.bind('<Configure>', self.on_entry_resize)

        self.root.bind('<Return>', lambda event: self.on_enter_click())

    def on_entry_resize(self, event):
        """Handle entry page resizing"""
        if hasattr(self, 'entry_canvas'):
            # Update background
            self.entry_canvas.coords(self.entry_bg_rect, 0, 0, event.width, event.height)
            
            center_x = event.width // 2
            center_y = event.height // 2
            
            # Update logo position (positioned higher on the screen)
            if hasattr(self, 'entry_logo'):
                self.entry_canvas.coords(self.entry_logo, center_x, 150)
            
            # Update title position (positioned below logo)
            if hasattr(self, 'title_text'):
                self.entry_canvas.coords(self.title_text, center_x, 300)
            
            # Update button frame position (positioned below title)
            if hasattr(self, 'button_frame_id'):
                self.entry_canvas.coords(self.button_frame_id, center_x, 450)

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
        # Start a 3-second timeout to close the main window
        self.timeout_id = self.root.after(3000, self.close_main_window)
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
            # Stop animations
            self.stop_loading_animations()
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
                # Stop animations
                self.stop_loading_animations()
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
        # Stop animations
        self.stop_loading_animations()
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
        # Stop animations
        self.stop_loading_animations()
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