# Installing Face Recognition Libraries

## Issue
Python 3.13 is very new and `dlib` (required by `face-recognition`) doesn't have pre-built wheels for it yet.

## Solutions

### Option 1: Install Visual C++ Build Tools (Recommended for Windows)

1. Download and install **Microsoft C++ Build Tools**:
   - Visit: https://visualstudio.microsoft.com/visual-cpp-build-tools/
   - Download "Build Tools for Visual Studio"
   - Install with "Desktop development with C++" workload

2. Then install dlib:
   ```bash
   pip install dlib
   ```

3. Install face-recognition:
   ```bash
   pip install face-recognition
   ```

### Option 2: Use Python 3.11 or 3.12 (Easier)

If you have Python 3.11 or 3.12 installed:

1. Create a virtual environment with Python 3.11/3.12:
   ```bash
   python3.11 -m venv venv_face
   venv_face\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   pip install face-recognition dlib
   ```

### Option 3: Use Alternative Library (Quick Fix)

We can modify the code to use `deepface` which is easier to install:

```bash
pip install deepface
```

Then the code would need minor modifications to use deepface instead of face-recognition.

### Option 4: Use Pre-built Wheel (If Available)

Try downloading a pre-built wheel for your system:
```bash
pip install dlib-binary --only-binary=:all:
```

## Current Status

The application is **fully functional** without face recognition:
- ✅ Manual attendance system works perfectly
- ✅ All other features work normally
- ⚠️ Face recognition feature shows a warning but doesn't break the app

## Test Installation

After installing, test with:
```bash
python -c "import face_recognition; print('Success!')"
```

## Need Help?

If you continue having issues, the manual attendance system is a great alternative and works perfectly!




