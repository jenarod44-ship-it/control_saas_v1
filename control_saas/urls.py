
from django.contrib import admin
from django.urls import path, include
import core.views

urlpatterns = [
    path("admin/", admin.site.urls),

    path("accounts/", include("django.contrib.auth.urls")),

    path("", core.views.dashboard, name="home"),
    path("dashboard/", core.views.dashboard, name="dashboard"),

    path("", include("core.urls")),   # ⭐ AGREGA ESTA

    path("nucleo/", include("nucleo.urls")),
]











