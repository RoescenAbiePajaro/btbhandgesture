import requests
import json
import time

class ClickTracker:
    def __init__(self, base_url="https://btbsitess.onrender.com/"):
        self.base_url = base_url
        self.is_online = False
        self.last_check = 0.0
        self.check_interval = 30.0  # seconds between connectivity checks
        self.check_connection(force=True)
    
    def check_connection(self, force=False):
        """Check if server is reachable"""
        if not force and (time.time() - self.last_check) < self.check_interval:
            return self.is_online

        self.last_check = time.time()
        try:
            response = requests.get(f"{self.base_url}/api/test", timeout=5)
            self.is_online = response.status_code == 200
        except requests.exceptions.RequestException:
            self.is_online = False
        return self.is_online
    
    def track_click(self, button, page):
        """Track button click - only works when online"""
        if not self.check_connection():
            print(f"Offline mode: Click not tracked - Button: {button}, Page: {page}")
            return False
        
        try:
            response = requests.post(
                f"{self.base_url}/api/clicks",
                json={
                    'button': button,
                    'page': page
                },
                headers={'Content-Type': 'application/json'},
                timeout=5
            )
            
            if response.status_code == 201:
                print(f"Click tracked successfully - Button: {button}, Page: {page}")
                return True
            
            try:
                error_detail = response.json()
            except (ValueError, json.JSONDecodeError):
                error_detail = response.text

            print(f"Failed to track click (status {response.status_code}): {error_detail}")
            return False
                
        except requests.exceptions.RequestException as e:
            print(f"Tracking failed: {e}")
            self.is_online = False
            self.last_check = 0.0  # Force re-check on next attempt
            return False
        except Exception as e:
            print(f"Unexpected tracking error: {e}")
            return False

# Global tracker instance
tracker = ClickTracker()