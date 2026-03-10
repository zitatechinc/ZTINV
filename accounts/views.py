from django.shortcuts import render
from django.views.generic.base import View
from core.views import BaseCRUDView,CustomUserCRUDView, AccountCRUDView,ChangePasswordCRUDView
from .models import User
from .forms import UserModelForm
from django.views.generic.edit import FormView
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.utils.http import url_has_allowed_host_and_scheme
from django.conf import settings
from django.contrib.auth.decorators import login_required
from .forms import CustomLoginForm,ChangePasswordForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import SetPasswordForm
from django.utils import timezone
import pytz
from django.views.generic.detail import DetailView

class CustomLoginView(FormView):
    template_name = "accounts/login.html"
    form_class = CustomLoginForm

    # def dispatch(self, request, *args, **kwargs):
    #     # If user is already logged in
    #     if request.user.is_authenticated:
    #         next_url = request.GET.get("next") or "home"  # 'home' is the name of the home URL pattern
    #         return redirect(next_url)
    #     return super().dispatch(request, *args, **kwargs)
    
    def dispatch(self, request, *args, **kwargs):
        # If user is already logged in
        if request.user.is_authenticated:
            # Redirect to the dashboard or home if already logged in
            return redirect("master_dashboard")  # 'master_dashboard' is the name of your dashboard URL
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        try:
            username = form.cleaned_data["username"]
            password = form.cleaned_data["password"]
            user = authenticate(self.request, username=username, password=password)
            if user is not None:
                login(self.request, user)
                user_tz = self.request.user.user_timezone
                timezone.activate(pytz.timezone(user_tz))
                next_url = self.request.GET.get('next') or self.request.POST.get('next')
                if next_url:
                    return redirect(next_url)
                # If no 'next' URL, redirect to the dashboard
                return redirect("master_dashboard")  # Redirect to your dashboard view
            else:
                messages.error(self.request, "Invalid username or password.")
                return self.form_invalid(form)
        except Exception as e:
            print (e)
            messages.error(self.request, "Something went wrong. Please try again later")
            return self.form_invalid(form)

def user_logout(request):
    try:
        if request.user.is_authenticated:
            logout(request)
            messages.success(request, "You’ve been logged out. See you again soon!")
        else:
            request.session.clear()
            messages.error(request, "Invalid Session. Please try again later")
    except Exception as e:
        request.session.clear()
        messages.error(request, "Something went wrong. Please try again later")
    return redirect("login")


class UserCRUDView(AccountCRUDView):
    model = User
    form_class = UserModelForm
    FieldList = (('first_name','First Name'),
                 ('last_name','Last Name'),
                 ('role','Role'),
                 ('email','Email'),
                 ('username','Username'),
                 ('mobile_number','Mobile Number'),
                 ('search_keywords','Search Keywords')
                 )
    

    def get_extra_context(self):
        return {
         
        }

    @property
    def get_name(self):
        return self.username



class ChangePasswordView(ChangePasswordCRUDView):
    model = User
    form_class = ChangePasswordForm
    def get_extra_context(self):
        return {
         
        }

@login_required
def change_password_view(request, pk):
    obj = get_object_or_404(User, pk=pk)
    if request.method == 'POST':
        form = ChangePasswordForm(user=obj, data=request.POST)
        if form.is_valid():
            user = form.save()
            # Keep the user logged in after password change
           
            update_session_auth_hash(request, user)
            messages.success(request, 'Your password was successfully updated!')
            return redirect('user-list')  # Replace 'profile' with your profile URL name
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = ChangePasswordForm(user=obj)

    return render(request, 'accounts/user_change_password.html', {'form': form, "model_name" : 'ChangePassword',
            'page_title': 'Change Password', "object" : obj})


@login_required
def home(request):
    return render(request, 'core/home.html', {"page_title" : "Home"})


class UserPermissionView(LoginRequiredMixin, DetailView):
    model = User
    template_name = "accounts/user_permissions.html"
    context_object_name = "user_obj"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "User Permissions"
        context["model_name"] = "User Permissions"
        return context