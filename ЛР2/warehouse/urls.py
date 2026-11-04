from django.urls import path

from . import views

app_name = "warehouse"

urlpatterns = [
    path("", views.product_list, name="products"),
    path("movements/", views.movement_list, name="movements"),
    path("movements/add/", views.movement_create, name="movement_add"),
    path("devices/", views.device_list, name="devices"),
    path("telemetry/", views.telemetry_list, name="telemetry"),
]
