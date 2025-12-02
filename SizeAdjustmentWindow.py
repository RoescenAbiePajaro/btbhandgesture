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
import gc

class SizeAdjustmentWindow:
    def __init__(self):
        self.window = tk.Tk()
        self.window.title("Other Settings")
        self.window.geometry("400x500")
        self.window.resizable(False, False)
        self.window.minsize(400, 500)
        self.window.maxsize(400, 500)
        
        # Configure black theme
        self.window.configure(bg='#1a1a1a')
        
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
        
        # Create main container with padding and black background
        main_frame = ttk.Frame(self.window, padding="15 15 15 15")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Create frames for brush and eraser controls with dark theme
        brush_frame = ttk.LabelFrame(main_frame, text="Brush Size", padding="15")
        brush_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=8)
        
        eraser_frame = ttk.LabelFrame(main_frame, text="Eraser Size", padding="15")
        eraser_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=8)
        
        # Brush size controls
        self.brush_size = tk.IntVar(value=min(max(1, self.current_brush_size), 200))
        
        # Brush size label with better styling
        self.brush_label = ttk.Label(brush_frame, text=f"Current Size: {self.current_brush_size}", 
                                   font=('Helvetica', 11, 'bold'))
        self.brush_label.pack(pady=(0, 12))
        
        # Brush size slider with red styling
        self.brush_slider = ttk.Scale(
            brush_frame,
            from_=1,
            to=200,
            orient="horizontal",
            variable=self.brush_size,
            command=self.update_brush_size,
            length=320
        )
        self.brush_slider.pack(fill="x", padx=15, pady=8)
        
        # Brush size min/max labels
        brush_size_frame = ttk.Frame(brush_frame)
        brush_size_frame.pack(fill="x", padx=15)
        ttk.Label(brush_size_frame, text="1", font=('Helvetica', 9)).pack(side="left")
        ttk.Label(brush_size_frame, text="200", font=('Helvetica', 9)).pack(side="right")
        
        # Eraser size controls
        self.eraser_size = tk.IntVar(value=min(max(10, self.current_eraser_size), 200))
        
        # Eraser size label with better styling
        self.eraser_label = ttk.Label(eraser_frame, text=f"Current Size: {self.current_eraser_size}", 
                                     font=('Helvetica', 11, 'bold'))
        self.eraser_label.pack(pady=(0, 12))
        
        # Eraser size slider with red styling
        self.eraser_slider = ttk.Scale(
            eraser_frame,
            from_=10,
            to=200,
            orient="horizontal",
            variable=self.eraser_size,
            command=self.update_eraser_size,
            length=320
        )
        self.eraser_slider.pack(fill="x", padx=15, pady=8)
        
        # Eraser size min/max labels
        eraser_size_frame = ttk.Frame(eraser_frame)
        eraser_size_frame.pack(fill="x", padx=15)
        ttk.Label(eraser_size_frame, text="10", font=('Helvetica', 9)).pack(side="left")
        ttk.Label(eraser_size_frame, text="200", font=('Helvetica', 9)).pack(side="right")
        
        # Add screenshot buttons frame
        screenshot_frame = ttk.LabelFrame(main_frame, text="Screenshot", padding="15")
        screenshot_frame.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=8)
        
        # Circular screenshot button
        self.capture_all_btn = tk.Button(
            screenshot_frame,
            text="📸",
            command=self.capture_screen,
            bg="#FF4444",
            fg='white',
            font=('Helvetica', 16, 'bold'),
            width=4,
            height=2,
            cursor="hand2",
            activebackground="#FF6666",
            activeforeground='white',
            relief=tk.FLAT,
            bd=0,
            borderwidth=0,
            highlightthickness=0
        )
        self.capture_all_btn.pack(pady=10)
        
        # Screenshot label
        screenshot_label = ttk.Label(screenshot_frame, text="Take Screenshot", font=('Helvetica', 10))
        screenshot_label.pack(pady=(0, 5))
        
        # Add a separator
        separator = ttk.Separator(main_frame, orient='horizontal')
        separator.grid(row=3, column=0, sticky=(tk.W, tk.E), pady=15)
        
        # Add status label
        self.status_label = ttk.Label(main_frame, text="Ready", font=('Helvetica', 9), foreground='#888888')
        self.status_label.grid(row=4, column=0, sticky=(tk.W, tk.E), pady=5)
        
        # Apply custom dark theme styles with red accents
        self._configure_dark_red_styles()
        
        # Make window stay on top
        self.window.attributes('-topmost', True)
        
        # Handle window close
        self.window.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # MEMORY OPTIMIZATION: Track screenshot operations to prevent memory leaks
        self.last_screenshot_time = 0
        self.screenshot_cooldown = 2.0  # Prevent rapid screenshots

    def _configure_dark_red_styles(self):
        """Configure tkinter styles for dark theme with red accents"""
        style = ttk.Style()
        
        # Configure dark theme
        style.theme_use('clam')  # Use 'clam' theme as base for better customization
        
        # Configure colors for dark theme with red accents
        bg_color = '#1a1a1a'
        frame_bg = '#2d2d2d'
        text_color = '#ffffff'
        accent_color = '#FF4444'  # Red accent color
        slider_color = '#FF4444'  # Red sliders
        
        # Configure main styles
        style.configure('TFrame', background=bg_color)
        style.configure('TLabel', background=frame_bg, foreground=text_color, font=('Helvetica', 10))
        style.configure('TLabelframe', background=bg_color, foreground=text_color)
        style.configure('TLabelframe.Label', background=bg_color, foreground=text_color)
        
        # Configure slider styles with RED accents
        style.configure('Horizontal.TScale', 
                       background=frame_bg, 
                       troughcolor='#404040', 
                       sliderrelief='raised',
                       borderwidth=0,
                       lightcolor=accent_color,
                       darkcolor=accent_color)
        
        # Configure the slider thumb (scroll resize) as RED CIRCLE
        style.element_create('Custom.Horizontal.Scale.slider', 'from', 'clam')
        style.layout('Custom.Horizontal.TScale',
                   [('Horizontal.Scale.trough', {'sticky': 'ew', 'children':
                       [('Custom.Horizontal.Scale.slider', {'side': 'left', 'sticky': ''})]})])
        
        # Configure red circular slider thumb
        style.configure('Custom.Horizontal.TScale',
                       background=frame_bg,
                       troughcolor='#404040',
                       sliderrelief='flat',
                       bordercolor=accent_color,
                       lightcolor=accent_color,
                       darkcolor=accent_color,
                       sliderlength=20)  # Circular appearance
        
        style.map('TScale',
                 background=[('active', frame_bg)],
                 troughcolor=[('active', '#505050')],
                 slidercolor=[('active', accent_color), ('!active', accent_color)])
        
        # Configure button styles
        style.configure('TButton', 
                      background='#333333',
                      foreground=text_color,
                      borderwidth=1,
                      focusthickness=3,
                      focuscolor='none',
                      font=('Helvetica', 10))
        style.map('TButton',
                 background=[('active', '#404040'), ('pressed', '#505050')],
                 foreground=[('active', text_color), ('pressed', text_color)])
        
        # Configure labelframe styles
        style.configure('TLabelframe', 
                       background=bg_color,
                       bordercolor='#404040',
                       relief='solid',
                       borderwidth=1)
        style.configure('TLabelframe.Label', 
                       background=bg_color,
                       foreground=text_color)
        
        # Apply custom slider style
        self.brush_slider.configure(style='Custom.Horizontal.TScale')
        self.eraser_slider.configure(style='Custom.Horizontal.TScale')

    def _make_circular_button(self, button):
        """Make a button circular - called after window creation"""
        try:
            # This is a conceptual function - in practice, we create circular appearance
            # through styling and dimensions
            button.configure(
                relief='flat',
                borderwidth=0,
                highlightthickness=0,
                padx=10,
                pady=10
            )
        except Exception as e:
            print(f"Error making button circular: {e}")

    def capture_screen(self):
        """Capture screenshot with memory optimization"""
        current_time = time.time()
        if current_time - self.last_screenshot_time < self.screenshot_cooldown:
            self.status_label.config(text="Please wait before taking another screenshot")
            return  # Prevent rapid screenshots
            
        self.last_screenshot_time = current_time
        
        try:
            # Update status with red accent
            self.status_label.config(text="Capturing screenshot...", foreground='#FF4444')
            self.window.update()
            
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
                
                # Show success message
                self.status_label.config(text=f"Screenshot saved to Downloads folder", foreground='#4CAF50')
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
            self.status_label.config(text="Error capturing screenshot", foreground='#FF4444')
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
            self.status_label.config(text="Please wait before taking another screenshot")
            return
            
        self.last_screenshot_time = current_time
        
        if not self.canvas_region:
            messagebox.showwarning("Warning", "Canvas region not set")
            return
            
        try:
            self.status_label.config(text="Capturing canvas...", foreground='#FF4444')
            self.window.update()
            
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
                
                self.status_label.config(text="Canvas saved successfully", foreground='#4CAF50')
                messagebox.showinfo("Success", f"Canvas saved to:\n{save_path}")
                print(f"Canvas saved to: {save_path}")
                
            finally:
                if screenshot:
                    del screenshot
                    
        except Exception as e:
            print(f"Error capturing canvas: {str(e)}")
            self.status_label.config(text="Error capturing canvas", foreground='#FF4444')
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