import requests
import json

class ClickTracker:
    def __init__(self, base_url="http://localhost:5000"):
        self.base_url = base_url
        self.is_online = False
        self.check_connection()
    
    def check_connection(self):
        """Check if server is reachable"""
        try:
            response = requests.get(f"{self.base_url}/api/test", timeout=5)
            self.is_online = response.status_code == 200
        except requests.exceptions.RequestException:
            self.is_online = False
    
    def track_click(self, button, page):
        """Track button click - only works when online"""
        if not self.is_online:
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
            else:
                print(f"Failed to track click: {response.json()}")
                return False
                
        except requests.exceptions.RequestException as e:
            print(f"Tracking failed: {e}")
            self.is_online = False
            return False

# Global tracker instance
tracker = ClickTracker()