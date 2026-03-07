from typing import Dict


class CalculatorService:
    def __init__(self, fee: float, client_bonus: float):
        self.fee = fee
        self.client_bonus = client_bonus

    def calculate(self, amount: float, source_currency: str, target_currency: str, rates: Dict[str, float]) -> Dict[str, float]:
        source = source_currency.upper()
        target = target_currency.upper()

        if source not in rates:
            raise ValueError(f"Unsupported source currency: {source}")
        if target not in rates:
            raise ValueError(f"Unsupported target currency: {target}")
        if amount <= 0:
            raise ValueError("Amount must be greater than 0")

        usd_amount = amount * rates[source]
        target_amount = usd_amount / rates[target]
        final_amount = target_amount * (1 - self.fee) * self.client_bonus
        final_rate = final_amount / amount

        return {
            "base_rate": rates[source] / rates[target],
            "final_rate": final_rate,
            "receive_amount": final_amount,
        }
