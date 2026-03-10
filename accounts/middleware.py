from django.utils import timezone
import pytz

class UserTimezoneMiddleware:

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):

        if request.user.is_authenticated:
            tz = request.user.user_timezone

            try:
                timezone.activate(pytz.timezone(tz))
            except Exception:
                timezone.deactivate()
        else:
            timezone.deactivate()

        response = self.get_response(request)
        return response