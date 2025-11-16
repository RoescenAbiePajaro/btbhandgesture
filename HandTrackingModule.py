# HandTrackingModule.py
import cv2
import mediapipe as mp
import time
import os
import gc

class handDetector:
    def __init__(self, mode=False, maxHands=2, detectionCon=0.3, trackCon=0.3):
        # MEMORY OPTIMIZATION: Initialize variables first
        self.results = None
        self.lmList = []
        self.mode = mode
        self.maxHands = maxHands
        self.detectionCon = detectionCon
        self.trackCon = trackCon

        # MEMORY OPTIMIZATION: Initialize MediaPipe with resource management
        self.mpHands = mp.solutions.hands
        self.hands = self.mpHands.Hands(
            static_image_mode=self.mode,
            max_num_hands=self.maxHands,
            min_detection_confidence=self.detectionCon,
            min_tracking_confidence=self.trackCon,
            model_complexity=0  # Reduced complexity for better performance
        )
        
        self.mpDraw = mp.solutions.drawing_utils
        self.mpDrawStyles = mp.solutions.drawing_styles
        self.tipIds = [4, 8, 12, 16, 20]
        
        # MEMORY OPTIMIZATION: Reusable variables to avoid repeated allocations
        self._img_shape = None
        self._landmark_cache = []

    def findHands(self, img, draw=True):
        """Detect hands in image with memory optimization"""
        if img is None or img.size == 0:
            return img
            
        try:
            # MEMORY OPTIMIZATION: Reuse RGB conversion
            imgRGB = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            self.results = self.hands.process(imgRGB)
            
            # MEMORY OPTIMIZATION: Clear previous results efficiently
            if hasattr(self, '_landmark_cache'):
                self._landmark_cache.clear()

            if self.results.multi_hand_landmarks:
                for handLms in self.results.multi_hand_landmarks:
                    if draw:
                        # Simplified drawing for better performance
                        self.mpDraw.draw_landmarks(
                            img, 
                            handLms,
                            self.mpHands.HAND_CONNECTIONS,
                            landmark_drawing_spec=self.mpDraw.DrawingSpec(
                                color=(0, 255, 0), thickness=2, circle_radius=2
                            ),
                            connection_drawing_spec=self.mpDraw.DrawingSpec(
                                color=(255, 0, 0), thickness=2
                            )
                        )
                        
                        # Cache landmarks for reuse
                        if not hasattr(self, '_landmark_cache'):
                            self._landmark_cache = []
                        self._landmark_cache.append(handLms)
            
            # MEMORY OPTIMIZATION: Clean up temporary variables
            del imgRGB
            
        except Exception as e:
            print(f"Error in findHands: {e}")
            
        return img

    def findPosition(self, img, handNo=0, draw=True):
        """Find hand landmark positions with memory optimization"""
        self.lmList = []  # Clear previous list
        
        if img is None:
            return self.lmList
            
        # MEMORY OPTIMIZATION: Cache image shape
        self._img_shape = img.shape
        
        if self.results and self.results.multi_hand_landmarks:
            try:
                # Validate hand number
                if handNo >= len(self.results.multi_hand_landmarks):
                    return self.lmList
                    
                myHand = self.results.multi_hand_landmarks[handNo]
                h, w, c = self._img_shape
                
                # MEMORY OPTIMIZATION: Pre-allocate list size
                self.lmList = [None] * len(myHand.landmark)
                
                for id, lm in enumerate(myHand.landmark):
                    cx, cy = int(lm.x * w), int(lm.y * h)
                    self.lmList[id] = [id, cx, cy]
                    
                    if draw and id in self.tipIds:  # Only draw fingertips for performance
                        cv2.circle(img, (cx, cy), 4, (255, 0, 255), cv2.FILLED)
                        
            except (IndexError, AttributeError) as e:
                # Silent fail for hand detection errors
                pass
            except Exception as e:
                print(f"Unexpected error in findPosition: {e}")
                
        return self.lmList

    def fingersUp(self):
        """Detect which fingers are up with optimized logic"""
        fingers = [0] * 5  # Pre-allocate list
        
        if not self.lmList or len(self.lmList) < 21:
            return fingers

        try:
            # Thumb - simplified logic
            if len(self.lmList) > 4 and self.lmList[self.tipIds[0]][1] > self.lmList[self.tipIds[0] - 1][1]:
                fingers[0] = 1

            # Four fingers - optimized comparison
            for id in range(1, 5):
                if (len(self.lmList) > self.tipIds[id] - 2 and 
                    self.lmList[self.tipIds[id]][2] < self.lmList[self.tipIds[id] - 2][2]):
                    fingers[id] = 1
                    
        except (IndexError, TypeError) as e:
            # Reset on error
            fingers = [0] * 5
            
        return fingers

    def getHandCount(self):
        """Get number of detected hands efficiently"""
        if self.results and self.results.multi_hand_landmarks:
            return len(self.results.multi_hand_landmarks)
        return 0

    def cleanup(self):
        """Explicit cleanup to prevent memory leaks"""
        try:
            # Clear data structures
            self.lmList.clear()
            if hasattr(self, '_landmark_cache'):
                self._landmark_cache.clear()
                
            # Clear results
            self.results = None
            
            # Close MediaPipe resources
            if hasattr(self, 'hands') and self.hands:
                self.hands.close()
                
            # Force garbage collection
            gc.collect()
            
            print("Hand detector cleanup completed")
            
        except Exception as e:
            print(f"Error during hand detector cleanup: {e}")

    def __del__(self):
        """Destructor for automatic cleanup"""
        self.cleanup()


def main():
    """Test function with memory optimization"""
    pTime = 0
    cap = None
    detector = None
    
    try:
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            print("Error: Could not open camera")
            return
            
        # Set camera properties for better performance
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        cap.set(cv2.CAP_PROP_FPS, 30)
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        
        detector = handDetector()
        frame_count = 0
        
        while True:
            success, img = cap.read()
            if not success:
                print("Failed to capture frame")
                continue

            # MEMORY OPTIMIZATION: Skip every other frame for testing
            frame_count += 1
            if frame_count % 2 == 0:
                continue

            img = detector.findHands(img)
            lmList = detector.findPosition(img, draw=False)  # Disable drawing for performance
            
            if lmList and len(lmList) > 4:
                print(f"Index finger: {lmList[8]}")  # Print index finger tip

            # Calculate FPS
            cTime = time.time()
            fps = 1 / (cTime - pTime) if (cTime - pTime) > 0 else 0
            pTime = cTime

            # Display FPS
            cv2.putText(img, f"FPS: {int(fps)}", (10, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 255), 2)

            cv2.imshow("Hand Tracking", img)
            
            # Exit on 'q' press
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
                
            # Periodic garbage collection
            if frame_count % 100 == 0:
                gc.collect()

    except KeyboardInterrupt:
        print("Program interrupted by user")
    except Exception as e:
        print(f"Error in main: {e}")
    finally:
        # MEMORY OPTIMIZATION: Proper cleanup
        print("Cleaning up resources...")
        if cap:
            cap.release()
        if detector:
            detector.cleanup()
        cv2.destroyAllWindows()
        gc.collect()


if __name__ == "__main__":
    main()