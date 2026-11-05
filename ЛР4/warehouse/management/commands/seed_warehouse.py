from django.core.management.base import BaseCommand

from warehouse.models import Device, Product

PRODUCTS = [
    ("EL-1001", "Акумулятор 18650", 140, 60),
    ("EL-1002", "Блок живлення 12V 2A", 35, 40),
    ("PK-2001", "Коробка картонна 40x30x30", 270, 100),
    ("PK-2002", "Стрейч-плівка 500 мм", 26, 20),
    ("FD-3001", "Йогурт полуничний 0.5 л", 70, 50),
    ("FD-3002", "Сир твердий 1 кг", 18, 30),
]

DEVICES = [
    ("SCN-01", "Сканер на рампі приймання", "scanner", "Рампа приймання"),
    ("SCN-02", "Сканер на рампі відвантаження", "scanner", "Рампа відвантаження"),
    ("SCL-01", "Ваги стелажу A-01", "scale", "Стелаж A-01"),
    ("CLM-01", "Датчик температури", "climate", "Холодильна камера"),
]


class Command(BaseCommand):
    help = "Заповнює склад тестовими товарами та IoT-пристроями"

    def handle(self, *args, **options):
        for sku, name, quantity, min_quantity in PRODUCTS:
            Product.objects.get_or_create(sku=sku, defaults={"name": name, "quantity": quantity, "min_quantity": min_quantity})
        for code, name, device_type, location in DEVICES:
            Device.objects.get_or_create(code=code, defaults={"name": name, "device_type": device_type, "location": location})
        self.stdout.write(self.style.SUCCESS(f"Товарів: {Product.objects.count()}, пристроїв: {Device.objects.count()}"))
