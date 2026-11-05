import math

import numpy as np
import pandas as pd
from django.conf import settings
from sklearn.linear_model import LinearRegression

from .models import Movement, Product

HORIZON = 14


def movements_dataframe():
    rows = Movement.objects.values_list("created_at", "product__sku", "movement_type", "quantity")
    df = pd.DataFrame(list(rows), columns=["created_at", "sku", "type", "quantity"])
    if not df.empty:
        df["date"] = pd.to_datetime(df["created_at"]).dt.tz_convert(settings.TIME_ZONE).dt.tz_localize(None).dt.normalize()
    return df


def daily_outflow(df):
    out = df[df["type"] == "out"]
    table = out.pivot_table(index="date", columns="sku", values="quantity", aggfunc="sum", fill_value=0)
    return table.asfreq("D", fill_value=0)


def detect_anomalies(daily, threshold=2.5):
    total = daily.sum(axis=1)
    values = total.to_numpy(dtype=float)
    z = (values - values.mean()) / values.std()
    mask = np.abs(z) > threshold
    return [{"date": d, "quantity": int(q), "z": round(float(s), 2)}
            for d, q, s in zip(total.index[mask], values[mask], z[mask])]


def forecast_stock(daily):
    days = np.arange(len(daily)).reshape(-1, 1)
    future = np.arange(len(daily), len(daily) + HORIZON).reshape(-1, 1)
    result = []
    for product in Product.objects.all():
        if product.sku not in daily.columns:
            continue
        model = LinearRegression().fit(days, daily[product.sku].to_numpy())
        demand = max(float(model.predict(future).sum()), 0.0)
        per_day = demand / HORIZON
        days_left = product.quantity / per_day if per_day > 0 else None
        order = max(math.ceil(demand + product.min_quantity - product.quantity), 0)
        result.append({
            "sku": product.sku,
            "name": product.name,
            "quantity": product.quantity,
            "avg": round(float(daily[product.sku].mean()), 1),
            "per_day": round(per_day, 1),
            "trend": round(float(model.coef_[0]) * 30, 1),
            "days_left": round(days_left, 1) if days_left is not None else None,
            "order": order,
        })
    return sorted(result, key=lambda r: r["days_left"] if r["days_left"] is not None else math.inf)


def build_report():
    df = movements_dataframe()
    if df.empty or (df["type"] == "out").sum() == 0:
        return None
    daily = daily_outflow(df)
    return {
        "start": daily.index.min(),
        "end": daily.index.max(),
        "operations": len(df),
        "shipped": int(df.loc[df["type"] == "out", "quantity"].sum()),
        "received": int(df.loc[df["type"] == "in", "quantity"].sum()),
        "forecast": forecast_stock(daily),
        "anomalies": detect_anomalies(daily),
        "horizon": HORIZON,
    }
