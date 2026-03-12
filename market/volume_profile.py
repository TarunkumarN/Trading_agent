from dataclasses import dataclass, asdict
from typing import Any


@dataclass
class VolumeProfile:
    poc: float
    value_area_low: float
    value_area_high: float
    high_volume_nodes: list[float]
    low_volume_nodes: list[float]
    imbalance: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def build_volume_profile(prices, volumes, bins: int = 24):
    if not prices or not volumes or len(prices) != len(volumes):
        return VolumeProfile(0.0, 0.0, 0.0, [], [], 0.0)

    price_min = min(prices)
    price_max = max(prices)
    if price_max == price_min:
        return VolumeProfile(price_max, price_min, price_max, [price_max], [price_min], 0.0)

    bucket_size = (price_max - price_min) / bins
    buckets = []
    for idx in range(bins):
        lower = price_min + idx * bucket_size
        upper = lower + bucket_size
        buckets.append({"mid": round((lower + upper) / 2, 2), "volume": 0.0})

    for price, volume in zip(prices, volumes):
        bucket_idx = min(int((price - price_min) / bucket_size), bins - 1)
        buckets[bucket_idx]["volume"] += float(volume)

    sorted_buckets = sorted(buckets, key=lambda item: item["volume"], reverse=True)
    total_volume = sum(item["volume"] for item in buckets) or 1.0
    cumulative = 0.0
    value_area = []
    for bucket in sorted_buckets:
        cumulative += bucket["volume"]
        value_area.append(bucket["mid"])
        if cumulative / total_volume >= 0.7:
            break

    poc = sorted_buckets[0]["mid"] if sorted_buckets else 0.0
    avg_bucket_volume = total_volume / len(buckets)
    hvn = [bucket["mid"] for bucket in buckets if bucket["volume"] >= avg_bucket_volume * 1.35]
    lvn = [bucket["mid"] for bucket in buckets if bucket["volume"] <= avg_bucket_volume * 0.55]
    buy_pressure = sum(v for p, v in zip(prices, volumes) if p >= poc)
    sell_pressure = sum(v for p, v in zip(prices, volumes) if p < poc)
    imbalance = ((buy_pressure - sell_pressure) / total_volume) * 100

    return VolumeProfile(
        poc=round(poc, 2),
        value_area_low=round(min(value_area), 2) if value_area else 0.0,
        value_area_high=round(max(value_area), 2) if value_area else 0.0,
        high_volume_nodes=sorted(hvn),
        low_volume_nodes=sorted(lvn),
        imbalance=round(imbalance, 2),
    )
