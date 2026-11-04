from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from warehouse.mongo import telemetry


class Command(BaseCommand):
    help = "Виконує основні команди MongoDB над колекцією telemetry"

    def show(self, title, result=None):
        self.stdout.write(self.style.MIGRATE_HEADING(f"\n{title}"))
        if result is not None:
            self.stdout.write(f"  {result}")

    def handle(self, *args, **options):
        now = timezone.now()

        telemetry.delete_many({})
        self.show("delete_many({}): колекцію очищено")

        result = telemetry.insert_one({
            "device": "CLM-01", "type": "climate", "timestamp": now,
            "data": {"temperature": 4.2, "humidity": 81},
        })
        self.show("insert_one():", f"inserted_id = {result.inserted_id}")

        result = telemetry.insert_many([
            {"device": "CLM-01", "type": "climate", "timestamp": now - timedelta(minutes=10),
             "data": {"temperature": 3.9, "humidity": 80}},
            {"device": "CLM-01", "type": "climate", "timestamp": now - timedelta(minutes=5),
             "data": {"temperature": 7.8, "humidity": 84}},
            {"device": "SCL-01", "type": "scale", "timestamp": now - timedelta(minutes=3),
             "data": {"weight_kg": 152.4, "shelf": "A-01"}},
            {"device": "SCN-01", "type": "scanner", "timestamp": now - timedelta(minutes=1),
             "data": {"barcode": "4820000123456", "sku": "PK-2001"}},
        ])
        self.show("insert_many():", f"додано документів: {len(result.inserted_ids)}")

        self.show("count_documents({}):", telemetry.count_documents({}))

        self.show('find({"type": "climate"}):')
        for doc in telemetry.find({"type": "climate"}, {"_id": 0, "timestamp": 0}):
            self.stdout.write(f"  {doc}")

        self.show('find({"data.temperature": {"$gt": 6}}): температура вище 6 градусів')
        for doc in telemetry.find({"data.temperature": {"$gt": 6}}, {"_id": 0, "device": 1, "data": 1}):
            self.stdout.write(f"  {doc}")

        doc = telemetry.find_one({"device": "SCN-01"}, {"_id": 0, "timestamp": 0})
        self.show('find_one({"device": "SCN-01"}):', doc)

        result = telemetry.update_one({"device": "SCL-01"}, {"$set": {"data.weight_kg": 148.0}})
        self.show('update_one({"device": "SCL-01"}, {"$set": ...}):', f"змінено документів: {result.modified_count}")

        result = telemetry.delete_one({"data.temperature": {"$gt": 6}})
        self.show('delete_one({"data.temperature": {"$gt": 6}}):', f"видалено документів: {result.deleted_count}")

        self.show("count_documents({}) після видалення:", telemetry.count_documents({}))
