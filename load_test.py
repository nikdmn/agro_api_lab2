"""
Тест 10: переполнение очереди (backpressure).

Одновременно отправляет 400 запросов в /predict-queued.
Очередь вмещает 100, поэтому часть запросов должна получить 429.

Запуск (сервер должен работать в другой вкладке терминала):
    python3 load_test.py
"""

import asyncio
from collections import Counter

import httpx

URL = "http://127.0.0.1:8000/predict-queued"
N = 400

PAYLOAD = {
    "farm_id": "FARM-LOAD",
    "region": "Krasnodar",
    "crop_type": "wheat",
    "area_ha": 2500,
    "temperature_avg": 24.3,
    "precipitation_mm": 320,
    "payment_delay_days": 45,
    "previous_defaults": 1,
    "debt": 6500000,
}


async def main():
    limits = httpx.Limits(max_connections=N, max_keepalive_connections=N)
    async with httpx.AsyncClient(timeout=30, limits=limits) as client:
        responses = await asyncio.gather(
            *[client.post(URL, json=PAYLOAD) for _ in range(N)],
            return_exceptions=True,
        )

    codes = Counter(
        r.status_code if isinstance(r, httpx.Response) else type(r).__name__
        for r in responses
    )
    print(f"Отправлено запросов: {N}")
    for code, count in sorted(codes.items(), key=lambda x: str(x[0])):
        print(f"  HTTP {code}: {count}")

    rejected = next(
        (r for r in responses if isinstance(r, httpx.Response) and r.status_code == 429),
        None,
    )
    if rejected is not None:
        print("\nПример ответа 429:")
        print("  Retry-After:", rejected.headers.get("retry-after"))
        print("  X-Request-ID:", rejected.headers.get("x-request-id"))
        print("  Body:", rejected.json())


if __name__ == "__main__":
    asyncio.run(main())
