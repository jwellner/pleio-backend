from django.urls import path, include
from django.conf.urls import url
from graphene_django.views import GraphQLView
from django.views.decorators.csrf import csrf_exempt

from core import admin
from core import views

urlpatterns = [
    path('logout/', views.logout, name='logout'),
    path(
        'graphql/',
        csrf_exempt(GraphQLView.as_view(graphiql=True)),
        name='graphql'
        ),
    path('oidc/failure/', views.oidc_failure, name='oidc_failure'),
    path('oidc/', include('mozilla_django_oidc.urls')),
    path('files/upload/', csrf_exempt(views.upload), name='upload'),
    path('admin/logout/', views.logout, name='logout'),
    path('admin/', admin.site.urls),
    path('', views.index, name='index')
]
