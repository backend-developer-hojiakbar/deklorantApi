from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model

User = get_user_model()

class PhoneBackend(ModelBackend):
    """
    Custom authentication backend that allows users to log in with their phone number
    """
    def authenticate(self, request, username=None, password=None, **kwargs):
        # Check if the username is a phone number
        if username is None:
            username = kwargs.get('phone')
        
        if username is None or password is None:
            return None
        
        try:
            # Try to find user by phone number
            user = User.objects.get(phone=username)
        except User.DoesNotExist:
            # Run the default password hasher once to reduce timing difference
            # between existing and non-existing users
            User().set_password(password)
            return None
        
        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        
        return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None