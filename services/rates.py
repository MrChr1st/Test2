import time
from typing import Dict
import aiohttp

class RateService:
    def __init__(self, coingecko_url: str, cache_ttl: int = 60) -> None:
        self.coingecko_url = coingecko_url
        self.cache_ttl = cache_ttl
        self._cache = None
        self._cache_ts = 0.0
        self.fiat_rates = {"USD": 1.0, "EUR": 1.09, "RUB": 0.011, "INR": 0.012}

    async def get_all_rates(self) -> Dict[str, float]:
        now = time.time()
        if self._cache and now - self._cache_ts < self.cache_ttl:
            return self._cache
        params = {"ids": "bitcoin,tether,the-open-network", "vs_currencies": "usd"}
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.coingecko_url, params=params, timeout=10) as resp:
                    resp.raise_for_status()
                    data = await resp.json()
            rates = {
                "BTC": float(data.get("bitcoin", {}).get("usd", 65000.0)),
                "USDT": float(data.get("tether", {}).get("usd", 1.0)),
                "TON": float(data.get("the-open-network", {}).get("usd", 5.0)),
                **self.fiat_rates,
            }
        except Exception:
            rates = {"BTC": 65000.0, "USDT": 1.0, "TON": 5.0, **self.fiat_rates}
        self._cache = rates
        self._cache_ts = now
        return rates
