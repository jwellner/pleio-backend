from django.urls import path, include
from django.contrib import admin

from graphene_django.views import GraphQLView

urlpatterns = [
    path('graphql/', GraphQLView.as_view(graphiql=True)),
    path('oidc/', include('mozilla_django_oidc.urls')),
    path('admin/', admin.site.urls)
]
