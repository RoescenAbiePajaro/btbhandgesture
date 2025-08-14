# Beyond The Brush - Virtual Painter Application

## Overview
Beyond The Brush is an interactive virtual painting application that uses hand tracking technology to create digital artwork. The application includes a secure login system and a comprehensive painting interface.

## Features
- **Secure Login System**: Separate access for students and educators
- **Hand Gesture Control**: Use hand movements to paint and navigate
- **Multiple Brush Colors**: Pink, Blue, Green, Yellow, and Eraser
- **Text Input**: Add text to your artwork using keyboard input
- **Guide System**: Interactive tutorials and guides
- **Undo/Redo**: Full history management for your artwork
- **Save Functionality**: Save your artwork to your Pictures folder

## How to Use

### 1. Launch the Application
Run `main.py` to start the launcher:
```bash
python main.py
```

### 2. Login Process
- **Students**: Enter your name and access code
- **Educators**: Enter your access code only
- Click "LOGIN" or press Enter to proceed

### 3. Painting Interface
After successful login, VirtualPainter.py will automatically launch with:
- **Two Fingers Up**: Selection mode for tools and colors
- **One Index Finger**: Drawing mode
- **One Index Finger + Guide Active**: Navigate through guides
- **Two Fingers + Keyboard Active**: Move text objects

### 4. Tool Selection (Two Fingers Up)
- **Left Area (0-128)**: Save artwork
- **Pink Area (128-256)**: Pink brush
- **Blue Area (256-384)**: Blue brush
- **Green Area (384-512)**: Green brush
- **Yellow Area (512-640)**: Yellow brush
- **Eraser Area (640-768)**: Eraser tool
- **Undo Area (768-896)**: Undo last action
- **Redo Area (896-1024)**: Redo last action
- **Guide Area (1024-1152)**: Show/hide guides
- **Keyboard Area (1155-1280)**: Open text input

### 5. Drawing (One Index Finger)
- Move your index finger to draw
- The application will create smooth lines between points
- Use different colors and brush sizes

### 6. Text Input
- Click the keyboard area to open text input
- Type your text and press Enter to confirm
- Use two fingers to drag text objects around

### 7. Guide Navigation
- Select the guide tool
- Use one finger to swipe left/right through guides
- Guides provide tutorials and help

## System Requirements
- Python 3.7+
- Webcam for hand tracking
- Windows 10/11 (tested)
- Required packages: see `requirements.txt`

## Installation
1. Install Python dependencies:
```bash
pip install -r requirements.txt
```

2. Ensure you have a working webcam
3. Run the application:
```bash
python main.py
```

## File Structure
- `main.py` - Launcher and login system
- `VirtualPainter.py` - Main painting application
- `HandTrackingModule.py` - Hand gesture detection
- `KeyboardInput.py` - Text input handling
- `icon/` - Application icons and logos
- `header/` - Tool selection interface images
- `guide/` - Tutorial and guide images

## Security
- Access codes are verified against MongoDB database
- Separate authentication for students and educators
- Secure connection handling

## Troubleshooting
- Ensure webcam is connected and accessible
- Check that all required packages are installed
- Verify MongoDB connection if using database features
- Make sure you have proper permissions for the Pictures folder

## Support
For technical support or questions, please contact your system administrator.
