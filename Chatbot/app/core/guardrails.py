import re
import logging
from langsmith import traceable

logger = logging.getLogger(__name__)

# Prompts that ask the LLM to ignore its instructions
_INJECTION_PATTERNS = re.compile(
    r"(?i)(?:"
    r"ignore\s+(?:all\s+)?(?:previous|above|below|the\s+above)\s+(?:instructions|prompts|directions|commands)"
    r"|disregard\s+(?:all\s+)?(?:previous|above|below)\s+(?:instructions|prompts|directions)"
    r"|forget\s+(?:all\s+)?(?:previous|above|below)\s+(?:instructions|prompts)"
    r"|you\s+(?:are\s+)?(?:now\s+)?(?:free|released|unleashed)"
    r"|new\s+instruction[s]?\s*:"
    r"|act\s+as\s+(?:if\s+you\s+are\s+)?(?:dan|jailbreak|sudo|system)"
    r"|you\s+(?:don'?t\s+)?(?:have\s+to\s+)?(?:obey|follow|listen)"
    r")",
    re.IGNORECASE,
)

# Sensitive info patterns (Egyptian phone numbers, full addresses)
_SENSITIVE_PATTERNS = re.compile(
    r"(?:(?:\+20|0)?1[0-2]\d{8})"  # Egyptian phone numbers
    r"|(?:\b\d{3}\s+\d{3}\s+\d{4}\b)",  # generic phone-like patterns
)

_MAX_INPUT_LENGTH = 2000
_MAX_OUTPUT_LENGTH = 4000


@traceable(run_type="chain")
def validate_input(text: str) -> tuple[bool, str]:
    """Validate user input for safety and sanity.

    Returns (is_valid, error_message_or_empty).
    """
    if not text or not text.strip():
        return False, "Please enter a message."

    if len(text) > _MAX_INPUT_LENGTH:
        return False, f"Message too long ({len(text)} chars). Please keep it under {_MAX_INPUT_LENGTH} characters."

    if _INJECTION_PATTERNS.search(text):
        logger.warning("Prompt injection pattern detected in input: %.100s", text)
        return False, "I can only help with car marketplace related questions."

    return True, ""


def validate_output(text: str) -> bool:
    """Post-process LLM output to catch obvious issues."""
    if len(text) > _MAX_OUTPUT_LENGTH:
        logger.warning("LLM output truncated (len=%d)", len(text))

    sensitive = _SENSITIVE_PATTERNS.findall(text)
    if sensitive:
        logger.warning("LLM output may contain sensitive data: %d matches", len(sensitive))

    return True


def is_car_related(text: str) -> bool:
    """Quick check if message is loosely car-marketplace related.

    Uses keyword matching for lightweight filtering before LLM processing.
    """
    car_keywords = [
        "car", "سيارة", "auto", "vehicle", "مركبة",
        "buy", "sell", "شراء", "بيع", "price", "سعر",
        "bmw", "mercedes", "toyota", "hyundai", "kia",
        "nissan", "chevrolet", "ford", "honda", "mitsubishi",
        "engine", "motor", "محرك", "gear", "ناقل",
        "insurance", "تأمين", "maintenance", "صيانة",
        "dealer", "وكيل", "showroom", "معرض",
        "compare", "مقارنة", "recommend", "ينصح",
        "budget", "ميزانية", "finance", "تمويل",
        "mileage", "km", "كيلومتر", "condition", "حالة",
        "ad", "إعلان", "listing", "market", "سوق",
    ]
    text_lower = text.lower()
    return any(kw in text_lower for kw in car_keywords)
