# register.py
import pymongo
import time
import os
from dotenv import load_dotenv

load_dotenv()

# MongoDB connection with error handling
try:
    # Try to get MongoDB URI from environment variable
    MONGODB_URI = os.getenv("MONGODB_URI")
    
    if not MONGODB_URI:
        raise ValueError("MONGODB_URI not set in environment variables")
    
    # Configure MongoDB client with SSL settings
    client = pymongo.MongoClient(
        MONGODB_URI,
        tls=True,
        tlsAllowInvalidCertificates=False,
        serverSelectionTimeoutMS=5000,
        connectTimeoutMS=10000,
        socketTimeoutMS=10000
    )
    # Test the connection
    client.admin.command('ping')
    db = client["beyond_the_brush"]
    access_codes_collection = db["access_codes"]
    students_collection = db["students"]
    print("✅ Connected to MongoDB successfully!")
except Exception as e:
    print(f"❌ MongoDB connection failed: {str(e)}")
    print("Please check your internet connection and MongoDB Atlas settings.")
    exit(1)


def register_student():
    print("\n" + "="*50)
    print("           STUDENT REGISTRATION")
    print("="*50)
    
    while True:
        print("\nPlease enter the following information:")
        
        # Get username
        while True:
            name = input("Username (8 characters): ").strip()
            if not name:
                print("❌ Username cannot be empty. Please try again.")
                continue
            elif len(name) != 8:
                print("❌ Username must be exactly 8 characters long. Please try again.")
                continue
            else:
                break
        
        # Get access code
        access_code = input("Access Code: ").strip()
        if not access_code:
            print("❌ Access code cannot be empty. Please try again.")
            continue
        
        print(f"\n📝 Registration Details:")
        print(f"   Username: {name}")
        print(f"   Access Code: {access_code}")
        
        # Confirm registration
        confirm = input("\nIs this information correct? (y/n): ").strip().lower()
        if confirm not in ['y', 'yes']:
            print("🔄 Registration cancelled. Starting over...")
            continue
        
        # Check if name already exists
        existing_student = students_collection.find_one({"name": name})
        if existing_student:
            print("⚠️  This username is already registered. Please use a different username.")
            continue
        
        # Check if access code exists in MongoDB
        code_data = access_codes_collection.find_one({"code": access_code})
        if code_data:
            # Register student
            student_data = {
                "name": name,
                "access_code": access_code,
                "registered_at": time.time(),
                "educator_id": code_data.get("educator_id", "")
            }
            students_collection.insert_one(student_data)
            print("\n🎉 Registration successful! You can now log in.")
            break
        else:
            print("❌ Invalid access code. Please ask your educator for a valid code.")
            continue


def check_student_exists(name, access_code):
    """Check if a student with the given name and access code already exists"""
    try:
        student = students_collection.find_one({"name": name, "access_code": access_code})
        return student is not None
    except Exception as e:
        print(f"Error checking student existence: {e}")
        return False

def is_valid_access_code(code):
    """Check if an access code is valid"""
    try:
        code_data = access_codes_collection.find_one({"code": code})
        return code_data is not None
    except Exception as e:
        print(f"Error checking access code: {e}")
        return False

def add_access_code(code, educator_id=""):
    """Add a new access code to the database"""
    try:
        # Check if code already exists
        if is_valid_access_code(code):
            print("Access code already exists")
            return False
        
        # Add new access code
        code_data = {
            "code": code,
            "educator_id": educator_id,
            "created_at": time.time()
        }
        access_codes_collection.insert_one(code_data)
        print("Access code added successfully")
        return True
    except Exception as e:
        print(f"Error adding access code: {e}")
        return False

def main():
    try:
        register_student()
        
        # Ask if user wants to register another student
        while True:
            another = input("\nWould you like to register another student? (y/n): ").strip().lower()
            if another in ['y', 'yes']:
                register_student()
            elif another in ['n', 'no']:
                print("\n👋 Thank you for using the registration system!")
                break
            else:
                print("Please enter 'y' for yes or 'n' for no.")
                
    except KeyboardInterrupt:
        print("\n\n👋 Registration cancelled. Goodbye!")
    except Exception as e:
        print(f"\n❌ An error occurred: {str(e)}")
    finally:
        if 'client' in locals():
            client.close()
            print("🔌 MongoDB connection closed.")


if __name__ == "__main__":
    main()