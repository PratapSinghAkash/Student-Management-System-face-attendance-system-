# Installation Quick Start Guide

Get your Student Attendance System running in minutes!

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Git

## Installation Steps

### 1. Clone the Repository

```bash
git clone https://github.com/PratapSinghAkash/Student-Management-System-face-attendance-system-.git
cd Student-Management-System-face-attendance-system-
```

### 2. Create Virtual Environment (Optional but Recommended)

```bash
# On Linux/Mac
python3 -m venv venv
source venv/bin/activate

# On Windows
python -m venv venv
venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Set Up Database

```bash
python manage.py migrate
```

### 5. Create Admin User

```bash
python manage.py createsuperuser
```

Follow the prompts to create your admin account.

### 6. Generate Sample Data (Optional)

```bash
# Create 10 sample students with attendance records
python manage.py populate_sample_data --students 10
```

### 7. Run the Server

```bash
python manage.py runserver
```

Visit `http://localhost:8000` to access the application!

## Default URLs

- **Home Dashboard**: http://localhost:8000/
- **Student List**: http://localhost:8000/students/
- **Manual Attendance**: http://localhost:8000/attendance/manual/
- **Face Recognition**: http://localhost:8000/attendance/mark/
- **Reports**: http://localhost:8000/attendance/report/
- **Admin Panel**: http://localhost:8000/admin/

## Quick Tour

### 1. Add Your First Student

1. Click "Students" in the navigation menu
2. Click "Add Student" button
3. Fill in the student details
4. Upload a clear photo (optional but needed for face recognition)
5. Click "Create Student"

### 2. Mark Attendance Manually

1. Navigate to "Manual Attendance"
2. Select status for each student (Present/Absent/Late)
3. Click "Mark" to record attendance

### 3. View Reports

1. Go to "Reports" in the menu
2. Select date range and department
3. Click "Generate Report" to view statistics

### 4. Admin Panel Features

Login to the admin panel (`/admin/`) to:
- Bulk manage students
- View detailed attendance records
- Manage courses and enrollments
- Export data

## Face Recognition Setup (Optional)

For automatic attendance using face recognition, see [FACE_RECOGNITION_GUIDE.md](FACE_RECOGNITION_GUIDE.md)

Quick install:

```bash
# Ubuntu/Debian
sudo apt-get install cmake libopenblas-dev liblapack-dev
pip install dlib face-recognition

# macOS
brew install cmake
pip install dlib face-recognition

# Windows
# Install Visual Studio Build Tools first
pip install cmake dlib face-recognition
```

## Troubleshooting

### Port Already in Use

```bash
# Run on a different port
python manage.py runserver 8080
```

### Database Issues

```bash
# Reset database
rm db.sqlite3
python manage.py migrate
python manage.py createsuperuser
python manage.py populate_sample_data
```

### Static Files Not Loading

```bash
python manage.py collectstatic
```

## Project Structure

```
Student-Management-System/
├── attendance_system/     # Django project settings
├── students/             # Main application
│   ├── templates/       # HTML templates
│   ├── management/      # Custom commands
│   ├── models.py        # Database models
│   ├── views.py         # View logic
│   └── forms.py         # Django forms
├── media/               # Uploaded photos
├── db.sqlite3          # Database file
├── manage.py           # Django management script
└── requirements.txt    # Python dependencies
```

## Common Commands

```bash
# Create sample data
python manage.py populate_sample_data --students 20

# Run development server
python manage.py runserver

# Create admin user
python manage.py createsuperuser

# Run migrations
python manage.py migrate

# Create new migrations
python manage.py makemigrations

# Django shell
python manage.py shell

# Check for issues
python manage.py check
```

## Next Steps

1. **Customize Settings**: Edit `attendance_system/settings.py` for production
2. **Add Students**: Populate with your actual student data
3. **Configure Face Recognition**: Follow the face recognition guide
4. **Set Up Courses**: Add courses via admin panel
5. **Train System**: Upload clear student photos for recognition

## Support

For detailed documentation, see:
- [README.md](README.md) - Complete project documentation
- [FACE_RECOGNITION_GUIDE.md](FACE_RECOGNITION_GUIDE.md) - Face recognition implementation

## License

MIT License - See project repository for details

---

Happy Attendance Tracking! 🎓📸✅
