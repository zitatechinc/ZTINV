from django.urls import path


from . import views

user_crud = views.UserCRUDView()
#user_password = views.ChangePasswordView()

from accounts import views
from .views import UserPermissionView


urlpatterns = [
    
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout', views.user_logout, name='logout'),
    #path('user/list', user_crud.list_view, name='user-list'),

    #path('forgot_password/', views.ForgotPasswordView.as_view(), name='forgot-password'),
    path('user/list', views.UserCRUDView.as_view(), name='user-list'),
    path('user/create', views.UserCRUDView.as_view(),  name='user-create'),
    path('user/<int:pk>/update', views.UserCRUDView.as_view(), name='user-update'),
    path('user/<int:pk>/delete',views.UserCRUDView.as_view(), name='user-delete'),
    path('user/<int:pk>/view', views.UserCRUDView.as_view(), name='user-view'),
    #path('user/<int:pk>/changepassword', views.change_password_view, name='user-changepassword'),
    path('user/<int:pk>/changepassword', views.ChangePasswordView.as_view(), name='user-changepassword'),
    path('user/<int:pk>/permissions/',UserPermissionView.as_view(),name='user-permissions-view'),

]