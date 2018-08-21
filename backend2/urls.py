from django.urls import path, include
from django.conf.urls import url
from graphene_django.views import GraphQLView
from django.views.decorators.csrf import csrf_exempt

from core import admin
from core.views import index, upload, logout, oidc_failure

urlpatterns = [
    url(r'logout/', logout, name='logout'),
    path('graphql/', csrf_exempt(GraphQLView.as_view(graphiql=True)), name='graphql'),
    path('oidc/', include('mozilla_django_oidc.urls')),
    path('files/upload/', csrf_exempt(upload), name='upload'),
    path('admin/', admin.site.urls),
    url(r'oidc_failure/', oidc_failure, name='oidc_failure'),
    path('', index, name='index')
]
