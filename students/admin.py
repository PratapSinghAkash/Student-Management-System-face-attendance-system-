from django.contrib import admin
from .models import Student, Attendance, Course


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ['roll_number', 'first_name', 'last_name', 'email', 'department', 'year', 'is_active']
    list_filter = ['department', 'year', 'is_active']
    search_fields = ['roll_number', 'first_name', 'last_name', 'email']
    ordering = ['roll_number']
    list_per_page = 20


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ['student', 'date', 'time', 'status', 'marked_by']
    list_filter = ['status', 'date', 'marked_by']
    search_fields = ['student__roll_number', 'student__first_name', 'student__last_name']
    date_hierarchy = 'date'
    ordering = ['-date', '-time']
    list_per_page = 50


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'department']
    list_filter = ['department']
    search_fields = ['code', 'name', 'department']
    filter_horizontal = ['students']
    ordering = ['code']
