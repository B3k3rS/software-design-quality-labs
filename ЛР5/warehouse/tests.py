from datetime import datetime
from io import StringIO
from unittest import mock
from zoneinfo import ZoneInfo

import pandas as pd
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse
from pymongo.errors import PyMongoError

from .analytics import daily_outflow, detect_anomalies, forecast_stock, movements_dataframe
from .forms import MovementForm
from .models import Device, Movement, Product
from .mqtt import parse_message


def outflow(rows):
    df = pd.DataFrame([(pd.Timestamp(day), sku, "out", quantity) for day, sku, quantity in rows],
                      columns=["date", "sku", "type", "quantity"])
    return daily_outflow(df)


class ProductModelTests(TestCase):
    def test_needs_reorder(self):
        self.assertTrue(Product(sku="A", name="A", quantity=5, min_quantity=10).needs_reorder())
        self.assertFalse(Product(sku="B", name="B", quantity=10, min_quantity=10).needs_reorder())

    def test_str(self):
        self.assertEqual(str(Product(sku="EL-1", name="Акумулятор")), "Акумулятор (EL-1)")


class MovementFormTests(TestCase):
    def setUp(self):
        self.product = Product.objects.create(sku="EL-1", name="Акумулятор", quantity=10, min_quantity=5)

    def form(self, movement_type, quantity):
        return MovementForm(data={"movement_type": movement_type, "product": self.product.pk, "quantity": quantity})

    def test_receipt_is_valid(self):
        self.assertTrue(self.form("in", 50).is_valid())

    def test_shipment_within_stock_is_valid(self):
        self.assertTrue(self.form("out", 10).is_valid())

    def test_shipment_above_stock_is_rejected(self):
        form = self.form("out", 11)
        self.assertFalse(form.is_valid())
        self.assertIn("На складі лише 10 шт.", form.non_field_errors()[0])

    def test_zero_quantity_is_rejected(self):
        self.assertFalse(self.form("in", 0).is_valid())


class ViewTests(TestCase):
    def setUp(self):
        self.product = Product.objects.create(sku="EL-1", name="Акумулятор", quantity=10, min_quantity=5)

    def post(self, movement_type, quantity):
        return self.client.post(reverse("warehouse:movement_add"),
                                {"movement_type": movement_type, "product": self.product.pk, "quantity": quantity})

    def test_pages_open(self):
        for name in ["products", "movements", "devices", "movement_add", "analytics"]:
            with self.subTest(page=name):
                self.assertEqual(self.client.get(reverse(f"warehouse:{name}")).status_code, 200)

    def test_receipt_increases_stock(self):
        response = self.post("in", 5)
        self.assertRedirects(response, reverse("warehouse:movements"))
        self.product.refresh_from_db()
        self.assertEqual(self.product.quantity, 15)
        self.assertEqual(Movement.objects.count(), 1)

    def test_shipment_decreases_stock(self):
        self.post("out", 3)
        self.product.refresh_from_db()
        self.assertEqual(self.product.quantity, 7)

    def test_rejected_shipment_changes_nothing(self):
        response = self.post("out", 20)
        self.assertEqual(response.status_code, 200)
        self.product.refresh_from_db()
        self.assertEqual(self.product.quantity, 10)
        self.assertEqual(Movement.objects.count(), 0)

    @mock.patch("warehouse.views.telemetry")
    def test_telemetry_without_mongodb(self, telemetry):
        telemetry.find.side_effect = PyMongoError("connection refused")
        self.assertContains(self.client.get(reverse("warehouse:telemetry")), "MongoDB недоступна")


class AnalyticsTests(TestCase):
    def test_daily_outflow_fills_missing_days(self):
        daily = outflow([("2026-10-01", "A", 3), ("2026-10-01", "A", 2), ("2026-10-03", "A", 4)])
        self.assertEqual(list(daily["A"]), [5, 0, 4])

    def test_spike_is_detected(self):
        rows = [(f"2026-10-{day:02d}", "A", 100 if day == 15 else 10) for day in range(1, 21)]
        anomalies = detect_anomalies(outflow(rows))
        self.assertEqual([a["date"] for a in anomalies], [pd.Timestamp("2026-10-15")])

    def test_forecast_for_constant_demand(self):
        Product.objects.create(sku="A", name="A", quantity=30, min_quantity=10)
        rows = [(f"2026-10-{day:02d}", "A", 3) for day in range(1, 21)]
        result = forecast_stock(outflow(rows))[0]
        self.assertAlmostEqual(result["per_day"], 3.0)
        self.assertAlmostEqual(result["days_left"], 10.0)

    def test_dates_use_local_time_zone(self):
        product = Product.objects.create(sku="A", name="A", quantity=10)
        movement = Movement.objects.create(product=product, movement_type="out", quantity=1)
        Movement.objects.filter(pk=movement.pk).update(created_at=datetime(2026, 10, 2, 1, 0, tzinfo=ZoneInfo("Europe/Kyiv")))
        self.assertEqual(movements_dataframe().loc[0, "date"], pd.Timestamp("2026-10-02"))


class GenerateHistoryTests(TestCase):
    def setUp(self):
        call_command("seed_warehouse", stdout=StringIO())

    def test_default_period(self):
        call_command("generate_history", stdout=StringIO())
        self.assertGreater(Movement.objects.filter(movement_type="out").count(), 0)

    def test_short_period(self):
        call_command("generate_history", days=7, stdout=StringIO())
        self.assertGreater(Movement.objects.filter(movement_type="out").count(), 0)


class MqttMessageTests(TestCase):
    def setUp(self):
        Device.objects.create(code="CLM-01", name="Датчик клімату", device_type="climate", location="Холодильна камера")

    def test_valid_message(self):
        payload = '{"timestamp": "2026-11-09T10:00:00+00:00", "data": {"temperature": 4.1, "humidity": 80}}'
        document = parse_message("warehouse/CLM-01/telemetry", payload)
        self.assertEqual(document["type"], "climate")
        self.assertEqual(document["data"]["temperature"], 4.1)

    def test_unknown_device_is_rejected(self):
        with self.assertRaises(ValueError):
            parse_message("warehouse/XXX-99/telemetry", '{"data": {"temperature": 4}}')

    def test_wrong_topic_is_rejected(self):
        with self.assertRaises(ValueError):
            parse_message("warehouse/CLM-01/status", '{"data": {"temperature": 4}}')

    def test_invalid_json_is_rejected(self):
        with self.assertRaises(ValueError):
            parse_message("warehouse/CLM-01/telemetry", "not json")
