import os
import django
from django.contrib.auth import get_user_model

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')
django.setup()

def create_admin_user():
    User = get_user_model()
    
    # Create admin user with phone as username
    admin_user = User.objects.create_superuser(
        phone='+998910574905',
        username='admin',
        password='StrongPass123!',  # Strong password to pass validation
        is_staff=True,
        is_superuser=True
    )
    
    print(f"Admin user created successfully!")
    print(f"Phone: {admin_user.phone}")
    print(f"Username: {admin_user.username}")
    print(f"Is staff: {admin_user.is_staff}")
    print(f"Is superuser: {admin_user.is_superuser}")

if __name__ == '__main__':
    create_admin_user()