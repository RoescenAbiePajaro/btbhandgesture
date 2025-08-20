import tkinter as tk
from tkinter import ttk
import json
import os

class SizeAdjustmentWindow:
    def __init__(self):
        self.window = tk.Tk()
        self.window.title("Size Adjustment")
        self.window.geometry("300x200")
        self.window.resizable(False, False)
        
        # Try to load last used sizes
        self.config_file = "size_config.json"
        self.load_config()
        
        # Create frames for brush and eraser controls
        brush_frame = ttk.LabelFrame(self.window, text="Brush Size", padding="5")
        brush_frame.pack(fill="x", padx=5, pady=5)
        
        eraser_frame = ttk.LabelFrame(self.window, text="Eraser Size", padding="5")
        eraser_frame.pack(fill="x", padx=5, pady=5)
        
        # Brush size controls
        self.brush_size = tk.IntVar(value=self.current_brush_size)
        self.brush_slider = ttk.Scale(
            brush_frame,
            from_=1,
            to=50,
            orient="horizontal",
            variable=self.brush_size,
            command=self.update_brush_size
        )
        self.brush_slider.pack(fill="x", padx=5)
        
        self.brush_label = ttk.Label(brush_frame, text=f"Size: {self.current_brush_size}")
        self.brush_label.pack()
        
        # Eraser size controls
        self.eraser_size = tk.IntVar(value=self.current_eraser_size)
        self.eraser_slider = ttk.Scale(
            eraser_frame,
            from_=10,
            to=200,
            orient="horizontal",
            variable=self.eraser_size,
            command=self.update_eraser_size
        )
        self.eraser_slider.pack(fill="x", padx=5)
        
        self.eraser_label = ttk.Label(eraser_frame, text=f"Size: {self.current_eraser_size}")
        self.eraser_label.pack()
        
        # Apply button
        self.apply_button = ttk.Button(
            self.window,
            text="Apply",
            command=self.apply_changes
        )
        self.apply_button.pack(pady=10)
        
        # Keep track of the last applied values
        self.last_brush_size = self.current_brush_size
        self.last_eraser_size = self.current_eraser_size
        
        # Initialize callback
        self.on_size_change_callback = None
        
        # Make window stay on top
        self.window.attributes('-topmost', True)
        
        # Handle window close
        self.window.protocol("WM_DELETE_WINDOW", self.on_closing)
        
    def load_config(self):
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    self.current_brush_size = config.get('brush_size', 10)
                    self.current_eraser_size = config.get('eraser_size', 100)
            else:
                self.current_brush_size = 10
                self.current_eraser_size = 100
        except:
            self.current_brush_size = 10
            self.current_eraser_size = 100
            
    def save_config(self):
        config = {
            'brush_size': self.current_brush_size,
            'eraser_size': self.current_eraser_size
        }
        try:
            with open(self.config_file, 'w') as f:
                json.dump(config, f)
        except Exception as e:
            print(f"Error saving config: {e}")
    
    def update_brush_size(self, value):
        size = int(float(value))
        self.brush_label.config(text=f"Size: {size}")
        if self.on_size_change_callback:
            self.on_size_change_callback('brush', size)
            
    def update_eraser_size(self, value):
        size = int(float(value))
        self.eraser_label.config(text=f"Size: {size}")
        if self.on_size_change_callback:
            self.on_size_change_callback('eraser', size)
    
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