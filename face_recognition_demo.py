"""
Face Recognition Utility Script

This script demonstrates how to use face_recognition library
to generate and store face encodings for students.

Usage:
    python face_recognition_demo.py

Note: Requires face_recognition library to be installed:
    pip install face-recognition
"""

import os
import sys

def check_dependencies():
    """Check if required libraries are installed"""
    try:
        import face_recognition
        import cv2
        import numpy as np
        from PIL import Image
        print("✓ All required libraries are installed!")
        return True
    except ImportError as e:
        print(f"✗ Missing dependency: {e}")
        print("\nPlease install required libraries:")
        print("  pip install face-recognition opencv-python-headless Pillow numpy")
        return False


def generate_face_encoding(image_path):
    """
    Generate face encoding from an image file
    
    Args:
        image_path: Path to the student's photo
        
    Returns:
        Face encoding as a numpy array or None if no face found
    """
    try:
        import face_recognition
        
        # Load the image
        image = face_recognition.load_image_file(image_path)
        
        # Find all face encodings in the image
        face_encodings = face_recognition.face_encodings(image)
        
        if len(face_encodings) > 0:
            # Return the first face encoding found
            return face_encodings[0]
        else:
            print(f"No face found in {image_path}")
            return None
            
    except Exception as e:
        print(f"Error processing {image_path}: {e}")
        return None


def compare_faces(known_encoding, unknown_encoding, tolerance=0.6):
    """
    Compare two face encodings
    
    Args:
        known_encoding: The stored face encoding
        unknown_encoding: The new face encoding to compare
        tolerance: How much distance between faces to consider a match (default 0.6)
        
    Returns:
        True if faces match, False otherwise
    """
    try:
        import face_recognition
        import numpy as np
        
        # Compare faces
        results = face_recognition.compare_faces(
            [known_encoding], 
            unknown_encoding, 
            tolerance=tolerance
        )
        
        # Calculate face distance
        distance = face_recognition.face_distance([known_encoding], unknown_encoding)[0]
        
        print(f"Face distance: {distance:.4f} (threshold: {tolerance})")
        
        return results[0]
        
    except Exception as e:
        print(f"Error comparing faces: {e}")
        return False


def detect_faces_in_webcam():
    """
    Detect faces using webcam (demo function)
    
    Press 'q' to quit
    """
    try:
        import cv2
        import face_recognition
        
        print("Starting webcam... Press 'q' to quit")
        
        # Get a reference to webcam
        video_capture = cv2.VideoCapture(0)
        
        while True:
            # Grab a single frame
            ret, frame = video_capture.read()
            
            if not ret:
                print("Failed to grab frame")
                break
            
            # Convert BGR (OpenCV) to RGB (face_recognition)
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Find all face locations in the frame
            face_locations = face_recognition.face_locations(rgb_frame)
            
            # Draw rectangles around faces
            for top, right, bottom, left in face_locations:
                cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
                cv2.putText(frame, 'Face Detected', (left, top - 10),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
            
            # Display the frame
            cv2.imshow('Face Detection Demo', frame)
            
            # Break loop on 'q' key press
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        
        # Release resources
        video_capture.release()
        cv2.destroyAllWindows()
        
    except Exception as e:
        print(f"Error accessing webcam: {e}")


def main():
    """Main function to demonstrate face recognition features"""
    print("=" * 60)
    print("Face Recognition Demo for Attendance System")
    print("=" * 60)
    print()
    
    # Check if dependencies are installed
    if not check_dependencies():
        print("\nExiting... Please install required dependencies first.")
        return
    
    print("\nAvailable Options:")
    print("1. Generate face encoding from image")
    print("2. Test webcam face detection")
    print("3. Exit")
    print()
    
    choice = input("Enter your choice (1-3): ").strip()
    
    if choice == '1':
        image_path = input("Enter path to student photo: ").strip()
        if os.path.exists(image_path):
            print(f"\nProcessing {image_path}...")
            encoding = generate_face_encoding(image_path)
            if encoding is not None:
                print("✓ Face encoding generated successfully!")
                print(f"  Encoding shape: {encoding.shape}")
                print(f"  Encoding (first 10 values): {encoding[:10]}")
        else:
            print(f"✗ File not found: {image_path}")
    
    elif choice == '2':
        detect_faces_in_webcam()
    
    elif choice == '3':
        print("Exiting...")
    
    else:
        print("Invalid choice!")


if __name__ == "__main__":
    main()
