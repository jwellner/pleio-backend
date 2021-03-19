from django.urls import path
from profile_sync import views


urlpatterns = [
    path('users', views.users, name='profile_sync_users'),
    path('users/<uuid:user_id>', views.users_delete, name='profile_sync_users_delete'),
    path('users/<uuid:user_id>/ban', views.ban_user, name='profile_sync_users_ban'),
    path('users/<uuid:user_id>/unban', views.unban_user, name='profile_sync_users_unban'),
    path('users/<uuid:user_id>/avatar', views.avatar_user, name='profile_sync_users_avatar'),
    path('logs', views.logs, name='profile_sync_logs'),
]
