from __future__ import annotations

from dataclasses import dataclass, field
from typing import List


@dataclass
class StructuredAnalysis:
    summary: str = ""
    pros: List[str] = field(default_factory=list)
    cons: List[str] = field(default_factory=list)
    risks: List[str] = field(default_factory=list)
    maintenance_expectations: str = ""
    value_for_money: str = ""
    price_fairness: str = ""
    suitable_buyer_type: str = ""

    overall_score: int = 0
    condition_score: int = 0
    price_score: int = 0
    reliability_score: int = 0
    market_reputation: str = ""

    confidence: float = 0.0


@dataclass
class CarAnalysis:
    ad_id: str
    brand: str
    model: str
    year: int
    price: float

    structured: StructuredAnalysis = field(default_factory=StructuredAnalysis)
    vision: dict | None = None
    market: dict | None = None

    confidence: float = 0.0

    def to_dict(self) -> dict:
        return {
            "ad_id": self.ad_id,
            "brand": self.brand,
            "model": self.model,
            "year": self.year,
            "price": self.price,
            "structured": {
                "summary": self.structured.summary,
                "pros": self.structured.pros,
                "cons": self.structured.cons,
                "risks": self.structured.risks,
                "maintenance_expectations": self.structured.maintenance_expectations,
                "value_for_money": self.structured.value_for_money,
                "price_fairness": self.structured.price_fairness,
                "suitable_buyer_type": self.structured.suitable_buyer_type,
            },
            "scores": {
                "overall": self.structured.overall_score,
                "condition": self.structured.condition_score,
                "price": self.structured.price_score,
                "reliability": self.structured.reliability_score,
                "market_reputation": self.structured.market_reputation,
            },
            "vision": self.vision,
            "market": self.market,
            "confidence": self.confidence,
        }


@dataclass
class ComparisonResult:
    winner: str
    summary: str
    advantages: dict
    disadvantages: dict
    recommendation: str
    buyer_type: dict
    confidence: float

    def to_dict(self) -> dict:
        return {
            "winner": self.winner,
            "summary": self.summary,
            "advantages": self.advantages,
            "disadvantages": self.disadvantages,
            "recommendation": self.recommendation,
            "buyer_type": self.buyer_type,
            "confidence": self.confidence,
        }


@dataclass
class ComparisonReport:
    car_a: CarAnalysis
    car_b: CarAnalysis
    comparison: ComparisonResult

    def to_dict(self) -> dict:
        return {
            "car_a": self.car_a.to_dict(),
            "car_b": self.car_b.to_dict(),
            "comparison": self.comparison.to_dict(),
        }
