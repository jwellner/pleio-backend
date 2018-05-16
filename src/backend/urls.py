from django.urls import path, include
from graphene_django.views import GraphQLView

from backend.core import admin
from backend.core.views import index

urlpatterns = [
    path('graphql/', GraphQLView.as_view(graphiql=True)),
    path('oidc/', include('mozilla_django_oidc.urls')),
    path('admin/', admin.site.urls),
    path('', index)
]
