from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('info.urls')),
    path('home/', include('info.urls')),
    path('accounts/login/', auth_views.LoginView.as_view(template_name='info/login.html'), name='login'),
    path('accounts/logout/', auth_views.LogoutView.as_view(template_name='info/logout.html'), name='logout'),
]

admin.site.site_header = "Campus Dynamics Admin"
admin.site.site_title = "Campus Dynamics Admin Portal"
admin.site.index_title = "Welcome to Campus Dynamics"
#admin.site.site_url = "Url for view site button"