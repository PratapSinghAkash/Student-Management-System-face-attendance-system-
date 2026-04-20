from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model


class EmailBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        UserModel = get_user_model()
        login_identifier = username or kwargs.get(UserModel.USERNAME_FIELD)
        if not login_identifier or not password:
            return None

        try:
            user = UserModel.objects.get(email=login_identifier)
        except UserModel.DoesNotExist:
            return None
        else:
            if user.check_password(password):
                return user
        return None
