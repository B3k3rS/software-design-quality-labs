from django.db import models


class Product(models.Model):
    sku = models.CharField("Артикул", max_length=30, unique=True)
    name = models.CharField("Назва", max_length=200)
    quantity = models.PositiveIntegerField("Кількість на складі", default=0)
    min_quantity = models.PositiveIntegerField("Мінімальний залишок", default=0)

    class Meta:
        verbose_name = "Товар"
        verbose_name_plural = "Товари"
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.sku})"

    def needs_reorder(self):
        return self.quantity < self.min_quantity


class Device(models.Model):
    TYPE_CHOICES = [
        ("scanner", "Сканер штрихкодів"),
        ("scale", "Ваги полиці"),
        ("climate", "Датчик клімату"),
    ]

    code = models.CharField("Код", max_length=20, unique=True)
    name = models.CharField("Назва", max_length=100)
    device_type = models.CharField("Тип", max_length=10, choices=TYPE_CHOICES)
    location = models.CharField("Місце встановлення", max_length=100)

    class Meta:
        verbose_name = "IoT-пристрій"
        verbose_name_plural = "IoT-пристрої"
        ordering = ["code"]

    def __str__(self):
        return self.code


class Movement(models.Model):
    TYPE_CHOICES = [
        ("in", "Приймання"),
        ("out", "Відвантаження"),
    ]

    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name="movements", verbose_name="Товар")
    movement_type = models.CharField("Операція", max_length=3, choices=TYPE_CHOICES)
    quantity = models.PositiveIntegerField("Кількість")
    device = models.ForeignKey(Device, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Пристрій")
    created_at = models.DateTimeField("Час", auto_now_add=True)

    class Meta:
        verbose_name = "Операція"
        verbose_name_plural = "Операції"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.get_movement_type_display()} {self.product.sku} x {self.quantity}"
