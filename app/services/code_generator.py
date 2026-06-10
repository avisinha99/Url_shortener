import secrets
import string

ALPHABET = string.ascii_letters + string.digits
CODE_LENGTH = 7
MAX_GENERATION_ATTEMPTS = 5


def generate_code(length: int = CODE_LENGTH) -> str:
    return "".join(secrets.choice(ALPHABET) for _ in range(length))
