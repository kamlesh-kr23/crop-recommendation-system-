from django.urls import path
from .views import (
    admin_delete_prediction,
    home,
    signup_view,
    login_view,
    logout_view,
    predict_view,
    user_profile_view,
    user_history_view,
    user_change_password_view,
    user_delete_predictions,
    admin_login_view,
    admin_dashboard_view,
    admin_logout_view,
    admin_view_predictions,
    admin_view_users,
    admin_delete_user
)

urlpatterns = [

    # Public
    path('', home, name='home'),
    path('signup/', signup_view, name='signup'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    

    # User
    path('predict/', predict_view, name='predict'),
    path('profile/', user_profile_view, name='profile'),
    path('history/', user_history_view, name='history'),
    path('change-password/', user_change_password_view, name='change_password'),
    path('delete-prediction/<int:pk>/', user_delete_predictions, name='delete_prediction'),

    # Admin
    path('admin-login/', admin_login_view, name='admin_login'),
    path('admin-dashboard/', admin_dashboard_view, name='admin_dashboard'),
    path('admin-logout/', admin_logout_view, name='admin_logout'),
    path('admin-predictions/', admin_view_predictions, name='admin_predictions'),
    path('admin-users/', admin_view_users, name='admin_users'),
    path('admin-delete-user/<int:pk>/', admin_delete_user, name='admin_delete_user'),
    path(
    "delete-prediction/<int:pk>/",
    user_delete_predictions,
    name="user_delete_predictions"
    
),
path(
        "admin/predictions/",
        admin_view_predictions,
        name="admin_predictions"
    ),

    path(
        "admin/delete/<int:pk>/",
        admin_delete_prediction,
        name="admin_delete_prediction"
    ),
]