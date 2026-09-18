import secrets

# No 0/1/I/L/O/U so codes survive being read aloud or retyped.
ALPHABET = "23456789ABCDEFGHJKMNPQRSTVWXYZ"


def random_code(n: int) -> str:
    return "".join(secrets.choice(ALPHABET) for _ in range(n))


def new_slug() -> str:
    return random_code(6)


def new_job_public_id() -> str:
    return "JOB-" + random_code(8)


def new_distribution_code(prefix: str) -> str:
    return f"{prefix}-{random_code(6)}"


def normalize_slug(raw: str) -> str:
    return raw.strip().upper()


def is_valid_slug(raw: str) -> bool:
    return 4 <= len(raw) <= 12 and all(c in ALPHABET for c in raw)
