from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.contrib.auth.management.commands.createsuperuser import get_default_username
from django.db import DEFAULT_DB_ALIAS
from django.core import exceptions
from django.utils.text import capfirst


class Command(BaseCommand):
    help = 'Used to create a superuser with phone number instead of username'
    requires_migrations_checks = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.UserModel = get_user_model()
        self.username_field = self.UserModel._meta.get_field(self.UserModel.USERNAME_FIELD)

    def add_arguments(self, parser):
        parser.add_argument(
            '--phone',
            dest=self.UserModel.USERNAME_FIELD,
            default=None,
            help='Specifies the phone number for the superuser.',
        )
        parser.add_argument(
            '--noinput', '--no-input',
            action='store_false',
            dest='interactive',
            help=(
                'Tells Django to NOT prompt the user for input of any kind. '
                'You must use --phone with --noinput, along with all the '
                'required field dependencies, defined in REQUIRED_FIELDS.'
            ),
        )

    def handle(self, *args, **options):
        phone = options.get(self.UserModel.USERNAME_FIELD)
        user_data = {}
        verbose_field_name = self.username_field.verbose_name
        try:
            self.UserModel._meta.get_field('email')
        except exceptions.FieldDoesNotExist:
            pass
        else:
            user_data['email'] = ''

        # Prompt for phone number
        while phone is None:
            message = self._get_input_message(verbose_field_name)
            phone = self.get_input_data(self.username_field, message, phone)
            if not phone:
                continue
            if self.validate_username(phone):
                user_data[self.UserModel.USERNAME_FIELD] = phone
                # Set phone as username as well
                user_data['username'] = phone
                break
            else:
                phone = None

        # Prompt for required fields
        for field_name in self.UserModel.REQUIRED_FIELDS:
            field = self.UserModel._meta.get_field(field_name)
            user_data[field_name] = options.get(field_name)
            while user_data[field_name] is None:
                message = self._get_input_message(field.verbose_name)
                input_value = self.get_input_data(field, message)
                user_data[field_name] = input_value

        # Set is_staff and is_superuser to True for superuser
        user_data['is_staff'] = True
        user_data['is_superuser'] = True
        user_data['password'] = None  # Will prompt for password

        self.UserModel._default_manager.db_manager(DEFAULT_DB_ALIAS).create_superuser(**user_data)
        if options.get('verbosity', 0) >= 1:
            self.stdout.write("Superuser created successfully.")

    def get_input_data(self, field, message, default=None):
        raw_value = input(message)
        if default and raw_value == '':
            raw_value = default
        try:
            return field.clean(raw_value, None)
        except exceptions.ValidationError as e:
            self.stderr.write("Error: %s" % '; '.join(e.messages))
            return None

    def _get_input_message(self, field_verbose_name):
        return '%s: ' % capfirst(field_verbose_name)

    def validate_username(self, username):
        """
        Validate the username. If invalid, return False.
        """
        try:
            self.UserModel._default_manager.db_manager().get_by_natural_key(username)
        except self.UserModel.DoesNotExist:
            pass
        else:
            self.stderr.write("Error: That phone number is already taken.")
            return False
        return True