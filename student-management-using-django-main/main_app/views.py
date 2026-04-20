import json
import base64
import random
import re
from io import BytesIO

import pyotp
import qrcode
import requests
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render, reverse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings

from .EmailBackend import EmailBackend
from .models import Attendance, CustomUser, Session, Subject


CHATBOT_MESSAGES = {
    "en": {
        "welcome": "Hi! I am your Student Management assistant. I am available 24/7. How can I help you today?",
        "greeting": "Hello! How can I assist you today?",
        "admission": "For admission details, please contact the administration office or use the contact section on this website.",
        "course": "You can check available courses after login from the course/subject sections.",
        "attendance": "Attendance information is available in the student and staff attendance sections after login.",
        "fee": "For fee details, please contact the accounts/admin office.",
        "contact": "You can reach the school administration from the contact section or by visiting the office during working hours.",
        "support": "For technical support, please report the issue to your school admin or staff coordinator.",
        "bye": "Thank you for visiting. I am here anytime you need help.",
        "fallback": "I can help with admission, courses, attendance, fees, contact, and support. Please tell me what you need."
    },
    "hi": {
        "welcome": "Namaste! Main Student Management assistant hoon. Main 24/7 uplabdh hoon. Main aapki kaise madad kar sakta hoon?",
        "greeting": "Namaste! Main aapki kaise madad kar sakta hoon?",
        "admission": "Admission ki jankari ke liye kripya administration office se sampark karein ya website ke contact section ka upyog karein.",
        "course": "Upalabdh courses login ke baad course/subject sections mein dekhe ja sakte hain.",
        "attendance": "Attendance ki jankari login ke baad student aur staff attendance sections mein uplabdh hai.",
        "fee": "Fee details ke liye kripya accounts/admin office se sampark karein.",
        "contact": "Aap contact section ke madhyam se ya office visit karke administration se sampark kar sakte hain.",
        "support": "Technical support ke liye kripya school admin ya staff coordinator ko issue batayen.",
        "bye": "Yahan aane ke liye dhanyavad. Jab bhi madad chahiye ho, main yahin hoon.",
        "fallback": "Main admission, courses, attendance, fees, contact aur support mein madad kar sakta hoon. Kripya batayen aapko kya chahiye."
    },
    "es": {
        "welcome": "Hola. Soy tu asistente del sistema estudiantil. Estoy disponible 24/7. ¿En que puedo ayudarte?",
        "greeting": "Hola. ¿Como puedo ayudarte hoy?",
        "admission": "Para detalles de admision, contacta a la oficina administrativa o usa la seccion de contacto del sitio.",
        "course": "Puedes ver los cursos disponibles despues de iniciar sesion en las secciones de cursos y materias.",
        "attendance": "La informacion de asistencia esta disponible despues de iniciar sesion en las secciones de asistencia.",
        "fee": "Para informacion de pagos, contacta a la oficina de administracion/cuentas.",
        "contact": "Puedes comunicarte con la administracion desde la seccion de contacto o visitando la oficina.",
        "support": "Para soporte tecnico, reporta el problema al administrador escolar o coordinador.",
        "bye": "Gracias por visitarnos. Estoy aqui cuando necesites ayuda.",
        "fallback": "Puedo ayudar con admision, cursos, asistencia, pagos, contacto y soporte. Dime que necesitas."
    },
    "fr": {
        "welcome": "Bonjour. Je suis votre assistant du systeme scolaire. Je suis disponible 24h/24 et 7j/7. Comment puis-je vous aider ?",
        "greeting": "Bonjour. Comment puis-je vous aider aujourd'hui ?",
        "admission": "Pour les informations d'admission, veuillez contacter l'administration ou utiliser la section contact du site.",
        "course": "Vous pouvez consulter les cours disponibles apres connexion dans les sections cours et matieres.",
        "attendance": "Les informations de presence sont disponibles apres connexion dans les sections de presence.",
        "fee": "Pour les details des frais, veuillez contacter le bureau des comptes/administration.",
        "contact": "Vous pouvez joindre l'administration via la section contact ou en visitant le bureau.",
        "support": "Pour le support technique, signalez le probleme a l'administrateur scolaire ou au coordinateur.",
        "bye": "Merci de votre visite. Je suis ici a tout moment pour vous aider.",
        "fallback": "Je peux aider pour l'admission, les cours, la presence, les frais, le contact et le support. Dites-moi ce dont vous avez besoin."
    },
}

CHATBOT_KEYWORDS = {
    "greeting": ["hi", "hello", "hey", "hola", "bonjour", "namaste"],
    "admission": ["admission", "admissions", "apply", "enroll", "enrol", "registration", "pravesh"],
    "course": ["course", "courses", "subject", "subjects", "class", "program", "programme", "syllabus"],
    "attendance": ["attendance", "present", "absent", "attend", "hajri"],
    "fee": ["fee", "fees", "payment", "tuition", "cost", "charges"],
    "contact": ["contact", "phone", "email", "address", "office", "help desk"],
    "support": ["support", "problem", "issue", "error", "bug", "login issue", "technical"],
    "bye": ["bye", "goodbye", "thanks", "thank you", "dhanyavad", "gracias", "merci"]
}


def _pick_chatbot_language(language_code):
    if not language_code:
        return "en"
    language_code = language_code.lower().strip()
    if language_code in CHATBOT_MESSAGES:
        return language_code
    if "-" in language_code:
        short_code = language_code.split("-")[0]
        if short_code in CHATBOT_MESSAGES:
            return short_code
    return "en"


def _detect_chatbot_intent(message_text):
    text = (message_text or "").lower().strip()
    if not text:
        return "welcome"

    for intent_name, keywords in CHATBOT_KEYWORDS.items():
        if any(keyword in text for keyword in keywords):
            return intent_name

    return "fallback"


@csrf_exempt
def website_chatbot(request):
    if request.method != 'POST':
        return JsonResponse({"error": "Only POST is allowed"}, status=405)

    try:
        payload = json.loads(request.body.decode('utf-8')) if request.body else {}
    except (ValueError, UnicodeDecodeError):
        payload = {}

    user_message = (payload.get('message') or '').strip()
    language_code = _pick_chatbot_language(payload.get('language') or request.headers.get('Accept-Language', 'en'))
    intent_name = _detect_chatbot_intent(user_message)

    response_bank = CHATBOT_MESSAGES.get(language_code, CHATBOT_MESSAGES["en"])
    reply_text = response_bank.get(intent_name, response_bank["fallback"])

    return JsonResponse({
        "reply": reply_text,
        "intent": intent_name,
        "language": language_code,
        "available_languages": list(CHATBOT_MESSAGES.keys()),
        "is_24_7": True,
    })

# Create your views here.


def login_page(request):
    if request.user.is_authenticated:
        if request.user.user_type == '1':
            return redirect(reverse("admin_home"))
        elif request.user.user_type == '2':
            return redirect(reverse("staff_home"))
        else:
            return redirect(reverse("student_home"))
    return render(request, 'main_app/login.html', {
        'registration_pending': bool(request.session.get('pending_registration')),
    })


def _normalize_mobile_number(mobile_number):
    return re.sub(r'\D', '', mobile_number or '')


def _send_registration_email_otp(email, otp_code):
    subject = "Student Management - Email Verification Code"
    message = (
        "Your verification code is: {code}\n\n"
        "This code is valid for one registration attempt."
    ).format(code=otp_code)
    from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', None) or getattr(settings, 'EMAIL_HOST_USER', None) or 'noreply@student-management.local'
    send_mail(subject, message, from_email, [email], fail_silently=False)


def _send_registration_mobile_otp(mobile_number, otp_code):
    account_sid = (getattr(settings, 'TWILIO_ACCOUNT_SID', '') or '').strip()
    auth_token = (getattr(settings, 'TWILIO_AUTH_TOKEN', '') or '').strip()
    from_number = (getattr(settings, 'TWILIO_FROM_NUMBER', '') or '').strip()

    if not account_sid or not auth_token or not from_number:
        raise RuntimeError('Twilio SMS is not configured.')

    to_number = mobile_number if mobile_number.startswith('+') else "+{0}".format(mobile_number)
    sms_body = "Your Student Management OTP is: {0}".format(otp_code)
    twilio_url = "https://api.twilio.com/2010-04-01/Accounts/{0}/Messages.json".format(account_sid)

    response = requests.post(
        twilio_url,
        data={
            'To': to_number,
            'From': from_number,
            'Body': sms_body,
        },
        auth=(account_sid, auth_token),
        timeout=20,
    )

    if response.status_code >= 300:
        raise RuntimeError('Twilio SMS delivery failed: {0}'.format(response.text))


def start_registration(request):
    if request.method != 'POST':
        return redirect(reverse('login_page'))

    first_name = (request.POST.get('first_name') or '').strip()
    last_name = (request.POST.get('last_name') or '').strip()
    email = (request.POST.get('email') or '').strip().lower()
    mobile_number = _normalize_mobile_number(request.POST.get('mobile_number'))
    password = request.POST.get('password') or ''
    confirm_password = request.POST.get('confirm_password') or ''

    if not first_name or not last_name:
        messages.error(request, "First name and last name are required.")
        return redirect(reverse('login_page'))

    if not email:
        messages.error(request, "Email is required.")
        return redirect(reverse('login_page'))

    if len(mobile_number) < 10:
        messages.error(request, "Enter a valid mobile number.")
        return redirect(reverse('login_page'))

    if len(password) < 8:
        messages.error(request, "Password must be at least 8 characters long.")
        return redirect(reverse('login_page'))

    if password != confirm_password:
        messages.error(request, "Password and confirm password do not match.")
        return redirect(reverse('login_page'))

    if CustomUser.objects.filter(email=email).exists():
        messages.error(request, "This email is already registered.")
        return redirect(reverse('login_page'))

    if CustomUser.objects.filter(mobile_number=mobile_number).exists():
        messages.error(request, "This mobile number is already registered.")
        return redirect(reverse('login_page'))

    email_otp = str(random.randint(100000, 999999))
    mobile_otp = str(random.randint(100000, 999999))

    request.session['pending_registration'] = {
        'first_name': first_name,
        'last_name': last_name,
        'email': email,
        'mobile_number': mobile_number,
        'password': password,
        'email_otp': email_otp,
        'mobile_otp': mobile_otp,
    }

    email_sent = False
    sms_sent = False

    try:
        _send_registration_email_otp(email, email_otp)
        email_sent = True
    except Exception:
        email_sent = False

    try:
        _send_registration_mobile_otp(mobile_number, mobile_otp)
        sms_sent = True
    except Exception:
        sms_sent = False

    if email_sent and sms_sent:
        messages.success(request, "Verification codes have been sent to your email and mobile.")
    elif email_sent and not sms_sent:
        messages.warning(request, "Email OTP sent successfully. SMS gateway is not configured yet.")
        messages.info(request, "Use this mobile OTP for now: {0}".format(mobile_otp))
    elif sms_sent and not email_sent:
        messages.warning(request, "Mobile OTP sent successfully, but email service is not configured.")
        messages.info(request, "Use this email OTP for now: {0}".format(email_otp))
    else:
        messages.warning(
            request,
            "Email and SMS services are not configured. Dev OTPs -> Email: {0}, Mobile: {1}".format(email_otp, mobile_otp),
        )

    return redirect(reverse('login_page'))


def complete_registration(request):
    if request.method != 'POST':
        return redirect(reverse('login_page'))

    pending_registration = request.session.get('pending_registration')
    if not pending_registration:
        messages.error(request, "Registration session expired. Please register again.")
        return redirect(reverse('login_page'))

    provided_email_otp = (request.POST.get('email_otp') or '').strip()
    provided_mobile_otp = (request.POST.get('mobile_otp') or '').strip()

    if provided_email_otp != pending_registration.get('email_otp'):
        messages.error(request, "Invalid email verification code.")
        return redirect(reverse('login_page'))

    if provided_mobile_otp != pending_registration.get('mobile_otp'):
        messages.error(request, "Invalid mobile verification code.")
        return redirect(reverse('login_page'))

    if CustomUser.objects.filter(email=pending_registration['email']).exists():
        messages.error(request, "This email is already registered.")
        request.session.pop('pending_registration', None)
        return redirect(reverse('login_page'))

    if CustomUser.objects.filter(mobile_number=pending_registration['mobile_number']).exists():
        messages.error(request, "This mobile number is already registered.")
        request.session.pop('pending_registration', None)
        return redirect(reverse('login_page'))

    CustomUser.objects.create_user(
        email=pending_registration['email'],
        password=pending_registration['password'],
        first_name=pending_registration['first_name'],
        last_name=pending_registration['last_name'],
        user_type='3',
        gender='M',
        address='Registered via website signup',
        profile_pic='default.png',
        mobile_number=pending_registration['mobile_number'],
        email_verified=True,
        mobile_verified=True,
    )

    request.session.pop('pending_registration', None)
    messages.success(request, "Registration successful. You can now login.")
    return redirect(reverse('login_page'))


def doLogin(request, **kwargs):
    if request.method != 'POST':
        return HttpResponse("<h4>Denied</h4>")
    else:
        # Temporarily disable reCAPTCHA for testing
        #Google recaptcha
        # captcha_token = request.POST.get('g-recaptcha-response')
        # captcha_url = "https://www.google.com/recaptcha/api/siteverify"
        # captcha_key = "6LfswtgZAAAAABX9gbLqe-d97qE2g1JP8oUYritJ"
        # data = {
        #     'secret': captcha_key,
        #     'response': captcha_token
        # }
        # # Make request
        # try:
        #     captcha_server = requests.post(url=captcha_url, data=data)
        #     response = json.loads(captcha_server.text)
        #     if response['success'] == False:
        #         messages.error(request, 'Invalid Captcha. Try Again')
        #         return redirect('/')
        # except:
        #     messages.error(request, 'Captcha could not be verified. Try Again')
        #     return redirect('/')
        
        # Authenticate
        user = authenticate(request, username=request.POST.get('email'), password=request.POST.get('password'))
        if user != None:
            if user.totp_enabled and user.totp_secret:
                # Store only user id for the OTP challenge phase.
                request.session['pre_2fa_user_id'] = user.id
                return redirect(reverse("verify_totp"))

            login(request, user)
            if user.user_type == '1':
                return redirect(reverse("admin_home"))
            elif user.user_type == '2':
                return redirect(reverse("staff_home"))
            else:
                return redirect(reverse("student_home"))
        else:
            messages.error(request, "Invalid details")
            return redirect("/")


def verify_totp(request):
    user_id = request.session.get('pre_2fa_user_id')
    if not user_id:
        messages.error(request, "Your login session has expired. Please login again.")
        return redirect(reverse("login_page"))

    try:
        from .models import CustomUser
        user = CustomUser.objects.get(id=user_id)
    except CustomUser.DoesNotExist:
        request.session.pop('pre_2fa_user_id', None)
        messages.error(request, "User not found.")
        return redirect(reverse("login_page"))

    if request.method == 'POST':
        token = request.POST.get('otp', '').strip().replace(' ', '')

        if not token.isdigit() or len(token) != 6:
            messages.error(request, "Enter a valid 6-digit OTP code.")
            return redirect(reverse("verify_totp"))

        totp = pyotp.TOTP(user.totp_secret)
        if totp.verify(token, valid_window=1):
            login(request, user)
            request.session.pop('pre_2fa_user_id', None)

            if user.user_type == '1':
                return redirect(reverse("admin_home"))
            elif user.user_type == '2':
                return redirect(reverse("staff_home"))
            else:
                return redirect(reverse("student_home"))

        messages.error(request, "Invalid OTP code. Please try again.")
        return redirect(reverse("verify_totp"))

    return render(request, 'main_app/verify_totp.html')


@login_required
def setup_totp(request):
    user = request.user

    if not user.totp_secret:
        user.totp_secret = pyotp.random_base32()
        user.save(update_fields=['totp_secret'])

    issuer = "Student Management System"
    account_name = user.email
    totp = pyotp.TOTP(user.totp_secret)
    provisioning_uri = totp.provisioning_uri(name=account_name, issuer_name=issuer)

    qr = qrcode.QRCode(box_size=8, border=2)
    qr.add_data(provisioning_uri)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    qr_b64 = base64.b64encode(buffer.getvalue()).decode('utf-8')

    if request.method == 'POST':
        token = request.POST.get('otp', '').strip().replace(' ', '')

        if not token.isdigit() or len(token) != 6:
            messages.error(request, "Enter a valid 6-digit OTP code.")
            return redirect(reverse("setup_totp"))

        if totp.verify(token, valid_window=1):
            user.totp_enabled = True
            user.save(update_fields=['totp_enabled'])
            messages.success(request, "Two-factor authentication has been enabled.")
            if user.user_type == '1':
                return redirect(reverse("admin_home"))
            elif user.user_type == '2':
                return redirect(reverse("staff_home"))
            return redirect(reverse("student_home"))

        messages.error(request, "Invalid OTP code. Please try again.")
        return redirect(reverse("setup_totp"))

    return render(request, 'main_app/setup_totp.html', {
        'qr_b64': qr_b64,
        'totp_secret': user.totp_secret,
        'account_name': account_name,
        'issuer': issuer,
    })


@login_required
def disable_totp(request):
    if request.method != 'POST':
        return redirect(reverse("setup_totp"))

    user = request.user
    user.totp_enabled = False
    user.totp_secret = ""
    user.save(update_fields=['totp_enabled', 'totp_secret'])
    messages.success(request, "Two-factor authentication has been disabled.")
    return redirect(reverse("setup_totp"))



def logout_user(request):
    if request.user != None:
        logout(request)
    return redirect("/")


@csrf_exempt
def get_attendance(request):
    subject_id = request.POST.get('subject')
    session_id = request.POST.get('session')
    try:
        subject = get_object_or_404(Subject, id=subject_id)
        session = get_object_or_404(Session, id=session_id)
        attendance = Attendance.objects.filter(subject=subject, session=session)
        attendance_list = []
        for attd in attendance:
            data = {
                    "id": attd.id,
                    "attendance_date": str(attd.date),
                    "session": attd.session.id
                    }
            attendance_list.append(data)
        return JsonResponse(json.dumps(attendance_list), safe=False)
    except Exception as e:
        return None


def showFirebaseJS(request):
    data = """
    // Give the service worker access to Firebase Messaging.
// Note that you can only use Firebase Messaging here, other Firebase libraries
// are not available in the service worker.
importScripts('https://www.gstatic.com/firebasejs/7.22.1/firebase-app.js');
importScripts('https://www.gstatic.com/firebasejs/7.22.1/firebase-messaging.js');

// Initialize the Firebase app in the service worker by passing in
// your app's Firebase config object.
// https://firebase.google.com/docs/web/setup#config-object
firebase.initializeApp({
    apiKey: "AIzaSyBarDWWHTfTMSrtc5Lj3Cdw5dEvjAkFwtM",
    authDomain: "sms-with-django.firebaseapp.com",
    databaseURL: "https://sms-with-django.firebaseio.com",
    projectId: "sms-with-django",
    storageBucket: "sms-with-django.appspot.com",
    messagingSenderId: "945324593139",
    appId: "1:945324593139:web:03fa99a8854bbd38420c86",
    measurementId: "G-2F2RXTL9GT"
});

// Retrieve an instance of Firebase Messaging so that it can handle background
// messages.
const messaging = firebase.messaging();
messaging.setBackgroundMessageHandler(function (payload) {
    const notification = JSON.parse(payload);
    const notificationOption = {
        body: notification.body,
        icon: notification.icon
    }
    return self.registration.showNotification(payload.notification.title, notificationOption);
});
    """
    return HttpResponse(data, content_type='application/javascript')
