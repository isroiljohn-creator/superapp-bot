def generate_referral_code(user_id):
    """Generates a referral code based on user ID."""
    return f"r{user_id}"

def get_referrer_id_from_code(code):
    """Extracts user ID from referral code."""
    if code.startswith("r") and code[1:].isdigit():
        return int(code[1:])
    return None
