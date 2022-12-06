from django.urls import path
from control import views

urlpatterns = [
    path('', views.home, name="home"),
    path('sites', views.sites, name="sites"),
    path('site/<int:site_id>', views.site),
    path('sites/add', views.sites_add, name="site_add"),
    path('sites/delete/<int:site_id>', views.sites_delete, name="site_delete"),
    path('sites/disable/<int:site_id>', views.sites_disable, name="site_disable"),
    path('sites/enable/<int:site_id>', views.sites_enable, name="site_enable"),
    path('sites/backup/<int:site_id>', views.sites_backup, name='site_backup'),
    path('tasks', views.tasks, name='tasks'),
    path('download-backup/<int:task_id>', views.download_backup, name='download_backup'),
    path('tools', views.tools, name='tools'),
    path('tools/download_site_admins', views.dowload_site_admins, name='download_site_admins'),
    path('tools/search_user', views.search_user),
    path('agreements', views.agreements),
    path('agreements/add', views.agreements_add),
    path('agreements/<int:agreement_id>/add', views.agreements_add_version),
]
