from django.urls import path, include
from graphene_django.views import GraphQLView
from django.views.decorators.csrf import csrf_exempt

from core import admin
from core.views import index, upload

urlpatterns = [
    path('graphql/', csrf_exempt(GraphQLView.as_view(graphiql=True)), name='graphql'),
    path('oidc/', include('mozilla_django_oidc.urls')),
    path('files/upload/', csrf_exempt(upload), name='upload'),
    path('admin/', admin.site.urls),
    path('', index, name='index')
]
