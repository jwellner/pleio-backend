from django.urls import path
from django.contrib import admin

from graphene_django.views import GraphQLView

urlpatterns = [
    path('graphql/', GraphQLView.as_view(graphiql=True)),
    path('admin/', admin.site.urls),
]
