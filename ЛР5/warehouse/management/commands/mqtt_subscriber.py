import paho.mqtt.client as mqtt
from django.conf import settings
from django.core.management.base import BaseCommand

from warehouse.mongo import telemetry
from warehouse.mqtt import TOPIC, parse_message


class Command(BaseCommand):
    help = "Приймає телеметрію пристроїв з MQTT і зберігає її в MongoDB"

    def handle(self, *args, **options):
        client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="wms-server")
        client.on_connect = self.on_connect
        client.on_message = self.on_message
        client.connect(settings.MQTT_HOST, settings.MQTT_PORT)
        client.loop_forever()

    def on_connect(self, client, userdata, flags, reason_code, properties):
        client.subscribe(TOPIC, qos=1)
        self.stdout.write(self.style.SUCCESS(f"Підключено до брокера, підписка на {TOPIC}"))

    def on_message(self, client, userdata, message):
        try:
            document = parse_message(message.topic, message.payload)
        except ValueError as error:
            self.stdout.write(self.style.ERROR(f"{message.topic}: {error}"))
            return
        telemetry.insert_one(document)
        self.stdout.write(f"{document['device']}: {document['data']} збережено в MongoDB")
