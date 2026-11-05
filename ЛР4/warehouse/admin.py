from django.contrib import admin

from .models import Device, Movement, Product

admin.site.register(Product)
admin.site.register(Device)
admin.site.register(Movement)
