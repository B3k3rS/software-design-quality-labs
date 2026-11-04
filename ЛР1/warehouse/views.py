from django.db import transaction
from django.shortcuts import redirect, render

from .forms import MovementForm
from .models import Device, Movement, Product


def product_list(request):
    return render(request, "warehouse/product_list.html", {"products": Product.objects.all()})


def movement_list(request):
    movements = Movement.objects.select_related("product", "device")[:50]
    return render(request, "warehouse/movement_list.html", {"movements": movements})


def device_list(request):
    return render(request, "warehouse/device_list.html", {"devices": Device.objects.all()})


def movement_create(request):
    form = MovementForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        with transaction.atomic():
            movement = form.save()
            product = movement.product
            if movement.movement_type == "in":
                product.quantity += movement.quantity
            else:
                product.quantity -= movement.quantity
            product.save()
        return redirect("warehouse:movements")
    return render(request, "warehouse/movement_form.html", {"form": form})
