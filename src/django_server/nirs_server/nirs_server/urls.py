"""nirs_server URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
import os
from django.contrib import admin
from django.urls import path, include, re_path
from .settings import BASE_DIR

urlpatterns = [
    path('admin/', admin.site.urls),
    re_path(r'^nested_admin/', include('nested_admin.urls')),
    # path('fingertest/', include('apps.fingertest.urls')),
]

# Add installed apps.
all_apps = os.listdir(os.path.join(BASE_DIR, "./apps"))
for item in all_apps:
    if os.path.isdir(os.path.join(BASE_DIR, "./apps/" + item)) and (item[0] != "_"):
        urlpatterns += [path('{}/'.format(item), include('apps.{}.urls'.format(item)))]




