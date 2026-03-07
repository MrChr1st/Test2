from typing import Dict

import aiohttp


class RateService:
    def __init__(self, coingecko_url: str):
        self.coingecko_url = coingecko_url
        self.fiat_rates = {
            "USD": 1.0,
            "EUR": 0.93,
            "RUB": 90.0,
            "INR": 83.0,
        }

    async def get_crypto_rates(self) -> Dict[str, float]:
        params = {
            "ids": "bitcoin,tether,the-open-network",
            "vs_currencies": "usd",
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.coingecko_url, params=params, timeout=10) as response:
                    response.raise_for_status()
                    data = await response.json()

            return {
                "BTC": float(data.get("bitcoin", {}).get("usd", 0)),
                "USDT": float(data.get("tether", {}).get("usd", 1)),
                "TON": float(data.get("the-open-network", {}).get("usd", 0)),
                "USD": 1.0,
                "EUR": self.fiat_rates["EUR"],
                "RUB": self.fiat_rates["RUB"],
                "INR": self.fiat_rates["INR"],
            }
        except Exception:
            return {
                "BTC": 60000.0,
                "USDT": 1.0,
                "TON": 5.0,
                "USD": 1.0,
                "EUR": self.fiat_rates["EUR"],
                "RUB": self.fiat_rates["RUB"],
                "INR": self.fiat_rates["INR"],
            }

    async def get_all_rates(self) -> Dict[str, float]:
        return await self.get_crypto_rates()

    async def get_rate(self, currency: str) -> float:
        rates = await self.get_all_rates()
        return float(rates.get(currency.upper(), 0))
