from datetime import timedelta

import numpy as np
from django.core.management.base import BaseCommand
from django.utils import timezone

from warehouse.models import Device, Movement, Product

DEMAND = {
    "EL-1001": (5, 0.04),
    "EL-1002": (2, 0.03),
    "PK-2001": (12, 0.05),
    "PK-2002": (2, 0.0),
    "FD-3001": (6, -0.03),
    "FD-3002": (2, 0.02),
}


class Command(BaseCommand):
    help = "Створює історію складських операцій за останні дні"

    def add_arguments(self, parser):
        parser.add_argument("--days", type=int, default=60)

    def handle(self, *args, **options):
        days = options["days"]
        rng = np.random.default_rng(42)
        in_device = Device.objects.get(code="SCN-01")
        out_device = Device.objects.get(code="SCN-02")
        products = {p.sku: p for p in Product.objects.filter(sku__in=DEMAND)}
        today = timezone.now().replace(hour=9, minute=0, second=0, microsecond=0)
        spike = int(rng.integers(10, days - 10))

        Movement.objects.all().delete()
        movements, times = [], []
        for day in range(days):
            moment = today - timedelta(days=days - day)
            for sku, (base, growth) in DEMAND.items():
                rate = max(base + growth * day, 0.5) * (4 if day == spike else 1)
                quantity = int(rng.poisson(rate))
                if quantity:
                    movements.append(Movement(product=products[sku], movement_type="out", quantity=quantity, device=out_device))
                    times.append(moment + timedelta(hours=int(rng.integers(1, 9))))
                if day % 7 == 0:
                    movements.append(Movement(product=products[sku], movement_type="in", quantity=int(base * 7), device=in_device))
                    times.append(moment)

        created = Movement.objects.bulk_create(movements)
        for movement, moment in zip(created, times):
            movement.created_at = moment
        Movement.objects.bulk_update(created, ["created_at"])
        self.stdout.write(self.style.SUCCESS(f"Створено операцій: {len(created)} за {days} днів"))
