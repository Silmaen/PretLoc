from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

app_name = "accounts"

urlpatterns = [
    path("signup/", views.signup, name="signup"),
    path(
        "login/",
        auth_views.LoginView.as_view(template_name="accounts/login.html"),
        name="login",
    ),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("manage/", views.manage_users, name="manage_users"),
    path("profile/", views.user_profile, name="user_profile"),
    path("edit/<int:user_id>/", views.edit_user, name="edit_user"),
    path(
        "password/change/",
        auth_views.PasswordChangeView.as_view(
            template_name="accounts/password_change.html",
            success_url="/accounts/password/change/done/",
        ),
        name="password_change",
    ),
    path(
        "password/change/done/",
        auth_views.PasswordChangeDoneView.as_view(
            template_name="accounts/password_change_done.html"
        ),
        name="password_change_done",
    ),
    path("reset_password/<int:user_id>/", views.reset_password, name="reset_password"),
    path("create_user/", views.create_user, name="create_user"),
    path("delete_user/<int:user_id>/", views.delete_user, name="delete_user"),
]
