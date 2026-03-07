def calculate_fee_with_referral_discount(
    base_fee: float,
    referrals_count: int,
    discount_per_user: float,
    max_discount: float,
) -> float:
    discount = referrals_count * discount_per_user
    if discount > max_discount:
        discount = max_discount
    fee = base_fee - discount
    return max(fee, 0.0)
