from django.contrib.auth.models import BaseUserManager
from rest_framework.views import exception_handler as drf_exception_handler
from rest_framework.response import Response
from rest_framework import status
from django.core.validators import RegexValidator, MinValueValidator, MaxValueValidator as DjangoValidationError
from django.core.exceptions import ValidationError 
from django.core.validators import URLValidator
import re


class UserManager(BaseUserManager):
    def create_user(self, email=None, phone=None, password=None, **extra_fields):
        if not email and not phone:
            raise ValueError("The user must have either an email or a phone number")

        if email:
            email = self.normalize_email(email)

        username = email or phone  # fallback username

        user = self.model(
            email=email,
            phone=phone,
            username=username,
            **extra_fields
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email=None, phone=None, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("role", 'admin')
        return self.create_user(email=email, phone=phone, password=password, **extra_fields)



#global exception handler
def custom_exception_handler(exc, context):
    response = drf_exception_handler(exc, context)

    if isinstance(exc, (ValueError, DjangoValidationError, ValidationError)):
        return Response(
            {'detail': str(exc)},
            status=status.HTTP_400_BAD_REQUEST
        )

    return response



#adding additional schemes

custom_url_validator = URLValidator(schemes=["http", "https", "rtsp", "rtmp"])


def validate_unique_name(model_class, value, instance=None):
    """
    Validate name is unique (case-insensitive) for a given model_class.
    If instance is provided, it's excluded from the check (for updates).
    """
    queryset = model_class.objects.filter(name__iexact=value)
    if instance:
        queryset = queryset.exclude(pk=instance.pk)
    if queryset.exists():
        raise ValidationError("This name already exists. Please choose a different name.")




# Function to validate the International Phone Numbers
def is_valid_phone_number(phone_number):
    # Regex to check valid phone number.
    pattern = r"^[+]{1}(?:[0-9\\-\\(\\)\\/" \
              "\\.]\\s?){6,15}[0-9]{1}$"

    # If the phone number is empty return false
    if not phone_number:
        return "false"


    # Return true if the phone number
    # matched the Regex
    if re.match(pattern, phone_number):
        return "true"
    else:
        return "false"