def calculate_transport(distance_km, invoice_total):
    """
    Transport rule:
    - Within 10km AND invoice total >= 500,000 UGX → FREE
    - Otherwise → 30,000 UGX charge
    """
    if distance_km <= 10 and invoice_total >= 500000:
        return 0
    return 30000