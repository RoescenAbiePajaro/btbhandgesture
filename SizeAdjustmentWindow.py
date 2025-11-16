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
import gc

class SizeAdjustmentWindow:
    def __init__(self):
        self.window = tk.Tk()
        self.window.title("Other Settings")
        self.window.geometry("350x450")
        self.window.resizable(False, False)
        self.window.minsize(350, 450)
        self.window.maxsize(350, 450)
        
        # Configure grid weights
        self.window.columnconfigure(0, weight=1)
        self.window.rowconfigure(0, weight=1)
        
        try:
            if sys.platform == "win32":
                self.window.wm_iconbitmap("icon/app.ico")
            else:
                icon_img = tk.PhotoImage(file="icon/app.ico")
                self.window.iconphoto(True, icon_img)
        except Exception as e:
            print(f"Could not set icon: {e}")

        # MEMORY OPTIMIZATION: Load config efficiently
        self.config_file = "size_config.json"
        self.load_config()
        
        # MEMORY OPTIMIZATION: Initialize variables
        self.on_size_change_callback = None
        self.canvas_region = None
        self.last_brush_size = self.current_brush_size
        self.last_eraser_size = self.current_eraser_size
        
        # Create main container with padding
        main_frame = ttk.Frame(self.window, padding="10 10 10 10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Create frames for brush and eraser controls
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
        brush_size_frame = ttk.Frame(brush_frame)
        brush_size_frame.pack(fill="x", padx=10)
        ttk.Label(brush_size_frame, text="1").pack(side="left")
        ttk.Label(brush_size_frame, text="200").pack(side="right")
        
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
        eraser_size_frame = ttk.Frame(eraser_frame)
        eraser_size_frame.pack(fill="x", padx=10)
        ttk.Label(eraser_size_frame, text="10").pack(side="left")
        ttk.Label(eraser_size_frame, text="200").pack(side="right")
        
        # Add screenshot buttons frame
        screenshot_frame = ttk.LabelFrame(main_frame, text="Screenshot", padding="10")
        screenshot_frame.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        
        # Button to capture entire screen (person + drawing)
        self.capture_all_btn = tk.Button(
            screenshot_frame,
            text="Take Screenshot",
            command=self.capture_screen,
            bg='#4CAF50',
            fg='white',
            font=('Helvetica', 10, 'bold'),
            padx=10,
            pady=10,
            cursor="hand2",
            activebackground='#45a049',
            activeforeground='white',
            relief=tk.RAISED,
            bd=2
        )
        self.capture_all_btn.pack(fill="x", padx=5, pady=10)
        
        # Apply custom style for buttons with better visibility
        self._configure_styles()
        
        # Make window stay on top
        self.window.attributes('-topmost', True)
        
        # Handle window close
        self.window.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # MEMORY OPTIMIZATION: Track screenshot operations to prevent memory leaks
        self.last_screenshot_time = 0
        self.screenshot_cooldown = 2.0  # Prevent rapid screenshots

    def _configure_styles(self):
        """Configure tkinter styles - separated for clarity"""
        style = ttk.Style()
        
        # Configure the default button style for better visibility
        style.configure('TButton', 
                      font=('Helvetica', 10, 'bold'),
                      padding=6)
        
        # Configure the accent button style
        style.configure('Accent.TButton', 
                       background='#4CAF50',
                       foreground='white',
                       font=('Helvetica', 10, 'bold'),
                       padding=6)
        
        # Map the button states for better visual feedback
        style.map('Accent.TButton',
                 background=[('active', '#45a049'), ('pressed', '#3d8b40')],
                 foreground=[('active', 'white'), ('pressed', 'white')])
        
        # Configure label styles
        style.configure('TLabel', 
                       font=('Helvetica', 10),
                       background='white')
        
        # Configure frame styles
        style.configure('TFrame', 
                       background='white')
        
        # Configure label frames
        style.configure('TLabelframe', 
                       font=('Helvetica', 10, 'bold'),
                       background='white')
        style.configure('TLabelframe.Label', 
                       font=('Helvetica', 10, 'bold'),
                       background='white')

    def capture_screen(self):
        """Capture screenshot with memory optimization"""
        current_time = time.time()
        if current_time - self.last_screenshot_time < self.screenshot_cooldown:
            return  # Prevent rapid screenshots
            
        self.last_screenshot_time = current_time
        
        try:
            # Create btbSavedImage folder in Downloads if it doesn't exist
            download_folder = os.path.join(os.path.expanduser("~"), "Downloads")
            save_folder = os.path.join(download_folder, "beyondthebrush_app_saved_canvas")
            os.makedirs(save_folder, exist_ok=True)
            
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            save_path = os.path.join(save_folder, f"btb_screenshot_{timestamp}.png")
            
            # Hide the window temporarily
            self.window.withdraw()
            
            # Small delay to ensure the window is hidden before taking screenshot
            self.window.update()
            time.sleep(0.5)
            
            # Take screenshot with memory optimization
            screenshot = None
            try:
                screenshot = pyautogui.screenshot()
                
                # MEMORY OPTIMIZATION: Convert and save immediately
                screenshot.save(save_path, optimize=True, quality=85)  # Reduced quality for smaller files
                
                # Track the screenshot action
                tracker.track_click(button="btb_screenshot", page="beyondthebrush_app")
                
                # Show success message
                messagebox.showinfo("Success", f"Screenshot saved to:\n{save_path}")
                print(f"Screenshot saved to: {save_path}")
                
            finally:
                # MEMORY OPTIMIZATION: Explicitly cleanup screenshot
                if screenshot:
                    del screenshot
                
                # Show the window again
                self.window.deiconify()
                self.window.lift()
                self.window.focus_force()
                
        except Exception as e:
            print(f"Error capturing screenshot: {str(e)}")
            messagebox.showerror("Error", f"Failed to capture screenshot: {str(e)}")
            # Ensure window is shown again in case of error
            self.window.deiconify()
        finally:
            # MEMORY OPTIMIZATION: Force garbage collection after screenshot
            gc.collect()

    def capture_canvas_region(self):
        """Capture only canvas region - optimized for memory"""
        current_time = time.time()
        if current_time - self.last_screenshot_time < self.screenshot_cooldown:
            return
            
        self.last_screenshot_time = current_time
        
        if not self.canvas_region:
            messagebox.showwarning("Warning", "Canvas region not set")
            return
            
        try:
            download_folder = os.path.join(os.path.expanduser("~"), "Downloads")
            save_folder = os.path.join(download_folder, "beyondthebrush_app_saved_canvas")
            os.makedirs(save_folder, exist_ok=True)
            
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            save_path = os.path.join(save_folder, f"btb_canvas_{timestamp}.png")
            
            # Capture specific region
            x, y, width, height = self.canvas_region
            screenshot = None
            try:
                screenshot = pyautogui.screenshot(region=(x, y, width, height))
                screenshot.save(save_path, optimize=True, quality=90)
                
                # Track the action
                tracker.track_click(button="btb_saved_canvas", page="beyondthebrush_app")
                
                messagebox.showinfo("Success", f"Canvas saved to:\n{save_path}")
                print(f"Canvas saved to: {save_path}")
                
            finally:
                if screenshot:
                    del screenshot
                    
        except Exception as e:
            print(f"Error capturing canvas: {str(e)}")
            messagebox.showerror("Error", f"Failed to capture canvas: {str(e)}")
        finally:
            gc.collect()
    
    def set_canvas_region(self, x, y, width, height):
        """Set the canvas region for screenshot capture - memory optimized"""
        # MEMORY OPTIMIZATION: Store as tuple instead of list
        self.canvas_region = (x, y, width, height)
    
    def load_config(self):
        """Load configuration with memory optimization"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    self.current_brush_size = config.get('brush_size', 10)
                    self.current_eraser_size = config.get('eraser_size', 100)
            else:
                # Default values
                self.current_brush_size = 10
                self.current_eraser_size = 100
        except Exception as e:
            print(f"Error loading config: {e}")
            # Safe defaults
            self.current_brush_size = 10
            self.current_eraser_size = 100
            
    def save_config(self):
        """Save configuration efficiently"""
        config = {
            'brush_size': self.current_brush_size,
            'eraser_size': self.current_eraser_size,
        }
        try:
            with open(self.config_file, 'w') as f:
                json.dump(config, f, separators=(',', ':'))  # Compact JSON
        except Exception as e:
            print(f"Error saving config: {e}")
    
    def update_brush_size(self, value):
        """Update brush size with validation"""
        try:
            size = int(float(value))
            # MEMORY OPTIMIZATION: Only update if changed significantly
            if abs(size - self.current_brush_size) >= 1:
                self.brush_label.config(text=f"Current Size: {size}")
                self.current_brush_size = size
                if self.on_size_change_callback:
                    self.on_size_change_callback('brush', size)
        except (ValueError, TypeError) as e:
            print(f"Error updating brush size: {e}")
            
    def update_eraser_size(self, value):
        """Update eraser size with validation"""
        try:
            size = int(float(value))
            # MEMORY OPTIMIZATION: Only update if changed significantly
            if abs(size - self.current_eraser_size) >= 1:
                self.eraser_label.config(text=f"Current Size: {size}")
                self.current_eraser_size = size
                if self.on_size_change_callback:
                    self.on_size_change_callback('eraser', size)
        except (ValueError, TypeError) as e:
            print(f"Error updating eraser size: {e}")
    
    def apply_changes(self):
        """Apply changes and save configuration"""
        self.current_brush_size = self.brush_size.get()
        self.current_eraser_size = self.eraser_size.get()
        self.save_config()
        self.last_brush_size = self.current_brush_size
        self.last_eraser_size = self.current_eraser_size
    
    def set_size_change_callback(self, callback):
        """Set callback for size changes"""
        self.on_size_change_callback = callback
        
    def on_closing(self):
        """Handle window closing with cleanup"""
        # Restore last applied values before closing
        if self.on_size_change_callback:
            self.on_size_change_callback('brush', self.last_brush_size)
            self.on_size_change_callback('eraser', self.last_eraser_size)
        
        # MEMORY OPTIMIZATION: Cleanup resources
        self.cleanup()
        
    def cleanup(self):
        """Explicit cleanup to prevent memory leaks"""
        try:
            # Clear callbacks
            self.on_size_change_callback = None
            
            # Clear region data
            self.canvas_region = None
            
            # Destroy window
            if hasattr(self, 'window') and self.window:
                self.window.destroy()
                
            # Force garbage collection
            gc.collect()
            
        except Exception as e:
            print(f"Error during cleanup: {e}")
    
    def run(self):
        """Run the main loop"""
        try:
            self.window.mainloop()
        except Exception as e:
            print(f"Error running window: {e}")
        finally:
            self.cleanup()

if __name__ == "__main__":
    # Test the window independently
    app = SizeAdjustmentWindow()
    try:
        app.run()
    except KeyboardInterrupt:
        app.cleanup()
    except Exception as e:
        print(f"Test error: {e}")
        app.cleanup()