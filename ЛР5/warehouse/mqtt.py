import json
from datetime import datetime

from django.utils import timezone

from .models import Device

TOPIC = "warehouse/+/telemetry"


def parse_message(topic, payload):
    parts = topic.split("/")
    if len(parts) != 3 or parts[0] != "warehouse" or parts[2] != "telemetry":
        raise ValueError(f"Невідомий топік {topic}")
    device = Device.objects.filter(code=parts[1]).first()
    if device is None:
        raise ValueError(f"Невідомий пристрій {parts[1]}")
    body = json.loads(payload)
    if not isinstance(body.get("data"), dict):
        raise ValueError("У повідомленні немає даних")
    timestamp = datetime.fromisoformat(body["timestamp"]) if "timestamp" in body else timezone.now()
    return {"device": device.code, "type": device.device_type, "timestamp": timestamp, "data": body["data"]}
