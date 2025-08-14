#!/usr/bin/env python3
"""
Test script to verify MongoDB connection and basic operations
"""

import pymongo
from pymongo import MongoClient
import os
from dotenv import load_dotenv

def test_mongodb_connection():
    """Test MongoDB connection and basic operations"""
    
    # Load environment variables
    load_dotenv()
    
    # Get MongoDB URI
    MONGODB_URI = os.getenv("MONGODB_URI")
    if not MONGODB_URI:
        # Fallback to hardcoded URI
        MONGODB_URI = "mongodb+srv://202211504:APoiboNwZGFYm9cQ@cluster0.eeyewov.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
    
    print(f"Testing MongoDB connection with URI: {MONGODB_URI[:50]}...")
    
    try:
        # Configure MongoDB client
        client = MongoClient(
            MONGODB_URI,
            tls=True,
            tlsAllowInvalidCertificates=False,
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=10000,
            socketTimeoutMS=10000
        )
        
        # Test the connection
        client.admin.command('ping')
        print("✅ MongoDB connection successful!")
        
        # Get database and collections
        db = client["beyond_the_brush"]
        students_collection = db["students"]
        access_codes_collection = db["access_codes"]
        
        print(f"✅ Database 'beyond_the_brush' accessed successfully")
        print(f"✅ Collections: students, access_codes")
        
        # Test basic operations
        print("\n--- Testing Basic Operations ---")
        
        # Count documents in collections
        student_count = students_collection.count_documents({})
        code_count = access_codes_collection.count_documents({})
        
        print(f"📊 Students collection: {student_count} documents")
        print(f"📊 Access codes collection: {code_count} documents")
        
        # Show sample documents
        if student_count > 0:
            sample_student = students_collection.find_one()
            print(f"👤 Sample student: {sample_student}")
        
        if code_count > 0:
            sample_code = access_codes_collection.find_one()
            print(f"🔑 Sample access code: {sample_code}")
        
        # Test verification logic
        print("\n--- Testing Verification Logic ---")
        
        # Test with a sample access code (if available)
        if code_count > 0:
            sample_code_doc = access_codes_collection.find_one()
            test_code = sample_code_doc.get("code", "test123")
            test_role = "educator"
            test_name = "Test User"
            
            print(f"🧪 Testing verification with code: {test_code}")
            
            # Test educator verification
            code_data = access_codes_collection.find_one({"code": test_code})
            if code_data:
                print(f"✅ Educator access code '{test_code}' is valid")
            else:
                print(f"❌ Educator access code '{test_code}' is invalid")
            
            # Test student verification (if we have student data)
            if student_count > 0:
                sample_student_doc = students_collection.find_one()
                test_student_name = sample_student_doc.get("name", "Test Student")
                test_student_code = sample_student_doc.get("access_code", "test456")
                
                student_data = students_collection.find_one({
                    "access_code": test_student_code, 
                    "name": test_student_name
                })
                
                if student_data:
                    print(f"✅ Student '{test_student_name}' with code '{test_student_code}' is valid")
                else:
                    print(f"❌ Student verification failed")
        
        client.close()
        print("\n✅ All tests completed successfully!")
        
    except Exception as e:
        print(f"❌ MongoDB connection failed: {str(e)}")
        print("Please check your internet connection and MongoDB Atlas settings.")

if __name__ == "__main__":
    test_mongodb_connection()
