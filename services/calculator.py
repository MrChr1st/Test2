def calculate_fee_with_referral_discount(base_fee: float, referrals_count: int, discount_per_user: float, max_discount: float) -> float:
    discount = min(referrals_count * discount_per_user, max_discount)
    return max(base_fee - discount, 0.0)
