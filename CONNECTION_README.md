# Connection Between main.py and register.py

## Overview
The two files `main.py` and `register.py` are now fully connected and integrated into a single launcher system. The main launcher (`main.py`) now includes student registration functionality directly from the GUI.

## How They're Connected

### 1. **Shared MongoDB Connection**
- Both files use the same MongoDB connection logic
- `register.py` establishes the connection and exports collections
- `main.py` imports helper functions from `register.py`

### 2. **Imported Functions from register.py**
```python
from register import check_student_exists, is_valid_access_code
```

**Available Functions:**
- `check_student_exists(name, access_code)` - Verifies if a student is registered
- `is_valid_access_code(code)` - Checks if an access code is valid
- `add_access_code(code, educator_id)` - Adds new access codes for educators

### 3. **Integrated GUI Features**
The main launcher now includes:

#### **Student Registration Page**
- Username entry (8 characters required)
- Access code entry
- Validation against existing registrations
- Direct database insertion

#### **Access Code Management**
- Educators can add new access codes
- Optional educator ID tracking
- Duplicate code prevention

#### **Seamless Navigation**
- Back buttons between pages
- Consistent UI design
- Error handling and user feedback

## File Structure

```
beyondthebrush/
├── main.py              # Main launcher with integrated registration
├── register.py          # Database functions and registration logic
├── test_connection.py   # Test script to verify integration
├── CONNECTION_README.md # This file
└── .env                 # Environment variables (MONGODB_URI)
```

## How to Use

### 1. **Run the Integrated System**
```bash
python main.py
```

### 2. **Test the Connection**
```bash
python test_connection.py
```

### 3. **Use Individual Components**
```bash
# For command-line registration only
python register.py

# For testing database functions
python -c "from register import *; print(check_student_exists('test', 'code'))"
```

## Database Collections

### **students**
```json
{
  "name": "username",
  "access_code": "code123",
  "registered_at": 1234567890,
  "educator_id": "optional_id"
}
```

### **access_codes**
```json
{
  "code": "code123",
  "educator_id": "optional_id",
  "created_at": 1234567890
}
```

## Key Benefits of Integration

1. **Single Entry Point** - Users don't need to run separate scripts
2. **Consistent UI** - Same design language across all features
3. **Better User Experience** - Registration and login in one place
4. **Centralized Database Management** - Single connection, shared collections
5. **Error Handling** - Consistent error messages and validation

## Environment Variables

Make sure you have a `.env` file with:
```
MONGODB_URI=your_mongodb_connection_string
```

## Troubleshooting

### **Import Errors**
- Ensure both files are in the same directory
- Check that all required packages are installed (`pymongo`, `python-dotenv`)

### **Database Connection Issues**
- Verify your MongoDB URI in the `.env` file
- Check internet connection and MongoDB Atlas settings
- Run `test_connection.py` to diagnose issues

### **Registration Issues**
- Ensure usernames are exactly 8 characters
- Check that access codes exist in the database
- Verify no duplicate usernames

## Future Enhancements

The integrated system is designed to be easily extensible:
- Add user profile management
- Implement password-based authentication
- Add session tracking
- Include usage analytics
- Add bulk user import/export

## Support

If you encounter issues:
1. Run `test_connection.py` first
2. Check the console output for error messages
3. Verify your MongoDB connection string
4. Ensure all dependencies are installed
