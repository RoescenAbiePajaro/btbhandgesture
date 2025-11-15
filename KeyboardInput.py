import cv2
import numpy as np
from collections import deque
import time

class KeyboardInput:
    def __init__(self):
        self.text = ""
        self.active = False
        self.cursor_visible = True
        self.cursor_timer = 0
        self.cursor_blink_interval = 0.5
        self.text_objects = deque(maxlen=15)  # Reduced from 20 for memory
        self.dragging = False
        self.drag_object_index = -1
        self.drag_offset = (0, 0)
        self.default_font = cv2.FONT_HERSHEY_SIMPLEX
        self.default_scale = 1.0
        self.default_thickness = 2
        self.default_color = (255, 255, 255)
        self.outline_color = (0, 0, 0)
        self.outline_thickness = 4
        self.current_input_position = (640, 360)
        self.input_dragging = False
        self.input_drag_offset = (0, 0)
        self.selected_object_index = -1
        
        # MEMORY OPTIMIZATIONS:
        self.text_history = deque(maxlen=8)  # Limited undo history
        self.history_index = -1
        self.smooth_text = deque(maxlen=30)  # Limited animation buffer
        
        self.last_key_time = time.time()
        self.key_repeat_delay = 0.03
        self.initial_delay = 0.2
        self.last_key = None
        self.animation_speed = 0.1
        self.char_delay = 0.01

    def toggle_keyboard_mode(self):
        self.active = not self.active
        if self.active:
            self.text = ""
            self.cursor_visible = True
            self.cursor_timer = 0
            # Create a new text object at center when toggling on
            self.current_input_position = (640, 360)

    def save_state(self):
        """Memory-optimized state saving"""
        if self.history_index < len(self.text_history) - 1:
            # Truncate future history if we're not at the end
            while len(self.text_history) > self.history_index + 1:
                self.text_history.pop()
        
        # Create minimal state copy
        state = []
        for obj in self.text_objects:
            state.append({
                'text': obj['text'],
                'position': obj['position'],
                'color': obj['color']
                # Omit constant values to save memory
            })
        
        self.text_history.append(state)
        self.history_index = len(self.text_history) - 1

    def restore_state(self, state):
        """Restore from minimal state"""
        self.text_objects.clear()
        for obj_data in state:
            self.text_objects.append({
                'text': obj_data['text'],
                'position': obj_data['position'],
                'color': obj_data['color'],
                'font': self.default_font,
                'scale': self.default_scale,
                'thickness': self.default_thickness,
                'selected': False
            })

    def undo(self):
        if self.history_index > 0:
            self.history_index -= 1
            self.restore_state(self.text_history[self.history_index])
            return True
        return False

    def redo(self):
        if self.history_index < len(self.text_history) - 1:
            self.history_index += 1
            self.restore_state(self.text_history[self.history_index])
            return True
        return False

    def get_selected_index(self):
        """Get the index of currently selected text object"""
        for i, obj in enumerate(self.text_objects):
            if obj.get('selected', False):
                return i
        return -1

    def process_key_input(self, key):
        if not self.active:
            return False

        current_time = time.time()
        time_since_last_key = current_time - self.last_key_time

        # Handle key repeat logic
        if key == self.last_key and time_since_last_key < self.key_repeat_delay:
            return False

        if key != self.last_key:
            self.last_key_time = current_time - self.initial_delay
            self.last_key = key
        else:
            self.last_key_time = current_time

        selected_index = self.get_selected_index()
        
        if key == 13:  # Enter key
            if selected_index >= 0:
                self.clear_selection()
                self.text = ""
            else:
                if self.text:
                    # Save state before adding new text
                    self.save_state()
                    left_position = (50, self.current_input_position[1])
                    self.text_objects.append({
                        'text': self.text,
                        'position': left_position,
                        'color': self.default_color,
                        'font': self.default_font,
                        'scale': self.default_scale,
                        'thickness': self.default_thickness,
                        'selected': False
                    })
                    self.text = ""
                    self.current_input_position = (640, 360)
            return True
            
        elif key == 8:  # Backspace
            if selected_index >= 0:
                text = self.text_objects[selected_index]['text']
                if text:  # Only save state if there's something to delete
                    self.save_state()
                chars_to_delete = 1
                if time_since_last_key < self.key_repeat_delay:
                    chars_to_delete = min(3, len(text))
                self.text_objects[selected_index]['text'] = text[:-chars_to_delete]
                if not self.text_objects[selected_index]['text']:
                    self.delete_selected()
            else:
                if self.text:  # Only save state if there's something to delete
                    self.save_state()
                chars_to_delete = 1
                if time_since_last_key < self.key_repeat_delay:
                    chars_to_delete = min(3, len(self.text))
                self.text = self.text[:-chars_to_delete]
            return True
            
        elif 32 <= key <= 126:  # Printable characters
            if selected_index >= 0:
                if not self.text_objects[selected_index]['text']:  # First character
                    self.save_state()
                self.text_objects[selected_index]['text'] += chr(key)
            else:
                if not self.text:  # First character
                    self.save_state()
                self.text += chr(key)
                
            # Add to smooth text buffer with size limit
            if len(self.smooth_text) >= 30:
                self.smooth_text.popleft()  # Remove oldest if at limit
                
            char_time = len(self.smooth_text) * self.char_delay
            self.smooth_text.append({
                'char': chr(key),
                'alpha': 0,
                'scale': 0.8,
                'y_offset': 10,
                'time': char_time,
                'elapsed': 0,
                'target_pos': len(self.text) - 1 if selected_index < 0 else len(self.text_objects[selected_index]['text']) - 1
            })
            return True

        return False

    def add_text_object(self):
        if not self.text:
            return

        self.save_state()

        self.text_objects.append({
            'text': self.text,
            'position': self.current_input_position,
            'color': self.default_color,
            'font': self.default_font,
            'scale': self.default_scale,
            'thickness': self.default_thickness,
            'selected': False
        })

    def delete_selected(self):
        """Delete the currently selected text object"""
        selected_index = self.get_selected_index()
        if selected_index >= 0:
            self.save_state()
            del self.text_objects[selected_index]
            self.drag_object_index = -1

    def update(self, dt):
        if not self.active:
            # Clean up animations when inactive
            if self.smooth_text:
                self.smooth_text.clear()
            return

        # Update cursor blink
        self.cursor_timer += dt
        if self.cursor_timer >= self.cursor_blink_interval:
            self.cursor_timer = 0
            self.cursor_visible = not self.cursor_visible

        # Update smooth text animations with cleanup
        current_time = time.time()
        completed_animations = []
        
        for char_data in self.smooth_text:
            char_data['elapsed'] += dt
            progress = min(1.0, char_data['elapsed'] / self.animation_speed)
            
            if progress >= 1.0:
                completed_animations.append(char_data)
            else:
                char_data['alpha'] = progress
                char_data['scale'] = 0.9 + (0.1 * progress)
                char_data['y_offset'] = 5 * (1 - progress)
        
        # Remove completed animations
        for completed in completed_animations:
            if completed in self.smooth_text:
                self.smooth_text.remove(completed)

    def draw(self, img):
        # Draw all existing text objects
        for i, obj in enumerate(self.text_objects):
            # Draw outline
            cv2.putText(
                img,
                obj['text'],
                obj['position'],
                obj['font'],
                obj['scale'],
                self.outline_color,
                self.outline_thickness
            )
            # Draw main text
            cv2.putText(
                img,
                obj['text'],
                obj['position'],
                obj['font'],
                obj['scale'],
                obj['color'],
                obj['thickness']
            )

            # Draw selection rectangle if selected
            if obj.get('selected', False):
                text_size = cv2.getTextSize(
                    obj['text'],
                    obj['font'],
                    obj['scale'],
                    obj['thickness']
                )[0]
                top_left = (
                    obj['position'][0] - 5,
                    obj['position'][1] - text_size[1] - 5
                )
                bottom_right = (
                    obj['position'][0] + text_size[0] + 5,
                    obj['position'][1] + 5
                )
                cv2.rectangle(img, top_left, bottom_right, (0, 255, 0), 2)

        # Draw current input text with smooth animation
        if self.active and (self.text or self.cursor_visible):
            base_text = self.text
            
            # Draw smooth text animations
            for char_data in self.smooth_text:
                pos = char_data['target_pos']
                alpha = char_data['alpha']
                scale = char_data['scale']
                y_offset = int(char_data['y_offset'])
                
                # Calculate position with offset
                text_before = base_text[:pos]
                text_size = cv2.getTextSize(text_before, self.default_font, 
                                         self.default_scale, self.default_thickness)[0]
                
                base_x = self.current_input_position[0] + text_size[0]
                base_y = self.current_input_position[1]
                
                # Apply animation offsets
                char_pos = (base_x, base_y + y_offset)
                
                # Calculate color with alpha
                color = tuple(int(c * alpha) for c in self.default_color)
                
                # Draw character with current scale and alpha
                font_scale = self.default_scale * scale
                cv2.putText(img, char_data['char'], char_pos, 
                          self.default_font, font_scale, 
                          color, self.default_thickness, 
                          cv2.LINE_AA)

            # Draw main text
            cv2.putText(img, self.text, self.current_input_position,
                       self.default_font, self.default_scale,
                       self.default_color, self.default_thickness)

            # Draw cursor
            if self.cursor_visible:
                text_size = cv2.getTextSize(
                    self.text,
                    self.default_font,
                    self.default_scale,
                    self.default_thickness
                )[0]
                cursor_pos = (
                    self.current_input_position[0] + text_size[0],
                    self.current_input_position[1]
                )
                cv2.line(
                    img,
                    cursor_pos,
                    (cursor_pos[0], cursor_pos[1] - 30),
                    self.default_color,
                    2
                )

    def check_drag_start(self, x, y):
        # First check if we're selecting existing text objects
        for i, obj in enumerate(reversed(self.text_objects)):
            idx = len(self.text_objects) - 1 - i  # Get original index
            text_size = cv2.getTextSize(
                obj['text'],
                obj['font'],
                obj['scale'],
                obj['thickness']
            )[0]

            text_left = obj['position'][0]
            text_right = obj['position'][0] + text_size[0]
            text_top = obj['position'][1] - text_size[1]
            text_bottom = obj['position'][1]

            if (text_left <= x <= text_right and
                    text_top <= y <= text_bottom):
                # Deselect all other objects
                for other_obj in self.text_objects:
                    other_obj['selected'] = False
                # Select this object
                self.text_objects[idx]['selected'] = True
                self.drag_object_index = idx
                self.drag_offset = (x - obj['position'][0], y - obj['position'][1])
                self.dragging = True
                # Make keyboard active when selecting text
                self.active = True
                return True
    
        # Then check if we're dragging current input text (only if keyboard active)
        if self.active and (self.text or self.cursor_visible):
            text_size = cv2.getTextSize(
                self.text,
                self.default_font,
                self.default_scale,
                self.default_thickness
            )[0]

            text_left = self.current_input_position[0]
            text_right = self.current_input_position[0] + text_size[0]
            text_top = self.current_input_position[1] - text_size[1]
            text_bottom = self.current_input_position[1]

            if (text_left <= x <= text_right and
                    text_top <= y <= text_bottom):
                self.input_dragging = True
                self.input_drag_offset = (
                    x - self.current_input_position[0],
                    y - self.current_input_position[1]
                )
                return True

        # If clicking elsewhere, deselect all
        self.clear_selection()
        return False

    def update_drag(self, x, y):
        if self.input_dragging:
            # Update position of current input text
            self.current_input_position = (
                x - self.input_drag_offset[0],
                y - self.input_drag_offset[1]
            )
        elif self.dragging and self.drag_object_index >= 0:
            # Update position of dragged text object
            if 0 <= self.drag_object_index < len(self.text_objects):
                obj = self.text_objects[self.drag_object_index]
                new_pos = (x - self.drag_offset[0], y - self.drag_offset[1])
                self.text_objects[self.drag_object_index]['position'] = new_pos

    def end_drag(self):
        self.input_dragging = False
        self.dragging = False
        self.drag_object_index = -1

    def clear_selection(self):
        """Clear all text selections"""
        for obj in self.text_objects:
            obj['selected'] = False
        self.drag_object_index = -1

    def cleanup(self):
        """Explicit cleanup method to prevent memory leaks"""
        self.text_objects.clear()
        self.text_history.clear()
        self.smooth_text.clear()
        self.text = ""
        self.active = False
        self.cursor_visible = True
        self.cursor_timer = 0
        self.dragging = False
        self.drag_object_index = -1
        self.input_dragging = False
        self.selected_object_index = -1
        self.current_input_position = (640, 360)

    def get_state_for_save(self):
        """Get minimal state for canvas saving"""
        return [{
            'text': obj['text'],
            'position': obj['position'],
            'color': obj['color'],
            'font': obj['font'],
            'scale': obj['scale'],
            'thickness': obj['thickness']
        } for obj in self.text_objects]

    def restore_state_from_save(self, saved_state):
        """Restore state from saved canvas data"""
        self.text_objects.clear()
        for obj_data in saved_state:
            self.text_objects.append({
                'text': obj_data['text'],
                'position': obj_data['position'],
                'color': obj_data['color'],
                'font': obj_data.get('font', self.default_font),
                'scale': obj_data.get('scale', self.default_scale),
                'thickness': obj_data.get('thickness', self.default_thickness),
                'selected': False
            })