from django.urls import path
from flow import views


urlpatterns = [
    path('comments/add', views.add_comment, name='flow_add_comment'),
    path('comments/edit', views.edit_comment, name='flow_edit_comment'),
]
