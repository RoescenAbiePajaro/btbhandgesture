# VirtualPainter.py
import cv2
import numpy as np
import os
import time
import HandTrackingModule as htm
from tkinter import *
from PIL import Image, ImageTk
from KeyboardInput import KeyboardInput
import tkinter as tk
from tkinter import messagebox
import sys
import atexit
import threading
from SizeAdjustmentWindow import SizeAdjustmentWindow
import gc
import platform
import json
import base64
from datetime import datetime
from pymongo import MongoClient
import hashlib

# =============================================================================
# UNIVERSAL COMPATIBILITY SETTINGS
# =============================================================================

class UniversalCompatibility:
    def __init__(self):
        self.system_type = self.detect_system_type()
        self.settings = self.get_optimal_settings()
        print(f"Detected system: {self.system_type}")
        print(f"Optimal settings: {self.settings}")
    
    def detect_system_type(self):
        """Detect if system is low-end, medium, or high-end"""
        try:
            import psutil
            ram_gb = psutil.virtual_memory().total / (1024**3)
            cpu_cores = psutil.cpu_count()
            
            # Low-end: <4GB RAM or dual-core
            if ram_gb < 4 or cpu_cores <= 2:
                return "low_end"
            # Medium: 4-8GB RAM
            elif ram_gb < 8:
                return "medium"
            # High-end: 8GB+ RAM and quad-core+
            else:
                return "high_end"
        except:
            return "medium"  # Conservative default
    
    def get_optimal_settings(self):
        """Get settings optimized for detected system type"""
        base_settings = {
            "low_end": {
                "fps": 30,
                "width": 640,
                "height": 480,
                "detection_confidence": 0.6,
                "enable_animations": False,
                "frame_skip": 1,  # Process every other frame
                "hand_tracking_quality": "fast"
            },
            "medium": {
                "fps": 45,
                "width": 1024,
                "height": 576,
                "detection_confidence": 0.7,
                "enable_animations": True,
                "frame_skip": 0,
                "hand_tracking_quality": "balanced"
            },
            "high_end": {
                "fps": 60,
                "width": 1280,
                "height": 720,
                "detection_confidence": 0.8,
                "enable_animations": True,
                "frame_skip": 0,
                "hand_tracking_quality": "accurate"
            }
        }
        return base_settings[self.system_type]

# Initialize universal compatibility
compat = UniversalCompatibility()

# Apply optimal settings
fps = compat.settings['fps']
time_per_frame = 1.0 / fps

# =============================================================================
# MONGODB IMAGE SAVER
# =============================================================================

class ImageDatabaseSaver:
    """Handles saving images to MongoDB"""
    def __init__(self):
        self.client = None
        self.db = None
        self.collection = None
        self.user_data = None
        self.load_user_data()
        self.connect()
    
    def load_user_data(self):
        """Load user data from JSON file"""
        try:
            # Try multiple possible locations
            possible_paths = [
                "user_data.json",
                os.path.join(os.path.dirname(os.path.abspath(__file__)), "user_data.json"),
                os.path.join(os.path.expanduser("~"), "user_data.json")
            ]
            
            for path in possible_paths:
                if os.path.exists(path):
                    with open(path, "r") as f:
                        self.user_data = json.load(f)
                    print(f" User data loaded from: {path}")
                    print(f"  Email: {self.user_data.get('email', 'No email')}")
                    print(f"  Role: {self.user_data.get('role', 'No role')}")
                    return
            
            print(" No user_data.json found - images will be saved locally only")
            self.user_data = None
            
        except Exception as e:
            print(f" Error loading user data: {e}")
            self.user_data = None
    
    def connect(self):
        """Connect to MongoDB"""
        try:
            mongodb_uri = "mongodb+srv://202211504:APoiboNwZGFYm9cQ@cluster0.eeyewov.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
            self.client = MongoClient(mongodb_uri)
            self.db = self.client.test  # Your database name
            self.collection = self.db.save_uploads  # Your collection name
            print(" Connected to MongoDB for image saving")
            
            # Test connection
            test_doc = {
                "test": "connection",
                "timestamp": datetime.utcnow()
            }
            result = self.collection.insert_one(test_doc)
            print(f" Test document inserted with ID: {result.inserted_id}")
            
            # Clean up test document
            self.collection.delete_one({"_id": result.inserted_id})
            print(" Test document cleaned up")
            
            return True
        except Exception as e:
            print(f" MongoDB connection failed: {e}")
            self.client = None
            return False
    
    def save_image_to_db(self, image_path, image_data=None):
        """Save image to MongoDB save_uploads collection"""
        if not self.client or not self.user_data:
            print(" Cannot save to DB: No connection or user data")
            return {"success": False, "message": "No database connection or user data"}
        
        try:
            # Read image if data not provided
            if image_data is None:
                with open(image_path, 'rb') as f:
                    image_data = f.read()
            
            # Convert to base64
            image_base64 = base64.b64encode(image_data).decode('utf-8')
            
            # Get file info
            file_size = len(image_data)
            file_name = os.path.basename(image_path)
            
            # Create document matching your MongoDB schema
            upload_doc = {
                "user_email": self.user_data.get('email', '').lower().strip(),
                "user_role": self.user_data.get('role', 'student'),
                "full_name": self.user_data.get('fullName', ''),
                "file_name": file_name,
                "file_path": image_path,
                "file_size": file_size,
                "image_data": image_base64,
                "upload_date": datetime.utcnow(),
                "timestamp": time.time(),
                "app_name": "Beyond The Brush",
                "version": "1.0.0"
            }
            
            print(f" Attempting to save image to MongoDB...")
            print(f"   User: {upload_doc['user_email']}")
            print(f"   Role: {upload_doc['user_role']}")
            print(f"   File: {upload_doc['file_name']}")
            print(f"   Size: {upload_doc['file_size']} bytes")
            
            # Insert into save_uploads collection
            result = self.collection.insert_one(upload_doc)
            
            print(f" Image saved to MongoDB. Document ID: {result.inserted_id}")
            return {
                "success": True,
                "message": "Image saved to database",
                "document_id": str(result.inserted_id)
            }
            
        except Exception as e:
            print(f" Error saving image to database: {e}")
            import traceback
            traceback.print_exc()
            return {"success": False, "message": f"Database save failed: {str(e)}"}
    
    def close(self):
        """Close MongoDB connection"""
        if self.client:
            self.client.close()
            print(" MongoDB connection closed")
            self.client.close()

# Initialize MongoDB saver
db_saver = ImageDatabaseSaver()

# =============================================================================
# UNIVERSAL CAMERA SYSTEM
# =============================================================================

def find_working_camera_universal():
    """Universal camera detection that works on ALL devices and camera types"""
    
    # Camera detection strategies for different platforms
    platform_strategies = {
        'windows': [
            (cv2.CAP_DSHOW, "DirectShow (Windows USB/Built-in)"),
            (cv2.CAP_MSMF, "Media Foundation (Windows)"),
        ],
        'linux': [
            (cv2.CAP_V4L2, "Video4Linux (Linux USB/Built-in)"),
        ],
        'darwin': [  # macOS
            (cv2.CAP_AVFOUNDATION, "AVFoundation (macOS)"),
        ]
    }
    
    current_platform = platform.system().lower()
    strategies = platform_strategies.get(current_platform, [(cv2.CAP_ANY, "Auto-detect")])
    
    print("Scanning for cameras...")
    
    # Try different strategies
    for backend, backend_name in strategies:
        print(f"Trying {backend_name}...")
        
        for camera_index in range(5):  # Check first 5 camera indices
            try:
                cap = cv2.VideoCapture(camera_index, backend)
                
                if cap.isOpened():
                    # Test if camera can actually read frames
                    ret, frame = cap.read()
                    if ret and frame is not None:
                        print(f"✅ Found working camera: Index {camera_index} with {backend_name}")
                        
                        # Apply optimal resolution
                        target_width = compat.settings['width']
                        target_height = compat.settings['height']
                        
                        # Try to set resolution (not all cameras support this)
                        cap.set(cv2.CAP_PROP_FRAME_WIDTH, target_width)
                        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, target_height)
                        
                        # Set buffer size to prevent lag
                        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                        cap.set(cv2.CAP_PROP_FPS, compat.settings['fps'])
                        
                        # Verify actual resolution
                        actual_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                        actual_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                        print(f"Camera resolution: {actual_width}x{actual_height}")
                        
                        return cap
                    else:
                        cap.release()
            except Exception as e:
                print(f"Camera {camera_index} with {backend_name} failed: {e}")
                continue
    
    # Final fallback: try without specific backend
    print("Trying fallback camera detection...")
    for camera_index in range(5):
        try:
            cap = cv2.VideoCapture(camera_index)
            if cap.isOpened():
                ret, frame = cap.read()
                if ret:
                    print(f"✅ Using fallback camera at index {camera_index}")
                    return cap
                cap.release()
        except:
            continue
    
    # If no camera found, provide helpful error message
    error_msg = """
❌ No working camera found!

Troubleshooting tips:
1. Make sure your camera is connected and not being used by another app
2. For USB cameras: try unplugging and reconnecting
3. Check camera permissions in system settings
4. Try a different USB port
5. Restart your computer if camera was recently connected

Supported cameras:
• Built-in laptop cameras
• USB webcams (Logitech, etc.)
• External USB cameras
• Most desktop cameras
"""
    raise Exception(error_msg)

# =============================================================================
# RESOURCE PATH HELPER
# =============================================================================

def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    
    return os.path.join(base_path, relative_path)

# =============================================================================
# ICON AND IMAGE LOADING (FIXED)
# =============================================================================

# Initialize variables
brushSize = 10
eraserSize = 100
overlayList = []
guideList = []
header = None
current_guide_index = 0
current_guide = None
show_guide = False

# Get the base path for resources
if getattr(sys, 'frozen', False):
    basePath = sys._MEIPASS
else:
    basePath = os.path.dirname(os.path.abspath(__file__))

print(f"Base path for resources: {basePath}")

# Load header images - KEEP ORIGINAL 1280x78 SIZE for icons to work properly
folderPath = os.path.join(basePath, 'header')
if os.path.exists(folderPath) and os.path.isdir(folderPath):
    try:
        myList = sorted(os.listdir(folderPath))
        print(f"Found {len(myList)} header images")
        
        for imPath in myList:
            img_path = os.path.join(folderPath, imPath)
            print(f"Loading header image: {img_path}")
            img = cv2.imread(img_path)
            if img is not None:
                # KEEP ORIGINAL SIZE 1280x78 for proper icon alignment
                img = cv2.resize(img, (1280, 78))
                overlayList.append(img)
                print(f"Successfully loaded: {imPath}")
            else:
                print(f"Warning: Failed to load header image: {imPath}")

        if overlayList:
            header = overlayList[0]
            print("Header images loaded successfully")
        else:
            print(f"Warning: No valid header images found in {folderPath}")
    except Exception as e:
        print(f"Error loading header images: {e}")
        import traceback
        traceback.print_exc()
else:
    print(f"Warning: Header folder not found: {folderPath}")

# Load guide images with adaptive sizing
folderPath = os.path.join(basePath, 'guide')
if os.path.exists(folderPath) and os.path.isdir(folderPath):
    try:
        myList = sorted(os.listdir(folderPath))
        print(f"Found {len(myList)} guide images")
        
        for imPath in myList:
            img_path = os.path.join(folderPath, imPath)
            img = cv2.imread(img_path)
            if img is not None:
                # Resize guide images to fit below header
                guide_height = compat.settings['height'] - 78
                img = cv2.resize(img, (compat.settings['width'], guide_height))
                guideList.append(img)
            else:
                print(f"Warning: Failed to load guide image: {imPath}")

        if guideList:
            current_guide_index = 0
            current_guide = guideList[current_guide_index]
            print("Guide images loaded successfully")
    except Exception as e:
        print(f"Error loading guide images: {e}")

# Swipe detection variables
swipe_threshold = 50
swipe_start_x = None
swipe_active = False

# Default drawing color
drawColor = (255, 0, 255)

# =============================================================================
# CAMERA INITIALIZATION
# =============================================================================

try:
    cap = find_working_camera_universal()
except Exception as e:
    print(f"Error initializing camera: {e}")
    # Show user-friendly error message
    if "No working camera found" in str(e):
        messagebox.showerror("Camera Error", 
            "No camera detected!\n\n"
            "Please ensure your camera is connected and not being used by another application.\n\n"
            "Supported cameras:\n"
            "• Built-in laptop cameras\n"
            "• USB webcams\n"
            "• External USB cameras")
    exit(1)

# =============================================================================
# HAND DETECTOR WITH ADAPTIVE SETTINGS
# =============================================================================

# Optimize hand detection based on system capability
detection_config = {
    "low_end": {"detectionCon": 0.6, "trackCon": 0.4, "maxHands": 1},
    "medium": {"detectionCon": 0.7, "trackCon": 0.5, "maxHands": 1},
    "high_end": {"detectionCon": 0.8, "trackCon": 0.6, "maxHands": 1}
}

config = detection_config[compat.system_type]
detector = htm.HandDetector(
    detectionCon=config['detectionCon'],
    trackCon=config['trackCon'],  
    maxHands=config['maxHands']
)

# =============================================================================
# CANVAS AND STATE MANAGEMENT
# =============================================================================

# Create Image Canvas with adaptive size but maintain header area
imgCanvas = np.zeros((compat.settings['height'], compat.settings['width'], 3), np.uint8)

# Previous points
xp, yp = 0, 0

# Undo/Redo Stack
undoStack = []
redoStack = []
MAX_UNDO_STACK_SIZE = 30  # Reduced for low-end systems

# Create keyboard input handler
keyboard_input = KeyboardInput()
last_time = time.time()

# Create size adjuster window
size_adjuster = SizeAdjustmentWindow()

# =============================================================================
# CORE FUNCTIONS (Optimized for performance)
# =============================================================================

def save_state():
    """Save current state with memory optimization"""
    if len(undoStack) >= MAX_UNDO_STACK_SIZE:
        old_state = undoStack.pop(0)
        del old_state
    
    return {
        'canvas': imgCanvas.copy(),
        'text_objects': keyboard_input.text_objects.copy()
    }

def restore_state(state):
    global imgCanvas
    imgCanvas = state['canvas'].copy()
    keyboard_input.text_objects = state['text_objects'].copy()

def show_transient_notification(message, duration=1.0):
    global notification_text, notification_time
    notification_text = message
    notification_time = time.time() + duration

def optimize_memory_usage():
    """Aggressive memory optimization for low-end systems"""
    if compat.system_type == "low_end":
        # Force garbage collection
        gc.collect()

def cleanup_resources():
    """Enhanced cleanup for all system types"""
    global cap, detector, keyboard_input, size_adjuster, overlayList, guideList, undoStack, redoStack
    
    print("Cleaning up resources...")
    
    # Close MongoDB connection
    if 'db_saver' in globals() and db_saver is not None:
        try:
            db_saver.close()
        except:
            pass
    
    # Release camera
    try:
        if 'cap' in globals() and cap is not None:
            cap.release()
    except Exception as e:
        print(f"Error releasing camera: {e}")
    
    # Close OpenCV windows
    try:
        cv2.destroyAllWindows()
    except:
        pass
    
    # Clean up tkinter windows
    try:
        if 'size_adjuster' in globals() and size_adjuster is not None:
            if hasattr(size_adjuster, 'window') and size_adjuster.window:
                try:
                    size_adjuster.window.after(100, size_adjuster.window.destroy())
                except:
                    pass
    except Exception as e:
        print(f"Error cleaning up tkinter windows: {e}")
    
    # Clear large data structures
    try:
        if 'overlayList' in globals():
            overlayList.clear()
        if 'guideList' in globals():
            guideList.clear()
        if 'undoStack' in globals():
            undoStack.clear()
        if 'redoStack' in globals():
            redoStack.clear()
    except Exception as e:
        print(f"Error clearing data structures: {e}")
    
    # Force garbage collection
    gc.collect()

def save_to_template(canvas_img):
    """Save the drawing onto the template image"""
    try:
        # Load the template image
        template_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Beyond The Brush Template.png")
        if not os.path.exists(template_path):
            print("Template image not found!")
            return None
            
        # Read template and canvas images
        template = cv2.imread(template_path)
        if template is None:
            print("Failed to load template image!")
            return None
            
        # Resize canvas to match template dimensions if needed
        if canvas_img.shape != template.shape[:2]:
            canvas_img = cv2.resize(canvas_img, (template.shape[1], template.shape[0]))
            
        # Create a mask where the white background is
        _, mask = cv2.threshold(cv2.cvtColor(canvas_img, cv2.COLOR_BGR2GRAY), 250, 255, cv2.THRESH_BINARY_INV)
        
        # Invert the mask to get the non-white areas
        mask_inv = cv2.bitwise_not(mask)
        
        # Extract the drawing (non-white parts of canvas)
        drawing = cv2.bitwise_and(canvas_img, canvas_img, mask=mask)
        
        # Extract the template background (white parts of canvas)
        template_bg = cv2.bitwise_and(template, template, mask=mask_inv)
        
        # Combine the template background with the drawing
        result = cv2.add(template_bg, drawing)
        
        # Save the result to beyondthebrush_app_saved_canvas folder
        download_folder = os.path.join(os.path.expanduser("~"), "Downloads", "beyondthebrush_app_saved_canvas")
        os.makedirs(download_folder, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = os.path.join(download_folder, f"beyond_the_brush_{timestamp}.png")
        cv2.imwrite(output_path, result)
        print(f"Drawing saved to {output_path}")
        return output_path
        
    except Exception as e:
        print(f"Error saving to template: {e}")
        return None

def btb_saved_canvas_async():
    """Save canvas with compatibility optimizations, save to template, and optionally to MongoDB"""
    global notification_text, notification_time
    
    try:
        # Create white canvas
        saved_img = np.ones_like(imgCanvas) * 255
        
        # Copy non-black pixels
        mask = imgCanvas.any(axis=2)
        saved_img[mask] = imgCanvas[mask]

        # Draw text objects
        for obj in keyboard_input.text_objects:
            if obj['position'][1] > 78:  # Only draw text below header
                cv2.putText(saved_img, obj['text'], obj['position'],
                          obj['font'], obj['scale'], (0, 0, 0), obj['thickness'] + 2)
                cv2.putText(saved_img, obj['text'], obj['position'],
                          obj['font'], obj['scale'], obj['color'], obj['thickness'])

        # Define target dimensions
        target_width = compat.settings['width']
        target_height = compat.settings['height'] - 60  # Account for header
        header_height = 78
        
        final_img = np.ones((target_height, target_width, 3), dtype=np.uint8) * 255
        
        src_y_start = header_height
        src_height = min(target_height, saved_img.shape[0] - header_height)
        
        final_img[0:src_height, 0:target_width] = saved_img[src_y_start:src_y_start+src_height, 0:target_width]
        
        # Save to template (this will be the only version saved)
        template_path = save_to_template(final_img)
        success = template_path is not None and os.path.exists(template_path)
        
        # Save to MongoDB in background
        mongo_success = False
        mongo_message = ""
        
        if db_saver.user_data and template_path:
            try:
                # Save only the template version to MongoDB
                with open(template_path, 'rb') as template_file:
                    template_data = template_file.read()
                result = db_saver.save_image_to_db(template_path, template_data)
                
                # Check result
                if result.get("success", False):
                    mongo_success = True
                    doc_id = result.get("document_id", "")[:8]  # First 8 chars of ID
                    mongo_message = f" (DB ID: {doc_id}...)"
                    print(f"Image saved to MongoDB with ID: {result.get('document_id', '')}")
                else:
                    mongo_message = f" (DB save failed: {result.get('message', 'Unknown error')})"
                    print(f"MongoDB save failed: {result.get('message', 'Unknown error')}")
                    
            except Exception as mongo_error:
                mongo_message = f" (DB error: {str(mongo_error)})"
                print(f"MongoDB save error: {mongo_error}")
        else:
            mongo_message = " (No user logged in - local save only)"
            print("No user data - saving locally only")
        
        # Clean up
        del saved_img, final_img
        
        if success:
            if mongo_success:
                notification_text = f"Image Saved to Database!{mongo_message}"
            else:
                notification_text = f"Image Saved Locally{mongo_message}"
            notification_time = time.time() + 3.0
            print(f"Drawing saved to: {template_path}")
        else:
            raise Exception("cv2.imwrite returned False")
        
    except Exception as e:
        print(f"Error saving canvas: {str(e)}")
        notification_text = f"Error saving image: {str(e)}"
        notification_time = time.time() + 3.0
    finally:
        gc.collect()

def btb_saved_canvas():
    save_thread = threading.Thread(target=btb_saved_canvas_async)
    save_thread.daemon = True
    save_thread.start()

def interpolate_points(x1, y1, x2, y2, num_points=5):  # Reduced points for performance
    points = []
    for i in range(num_points):
        x = int(x1 + (x2 - x1) * (i / num_points))
        y = int(y1 + (y2 - y1) * (i / num_points))
        points.append((x, y))
    return points

# =============================================================================
# HEADER ICON MANAGEMENT (FIXED)
# =============================================================================

def get_header_for_resolution():
    """Get properly scaled header for current resolution"""
    if header is None:
        return None
    
    # Scale header to match current width while maintaining aspect ratio
    current_width = compat.settings['width']
    if current_width != 1280:  # Only resize if different from original
        scale_factor = current_width / 1280.0
        new_width = current_width
        new_height = int(78 * scale_factor)  # Maintain aspect ratio
        return cv2.resize(header, (new_width, new_height))
    else:
        return header

def get_button_boundaries():
    """Calculate button boundaries based on current resolution"""
    button_width = compat.settings['width'] // 10  # 10 buttons across
    boundaries = []
    for i in range(10):
        start_x = i * button_width
        end_x = (i + 1) * button_width
        boundaries.append((start_x, end_x))
    return boundaries

# =============================================================================
# MAIN APPLICATION LOOP (Optimized with Fixed Icons)
# =============================================================================

# Global flags
is_closing = False
running = True
last_save_time = 0
SAVE_COOLDOWN = 1.0
notification_text = ""
notification_time = 0
frame_count = 0

def on_close():
    global running, is_closing
    if is_closing:
        return
        
    is_closing = True
    running = False
    
    try:
        print("Closing application, please wait...")
        cleanup_resources()
    except Exception as e:
        print(f"Error during close: {e}")
    finally:
        import threading
        def force_exit():
            import os
            import time
            time.sleep(1)
            os._exit(0)
            
        threading.Thread(target=force_exit, daemon=True).start()
        sys.exit(0)

def on_window_close(event=None):
    on_close()

def handle_size_change(tool_type, size):
    global brushSize, eraserSize
    if tool_type == 'brush':
        brushSize = size
    else:
        eraserSize = size

# Set the callback
size_adjuster.set_size_change_callback(handle_size_change)

# Register cleanup function
atexit.register(cleanup_resources)

# Call memory optimization
optimize_memory_usage()

# Main Loop
try:
    # Create window with adaptive size
    window_name = "Beyond The Brush"
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(window_name, compat.settings['width'], compat.settings['height'])
    cv2.setWindowProperty(window_name, cv2.WND_PROP_TOPMOST, 0)
    
    # Set window icon (Windows)
    try:
        if sys.platform.startswith('win'):
            icon_path = resource_path(os.path.join('icon', 'app.ico'))
            if os.path.exists(icon_path):
                import ctypes
                hwnd = ctypes.windll.user32.FindWindowW(None, "Beyond The Brush")
                if hwnd:
                    # Load the icon
                    ICON_SMALL = 0
                    ICON_BIG = 1
                    icon_handle = ctypes.windll.user32.LoadImageW(0, icon_path, 1, 0, 0, 0x00000010)
                    if icon_handle:
                        ctypes.windll.user32.SendMessageW(hwnd, 0x80, ICON_SMALL, icon_handle)
                        ctypes.windll.user32.SendMessageW(hwnd, 0x80, ICON_BIG, icon_handle)
    except Exception as e:
        print(f"Could not set window icon: {e}")
    
    # Performance monitoring
    frame_skip_counter = 0
    frames_to_skip = compat.settings['frame_skip']
    
    while running:
        start_time = time.time()
        frame_count += 1
        frame_skip_counter += 1

        # Frame skipping for low-end systems
        if frame_skip_counter <= frames_to_skip:
            # Still process some essential operations
            try:
                key = cv2.waitKey(1) & 0xFF
                if key == 27:  # ESC key
                    on_close()
                    break
            except:
                pass
            continue
        frame_skip_counter = 0

        # 1. Import Image
        success, img = cap.read()
        if not success:
            print("Failed to capture image from camera")
            # Try to reinitialize camera
            try:
                cap.release()
                time.sleep(0.1)
                cap = find_working_camera_universal()
                continue
            except:
                print("Could not reinitialize camera")
                break

        # Flip the image horizontally for mirror effect
        img = cv2.flip(img, 1)

        # 2. Find Hand Landmarks (with performance optimization)
        if compat.system_type == "low_end":
            # Reduce processing for low-end systems
            img_small = cv2.resize(img, (320, 240))
            img_small = detector.findHands(img_small, draw=False)
            lmList = detector.findPosition(img_small, draw=False)
            # Scale coordinates back to original size
            if lmList:
                scale_x = compat.settings['width'] / 320
                scale_y = compat.settings['height'] / 240
                for lm in lmList:
                    lm[1] = int(lm[1] * scale_x)
                    lm[2] = int(lm[2] * scale_y)
        else:
            img = detector.findHands(img, draw=False)
            lmList = detector.findPosition(img, draw=False)
        
        # Reset smoothing if no hand detected
        if not lmList or len(lmList) < 21:
            detector.reset_smoothing()

        # Position notification below header
        notification_y = 110
        
        # Draw mode indicator
        cv2.putText(img, "Selection Mode - Two Fingers Up", (compat.settings['width'] - 400, notification_y),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 4)
        cv2.putText(img, "Selection Mode - Two Fingers Up", (compat.settings['width'] - 400, notification_y),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

        # Check if lmList is empty or doesn't have enough landmarks before proceeding
        if lmList and len(lmList) >= 21:
            # Tip of index and middle fingers
            x1, y1 = lmList[8][1:]
            x2, y2 = lmList[12][1:]

            # 3. Check which fingers are up
            fingers = detector.fingersUp()

            # 4. Selection Mode - Two Fingers Up
            if fingers[1] and fingers[2]:
                xp, yp = 0, 0  # Reset points
                swipe_start_x = None  # Reset swipe tracking when in selection mode

                # Get button boundaries for current resolution
                button_boundaries = get_button_boundaries()
                
                # Detecting selection based on X coordinate
                if y1 < 78:  # Header area
                    current_header = get_header_for_resolution()
                    header_height = current_header.shape[0] if current_header is not None else 78
                    
                    # Scale y1 coordinate for header detection
                    scaled_y1 = y1
                    if current_header is not None and current_header.shape[0] != 78:
                        scale_factor = current_header.shape[0] / 78.0
                        scaled_y1 = int(y1 * scale_factor)
                    
                    if scaled_y1 < header_height:
                        # Check each button area
                        for i, (start_x, end_x) in enumerate(button_boundaries):
                            if start_x < x1 < end_x:
                                # Button clicked - handle based on button index
                                if i == 0:  # Save
                                    current_time = time.time()
                                    if current_time - last_save_time > SAVE_COOLDOWN:
                                        if len(overlayList) > 1:
                                            header = overlayList[1]
                                        btb_saved_canvas_async()
                                        last_save_time = current_time
                                        show_guide = False
                                        cv2.putText(img, "Saving...", (50, notification_y),
                                                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 4)
                                        cv2.putText(img, "Saving...", (50, notification_y),
                                                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

                                elif i == 1:  # Dark Gray
                                    if len(overlayList) > 2:
                                        header = overlayList[2]
                                    drawColor = (64, 64, 64)
                                    cv2.putText(img, "Dark Gray brush selected", (50, notification_y),
                                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 4)
                                    cv2.putText(img, "Dark Gray brush selected", (50, notification_y),
                                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)
                                    show_guide = False
                                    keyboard_input.active = False

                                elif i == 2:  # Blue
                                    if len(overlayList) > 3:
                                        header = overlayList[3]
                                    drawColor = (255, 0, 0)
                                    cv2.putText(img, "Blue brush selected", (50, notification_y),
                                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 4)
                                    cv2.putText(img, "Blue brush selected", (50, notification_y),
                                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                                    show_guide = False
                                    keyboard_input.active = False

                                elif i == 3:  # Green
                                    if len(overlayList) > 4:
                                        header = overlayList[4]
                                    drawColor = (0, 255, 0)
                                    cv2.putText(img, "Green brush selected", (50, notification_y),
                                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 4)
                                    cv2.putText(img, "Green brush selected", (50, notification_y),
                                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                                    show_guide = False
                                    keyboard_input.active = False

                                elif i == 4:  # Yellow
                                    if len(overlayList) > 5:
                                        header = overlayList[5]
                                    drawColor = (0, 255, 255)
                                    cv2.putText(img, "Yellow brush selected", (50, notification_y),
                                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 4)
                                    cv2.putText(img, "Yellow brush selected", (50, notification_y),
                                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                                    show_guide = False
                                    keyboard_input.active = False

                                elif i == 5:  # Eraser
                                    if len(overlayList) > 6:
                                        header = overlayList[6]
                                    drawColor = (0, 0, 0)
                                    cv2.putText(img, "Eraser selected", (50, notification_y),
                                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 4)
                                    cv2.putText(img, "Eraser selected", (50, notification_y),
                                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                                    show_guide = False
                                    keyboard_input.active = False
                                    keyboard_input.delete_selected()

                                elif i == 6:  # Undo
                                    if len(overlayList) > 7:
                                        header = overlayList[7]
                                    else:
                                        header = overlayList[0] if overlayList else None
                                    if len(undoStack) > 0:
                                        redoStack.append(save_state())
                                        state = undoStack.pop()
                                        restore_state(state)
                                        cv2.putText(img, "Undo", (50, notification_y),
                                                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 4)
                                        cv2.putText(img, "Undo", (50, notification_y),
                                                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                                    else:
                                        cv2.putText(img, "Nothing to undo", (50, notification_y),
                                                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 4)
                                        cv2.putText(img, "Nothing to undo", (50, notification_y),
                                                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                                    show_guide = False

                                elif i == 7:  # Redo
                                    if len(overlayList) > 8:
                                        header = overlayList[8]
                                    if len(redoStack) > 0:
                                        undoStack.append(save_state())
                                        state = redoStack.pop()
                                        restore_state(state)
                                        cv2.putText(img, "Redo", (50, notification_y),
                                                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 4)
                                        cv2.putText(img, "Redo", (50, notification_y),
                                                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                                    else:
                                        cv2.putText(img, "Nothing to redo", (50, notification_y),
                                                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 4)
                                        cv2.putText(img, "Nothing to redo", (50, notification_y),
                                                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                                    show_guide = False

                                elif i == 8:  # Guide
                                    if len(overlayList) > 9:
                                        header = overlayList[9]
                                    cv2.putText(img, "Guide selected", (50, notification_y),
                                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 4)
                                    cv2.putText(img, "Guide selected", (50, notification_y),
                                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                                    show_guide = True
                                    if guideList:
                                        current_guide_index = 0
                                        current_guide = guideList[current_guide_index]
                                    keyboard_input.active = False

                                elif i == 9:  # Keyboard
                                    if not keyboard_input.active:
                                        keyboard_input.active = True
                                        cv2.putText(img, "Keyboard Mode Opened", (50, notification_y),
                                                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 4)
                                        cv2.putText(img, "Keyboard Mode Opened", (50, notification_y),
                                                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                                    if len(overlayList) > 10:
                                        header = overlayList[10]
                                    show_guide = False

                                break

                # Show selection rectangle
                cv2.rectangle(img, (x1, y1 - 25), (x2, y2 + 25), drawColor, cv2.FILLED)

        # ==================== HAND GESTURE LOGIC ====================
            # GUIDE NAVIGATION MODE - One index finger, guide visible, keyboard not active
            if fingers[1] and not fingers[2] and show_guide and not keyboard_input.active:
                # Start or continue swipe gesture
                if swipe_start_x is None:
                    swipe_start_x = x1
                    swipe_active = True

                # Calculate swipe distance
                if swipe_start_x is not None:
                    delta_x = x1 - swipe_start_x
                    
                    # Check if swipe threshold is crossed
                    if abs(delta_x) > swipe_threshold and swipe_active and guideList:
                        if delta_x > 0:
                            current_guide_index = max(0, current_guide_index - 1)
                        else:
                            current_guide_index = min(len(guideList) - 1, current_guide_index + 1)

                        if 0 <= current_guide_index < len(guideList):
                            current_guide = guideList[current_guide_index]
                            show_transient_notification(f"Guide {current_guide_index + 1}/{len(guideList)}")
                        swipe_start_x = x1
                        swipe_active = False

                # Enhanced visual feedback for guide cursor
                cursor_radius = 20
                cv2.circle(img, (x1, y1), cursor_radius + 5, (0, 255, 0, 50), 2)
                cv2.circle(img, (x1, y1), cursor_radius, (0, 255, 0), cv2.FILLED)
                cv2.circle(img, (x1, y1), 3, (0, 0, 0), cv2.FILLED)
                
                # Show current guide number
                guide_text = f"Guide: {current_guide_index + 1}/{len(guideList)}"
                text_size = cv2.getTextSize(guide_text, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)[0]
                text_x = max(10, min(x1 - text_size[0] // 2, compat.settings['width'] - text_size[0] - 10))
                text_y = max(30, y1 - cursor_radius - 10)
                
                cv2.rectangle(img, (text_x - 5, text_y - 25), (text_x + text_size[0] + 5, text_y + 5), (0, 0, 0), -1)
                cv2.putText(img, guide_text, (text_x, text_y), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

            # DRAWING MODE - One index finger, guide hidden, keyboard not active
            elif fingers[1] and not fingers[2] and not show_guide and not keyboard_input.active:
                swipe_start_x = None

                # Eraser: Check for overlapping with existing text
                if drawColor == (0, 0, 0):
                    for i, obj in enumerate(reversed(keyboard_input.text_objects)):
                        idx = len(keyboard_input.text_objects) - 1 - i
                        text_size = cv2.getTextSize(obj['text'], obj['font'], obj['scale'], obj['thickness'])[0]
                        x_text, y_text = obj['position']
                        if (x_text <= x1 <= x_text + text_size[0] and
                                y_text - text_size[1] <= y1 <= y_text):
                            del keyboard_input.text_objects[idx]
                            break

                # Visual feedback
                cv2.circle(img, (x1, y1), 15, drawColor, cv2.FILLED)

                if xp == 0 and yp == 0:
                    xp, yp = x1, y1

                # Smooth drawing
                points = interpolate_points(xp, yp, x1, y1)
                for point in points:
                    if drawColor == (0, 0, 0):  # eraser
                        half_size = eraserSize // 2
                        top_left = (point[0] - half_size, point[1] - half_size)
                        bottom_right = (point[0] + half_size, point[1] + half_size)
                        cv2.rectangle(img, top_left, bottom_right, drawColor, -1)
                        cv2.rectangle(imgCanvas, top_left, bottom_right, drawColor, -1)
                    else:
                        cv2.line(img, (xp, yp), point, drawColor, brushSize)
                        cv2.line(imgCanvas, (xp, yp), point, drawColor, brushSize)
                    xp, yp = point

                # Update undo/redo stacks
                if len(undoStack) >= MAX_UNDO_STACK_SIZE:
                    undoStack.pop(0)
                undoStack.append(save_state())
                redoStack.clear()

            # TEXT DRAGGING MODE - Two fingers, keyboard active
            elif keyboard_input.active and fingers[1] and fingers[2]:
                center_x = (x1 + x2) // 2
                center_y = (y1 + y2) // 2

                if not keyboard_input.dragging:
                    if keyboard_input.text or keyboard_input.cursor_visible:
                        keyboard_input.check_drag_start(center_x, center_y)
                else:
                    keyboard_input.update_drag(center_x, center_y)

                cv2.circle(img, (center_x, center_y), 15, (0, 255, 255), cv2.FILLED)

            else:
                # Reset states
                xp, yp = 0, 0
                swipe_start_x = None
                swipe_active = False
                if keyboard_input.dragging:
                    keyboard_input.end_drag()

        else:
            # No hand detected
            xp, yp = 0, 0
            swipe_start_x = None
            swipe_active = False
            if keyboard_input.dragging:
                keyboard_input.end_drag()

        # Handle keyboard input
        current_time = time.time()
        dt = current_time - last_time
        last_time = current_time
        keyboard_input.update(dt)

        # Check for keyboard input
        try:
            key = cv2.waitKey(1) & 0xFF
            if keyboard_input.process_key_input(key):
                if len(undoStack) >= MAX_UNDO_STACK_SIZE:
                    undoStack.pop(0)
                undoStack.append(save_state())
                redoStack.clear()
        except KeyboardInterrupt:
            print("Program terminated by user")
            on_close()

        # 8. Blend the drawing canvas with the camera feed
        mask = cv2.cvtColor(cv2.cvtColor(imgCanvas, cv2.COLOR_BGR2GRAY), cv2.COLOR_GRAY2BGR)
        mask = (mask > 0).astype(np.uint8) * 255
        img = cv2.bitwise_and(img, 255 - mask)
        img = cv2.add(img, imgCanvas)

        # 9. Set Header Image (FIXED - Icons will now display properly)
        current_header = get_header_for_resolution()
        if current_header is not None:
            header_height = current_header.shape[0]
            # Make sure we don't exceed image bounds
            if header_height <= img.shape[0] and current_header.shape[1] <= img.shape[1]:
                img[0:header_height, 0:current_header.shape[1]] = current_header

        # 10. Draw keyboard text and placeholder
        if keyboard_input.active:
            typing_area = np.zeros((100, compat.settings['width'], 3), dtype=np.uint8)
            typing_area[:] = (50, 50, 50)
            img[compat.settings['height']-100:compat.settings['height'], 0:compat.settings['width']] = cv2.addWeighted(
                img[compat.settings['height']-100:compat.settings['height'], 0:compat.settings['width']], 0.7, typing_area, 0.3, 0)

            keyboard_input.draw(img)

            instruction_text = "Press Enter to confirm text, ESC to cancel"
            cv2.putText(img, instruction_text, (20, compat.settings['height'] - 20),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
        else:
            keyboard_input.draw(img)

        # 11. Display Guide Image if active
        if show_guide and current_guide is not None:
            header_height = get_header_for_resolution().shape[0] if get_header_for_resolution() is not None else 78
            guide_area = img[header_height:compat.settings['height'], 0:compat.settings['width']].copy()
            blended_guide = cv2.addWeighted(current_guide, 0.3, guide_area, 0.3, 0)
            img[header_height:compat.settings['height'], 0:compat.settings['width']] = blended_guide

            cv2.putText(img, f"Guide {current_guide_index + 1}/{len(guideList)}", 
                       (compat.settings['width'] - 200, notification_y),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

        # Show notification if active
        current_time = time.time()
        if current_time < notification_time and notification_text:
            text_size = cv2.getTextSize(notification_text, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)[0]
            cv2.rectangle(img, (10, notification_y - 25), (20 + text_size[0], notification_y + 5), (50, 50, 50), -1)
            cv2.rectangle(img, (10, notification_y - 25), (20 + text_size[0], notification_y + 5), (200, 200, 200), 1)
            cv2.putText(img, notification_text, (20, notification_y), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

        # 12. Display the image
        cv2.imshow(window_name, img)

        # Adaptive garbage collection
        if frame_count % 50 == 0:
            gc.collect()

        # Maintain target FPS
        elapsed_time = time.time() - start_time
        if elapsed_time < time_per_frame:
            time.sleep(time_per_frame - elapsed_time)

        # Process Tkinter events
        try:
            size_adjuster.window.update()
        except tk.TclError:
            break

        # Check if window should close
        try:
            window_visible = cv2.getWindowProperty(window_name, cv2.WND_PROP_VISIBLE)
            if window_visible < 1:
                on_close()
                break
        except cv2.error:
            on_close()
            break
            
        # Check for ESC key
        if cv2.waitKey(1) & 0xFF == 27:
            on_close()
            break
            
except KeyboardInterrupt:
    print("\nProgram terminated by user")
    on_close()
except Exception as e:
    print(f"\nUnexpected error: {e}")
    import traceback
    traceback.print_exc()
    on_close()
finally:
    try:
        on_close()
    except:
        sys.exit(1)

def run_application(role=None):
    try:
        # This function is called by the launcher
        print("VirtualPainter application started successfully!")
        print(f"User logged in: {db_saver.user_data.get('email', 'No user')}")
        print(f"User role: {db_saver.user_data.get('role', 'No role')}")
    except Exception as e:
        print(f"Error running application: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    role = None
    if len(sys.argv) > 1:
        role = sys.argv[1]
    run_application(role)