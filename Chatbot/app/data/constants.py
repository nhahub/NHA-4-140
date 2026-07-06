import json
from app.enums import NodeName

# ---- Search quality thresholds ----
SEARCH_QUALITY_TOP_SCORE_MIN = 0.65
SEARCH_QUALITY_AVG_SCORE_MIN = 0.5

# ---- Search result limits ----
SEARCH_INITIAL_LIMIT = 5
SEARCH_BROAD_LIMIT = 10
MERGE_MAX_COUNT = 2

# ---- Recommendation search limits ----
RECOMMENDATION_LIMIT = 8

# ---- Seller price analysis ----
SELLER_DEFAULT_YEAR_RANGE = 2
SELLER_MARKET_LIMIT = 10
SELLER_MEDIAN_MULTIPLIER_LOW = 0.9
SELLER_MEDIAN_MULTIPLIER_HIGH = 1.1
SELLER_HIGH_KM_MULTIPLIER_LOW = 0.85
SELLER_HIGH_KM_MULTIPLIER_HIGH = 1.05

# ---- Preference inference ----
USE_INFERRED_AS_HARD_FILTER = False  # inferred body types are soft signal only by default

# ---- Response streaming ----
RESPONDER_TOKEN_DELAY_SECONDS = 0.02

# ---- Node status messages ----
NODE_STATUS_MAP = {
    NodeName.CATALOGUE: "Checking our catalogue...",
    NodeName.SEARCH: "Searching listings...",
    NodeName.RECOMMENDATION: "Finding alternatives...",
    NodeName.ADVISOR: "Analyzing this car...",
    NodeName.SELLER: "Analyzing market data...",
    NodeName.GUIDE: "Looking that up...",
    NodeName.GENERAL: "",
}


def format_status_map() -> str:
    return json.dumps(NODE_STATUS_MAP, ensure_ascii=False)
