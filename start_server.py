import os
import django
from django.core.management import execute_from_command_line

if __name__ == '__main__':
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')
    django.setup()
    
    # Start the development server
    from django.core.management.commands.runserver import Command as RunServerCommand
    command = RunServerCommand()
    
    print("Starting Django development server...")
    print("API endpoints will be available at:")
    print("  - http://localhost:8000/api/auth/register/ (POST)")
    print("  - http://localhost:8000/api/auth/login/ (POST)")
    print("  - http://localhost:8000/api/declarations/ (GET, POST with auth)")
    print("  - http://localhost:8000/api/hs-codes/ (GET, POST with auth)")
    print("  - http://localhost:8000/api/product-items/ (GET, POST with auth)")
    print("\nAdmin panel: http://localhost:8000/admin/")
    
    try:
        execute_from_command_line(['manage.py', 'runserver', '8000'])
    except KeyboardInterrupt:
        print("\nServer stopped.")