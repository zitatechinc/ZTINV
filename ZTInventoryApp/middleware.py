# myproject/middleware.py
from django.shortcuts import render, redirect
from django.conf import settings
from django.http import HttpResponseForbidden, HttpResponseNotFound, HttpResponseServerError

class SessionRedirectMiddleware:
    """Middleware to handle session redirects and custom error pages."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            response = self.get_response(request)
        except Exception:
            # Handle unexpected server errors (500)
            return HttpResponseServerError(
                render(request, "core/500.html", {
                    "message": "Something went wrong on our end. Please try again later."
                })
            )

        # Handle 404 page not found
        if response.status_code == 404:
            return HttpResponseNotFound(
                render(request, "core/404.html", {
                    "message": "Sorry, the page you requested could not be found."
                })
            )

        # Handle forbidden / expired session (403)
        if isinstance(response, HttpResponseForbidden):
            return redirect(settings.LOGIN_URL)

        return response
