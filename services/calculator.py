def calculate_exchange(amount: float, from_rate_usd: float, to_rate_usd: float, client_bonus: float) -> float:
    if amount <= 0:
        raise ValueError("Amount must be greater than zero")

    if from_rate_usd <= 0 or to_rate_usd <= 0:
        raise ValueError("Rates must be greater than zero")

    result = amount * from_rate_usd / to_rate_usd
    result *= client_bonus
    return result