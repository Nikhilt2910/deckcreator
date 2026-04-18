import hashlib
import hmac
import os

from dotenv import load_dotenv


load_dotenv()


def build_review_token(ticket_id: str) -> str:
    secret = _get_secret()
    digest = hmac.new(secret.encode("utf-8"), ticket_id.encode("utf-8"), hashlib.sha256)
    return digest.hexdigest()


def validate_review_token(ticket_id: str, token: str | None) -> bool:
    if not token:
        return False
    expected = build_review_token(ticket_id)
    return hmac.compare_digest(expected, token)


def _get_secret() -> str:
    return os.getenv("APP_REVIEW_SECRET") or os.getenv("OPENAI_API_KEY") or "local-review-secret"
