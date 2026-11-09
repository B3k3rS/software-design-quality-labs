#!/usr/bin/env python3
import argparse
import json
import random
import time
from datetime import datetime, timezone

import paho.mqtt.client as mqtt


def measure(device_type):
    if device_type == "climate":
        return {"temperature": round(random.gauss(4.0, 0.6), 1), "humidity": round(random.gauss(80, 2))}
    return {"weight_kg": round(random.uniform(140, 155), 1), "shelf": "A-01"}


def main():
    parser = argparse.ArgumentParser(description="Edge-пристрій складу, що публікує телеметрію в MQTT")
    parser.add_argument("--device", default="CLM-01")
    parser.add_argument("--type", choices=["climate", "scale"], default="climate")
    parser.add_argument("--interval", type=float, default=2)
    parser.add_argument("--count", type=int, default=10)
    parser.add_argument("--host", default="localhost")
    args = parser.parse_args()

    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=args.device)
    client.connect(args.host, 1883)
    client.loop_start()
    topic = f"warehouse/{args.device}/telemetry"

    for _ in range(args.count):
        message = {"timestamp": datetime.now(timezone.utc).isoformat(), "data": measure(args.type)}
        client.publish(topic, json.dumps(message), qos=1).wait_for_publish()
        print(f"{topic} {message['data']}")
        time.sleep(args.interval)

    client.loop_stop()
    client.disconnect()


if __name__ == "__main__":
    main()
