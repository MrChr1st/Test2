import time
from typing import Dict

import aiohttp


class RateService:
    def __init__(self, coingecko_url: str, frankfurter_url: str, cache_ttl: int = 60):
        self.coingecko_url = coingecko_url
        self.frankfurter_url = frankfurter_url
        self.cache_ttl = cache_ttl
        self.cache: Dict[str, float] | None = None
        self.cache_time: float = 0.0

    async def _crypto(self) -> Dict[str, float]:
        params = {"ids": "bitcoin,tether,toncoin", "vs_currencies": "usd"}
        async with aiohttp.ClientSession() as session:
            async with session.get(self.coingecko_url, params=params, timeout=15) as resp:
                resp.raise_for_status()
                data = await resp.json()
        return {
            "BTC": float(data["bitcoin"]["usd"]),
            "USDT": float(data["tether"]["usd"]),
            "TON": float(data["toncoin"]["usd"]),
            "USD": 1.0,
        }

    async def _fiat(self) -> Dict[str, float]:
        url = f"{self.frankfurter_url}?base=USD&symbols=EUR,INR,RUB"
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=15) as resp:
                resp.raise_for_status()
                data = await resp.json()
        rates = data["rates"]
        return {
            "USD": 1.0,
            "EUR": 1 / float(rates["EUR"]),
            "INR": 1 / float(rates["INR"]),
            "RUB": 1 / float(rates["RUB"]),
        }

    async def get_usd_values(self) -> Dict[str, float]:
        if self.cache and time.time() - self.cache_time < self.cache_ttl:
            return self.cache
        try:
            values = {}
            values.update(await self._crypto())
            values.update(await self._fiat())
            self.cache = values
            self.cache_time = time.time()
            return values
        except Exception:
            if self.cache:
                return self.cache
            return {
                "BTC": 90000.0,
                "USDT": 1.0,
                "TON": 4.0,
                "USD": 1.0,
                "EUR": 1.09,
                "INR": 0.012,
                "RUB": 0.011,
            }

    async def convert(self, amount: float, from_currency: str, to_currency: str, fee_fraction: float):
        values = await self.get_usd_values()
        market_rate = values[from_currency] / values[to_currency]
        result = amount * market_rate * (1 - fee_fraction)
        return round(result, 8), round(market_rate, 8)

    async def get_table(self, quote: str):
        values = await self.get_usd_values()
        q = values[quote]
        return {cur: round(val / q, 8) for cur, val in values.items()}
