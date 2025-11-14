# SizeAdjustmentWindow

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import json
import os
import sys
import pyautogui
import numpy as np
from PIL import Image, ImageGrab
import cv2
import time
from track_click import tracker

class SizeAdjustmentWindow:
    def __init__(self):
        self.window = tk.Tk()
        self.window.title("Control Panel")
        self.window.geometry("400x500")  # Set initial size
        self.window.resizable(False, False)  # Disable resizing in both directions
        self.window.minsize(400, 500)  # Set minimum size same as initial size
        self.window.maxsize(400, 500)  # Set maximum size same as initial size
        
        # Configure grid weights
        self.window.columnconfigure(0, weight=1)
        self.window.rowconfigure(0, weight=1)
        
        # Control mode is now fixed to hand gesture control
        
        try:
            if sys.platform == "win32":
                self.window.wm_iconbitmap("icon/app.ico")
            else:
                icon_img = tk.PhotoImage(file="icon/app.ico")
                self.window.iconphoto(True, icon_img)
        except Exception as e:
            print(f"Could not set icon: {e}")

        # Try to load last used sizes and settings
        self.config_file = "size_config.json"
        self.load_config()
        
        # Control mode is now fixed to hand gesture control
        # Set window background to black
        self.window.configure(bg='black')
        
        # Create main container with padding and black background
        style = ttk.Style()
        style.configure('TFrame', background='black')
        style.configure('TLabelframe', background='black', foreground='white')
        style.configure('TLabelframe.Label', background='black', foreground='white')
        style.configure('TLabel', background='black', foreground='white')
        
        main_frame = ttk.Frame(self.window, padding="10 10 10 10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Create frames for brush and eraser controls with dark theme
        style.configure('TLabelframe', background='#1E1E1E', foreground='white')
        style.configure('TLabelframe.Label', background='#1E1E1E', foreground='white')
        
        brush_frame = ttk.LabelFrame(main_frame, text="Brush Size", padding="10")
        brush_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        
        eraser_frame = ttk.LabelFrame(main_frame, text="Eraser Size", padding="10")
        eraser_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        
        # Brush size controls
        self.brush_size = tk.IntVar(value=min(max(1, self.current_brush_size), 200))
        
        # Brush size label
        self.brush_label = ttk.Label(brush_frame, text=f"Current Size: {self.current_brush_size}", 
                                   font=('Helvetica', 10, 'bold'))
        self.brush_label.pack(pady=(0, 10))
        
        # Brush size slider
        self.brush_slider = ttk.Scale(
            brush_frame,
            from_=1,
            to=200,
            orient="horizontal",
            variable=self.brush_size,
            command=self.update_brush_size,
            length=300
        )
        self.brush_slider.pack(fill="x", padx=10, pady=5)
        
        # Brush size min/max labels
        size_frame = ttk.Frame(brush_frame)
        size_frame.pack(fill="x", padx=10)
        ttk.Label(size_frame, text="1").pack(side="left")
        ttk.Label(size_frame, text="200").pack(side="right")
        
        # Eraser size controls
        self.eraser_size = tk.IntVar(value=min(max(10, self.current_eraser_size), 200))
        
        # Eraser size label
        self.eraser_label = ttk.Label(eraser_frame, text=f"Current Size: {self.current_eraser_size}", 
                                     font=('Helvetica', 10, 'bold'))
        self.eraser_label.pack(pady=(0, 10))
        
        # Eraser size slider
        self.eraser_slider = ttk.Scale(
            eraser_frame,
            from_=10,
            to=200,
            orient="horizontal",
            variable=self.eraser_size,
            command=self.update_eraser_size,
            length=300
        )
        self.eraser_slider.pack(fill="x", padx=10, pady=5)
        
        # Eraser size min/max labels
        size_frame = ttk.Frame(eraser_frame)
        size_frame.pack(fill="x", padx=10)
        ttk.Label(size_frame, text="10").pack(side="left")
        ttk.Label(size_frame, text="200").pack(side="right")
        
        
        # Keep track of the last applied values
        self.last_brush_size = self.current_brush_size
        self.last_eraser_size = self.current_eraser_size
        
        # Initialize callback
        self.on_size_change_callback = None
        # Make window stay on top
        self.window.attributes('-topmost', True)
        
        # Add screenshot buttons frame with dark theme
        screenshot_frame = ttk.LabelFrame(main_frame, text="Screenshot", padding="10")
        screenshot_frame.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        
        # Configure slider and scale colors
        style.configure('TScale', background='#1E1E1E', troughcolor='#333333', foreground='white')
        style.configure('Horizontal.TScale', background='#1E1E1E')
        style.map('TScale', 
                 background=[('active', '#1E1E1E')],
                 troughcolor=[('active', '#555555')])
        
        # Button to capture entire screen (person + drawing)
        self.capture_all_btn = ttk.Button(
            screenshot_frame,
            text="Capture Person + Drawing",
            command=self.capture_screen,
            style="Accent.TButton",
            width=28
        )
        self.capture_all_btn.pack(fill="x", padx=5, pady=10, ipady=5)
        
        # Canvas region storage (kept in case needed by other parts of the code)
        self.canvas_region = None
        
        # Apply custom style for buttons with dark theme
        style = ttk.Style()
        
        # Configure the default button style for dark theme
        style.configure('TButton', 
                      font=('Helvetica', 10, 'bold'),
                      padding=8,
                      relief='raised',
                      borderwidth=2,
                      background='#333333',
                      foreground='white')
        
        # Configure the accent button style
        style.configure('Accent.TButton', 
                       background='#4CAF50',
                       foreground='white',
                       font=('Helvetica', 10, 'bold'),
                       padding=10,
                       borderwidth=2,
                       relief='raised')
        
        # Map the button states for better visual feedback
        style.map('TButton',
                 background=[('active', '#555555'), ('pressed', '#444444'), ('!disabled', '#333333')],
                 foreground=[('active', 'white'), ('pressed', 'white'), ('!disabled', 'white')],
                 relief=[('pressed', 'sunken'), ('!pressed', 'raised')])
                 
        style.map('Accent.TButton',
                 background=[('active', '#45a049'), ('pressed', '#3d8b40'), ('!disabled', '#4CAF50')],
                 foreground=[('active', 'white'), ('pressed', 'white'), ('!disabled', 'white')],
                 relief=[('pressed', 'sunken'), ('!pressed', 'raised')])
        
        # Configure label styles for dark theme
        style.configure('TLabel', 
                       font=('Helvetica', 10),
                       background='black',
                       foreground='white')
        
        # Configure frame styles for dark theme
        style.configure('TFrame', 
                       background='black')
        
        # Configure label frames for dark theme
        style.configure('TLabelframe', 
                       font=('Helvetica', 10, 'bold'),
                       background='#1E1E1E',
                       foreground='white')
        style.configure('TLabelframe.Label', 
                       font=('Helvetica', 10, 'bold'),
                       background='#1E1E1E',
                       foreground='white')
        
        # Handle window close
        self.window.protocol("WM_DELETE_WINDOW", self.on_closing)
        
    def capture_screen(self):
        try:
            # Hide the window
            self.window.withdraw()
            
            # Give the window time to hide
            self.window.update()
            time.sleep(0.5)  # Small delay to ensure window is hidden
            
            try:
                # Create btbSavedImage folder in Downloads if it doesn't exist
                download_folder = os.path.join(os.path.expanduser("~"), "Downloads")
                save_folder = os.path.join(download_folder, "beyondthebrush_app_saved_canvas")
                os.makedirs(save_folder, exist_ok=True)
                
                timestamp = time.strftime("%Y%m%d_%H%M%S")
                save_path = os.path.join(save_folder, f"btb_screenshot_{timestamp}.png")
                
                # Take screenshot
                screenshot = pyautogui.screenshot()
                
                # Save the image
                screenshot.save(save_path)
                
                # Track the screenshot action
                tracker.track_click(button="btb_screenshot", page="beyondthebrush_app")
                
                # Show success message
                messagebox.showinfo("Success", f"Screenshot saved to:\n{save_path}")
                print(f"Screenshot saved to: {save_path}")
                
            except Exception as e:
                print(f"Error capturing screenshot: {str(e)}")
                messagebox.showerror("Error", f"Failed to capture screenshot: {str(e)}")
            
        finally:
            # Always restore the window, even if an error occurred
            self.window.deiconify()
            self.window.lift()
            self.window.focus_force()  # Bring window to front and give it focus
    
    def set_canvas_region(self, x, y, width, height):
        """Set the canvas region for screenshot capture"""
        self.canvas_region = (x, y, width, height)
    
    def load_config(self):
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    self.current_brush_size = config.get('brush_size', 100)
                    self.current_eraser_size = config.get('eraser_size', 100)
            else:
                self.current_brush_size = 100
                self.current_eraser_size = 100
        except:
            self.current_brush_size = 100
            self.current_eraser_size = 100
            
    def save_config(self):
        config = {
            'brush_size': self.current_brush_size,
            'eraser_size': self.current_eraser_size,
        }
        try:
            with open(self.config_file, 'w') as f:
                json.dump(config, f)
        except Exception as e:
            print(f"Error saving config: {e}")
    
    def update_brush_size(self, value):
        try:
            size = int(float(value))
            self.brush_label.config(text=f"Current Size: {size}")
            self.current_brush_size = size
            if self.on_size_change_callback:
                self.on_size_change_callback('brush', size)
        except (ValueError, TypeError):
            pass
            
    def update_eraser_size(self, value):
        try:
            size = int(float(value))
            self.eraser_label.config(text=f"Current Size: {size}")
            self.current_eraser_size = size
            if self.on_size_change_callback:
                self.on_size_change_callback('eraser', size)
        except (ValueError, TypeError):
            pass
    
    def apply_changes(self):
        self.current_brush_size = self.brush_size.get()
        self.current_eraser_size = self.eraser_size.get()
        self.save_config()
        self.last_brush_size = self.current_brush_size
        self.last_eraser_size = self.current_eraser_size
    
    def set_size_change_callback(self, callback):
        self.on_size_change_callback = callback
        
    def on_closing(self):
        # Restore last applied values before closing
        if self.on_size_change_callback:
            self.on_size_change_callback('brush', self.last_brush_size)
            self.on_size_change_callback('eraser', self.last_eraser_size)
        self.window.destroy()
    
    def run(self):
        self.window.mainloop()

if __name__ == "__main__":
    # Test the window independently
    app = SizeAdjustmentWindow()
    app.run()