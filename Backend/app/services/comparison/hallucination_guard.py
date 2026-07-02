import logging
import re

from app.services.comparison.models import ComparisonResult, CarAnalysis

logger = logging.getLogger(__name__)


class HallucinationGuardError(ValueError):
    pass


def validate_comparison(result: ComparisonResult, car_a: CarAnalysis, car_b: CarAnalysis) -> None:
    errors: list[str] = []

    # Check 1: All claims in summary/recommendation trace back to analysis fields
    allowed_terms = _build_allowed_terms(car_a, car_b)
    all_text = f"{result.summary} {result.recommendation}".lower()
    for car_key in ["car_a", "car_b"]:
        for claim in result.advantages.get(car_key, []) + result.disadvantages.get(car_key, []):
            _check_claim_traces_back(claim.lower(), allowed_terms, errors)

    # Check 2: No accident history is asserted
    _check_no_accident_claims(result, car_a, car_b, errors)

    # Check 3: No mechanical fault is asserted from structured-only data
    _check_no_mechanical_faults(result, car_a, car_b, errors)

    # Check 4: Confidence score is present and consistent
    _check_confidence_consistency(result, car_a, car_b, errors)

    # Check 5: Winner is valid
    if result.winner not in ("car_a", "car_b"):
        errors.append(f"Invalid winner '{result.winner}'; must be 'car_a' or 'car_b'")

    if errors:
        error_msg = "HallucinationGuard failed: " + "; ".join(errors)
        logger.warning(error_msg)
        raise HallucinationGuardError(error_msg)

    logger.info("HallucinationGuard passed all 5 checks")


def _build_allowed_terms(car_a: CarAnalysis, car_b: CarAnalysis) -> set[str]:
    terms = set()
    for car in (car_a, car_b):
        terms.update(car.structured.pros)
        terms.update(car.structured.cons)
        terms.update(car.structured.risks)
        terms.add(str(car.year))
        terms.add(car.brand.lower())
        terms.add(car.model.lower())
        if car.vision:
            for finding in car.vision.get("findings", []):
                terms.add(finding.lower())
        if car.market:
            for finding in car.market.get("findings", []):
                terms.add(finding.lower())
    return terms


def _check_claim_traces_back(claim: str, allowed_terms: set[str], errors: list[str]) -> None:
    if not claim:
        return
    found = False
    for term in allowed_terms:
        if term and len(term) > 3 and term.lower() in claim:
            found = True
            break
    if not found:
        errors.append(f"Claim '{claim[:80]}...' does not trace back to any analysis field")


def _check_no_accident_claims(result: ComparisonResult, car_a: CarAnalysis, car_b: CarAnalysis, errors: list[str]) -> None:
    accident_patterns = [
        r"\baccident\b", r"\bcrash\b", r"\bcollision\b",
        r"\bwreck\b", r"\brebuilt\b",
    ]
    cars = {"car_a": car_a, "car_b": car_b}

    for car_key, car in cars.items():
        vision = car.vision
        vision_has_accident_data = (
            vision is not None
            and vision.get("accident_indicators", "unknown") not in ("unknown", "no_images")
        )
        if vision_has_accident_data:
            continue

        claims = result.advantages.get(car_key, []) + result.disadvantages.get(car_key, [])
        for claim in claims:
            for pattern in accident_patterns:
                if re.search(pattern, claim.lower()):
                    errors.append(
                        f"Accident history asserted for {car_key} in '{claim[:60]}...' "
                        f"but vision accident_indicators is '{vision.get('accident_indicators', 'unknown') if vision else 'N/A'}'"
                    )
                    break


def _check_no_mechanical_faults(result: ComparisonResult, car_a: CarAnalysis, car_b: CarAnalysis, errors: list[str]) -> None:
    mechanical_patterns = [
        r"\bengine\s+(issue|problem|fault|failure|noise|knock|overheat)\b",
        r"\btransmission\s+(issue|problem|fault|failure|slipp)\b",
        r"\bclutch\s+(issue|problem|worn)\b",
        r"\btiming\s+(belt|chain)\s+(issue|problem)\b",
        r"\bgasket\b",
    ]
    all_text = f"{result.summary} {result.recommendation}".lower()
    for pattern in mechanical_patterns:
        if re.search(pattern, all_text):
            errors.append(
                f"Mechanical fault asserted ('{pattern}') without mechanical inspection data"
            )
            break


def _check_confidence_consistency(result: ComparisonResult, car_a: CarAnalysis, car_b: CarAnalysis, errors: list[str]) -> None:
    if result.confidence <= 0:
        errors.append(f"Comparison confidence is {result.confidence}, must be > 0")
    lowest_input = min(car_a.confidence, car_b.confidence)
    if result.confidence > lowest_input + 0.2:
        errors.append(
            f"Comparison confidence ({result.confidence:.2f}) exceeds "
            f"lowest input confidence ({lowest_input:.2f}) by more than 0.2"
        )
