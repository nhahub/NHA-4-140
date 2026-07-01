import re


def verify_results(results: list[dict]) -> list[dict]:
    return [r for r in results if r.get("is_active", False) is True]


def build_grounding_block(ad_payload: dict) -> str:
    images = ad_payload.get("images", [])
    cover = ad_payload.get("cover_image_url")
    has_images = bool(images) or bool(cover)

    return (
        "[VERIFIED LISTING DATA — base all answers on this block only]\n"
        f"Brand: {ad_payload.get('brand', 'N/A')} | Model: {ad_payload.get('model', 'N/A')} | Year: {ad_payload.get('year', 'N/A')}\n"
        f"Price: {ad_payload.get('price', 'N/A')} EGP | KM: {ad_payload.get('km_driven', 'N/A')} | Condition: {ad_payload.get('condition', 'N/A')}\n"
        f"Fuel: {ad_payload.get('fuel_type', 'N/A')} | Transmission: {ad_payload.get('transmission', 'N/A')} | City: {ad_payload.get('city', 'N/A')}\n"
        f"Description: {ad_payload.get('description', 'N/A')}\n"
        f"Special conditions: {ad_payload.get('special_conditions', 'N/A')}\n"
        f"Images available: {'Yes' if has_images else 'No'}\n"
        "[END VERIFIED DATA]"
    )


def validate_response(response: str, ad_payload: dict) -> str:
    price_numbers = re.findall(r'\b\d{5,7}\b', response)
    years = re.findall(r'\b(19[9]\d|20[0-2]\d|2030)\b', response)
    numbers_to_check = price_numbers + years
    for num_str in numbers_to_check:
        num = int(num_str)
        for field in ("price", "km_driven", "year"):
            val = ad_payload.get(field)
            if val is None:
                continue
            val = float(val)
            if val > 0 and abs(num - val) / val > 0.05:
                response += (
                    "\n\n\u26a0\ufe0f Please verify all specifications directly with the seller."
                )
                return response
    return response
