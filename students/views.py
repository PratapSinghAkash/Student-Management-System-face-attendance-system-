from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q, Count
from datetime import datetime, timedelta
import json
import cv2
import numpy as np
import base64
from .models import Student, Attendance, Course
from .forms import StudentForm


def home(request):
    """Home page with dashboard statistics"""
    total_students = Student.objects.filter(is_active=True).count()
    today = timezone.now().date()
    today_attendance = Attendance.objects.filter(date=today).count()
    total_courses = Course.objects.count()
    
    # Recent attendance records
    recent_attendance = Attendance.objects.select_related('student').order_by('-created_at')[:10]
    
    context = {
        'total_students': total_students,
        'today_attendance': today_attendance,
        'total_courses': total_courses,
        'recent_attendance': recent_attendance,
    }
    return render(request, 'students/home.html', context)


def student_list(request):
    """Display list of all students"""
    query = request.GET.get('q', '')
    department = request.GET.get('department', '')
    year = request.GET.get('year', '')
    
    students = Student.objects.filter(is_active=True)
    
    if query:
        students = students.filter(
            Q(roll_number__icontains=query) |
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(email__icontains=query)
        )
    
    if department:
        students = students.filter(department=department)
    
    if year:
        students = students.filter(year=year)
    
    departments = Student.objects.values_list('department', flat=True).distinct()
    years = Student.objects.values_list('year', flat=True).distinct().order_by('year')
    
    context = {
        'students': students,
        'query': query,
        'departments': departments,
        'years': years,
        'selected_department': department,
        'selected_year': year,
    }
    return render(request, 'students/student_list.html', context)


def student_detail(request, pk):
    """Display detailed information about a student"""
    student = get_object_or_404(Student, pk=pk)
    attendances = student.attendances.order_by('-date')[:30]
    
    # Calculate attendance statistics
    total_days = attendances.count()
    present_days = attendances.filter(status='present').count()
    attendance_percentage = (present_days / total_days * 100) if total_days > 0 else 0
    
    context = {
        'student': student,
        'attendances': attendances,
        'attendance_percentage': round(attendance_percentage, 2),
    }
    return render(request, 'students/student_detail.html', context)


def student_create(request):
    """Create a new student"""
    if request.method == 'POST':
        form = StudentForm(request.POST, request.FILES)
        if form.is_valid():
            student = form.save()
            messages.success(request, f'Student {student.get_full_name()} created successfully!')
            return redirect('student_detail', pk=student.pk)
    else:
        form = StudentForm()
    
    return render(request, 'students/student_form.html', {'form': form, 'action': 'Create'})


def student_update(request, pk):
    """Update an existing student"""
    student = get_object_or_404(Student, pk=pk)
    
    if request.method == 'POST':
        form = StudentForm(request.POST, request.FILES, instance=student)
        if form.is_valid():
            student = form.save()
            messages.success(request, f'Student {student.get_full_name()} updated successfully!')
            return redirect('student_detail', pk=student.pk)
    else:
        form = StudentForm(instance=student)
    
    return render(request, 'students/student_form.html', {'form': form, 'action': 'Update', 'student': student})


def student_delete(request, pk):
    """Soft delete a student"""
    student = get_object_or_404(Student, pk=pk)
    
    if request.method == 'POST':
        student.is_active = False
        student.save()
        messages.success(request, f'Student {student.get_full_name()} deleted successfully!')
        return redirect('student_list')
    
    return render(request, 'students/student_confirm_delete.html', {'student': student})


def mark_attendance(request):
    """Mark attendance using face recognition"""
    if request.method == 'POST':
        # Handle face recognition data from webcam
        data = json.loads(request.body)
        image_data = data.get('image')
        
        # Process the image and recognize face
        # This is a placeholder for actual face recognition logic
        # In production, you would use face_recognition library here
        
        messages.info(request, 'Face recognition feature requires face_recognition library installation.')
        return redirect('home')
    
    return render(request, 'students/mark_attendance.html')


def manual_attendance(request):
    """Manually mark attendance for students"""
    if request.method == 'POST':
        student_id = request.POST.get('student_id')
        status = request.POST.get('status', 'present')
        remarks = request.POST.get('remarks', '')
        
        student = get_object_or_404(Student, pk=student_id)
        today = timezone.now().date()
        
        # Check if attendance already exists for today
        attendance, created = Attendance.objects.get_or_create(
            student=student,
            date=today,
            defaults={
                'time': timezone.now().time(),
                'status': status,
                'marked_by': 'Manual Entry',
                'remarks': remarks,
            }
        )
        
        if not created:
            attendance.status = status
            attendance.time = timezone.now().time()
            attendance.marked_by = 'Manual Entry'
            attendance.remarks = remarks
            attendance.save()
            messages.info(request, f'Attendance updated for {student.get_full_name()}')
        else:
            messages.success(request, f'Attendance marked for {student.get_full_name()}')
        
        return redirect('manual_attendance')
    
    students = Student.objects.filter(is_active=True).order_by('roll_number')
    today = timezone.now().date()
    today_attendance = Attendance.objects.filter(date=today).values_list('student_id', flat=True)
    
    context = {
        'students': students,
        'today_attendance': list(today_attendance),
    }
    return render(request, 'students/manual_attendance.html', context)


def attendance_report(request):
    """Display attendance reports"""
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    department = request.GET.get('department', '')
    
    if not start_date:
        start_date = (timezone.now() - timedelta(days=30)).date()
    else:
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
    
    if not end_date:
        end_date = timezone.now().date()
    else:
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
    
    # Get attendance records
    attendances = Attendance.objects.filter(date__range=[start_date, end_date])
    
    if department:
        attendances = attendances.filter(student__department=department)
    
    # Group by student and calculate statistics
    student_stats = {}
    students = Student.objects.filter(is_active=True)
    
    if department:
        students = students.filter(department=department)
    
    for student in students:
        student_attendances = attendances.filter(student=student)
        total = student_attendances.count()
        present = student_attendances.filter(status='present').count()
        percentage = (present / total * 100) if total > 0 else 0
        
        student_stats[student.id] = {
            'student': student,
            'total': total,
            'present': present,
            'absent': total - present,
            'percentage': round(percentage, 2),
        }
    
    departments = Student.objects.values_list('department', flat=True).distinct()
    
    context = {
        'student_stats': student_stats.values(),
        'start_date': start_date,
        'end_date': end_date,
        'departments': departments,
        'selected_department': department,
    }
    return render(request, 'students/attendance_report.html', context)
