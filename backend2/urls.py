from django.urls import path, include
from graphene_django.views import GraphQLView
from django.views.decorators.csrf import csrf_exempt

from core import admin
from core.views import index

urlpatterns = [
    path('graphql/', csrf_exempt(GraphQLView.as_view(graphiql=True))),
    path('oidc/', include('mozilla_django_oidc.urls')),
    path('files/', include('files.urls')),
    path('admin/', admin.site.urls),
    path('', index)
]
