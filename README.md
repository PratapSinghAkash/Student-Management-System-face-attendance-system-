# Student Management System with Face Attendance

Student Management System with Automatic Attendance using Django, OpenCV, and Face Recognition. Detects and recognizes student faces in real time and marks attendance automatically, storing records in SQLite. A fast, accurate, and modern solution for digital attendance tracking.

## Features

- 📚 **Student Management**: Add, edit, view, and manage student records
- 📸 **Face Recognition Attendance**: Automatic attendance marking using facial recognition (requires face_recognition library)
- ✍️ **Manual Attendance**: Mark attendance manually when needed
- 📊 **Attendance Reports**: Generate detailed attendance reports with statistics
- 🎓 **Course Management**: Manage courses and student enrollments
- 🔍 **Search & Filter**: Search students by name, roll number, department, or year
- 📱 **Responsive Design**: Mobile-friendly interface using Bootstrap 5
- 🗄️ **SQLite Database**: Lightweight database for storing all records

## Technology Stack

- **Backend**: Django 5.2.8
- **Database**: SQLite3
- **Frontend**: Bootstrap 5, Bootstrap Icons
- **Computer Vision**: OpenCV
- **Face Recognition**: face_recognition library (optional)
- **Image Processing**: Pillow, NumPy

## Installation

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)

### Step 1: Clone the Repository

```bash
git clone https://github.com/PratapSinghAkash/Student-Management-System-face-attendance-system-.git
cd Student-Management-System-face-attendance-system-
```

### Step 2: Create Virtual Environment (Recommended)

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Install Face Recognition (Optional but Recommended)

The face recognition feature requires additional libraries. Install them based on your operating system:

#### For Ubuntu/Debian:
```bash
sudo apt-get update
sudo apt-get install cmake
sudo apt-get install libopenblas-dev liblapack-dev
pip install dlib
pip install face-recognition
```

#### For macOS:
```bash
brew install cmake
pip install dlib
pip install face-recognition
```

#### For Windows:
```bash
# Install Visual Studio Build Tools first
# Then install dlib and face_recognition
pip install dlib
pip install face-recognition
```

**Note**: If face_recognition installation fails, you can still use the system with manual attendance marking.

### Step 5: Run Migrations

```bash
python manage.py migrate
```

### Step 6: Create Superuser (Admin)

```bash
python manage.py createsuperuser
```

Follow the prompts to create an admin account.

### Step 7: Run the Development Server

```bash
python manage.py runserver
```

The application will be available at `http://localhost:8000`

## Usage

### Admin Panel

Access the admin panel at `http://localhost:8000/admin/` to:
- Manage students, attendance records, and courses
- View comprehensive data tables
- Perform bulk operations

### Main Application

#### 1. Dashboard (Home)
- View statistics: Total students, today's attendance, total courses
- Quick actions for marking attendance
- Recent attendance records

#### 2. Student Management
- **Add Students**: Navigate to Students → Add Student
  - Enter student details (roll number, name, email, department, year)
  - Upload a clear photo for face recognition
- **View Students**: Browse all students with search and filter options
- **Edit Students**: Update student information
- **View Details**: See student profile and attendance history

#### 3. Mark Attendance

##### Option A: Face Recognition (Recommended)
1. Navigate to "Face Recognition" in the menu
2. Allow camera access
3. Students' faces will be detected and matched automatically
4. Attendance is marked in real-time

##### Option B: Manual Entry
1. Navigate to "Manual Attendance"
2. Select student status (Present/Absent/Late)
3. Click "Mark" to record attendance

#### 4. Attendance Reports
- Navigate to "Reports" in the menu
- Select date range and department
- View attendance statistics and percentages
- Print reports for record-keeping

## Project Structure

```
Student-Management-System-face-attendance-system-/
├── attendance_system/          # Django project settings
│   ├── settings.py            # Project configuration
│   ├── urls.py                # Main URL routing
│   └── wsgi.py                # WSGI configuration
├── students/                   # Main application
│   ├── models.py              # Database models (Student, Attendance, Course)
│   ├── views.py               # View functions
│   ├── forms.py               # Django forms
│   ├── urls.py                # App URL routing
│   ├── admin.py               # Admin panel configuration
│   ├── templates/             # HTML templates
│   │   └── students/          # App templates
│   └── migrations/            # Database migrations
├── media/                      # User uploaded files (student photos)
├── staticfiles/               # Collected static files
├── db.sqlite3                 # SQLite database
├── manage.py                  # Django management script
├── requirements.txt           # Python dependencies
├── .gitignore                 # Git ignore rules
└── README.md                  # This file
```

## Models

### Student
- Roll number (unique identifier)
- Name (first and last)
- Email
- Phone
- Department
- Year
- Photo (for face recognition)
- Face encoding (stored for matching)
- Active status

### Attendance
- Student reference
- Date and time
- Status (Present/Absent/Late)
- Marked by (system or manual)
- Remarks

### Course
- Course code
- Course name
- Description
- Department
- Enrolled students

## API Endpoints

- `/` - Home dashboard
- `/students/` - List all students
- `/students/<id>/` - Student detail view
- `/students/create/` - Add new student
- `/students/<id>/update/` - Edit student
- `/students/<id>/delete/` - Delete student
- `/attendance/mark/` - Face recognition attendance
- `/attendance/manual/` - Manual attendance marking
- `/attendance/report/` - Attendance reports
- `/admin/` - Django admin panel

## Configuration

### Settings (attendance_system/settings.py)

Key configurations:
- `DEBUG`: Set to `False` in production
- `ALLOWED_HOSTS`: Add your domain in production
- `DATABASES`: SQLite by default (can be changed to PostgreSQL/MySQL)
- `MEDIA_ROOT`: Location for uploaded files
- `STATIC_ROOT`: Location for static files

## Face Recognition Setup

The face recognition system works by:
1. Extracting face encodings from student photos during registration
2. Storing encodings in the database
3. Comparing live camera feed against stored encodings
4. Automatically marking attendance when a match is found

For best results:
- Use clear, front-facing photos
- Ensure good lighting
- Avoid obstructions (glasses, masks may affect recognition)

## Troubleshooting

### Face Recognition Installation Issues
If you encounter errors installing face_recognition:
- Ensure cmake is installed
- Install build tools for your platform
- Use the manual attendance feature as an alternative

### Database Errors
If you see database errors:
```bash
python manage.py migrate --run-syncdb
```

### Static Files Not Loading
Collect static files:
```bash
python manage.py collectstatic
```

### Port Already in Use
Run on a different port:
```bash
python manage.py runserver 8080
```

## Security Notes

- Change `SECRET_KEY` in production
- Set `DEBUG = False` in production
- Use environment variables for sensitive data
- Implement HTTPS in production
- Regularly backup the database

## Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

This project is open source and available under the MIT License.

## Support

For issues, questions, or contributions, please visit:
https://github.com/PratapSinghAkash/Student-Management-System-face-attendance-system-

## Acknowledgments

- Django framework
- OpenCV library
- face_recognition library by Adam Geitgey
- Bootstrap team

---

Made with ❤️ for educational institutions seeking automated attendance solutions.
