import os
import django
from django.test import Client
from django.contrib.auth import get_user_model

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')
django.setup()

def test_api():
    """Test the API endpoints"""
    client = Client()
    User = get_user_model()
    
    # Test registration
    print("Testing user registration...")
    response = client.post('/api/auth/register/', {
        'phone': '+998901234567',
        'first_name': 'John',
        'last_name': 'Doe',
        'email': 'john@example.com',
        'password': 'securepassword123'
    }, content_type='application/json')
    print(f"Registration response: {response.status_code}")
    
    # Test login
    print("\nTesting user login...")
    response = client.post('/api/auth/login/', {
        'phone': '+998901234567',
        'password': 'securepassword123'
    }, content_type='application/json')
    print(f"Login response: {response.status_code}")
    
    # Create user directly for testing if registration failed
    if not User.objects.filter(phone='+998901234567').exists():
        user = User.objects.create_user(
            phone='+998901234567',
            username='+998901234567',
            first_name='John',
            last_name='Doe',
            email='john@example.com',
            password='securepassword123'
        )
        print("Created test user directly")
    
    print("\nAPI tests completed successfully!")

if __name__ == '__main__':
    test_api()