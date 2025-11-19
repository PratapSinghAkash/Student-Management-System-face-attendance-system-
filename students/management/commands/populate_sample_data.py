"""
Django management command to populate the database with sample data
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
import random

from students.models import Student, Course, Attendance


class Command(BaseCommand):
    help = 'Populates the database with sample student and attendance data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--students',
            type=int,
            default=10,
            help='Number of sample students to create (default: 10)'
        )

    def handle(self, *args, **options):
        num_students = options['students']
        
        self.stdout.write(self.style.WARNING(f'Creating {num_students} sample students...'))
        
        # Sample data
        departments = ['Computer Science', 'Electronics', 'Mechanical', 'Civil', 'Electrical']
        first_names = ['John', 'Emma', 'Michael', 'Sophia', 'William', 'Olivia', 'James', 'Ava', 'Robert', 'Isabella']
        last_names = ['Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller', 'Davis', 'Rodriguez', 'Martinez']
        
        # Create students
        students_created = 0
        for i in range(num_students):
            roll_number = f'STU{2024}{i+1:04d}'
            first_name = random.choice(first_names)
            last_name = random.choice(last_names)
            email = f'{first_name.lower()}.{last_name.lower()}{i}@university.edu'
            department = random.choice(departments)
            year = random.randint(1, 4)
            
            try:
                student, created = Student.objects.get_or_create(
                    roll_number=roll_number,
                    defaults={
                        'first_name': first_name,
                        'last_name': last_name,
                        'email': email,
                        'department': department,
                        'year': year,
                        'phone': f'+1-555-{random.randint(1000, 9999)}',
                        'is_active': True
                    }
                )
                
                if created:
                    students_created += 1
                    self.stdout.write(f'  Created: {student}')
                    
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'  Error creating student: {e}'))
        
        self.stdout.write(self.style.SUCCESS(f'\n✓ Created {students_created} new students'))
        
        # Create sample courses
        self.stdout.write(self.style.WARNING('\nCreating sample courses...'))
        courses_data = [
            ('CS101', 'Introduction to Programming', 'Computer Science'),
            ('CS201', 'Data Structures', 'Computer Science'),
            ('EE101', 'Basic Electronics', 'Electronics'),
            ('ME101', 'Engineering Mechanics', 'Mechanical'),
        ]
        
        courses_created = 0
        for code, name, dept in courses_data:
            course, created = Course.objects.get_or_create(
                code=code,
                defaults={
                    'name': name,
                    'department': dept,
                    'description': f'This is {name} course for {dept} department'
                }
            )
            
            if created:
                courses_created += 1
                # Assign random students to the course
                students = Student.objects.filter(department=dept)[:5]
                course.students.set(students)
                self.stdout.write(f'  Created: {course} with {students.count()} students')
        
        self.stdout.write(self.style.SUCCESS(f'\n✓ Created {courses_created} new courses'))
        
        # Create sample attendance records for the last 7 days
        self.stdout.write(self.style.WARNING('\nCreating sample attendance records...'))
        attendance_created = 0
        
        all_students = Student.objects.filter(is_active=True)
        today = timezone.now().date()
        
        for day in range(7):
            date = today - timedelta(days=day)
            
            for student in all_students:
                # Randomly mark attendance (90% present, 10% absent)
                status = 'present' if random.random() < 0.9 else 'absent'
                
                try:
                    attendance, created = Attendance.objects.get_or_create(
                        student=student,
                        date=date,
                        defaults={
                            'time': timezone.now().time(),
                            'status': status,
                            'marked_by': 'Sample Data Generator',
                            'remarks': 'Auto-generated for demo'
                        }
                    )
                    
                    if created:
                        attendance_created += 1
                        
                except Exception as e:
                    pass  # Skip duplicates
        
        self.stdout.write(self.style.SUCCESS(f'\n✓ Created {attendance_created} attendance records'))
        
        # Summary
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS('Database populated successfully!'))
        self.stdout.write('='*60)
        self.stdout.write(f'\nTotal Students: {Student.objects.count()}')
        self.stdout.write(f'Total Courses: {Course.objects.count()}')
        self.stdout.write(f'Total Attendance Records: {Attendance.objects.count()}')
        self.stdout.write('\nYou can now access the application at http://localhost:8000')
        self.stdout.write('Admin panel: http://localhost:8000/admin/\n')
