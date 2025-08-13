from rest_framework_simplejwt.authentication import JWTAuthentication
from django.conf import settings

from rest_framework.authentication import CSRFCheck
from rest_framework import exceptions

def enforce_csrf(request):
    """
    Enforce CSRF validation.
    """
    check = CSRFCheck(request)
    print('csrf check', check)
    check.process_request(request)
    reason = check.process_view(request, None, (), {})
    print('csrf reason', reason)
    if reason:
        raise exceptions.PermissionDenied('CSRF Failed: %s' % reason)

class CustomJWTAuthentication(JWTAuthentication):
    """Custom authentication class"""
    def authenticate(self, request):
        header = self.get_header(request)
        print('header::', header)
        if header is None:
            raw_token = request.COOKIES.get(settings.SIMPLE_JWT['AUTH_COOKIE']) or None
        else:
            raw_token = self.get_raw_token(header)
        if raw_token is None:
            return None
        print('raw_token::', raw_token)
        validated_token = self.get_validated_token(raw_token)
        enforce_csrf(request)
        return self.get_user(validated_token), validated_token