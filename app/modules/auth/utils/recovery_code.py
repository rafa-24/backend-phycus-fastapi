import random


def generate_recovery_code() -> int:
    return random.randint(100000, 999999)
