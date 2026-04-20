import json
import base64
from io import BytesIO

from django.contrib import messages
from django.core.files.storage import FileSystemStorage
from django.http import HttpResponse, JsonResponse
from django.shortcuts import (HttpResponseRedirect, get_object_or_404,redirect, render)
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt

from .forms import *
from .models import *

# Try to import face recognition dependencies
FACE_RECOGNITION_AVAILABLE = False
np = None
Image = None
face_recognition = None
deepface = None
cv2 = None

try:
    import numpy as np
    from PIL import Image
    import cv2
    import os
    
    # Try DeepFace first
    try:
        from deepface import DeepFace
        deepface = DeepFace
        FACE_RECOGNITION_AVAILABLE = True
        print("✅ Using DeepFace for face recognition")
    except ImportError:
        # Try face_recognition as fallback
        try:
            import face_recognition
            face_recognition = face_recognition
            FACE_RECOGNITION_AVAILABLE = True
            print("✅ Using face_recognition library")
        except ImportError:
            # Use OpenCV with LBPH Face Recognizer as last resort
            FACE_RECOGNITION_AVAILABLE = True
            cv2 = cv2
            print("✅ Using OpenCV for face recognition")
except ImportError as e:
    FACE_RECOGNITION_AVAILABLE = False
    import sys
    print(f"⚠️ Face recognition not available: {e}", file=sys.stderr)
except Exception as e:
    FACE_RECOGNITION_AVAILABLE = False
    import sys
    print(f"⚠️ Face recognition import error: {e}", file=sys.stderr)


def staff_home(request):
    staff = get_object_or_404(Staff, admin=request.user)
    total_students = Student.objects.filter(course=staff.course).count()
    total_leave = LeaveReportStaff.objects.filter(staff=staff).count()
    subjects = Subject.objects.filter(staff=staff)
    total_subject = subjects.count()
    attendance_list = Attendance.objects.filter(subject__in=subjects)
    total_attendance = attendance_list.count()
    attendance_list = []
    subject_list = []
    for subject in subjects:
        attendance_count = Attendance.objects.filter(subject=subject).count()
        subject_list.append(subject.name)
        attendance_list.append(attendance_count)
    context = {
        'page_title': 'Staff Panel - ' + str(staff.admin.last_name) + ' (' + str(staff.course) + ')',
        'total_students': total_students,
        'total_attendance': total_attendance,
        'total_leave': total_leave,
        'total_subject': total_subject,
        'subject_list': subject_list,
        'attendance_list': attendance_list
    }
    return render(request, 'staff_template/home_content.html', context)


def staff_take_attendance(request):
    staff = get_object_or_404(Staff, admin=request.user)
    subjects = Subject.objects.filter(staff_id=staff)
    sessions = Session.objects.all()
    context = {
        'subjects': subjects,
        'sessions': sessions,
        'page_title': 'Take Attendance'
    }

    return render(request, 'staff_template/staff_take_attendance.html', context)


@csrf_exempt
def get_students(request):
    subject_id = request.POST.get('subject')
    session_id = request.POST.get('session')
    try:
        subject = get_object_or_404(Subject, id=subject_id)
        session = get_object_or_404(Session, id=session_id)
        students = Student.objects.filter(
            course_id=subject.course.id, session=session)
        student_data = []
        for student in students:
            data = {
                    "id": student.id,
                    "name": student.admin.last_name + " " + student.admin.first_name
                    }
            student_data.append(data)
        return JsonResponse(json.dumps(student_data), content_type='application/json', safe=False)
    except Exception as e:
        return e



@csrf_exempt
def save_attendance(request):
    student_data = request.POST.get('student_ids')
    date = request.POST.get('date')
    subject_id = request.POST.get('subject')
    session_id = request.POST.get('session')
    students = json.loads(student_data)
    try:
        session = get_object_or_404(Session, id=session_id)
        subject = get_object_or_404(Subject, id=subject_id)

        # Check if an attendance object already exists for the given date and session
        attendance, created = Attendance.objects.get_or_create(session=session, subject=subject, date=date)

        for student_dict in students:
            student = get_object_or_404(Student, id=student_dict.get('id'))

            # Check if an attendance report already exists for the student and the attendance object
            attendance_report, report_created = AttendanceReport.objects.get_or_create(student=student, attendance=attendance)

            # Update the status only if the attendance report was newly created
            if report_created:
                attendance_report.status = student_dict.get('status')
                attendance_report.save()

    except Exception as e:
        return None

    return HttpResponse("OK")


def staff_update_attendance(request):
    staff = get_object_or_404(Staff, admin=request.user)
    subjects = Subject.objects.filter(staff_id=staff)
    sessions = Session.objects.all()
    context = {
        'subjects': subjects,
        'sessions': sessions,
        'page_title': 'Update Attendance'
    }

    return render(request, 'staff_template/staff_update_attendance.html', context)


@csrf_exempt
def get_student_attendance(request):
    attendance_date_id = request.POST.get('attendance_date_id')
    try:
        date = get_object_or_404(Attendance, id=attendance_date_id)
        attendance_data = AttendanceReport.objects.filter(attendance=date)
        student_data = []
        for attendance in attendance_data:
            data = {"id": attendance.student.admin.id,
                    "name": attendance.student.admin.last_name + " " + attendance.student.admin.first_name,
                    "status": attendance.status}
            student_data.append(data)
        return JsonResponse(json.dumps(student_data), content_type='application/json', safe=False)
    except Exception as e:
        return e


@csrf_exempt
def update_attendance(request):
    student_data = request.POST.get('student_ids')
    date = request.POST.get('date')
    students = json.loads(student_data)
    try:
        attendance = get_object_or_404(Attendance, id=date)

        for student_dict in students:
            student = get_object_or_404(
                Student, admin_id=student_dict.get('id'))
            attendance_report = get_object_or_404(AttendanceReport, student=student, attendance=attendance)
            attendance_report.status = student_dict.get('status')
            attendance_report.save()
    except Exception as e:
        return None

    return HttpResponse("OK")


def staff_apply_leave(request):
    form = LeaveReportStaffForm(request.POST or None)
    staff = get_object_or_404(Staff, admin_id=request.user.id)
    context = {
        'form': form,
        'leave_history': LeaveReportStaff.objects.filter(staff=staff),
        'page_title': 'Apply for Leave'
    }
    if request.method == 'POST':
        if form.is_valid():
            try:
                obj = form.save(commit=False)
                obj.staff = staff
                obj.save()
                messages.success(
                    request, "Application for leave has been submitted for review")
                return redirect(reverse('staff_apply_leave'))
            except Exception:
                messages.error(request, "Could not apply!")
        else:
            messages.error(request, "Form has errors!")
    return render(request, "staff_template/staff_apply_leave.html", context)


def staff_feedback(request):
    form = FeedbackStaffForm(request.POST or None)
    staff = get_object_or_404(Staff, admin_id=request.user.id)
    context = {
        'form': form,
        'feedbacks': FeedbackStaff.objects.filter(staff=staff),
        'page_title': 'Add Feedback'
    }
    if request.method == 'POST':
        if form.is_valid():
            try:
                obj = form.save(commit=False)
                obj.staff = staff
                obj.save()
                messages.success(request, "Feedback submitted for review")
                return redirect(reverse('staff_feedback'))
            except Exception:
                messages.error(request, "Could not Submit!")
        else:
            messages.error(request, "Form has errors!")
    return render(request, "staff_template/staff_feedback.html", context)


def staff_view_profile(request):
    staff = get_object_or_404(Staff, admin=request.user)
    form = StaffEditForm(request.POST or None, request.FILES or None,instance=staff)
    context = {'form': form, 'page_title': 'View/Update Profile'}
    if request.method == 'POST':
        try:
            if form.is_valid():
                first_name = form.cleaned_data.get('first_name')
                last_name = form.cleaned_data.get('last_name')
                password = form.cleaned_data.get('password') or None
                address = form.cleaned_data.get('address')
                gender = form.cleaned_data.get('gender')
                passport = request.FILES.get('profile_pic') or None
                admin = staff.admin
                if password != None:
                    admin.set_password(password)
                if passport != None:
                    fs = FileSystemStorage()
                    filename = fs.save(passport.name, passport)
                    passport_url = fs.url(filename)
                    admin.profile_pic = passport_url
                admin.first_name = first_name
                admin.last_name = last_name
                admin.address = address
                admin.gender = gender
                admin.save()
                staff.save()
                messages.success(request, "Profile Updated!")
                return redirect(reverse('staff_view_profile'))
            else:
                messages.error(request, "Invalid Data Provided")
                return render(request, "staff_template/staff_view_profile.html", context)
        except Exception as e:
            messages.error(
                request, "Error Occured While Updating Profile " + str(e))
            return render(request, "staff_template/staff_view_profile.html", context)

    return render(request, "staff_template/staff_view_profile.html", context)


@csrf_exempt
def staff_fcmtoken(request):
    token = request.POST.get('token')
    try:
        staff_user = get_object_or_404(CustomUser, id=request.user.id)
        staff_user.fcm_token = token
        staff_user.save()
        return HttpResponse("True")
    except Exception as e:
        return HttpResponse("False")


def staff_view_notification(request):
    staff = get_object_or_404(Staff, admin=request.user)
    notifications = NotificationStaff.objects.filter(staff=staff)
    context = {
        'notifications': notifications,
        'page_title': "View Notifications"
    }
    return render(request, "staff_template/staff_view_notification.html", context)


def staff_add_result(request):
    staff = get_object_or_404(Staff, admin=request.user)
    subjects = Subject.objects.filter(staff=staff)
    sessions = Session.objects.all()
    context = {
        'page_title': 'Result Upload',
        'subjects': subjects,
        'sessions': sessions
    }
    if request.method == 'POST':
        try:
            student_id = request.POST.get('student_list')
            subject_id = request.POST.get('subject')
            test = request.POST.get('test')
            exam = request.POST.get('exam')
            student = get_object_or_404(Student, id=student_id)
            subject = get_object_or_404(Subject, id=subject_id)
            try:
                data = StudentResult.objects.get(
                    student=student, subject=subject)
                data.exam = exam
                data.test = test
                data.save()
                messages.success(request, "Scores Updated")
            except:
                result = StudentResult(student=student, subject=subject, test=test, exam=exam)
                result.save()
                messages.success(request, "Scores Saved")
        except Exception as e:
            messages.warning(request, "Error Occured While Processing Form")
    return render(request, "staff_template/staff_add_result.html", context)


@csrf_exempt
def fetch_student_result(request):
    try:
        subject_id = request.POST.get('subject')
        student_id = request.POST.get('student')
        student = get_object_or_404(Student, id=student_id)
        subject = get_object_or_404(Subject, id=subject_id)
        result = StudentResult.objects.get(student=student, subject=subject)
        result_data = {
            'exam': result.exam,
            'test': result.test
        }
        return HttpResponse(json.dumps(result_data))
    except Exception as e:
        return HttpResponse('False')


def staff_take_attendance_face(request):
    """Face recognition based attendance page"""
    staff = get_object_or_404(Staff, admin=request.user)
    subjects = Subject.objects.filter(staff_id=staff)
    sessions = Session.objects.all()
    context = {
        'subjects': subjects,
        'sessions': sessions,
        'page_title': 'Take Attendance (Face Recognition)',
        'face_recognition_available': FACE_RECOGNITION_AVAILABLE
    }
    return render(request, 'staff_template/staff_take_attendance_face.html', context)


@csrf_exempt
def register_student_face(request):
    """Register face encoding for a student"""
    if not FACE_RECOGNITION_AVAILABLE:
        return JsonResponse({'success': False, 'message': 'Face recognition library not available'})
    
    try:
        student_id = request.POST.get('student_id')
        image_data = request.POST.get('image')
        
        student = get_object_or_404(Student, id=student_id)
        
        # Decode base64 image
        image_data = image_data.split(',')[1] if ',' in image_data else image_data
        image_bytes = base64.b64decode(image_data)
        image = Image.open(BytesIO(image_bytes))
        
        # Convert RGBA to RGB if necessary (JPEG doesn't support transparency)
        if image.mode == 'RGBA':
            rgb_image = Image.new('RGB', image.size, (255, 255, 255))
            rgb_image.paste(image, mask=image.split()[3])  # Use alpha channel as mask
            image = rgb_image
        elif image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Save image temporarily
        import tempfile
        import os
        temp_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'media', 'temp_faces')
        os.makedirs(temp_dir, exist_ok=True)
        temp_image_path = os.path.join(temp_dir, f'student_{student_id}_temp.jpg')
        image.save(temp_image_path, 'JPEG')
        
        try:
            if deepface:
                # Use DeepFace to get embedding
                embedding = DeepFace.represent(
                    img_path=temp_image_path,
                    model_name='VGG-Face',
                    enforce_detection=False
                )
                
                if not embedding or len(embedding) == 0:
                    return JsonResponse({'success': False, 'message': 'No face detected in image'})
                
                if len(embedding) > 1:
                    return JsonResponse({'success': False, 'message': 'Multiple faces detected. Please use an image with only one face'})
                
                # Get embedding vector
                embedding_vector = embedding[0]['embedding']
                # Convert to numpy array and encode
                encoding_array = np.array(embedding_vector, dtype=np.float64)
                encoding_bytes = encoding_array.tobytes()
                encoding_base64 = base64.b64encode(encoding_bytes).decode('utf-8')
            elif face_recognition:
                # Fallback to face_recognition
                image_rgb = image.convert('RGB')
                img_array = np.array(image_rgb)
                face_encodings = face_recognition.face_encodings(img_array)
                
                if len(face_encodings) == 0:
                    return JsonResponse({'success': False, 'message': 'No face detected in image'})
                
                if len(face_encodings) > 1:
                    return JsonResponse({'success': False, 'message': 'Multiple faces detected. Please use an image with only one face'})
                
                encoding_bytes = face_encodings[0].tobytes()
                encoding_base64 = base64.b64encode(encoding_bytes).decode('utf-8')
            elif cv2:
                # Use OpenCV for face detection and feature extraction
                img_cv = cv2.imread(temp_image_path)
                gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
                
                # Load face detector
                face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
                faces = face_cascade.detectMultiScale(gray, 1.3, 5)
                
                if len(faces) == 0:
                    return JsonResponse({'success': False, 'message': 'No face detected in image'})
                
                if len(faces) > 1:
                    return JsonResponse({'success': False, 'message': 'Multiple faces detected. Please use an image with only one face'})
                
                # Extract face region
                (x, y, w, h) = faces[0]
                face_roi = gray[y:y+h, x:x+w]
                face_roi = cv2.resize(face_roi, (128, 128))
                
                # Flatten and normalize the face image
                face_features = face_roi.flatten().astype(np.float64)
                face_features = face_features / np.linalg.norm(face_features)  # Normalize
                
                encoding_bytes = face_features.tobytes()
                encoding_base64 = base64.b64encode(encoding_bytes).decode('utf-8')
            else:
                return JsonResponse({'success': False, 'message': 'Face recognition not available'})
            
            # Save or update face encoding
            face_encoding_obj, created = StudentFaceEncoding.objects.get_or_create(
                student=student,
                defaults={'encoding': encoding_base64}
            )
            
            if not created:
                face_encoding_obj.encoding = encoding_base64
                face_encoding_obj.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Face registered successfully!' if created else 'Face updated successfully!'
            })
        finally:
            # Clean up temp file
            if os.path.exists(temp_image_path):
                os.remove(temp_image_path)
        
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})


@csrf_exempt
def recognize_face_and_mark_attendance(request):
    """Recognize face from image and mark attendance automatically"""
    if not FACE_RECOGNITION_AVAILABLE:
        return JsonResponse({'success': False, 'message': 'Face recognition library not available'})
    
    try:
        image_data = request.POST.get('image')
        subject_id = request.POST.get('subject')
        session_id = request.POST.get('session')
        date = request.POST.get('date')
        
        if not all([subject_id, session_id, date]):
            return JsonResponse({'success': False, 'message': 'Missing required parameters'})
        
        subject = get_object_or_404(Subject, id=subject_id)
        session = get_object_or_404(Session, id=session_id)
        
        # Decode base64 image
        image_data = image_data.split(',')[1] if ',' in image_data else image_data
        image_bytes = base64.b64decode(image_data)
        image = Image.open(BytesIO(image_bytes))
        
        # Convert RGBA to RGB if necessary (JPEG doesn't support transparency)
        if image.mode == 'RGBA':
            rgb_image = Image.new('RGB', image.size, (255, 255, 255))
            rgb_image.paste(image, mask=image.split()[3])  # Use alpha channel as mask
            image = rgb_image
        elif image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Save image temporarily
        import tempfile
        import os
        temp_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'media', 'temp_faces')
        os.makedirs(temp_dir, exist_ok=True)
        temp_image_path = os.path.join(temp_dir, 'unknown_temp.jpg')
        image.save(temp_image_path, 'JPEG')
        
        try:
            # Get face encoding from uploaded image
            if deepface:
                unknown_embedding = DeepFace.represent(
                    img_path=temp_image_path,
                    model_name='VGG-Face',
                    enforce_detection=False
                )
                
                if not unknown_embedding or len(unknown_embedding) == 0:
                    return JsonResponse({'success': False, 'message': 'No face detected. Please ensure your face is visible.'})
                
                if len(unknown_embedding) > 1:
                    return JsonResponse({'success': False, 'message': 'Multiple faces detected. Please ensure only one person is in frame.'})
                
                unknown_encoding = np.array(unknown_embedding[0]['embedding'], dtype=np.float64)
            elif face_recognition:
                # Fallback to face_recognition
                image_rgb = image.convert('RGB')
                img_array = np.array(image_rgb)
                face_encodings = face_recognition.face_encodings(img_array)
                
                if len(face_encodings) == 0:
                    return JsonResponse({'success': False, 'message': 'No face detected. Please ensure your face is visible.'})
                
                if len(face_encodings) > 1:
                    return JsonResponse({'success': False, 'message': 'Multiple faces detected. Please ensure only one person is in frame.'})
                
                unknown_encoding = face_encodings[0]
            elif cv2:
                # Use OpenCV for face detection
                img_cv = cv2.imread(temp_image_path)
                gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
                
                face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
                faces = face_cascade.detectMultiScale(gray, 1.3, 5)
                
                if len(faces) == 0:
                    return JsonResponse({'success': False, 'message': 'No face detected. Please ensure your face is visible.'})
                
                if len(faces) > 1:
                    return JsonResponse({'success': False, 'message': 'Multiple faces detected. Please ensure only one person is in frame.'})
                
                (x, y, w, h) = faces[0]
                face_roi = gray[y:y+h, x:x+w]
                face_roi = cv2.resize(face_roi, (128, 128))
                face_features = face_roi.flatten().astype(np.float64)
                face_features = face_features / np.linalg.norm(face_features)
                unknown_encoding = face_features
            else:
                return JsonResponse({'success': False, 'message': 'Face recognition not available'})
            
            # Get all students for this course and session
            students = Student.objects.filter(course=subject.course, session=session)
            
            # Compare with stored face encodings
            recognized_students = []
            for student in students:
                try:
                    face_encoding_obj = StudentFaceEncoding.objects.get(student=student)
                    # Decode stored encoding
                    stored_encoding_bytes = base64.b64decode(face_encoding_obj.encoding)
                    stored_encoding = np.frombuffer(stored_encoding_bytes, dtype=np.float64)
                    
                    # Compare faces
                    if deepface:
                        # Use cosine similarity for DeepFace
                        from sklearn.metrics.pairwise import cosine_similarity
                        similarity = cosine_similarity([unknown_encoding], [stored_encoding])[0][0]
                        face_distance = 1 - similarity
                        matches = similarity > 0.6
                    elif face_recognition:
                        # Use face_recognition methods
                        matches = face_recognition.compare_faces([stored_encoding], unknown_encoding, tolerance=0.6)
                        face_distance = face_recognition.face_distance([stored_encoding], unknown_encoding)[0]
                        matches = matches[0] if isinstance(matches, list) else matches
                    elif cv2:
                        # Use cosine similarity for OpenCV features
                        from sklearn.metrics.pairwise import cosine_similarity
                        similarity = cosine_similarity([unknown_encoding], [stored_encoding])[0][0]
                        face_distance = 1 - similarity
                        matches = similarity > 0.7  # Slightly higher threshold for OpenCV
                    else:
                        matches = False
                        face_distance = 1.0
                    
                    threshold = 0.6 if not cv2 else 0.3  # Different threshold for OpenCV
                    if matches and face_distance < threshold:
                        confidence = (1 - face_distance) * 100
                        recognized_students.append({
                            'student_id': student.id,
                            'name': f"{student.admin.first_name} {student.admin.last_name}",
                            'confidence': round(confidence, 2)
                        })
                except StudentFaceEncoding.DoesNotExist:
                    continue
            
            if not recognized_students:
                return JsonResponse({
                    'success': False,
                    'message': 'Face not recognized. Please register your face first or ensure good lighting.',
                    'recognized': []
                })
            
            # Get the best match (highest confidence)
            best_match = max(recognized_students, key=lambda x: x['confidence'])
            
            # Mark attendance for recognized student
            attendance, created = Attendance.objects.get_or_create(
                session=session,
                subject=subject,
                date=date
            )
            
            student = get_object_or_404(Student, id=best_match['student_id'])
            attendance_report, report_created = AttendanceReport.objects.get_or_create(
                student=student,
                attendance=attendance
            )
            
            if report_created:
                attendance_report.status = True
                attendance_report.save()
            
            return JsonResponse({
                'success': True,
                'message': f'Attendance marked for {best_match["name"]} (Confidence: {best_match["confidence"]}%)',
                'recognized': best_match
            })
        finally:
            # Clean up temp file
            if os.path.exists(temp_image_path):
                os.remove(temp_image_path)
        
    except Exception as e:
        import traceback
        return JsonResponse({'success': False, 'message': f'Error: {str(e)}\n{traceback.format_exc()}'})


@csrf_exempt
def get_students_for_face_registration(request):
    """Get list of students for face registration"""
    subject_id = request.POST.get('subject')
    session_id = request.POST.get('session')
    try:
        subject = get_object_or_404(Subject, id=subject_id)
        session = get_object_or_404(Session, id=session_id)
        students = Student.objects.filter(
            course_id=subject.course.id, session=session)
        student_data = []
        for student in students:
            has_face = StudentFaceEncoding.objects.filter(student=student).exists()
            data = {
                "id": student.id,
                "name": student.admin.last_name + " " + student.admin.first_name,
                "has_face_registered": has_face
            }
            student_data.append(data)
        return JsonResponse(json.dumps(student_data), content_type='application/json', safe=False)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)
