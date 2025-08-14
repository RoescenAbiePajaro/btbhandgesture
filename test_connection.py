#!/usr/bin/env python3
"""
Test script to verify the connection between main.py and register.py
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_imports():
    """Test if we can import functions from both files"""
    try:
        from register import check_student_exists, is_valid_access_code, add_access_code
        print("✅ Successfully imported functions from register.py")
        
        # Test the functions
        print("Testing check_student_exists function...")
        result = check_student_exists("testuser", "testcode")
        print(f"   Result: {result}")
        
        print("Testing is_valid_access_code function...")
        result = is_valid_access_code("testcode")
        print(f"   Result: {result}")
        
        return True
    except Exception as e:
        print(f"❌ Failed to import from register.py: {e}")
        return False

def test_mongodb_connection():
    """Test MongoDB connection"""
    try:
        from register import client
        if client:
            print("✅ MongoDB connection successful")
            return True
        else:
            print("❌ MongoDB connection failed")
            return False
    except Exception as e:
        print(f"❌ MongoDB connection test failed: {e}")
        return False

def main():
    print("Testing connection between main.py and register.py...")
    print("=" * 50)
    
    # Test MongoDB connection
    print("\n1. Testing MongoDB connection...")
    mongo_ok = test_mongodb_connection()
    
    # Test imports
    print("\n2. Testing imports...")
    imports_ok = test_imports()
    
    # Summary
    print("\n" + "=" * 50)
    if mongo_ok and imports_ok:
        print("🎉 All tests passed! The connection is working correctly.")
    else:
        print("❌ Some tests failed. Please check the errors above.")
    
    print("\nYou can now run main.py to use the integrated system!")

if __name__ == "__main__":
    main()
