# -*- coding: utf-8 -*-
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
import gc
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

# Load environment variables (still works from the project folder)
load_dotenv()

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

    # ------------------------------------------------------------------
    # UI INITIALISATION
    # ------------------------------------------------------------------
    def initialize_ui(self):
        """Initialize UI components with memory optimization"""
        try:
            self.root = tk.Tk()
            self.root.title("Beyond The Brush")

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

            # Jump straight to entry page (no loading screen at start)
            self.show_entry_page()

            self.root.mainloop()

        except Exception as e:
            print(f"UI initialization failed: {e}")
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
        self.root.bind("<Return>", lambda e: self.on_enter_click())

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
            text="Enter",
            font=self.normal_font,
            command=self.on_enter_click,
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
            text="Warning: When you click Enter, please wait\nand do not turn off your computer.",
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

    def on_enter_click(self):
        if not self.check_internet_connection():
            messagebox.showerror(
                "Connection Error",
                "Connection Lost, Please Try Again\n\n"
                "Please check your internet connection and try again.",
            )
            return

        # 3-second safety timeout – close launcher if VP never signals ready
        self.timeout_id = self.root.after(3000, self.close_main_window)
        self.launch_application()

    def launch_application(self):
        try:
            if not self.check_internet_connection():
                self.cancel_timeout()
                messagebox.showerror(
                    "Connection Error",
                    "Connection Lost, Please Try Again\n\n"
                    "Please check your internet connection and try again.",
                )
                return

            self.show_background_loading_screen()
            self.vp_ready = False
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
            import VirtualPainter
            VirtualPainter.run_application()
            self.vp_ready = True
        except Exception as e:
            print(f"VirtualPainter error: {e}")
            self.root.after(
                0,
                lambda: messagebox.showerror(
                    "Error", "Could not start the painting application"
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
        self.canvas = self.entry_canvas = None
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