# Face Recognition Implementation Guide

This guide explains how to implement and use the face recognition feature in the Student Attendance System.

## Overview

The face recognition system uses the `face_recognition` library (built on dlib) to:
1. Extract facial features from student photos
2. Store these features as encodings in the database
3. Compare live camera feed against stored encodings
4. Automatically mark attendance when a match is found

## Installation

### Prerequisites

Before installing face_recognition, ensure you have:
- Python 3.7 or higher
- CMake (for building dlib)
- A C++ compiler (gcc, Visual Studio, etc.)

### Ubuntu/Debian

```bash
# Install system dependencies
sudo apt-get update
sudo apt-get install cmake
sudo apt-get install build-essential
sudo apt-get install libopenblas-dev liblapack-dev
sudo apt-get install libx11-dev libgtk-3-dev

# Install Python packages
pip install dlib
pip install face-recognition
```

### macOS

```bash
# Install Homebrew if not already installed
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install dependencies
brew install cmake
brew install dlib

# Install Python packages
pip install dlib
pip install face-recognition
```

### Windows

```bash
# Install Visual Studio Build Tools first
# Download from: https://visualstudio.microsoft.com/downloads/

# Install CMake
# Download from: https://cmake.org/download/

# Install Python packages
pip install cmake
pip install dlib
pip install face-recognition
```

## How It Works

### 1. Face Encoding Generation

When a student is registered with a photo:

```python
import face_recognition
import numpy as np

# Load the image
image = face_recognition.load_image_file('student_photo.jpg')

# Generate face encoding (128-dimensional vector)
face_encoding = face_recognition.face_encodings(image)[0]

# Convert to string for database storage
encoding_str = ','.join(map(str, face_encoding))
student.face_encoding = encoding_str
student.save()
```

### 2. Live Face Detection

The system captures frames from the webcam:

```python
import cv2

# Open webcam
video_capture = cv2.VideoCapture(0)

while True:
    # Capture frame
    ret, frame = video_capture.read()
    
    # Convert BGR (OpenCV) to RGB (face_recognition)
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    
    # Find faces in the frame
    face_locations = face_recognition.face_locations(rgb_frame)
    face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)
    
    # Process each face found
    for face_encoding in face_encodings:
        # Compare with known faces
        matches = compare_with_database(face_encoding)
```

### 3. Face Matching

Compare detected faces with stored encodings:

```python
def compare_with_database(unknown_encoding):
    # Get all students with face encodings
    students = Student.objects.exclude(face_encoding__isnull=True)
    
    for student in students:
        # Convert stored encoding back to numpy array
        known_encoding = np.array([float(x) for x in student.face_encoding.split(',')])
        
        # Compare faces
        match = face_recognition.compare_faces([known_encoding], unknown_encoding, tolerance=0.6)
        
        if match[0]:
            # Mark attendance
            mark_attendance(student)
            return student
    
    return None
```

## Implementation Steps

### Step 1: Update views.py

Add the face recognition logic to `students/views.py`:

```python
import face_recognition
import cv2
import numpy as np
from django.http import JsonResponse
import base64

def process_face_recognition(request):
    if request.method == 'POST':
        # Get image data from request
        image_data = request.POST.get('image')
        
        # Decode base64 image
        image_bytes = base64.b64decode(image_data.split(',')[1])
        nparr = np.frombuffer(image_bytes, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        # Convert to RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Find faces
        face_locations = face_recognition.face_locations(rgb_frame)
        face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)
        
        recognized_students = []
        
        for face_encoding in face_encodings:
            # Compare with all students
            students = Student.objects.exclude(face_encoding__isnull=True)
            
            for student in students:
                if not student.face_encoding:
                    continue
                
                # Convert stored encoding to numpy array
                known_encoding = np.array([float(x) for x in student.face_encoding.split(',')])
                
                # Compare faces
                matches = face_recognition.compare_faces([known_encoding], face_encoding, tolerance=0.6)
                
                if matches[0]:
                    # Mark attendance
                    today = timezone.now().date()
                    attendance, created = Attendance.objects.get_or_create(
                        student=student,
                        date=today,
                        defaults={
                            'time': timezone.now().time(),
                            'status': 'present',
                            'marked_by': 'Face Recognition System'
                        }
                    )
                    
                    recognized_students.append({
                        'id': student.id,
                        'name': student.get_full_name(),
                        'roll_number': student.roll_number,
                        'created': created
                    })
                    break
        
        return JsonResponse({
            'success': True,
            'students': recognized_students
        })
```

### Step 2: Update Student Model

Add a method to generate face encoding when photo is uploaded:

```python
def save(self, *args, **kwargs):
    # If photo is uploaded and face_encoding doesn't exist
    if self.photo and not self.face_encoding:
        try:
            import face_recognition
            import numpy as np
            
            # Load image
            image = face_recognition.load_image_file(self.photo.path)
            
            # Generate encoding
            encodings = face_recognition.face_encodings(image)
            
            if len(encodings) > 0:
                # Store as comma-separated string
                encoding = encodings[0]
                self.face_encoding = ','.join(map(str, encoding))
        except Exception as e:
            print(f"Error generating face encoding: {e}")
    
    super().save(*args, **kwargs)
```

### Step 3: Update Frontend (mark_attendance.html)

Add JavaScript to capture and send images:

```javascript
const video = document.getElementById('video');
const canvas = document.getElementById('canvas');
const context = canvas.getContext('2d');

// Access webcam
navigator.mediaDevices.getUserMedia({ video: true })
    .then(stream => {
        video.srcObject = stream;
        video.play();
        
        // Capture and process frame every 2 seconds
        setInterval(() => {
            captureAndRecognize();
        }, 2000);
    });

function captureAndRecognize() {
    // Draw current video frame to canvas
    context.drawImage(video, 0, 0, canvas.width, canvas.height);
    
    // Convert to base64
    const imageData = canvas.toDataURL('image/jpeg');
    
    // Send to server
    fetch('/attendance/recognize/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: `image=${encodeURIComponent(imageData)}`
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Show recognized students
            displayRecognizedStudents(data.students);
        }
    });
}

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}
```

## Configuration

### Face Recognition Parameters

Adjust these parameters in your implementation:

```python
# Tolerance for face matching (lower = stricter)
# Range: 0.0 to 1.0, default: 0.6
FACE_RECOGNITION_TOLERANCE = 0.6

# Model to use for face detection
# Options: 'hog' (faster, CPU) or 'cnn' (more accurate, GPU)
FACE_DETECTION_MODEL = 'hog'

# Number of times to upsample the image
# Higher = detect more faces but slower
FACE_DETECTION_UPSAMPLE = 1
```

## Best Practices

### For Students' Photos

1. **Good Lighting**: Ensure face is well-lit
2. **Clear Face**: No obstructions (glasses, masks, hats)
3. **Front-Facing**: Look directly at camera
4. **High Resolution**: Use at least 640x480 pixels
5. **Single Person**: Only one face in the photo

### For Live Recognition

1. **Lighting Conditions**: Match training photo lighting
2. **Camera Position**: Same angle as training photos
3. **Distance**: 1-2 feet from camera
4. **Processing Interval**: Don't process every frame (use 1-2 second intervals)

### Performance Optimization

1. **Resize Images**: Scale down large images before processing
2. **Use HOG Model**: Faster than CNN for CPU-based systems
3. **Limit Database Queries**: Cache student encodings in memory
4. **Async Processing**: Use background tasks for encoding generation

## Troubleshooting

### Common Issues

1. **"No module named 'dlib'"**
   - Install dlib: `pip install dlib`
   - May need CMake and C++ compiler

2. **"No faces found in image"**
   - Check image quality
   - Ensure face is visible and clear
   - Try different lighting

3. **"Too many false positives"**
   - Decrease tolerance (e.g., 0.5 or 0.4)
   - Use better quality training photos

4. **"Recognition too slow"**
   - Use 'hog' model instead of 'cnn'
   - Reduce image resolution
   - Increase processing interval

## Testing

Use the provided demo script:

```bash
python face_recognition_demo.py
```

This will:
1. Check if dependencies are installed
2. Allow you to test encoding generation
3. Provide webcam face detection demo

## Resources

- [face_recognition Documentation](https://face-recognition.readthedocs.io/)
- [dlib Documentation](http://dlib.net/)
- [OpenCV Documentation](https://docs.opencv.org/)

## Security Considerations

1. **Data Privacy**: Store face encodings securely
2. **Consent**: Obtain student consent before capturing biometric data
3. **Access Control**: Restrict access to attendance system
4. **Data Retention**: Define clear policies for data retention
5. **GDPR Compliance**: Ensure compliance with data protection regulations
