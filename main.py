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
import gc

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
        # MEMORY OPTIMIZATION: Predefine fonts and sizes
        self.title_font = ("Arial", 48, "bold")
        self.normal_font = ("Arial", 18)
        self.loading_font = ("Arial", 24)
        self.small_font = ("Arial", 14)
        
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
        self.vp_ready = False
        
        self.initialize_ui()

    def initialize_ui(self):
        """Initialize UI components with memory optimization"""
        try:
            self.root = tk.Tk()
            self.root.title("Beyond The Brush")
            
            # Set window properties to match VirtualPainter.py
            self.root.geometry("1280x720")
            self.center_window()
            
            # Configure window properties
            self.root.state('zoomed')  # Maximize the window
            self.root.minsize(1024, 576)  # Set minimum size to maintain aspect ratio
            
            # Disable minimize button while keeping maximize and close buttons
            self.root.resizable(True, True)
            self.root.attributes('-toolwindow', 1)
            self.root.attributes('-toolwindow', 0)
            
            self.set_window_icon()
            self.root.protocol("WM_DELETE_WINDOW", self.force_close)
            
            # Show entry page immediately instead of loading screen
            self.show_entry_page()
            
            self.root.mainloop()
            
        except Exception as e:
            print(f"UI initialization failed: {e}")
            self.cleanup_resources()
            raise

    def set_window_icon(self):
        """Set window icon with memory optimization"""
        try:
            icon_path = os.path.join(basePath, "icon", "app.ico")
            if os.path.exists(icon_path):
                self.root.iconbitmap(icon_path)
            else:
                png_path = os.path.join(basePath, "icon", "logo.png")
                if os.path.exists(png_path):
                    # MEMORY OPTIMIZATION: Load and resize efficiently
                    icon_img = Image.open(png_path)
                    icon_img.thumbnail((32, 32), Image.Resampling.LANCZOS)  # Smaller size
                    icon_photo = ImageTk.PhotoImage(icon_img)
                    self.root.iconphoto(True, icon_photo)
                    # MEMORY OPTIMIZATION: Store reference to prevent garbage collection
                    self._icon_photo = icon_photo
        except Exception as e:
            print(f"Icon setting failed: {e}")

    def center_window(self):
        """Center window on screen"""
        try:
            screen_width = self.root.winfo_screenwidth()
            screen_height = self.root.winfo_screenheight()
            x = (screen_width - 1280) // 2
            y = (screen_height - 720) // 2
            self.root.geometry(f"1280x720+{x}+{y}")
        except Exception as e:
            print(f"Window centering failed: {e}")

    def show_background_loading_screen(self):
        """Show loading screen with memory optimization"""
        # MEMORY OPTIMIZATION: Clear previous widgets efficiently
        self.clear_widgets()
        
        try:
            # Create a frame that will handle resizing
            main_frame = tk.Frame(self.root)
            main_frame.pack(fill=tk.BOTH, expand=True)
            
            canvas = tk.Canvas(main_frame, width=1280, height=720)
            canvas.pack(fill=tk.BOTH, expand=True)
            
            # Store canvas reference for resizing
            self.canvas = canvas
            
            bg_color = "#000000"
            self.bg_rect = canvas.create_rectangle(0, 0, 1280, 720, fill=bg_color, outline="")
            
            # MEMORY OPTIMIZATION: Load logo efficiently
            self.load_logo_image(canvas, 640, 150)
            
            # Create loading text and animation
            self.loading_text = canvas.create_text(640, 360, text="Loading Please Wait...",
                                                font=self.loading_font, fill="white")
            
            # Create rectangular loading animation
            self.loading_rect = canvas.create_rectangle(440, 400, 440, 430, fill="#2575fc", outline="")
            
            # Bind resize event
            canvas.bind('<Configure>', self.on_canvas_resize)
            
            # Start animations
            self.start_loading_animations()
            
        except Exception as e:
            print(f"Loading screen setup failed: {e}")
            self.show_entry_page()

    def load_logo_image(self, canvas, x, y):
        """Load logo image with memory optimization"""
        try:
            logo_path = os.path.join(basePath, "icon", "logo.png")
            if os.path.exists(logo_path):
                # MEMORY OPTIMIZATION: Load with optimal size
                logo_img = Image.open(logo_path)
                logo_img.thumbnail((200, 200), Image.Resampling.LANCZOS)
                self.logo_photo = ImageTk.PhotoImage(logo_img)
                self.logo_image = canvas.create_image(x, y, image=self.logo_photo)
                # MEMORY OPTIMIZATION: Store reference
                self._logo_photo_ref = self.logo_photo
            else:
                raise FileNotFoundError("Logo not found")
        except Exception as e:
            print(f"Logo loading failed: {e}")
            # Fallback to text
            self.logo_text = canvas.create_text(x, y, text="Beyond The Brush",
                             font=self.title_font, fill="white")

    def on_canvas_resize(self, event):
        """Handle canvas resizing with memory optimization"""
        try:
            if hasattr(self, 'canvas'):
                # Update background rectangle
                self.canvas.coords(self.bg_rect, 0, 0, event.width, event.height)
                
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
                    bar_width = min(400, event.width - 200)
                    bar_x = center_x - bar_width // 2
                    if self.loading_start_time:
                        elapsed = time.time() - self.loading_start_time
                        progress = min(elapsed / 30.0, 1.0)
                        current_width = int(bar_width * progress)
                        self.canvas.coords(self.loading_rect, bar_x, center_y + 40, bar_x + current_width, center_y + 70)
                    else:
                        self.canvas.coords(self.loading_rect, bar_x, center_y + 40, bar_x, center_y + 70)
        except Exception as e:
            print(f"Canvas resize failed: {e}")

    def start_loading_animations(self):
        """Start loading animations with memory optimization"""
        self.animation_running = True
        self.loading_start_time = time.time()
        self.last_width = 0
        
        # Start dots animation
        self.animate_dots()
        
        # Start rectangle animation
        self.animate_rectangle()

    def stop_loading_animations(self):
        """Stop all loading animations and cleanup"""
        self.animation_running = False
        if self.dots_animation_id:
            self.root.after_cancel(self.dots_animation_id)
            self.dots_animation_id = None
        if self.rectangle_animation_id:
            self.root.after_cancel(self.rectangle_animation_id)
            self.rectangle_animation_id = None

    def animate_dots(self):
        """Animate loading dots with memory optimization"""
        if not self.animation_running or not hasattr(self, 'canvas'):
            return
            
        try:
            current_text = self.canvas.itemcget(self.loading_text, "text")
            if current_text.endswith("..."):
                new_text = "Loading Please Wait"
            else:
                new_text = current_text + "."
            self.canvas.itemconfig(self.loading_text, text=new_text)
            self.dots_animation_id = self.root.after(500, self.animate_dots)
        except (tk.TclError, AttributeError):
            return

    def animate_rectangle(self):
        """Animate loading rectangle with memory optimization"""
        if not self.animation_running or not hasattr(self, 'canvas'):
            return
            
        try:
            if self.loading_start_time is None:
                self.loading_start_time = time.time()
                self.last_width = 0
                
            # Calculate elapsed time and progress
            elapsed = time.time() - self.loading_start_time
            progress = min(elapsed / 3.0, 1.0)
            
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
                # Restart animation if it completes
                self.loading_start_time = time.time()
                self.last_width = 0
                self.rectangle_animation_id = self.root.after(50, self.animate_rectangle)
                
        except (tk.TclError, AttributeError):
            return

    def show_entry_page(self):
        """Show entry page with memory optimization"""
        self.center_window()
        self.clear_widgets()
        
        try:
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
            
            # Load logo efficiently
            self.load_entry_logo(canvas, 640, 150)

            self.title_text = canvas.create_text(640, 300, text="Beyond The Brush",
                         font=("Arial", 36,), fill="white")
            
            # Create button frame that centers properly
            self.button_frame = tk.Frame(canvas, bg=bg_color)
            self.button_frame_id = canvas.create_window(640, 450, window=self.button_frame, anchor='center')

            # Create buttons
            self.create_entry_buttons()

            # Bind resize event
            canvas.bind('<Configure>', self.on_entry_resize)

            self.root.bind('<Return>', lambda event: self.on_enter_click())

        except Exception as e:
            print(f"Entry page setup failed: {e}")

    def load_entry_logo(self, canvas, x, y):
        """Load entry page logo with memory optimization"""
        try:
            logo_path = os.path.join(basePath, "icon", "logo.png")
            if os.path.exists(logo_path):
                logo_img = Image.open(logo_path)
                logo_img.thumbnail((200, 200), Image.Resampling.LANCZOS)
                self.entry_logo_photo = ImageTk.PhotoImage(logo_img)
                self.entry_logo = canvas.create_image(x, y, image=self.entry_logo_photo)
                # MEMORY OPTIMIZATION: Store reference
                self._entry_logo_photo_ref = self.entry_logo_photo
            else:
                raise FileNotFoundError("Logo not found")
        except Exception as e:
            print(f"Entry logo loading failed: {e}")
            self.entry_logo = canvas.create_text(x, y, text="Beyond The Brush",
                               font=self.title_font, fill="white")

    def create_entry_buttons(self):
        """Create entry page buttons with memory optimization"""
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
                                 font=self.small_font, fg="gray", bg="#000000", justify="center")
        warning_label.pack(pady=5)

    def on_entry_resize(self, event):
        """Handle entry page resizing with memory optimization"""
        try:
            if hasattr(self, 'entry_canvas'):
                # Update background
                self.entry_canvas.coords(self.entry_bg_rect, 0, 0, event.width, event.height)
                
                center_x = event.width // 2
                center_y = event.height // 2
                
                # Update logo position
                if hasattr(self, 'entry_logo'):
                    self.entry_canvas.coords(self.entry_logo, center_x, 150)
                
                # Update title position
                if hasattr(self, 'title_text'):
                    self.entry_canvas.coords(self.title_text, center_x, 300)
                
                # Update button frame position
                if hasattr(self, 'button_frame_id'):
                    self.entry_canvas.coords(self.button_frame_id, center_x, 450)
        except Exception as e:
            print(f"Entry resize failed: {e}")

    def clear_widgets(self):
        """Clear all widgets efficiently to prevent memory leaks"""
        try:
            if hasattr(self, 'root'):
                for widget in self.root.winfo_children():
                    widget.destroy()
        except tk.TclError:
            pass

    def check_internet_connection(self, host="8.8.8.8", port=53, timeout=3):
        """Check internet connection with memory optimization"""
        try:
            socket.setdefaulttimeout(timeout)
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            result = sock.connect_ex((host, port))
            sock.close()
            return result == 0
        except Exception:
            return False

    def on_enter_click(self):
        """Handle enter button click with memory optimization"""
        tracker.track_click(button="btb_enter", page="beyondthebrush_app")
        
        if not self.check_internet_connection():
            messagebox.showerror("Connection Error", 
                              "Connection Lost, Please Try Again\n\n"
                              "Please check your internet connection and try again.")
            return
            
        # Start a 3-second timeout to close the main window
        self.timeout_id = self.root.after(3000, self.close_main_window)
        self.launch_application()

    def launch_application(self):
        """Launch VirtualPainter application with memory optimization"""
        try:
            if not self.check_internet_connection():
                # Cancel timeout if no internet
                self.cancel_timeout()
                messagebox.showerror("Connection Error",
                                  "Connection Lost, Please Try Again\n\n"
                                  "Please check your internet connection and try again.")
                return
                
            # Show loading screen
            self.show_background_loading_screen()
            
            # Create a flag to track VirtualPainter readiness
            self.vp_ready = False
            threading.Thread(target=self.launch_VirtualPainter_program, daemon=True).start()
            
            # Check periodically if VirtualPainter is ready
            self.check_vp_ready()

        except Exception as e:
            self.cancel_timeout()
            self.stop_loading_animations()
            messagebox.showerror("Error", f"Failed to launch application: {str(e)}")
            self.show_entry_page()

    def check_vp_ready(self):
        """Periodically check if VirtualPainter is ready"""
        try:
            if self.vp_ready:
                self.cancel_timeout()
                self.stop_loading_animations()
                self.root.destroy()
            else:
                self.root.after(100, self.check_vp_ready)
        except tk.TclError:
            return

    def launch_VirtualPainter_program(self):
        """Launch VirtualPainter in a separate thread"""
        try:
            print("Launching VirtualPainter")
            import VirtualPainter
            
            # Run VirtualPainter
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

    def cancel_timeout(self):
        """Cancel any pending timeout"""
        if self.timeout_id:
            self.root.after_cancel(self.timeout_id)
            self.timeout_id = None

    def close_main_window(self):
        """Close main window with cleanup"""
        self.cancel_timeout()
        self.stop_loading_animations()
        try:
            self.root.destroy()
        except tk.TclError:
            pass

    def force_close(self):
        """Force close application with full cleanup"""
        tracker.track_click(button="btb_exit", page="beyondthebrush_app")
        self.cancel_timeout()
        self.stop_loading_animations()
        try:
            self.root.destroy()
        except tk.TclError:
            pass
        self.process_alive = False
        self.cleanup_resources()

    def cleanup_resources(self):
        """Clean up all resources to prevent memory leaks"""
        try:
            # Stop animations
            self.stop_loading_animations()
            
            # Cancel timeouts
            self.cancel_timeout()
            
            # Clear references
            if hasattr(self, 'canvas'):
                self.canvas = None
            if hasattr(self, 'entry_canvas'):
                self.entry_canvas = None
                
            # Force garbage collection
            gc.collect()
            
            print("Launcher cleanup completed")
            
        except Exception as e:
            print(f"Cleanup error: {e}")

    def __del__(self):
        """Destructor for automatic cleanup"""
        self.cleanup_resources()


if __name__ == "__main__":
    launcher = None
    try:
        launcher = Launcher()
        # Keep process alive after mainloop ends if VirtualPainter is running
        while launcher and launcher.process_alive:
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("Application terminated by user")
        if launcher:
            launcher.cleanup_resources()
        sys.exit(0)
    except Exception as e:
        print(f"Fatal error: {e}")
        import traceback
        traceback.print_exc()
        if launcher:
            launcher.cleanup_resources()
        messagebox.showerror("Error", "Application failed to start")
        sys.exit(1)
    finally:
        if launcher:
            launcher.cleanup_resources()