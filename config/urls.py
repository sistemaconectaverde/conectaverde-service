from django.contrib import admin
from django.urls import path

from config.api import api

admin.site.site_header = "Conecta Verde — Administração"
admin.site.site_title = "Conecta Verde"

urlpatterns = [
    path("django-admin/", admin.site.urls),
    path("api/", api.urls),  # Swagger em /api/docs
]
