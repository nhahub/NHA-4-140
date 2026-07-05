import logging
from qdrant_client import QdrantClient
from qdrant_client.http import models as qmodels
from typing import Optional, List
from app.config import settings

logger = logging.getLogger(__name__)


class QdrantSearch:
    def __init__(self, client: QdrantClient):
        self.client = client
        self.collection = settings.qdrant_collection

    def _build_filter(
        self,
        price_min: Optional[float] = None,
        price_max: Optional[float] = None,
        city: Optional[str] = None,
        brand: Optional[str] = None,
        brands: Optional[List[str]] = None,
        fuel_type: Optional[str] = None,
        transmission: Optional[str] = None,
        body_types: Optional[List[str]] = None,
        excluded_body_types: Optional[List[str]] = None,
        excluded_brands: Optional[List[str]] = None,
        excluded_models: Optional[List[str]] = None,
        year_min: Optional[int] = None,
        year_max: Optional[int] = None,
    ) -> Optional[qmodels.Filter]:
        must = [qmodels.FieldCondition(
            key="is_active", match=qmodels.MatchValue(value=True)
        )]
        must_not = []

        if price_min is not None:
            must.append(qmodels.FieldCondition(
                key="price", range=qmodels.Range(gte=price_min)
            ))
        if price_max is not None:
            must.append(qmodels.FieldCondition(
                key="price", range=qmodels.Range(lte=price_max)
            ))
        if city:
            must.append(qmodels.FieldCondition(
                key="city", match=qmodels.MatchValue(value=city)
            ))
        if brands:
            must.append(qmodels.FieldCondition(
                key="brand", match=qmodels.MatchAny(any=brands)
            ))
        elif brand:
            must.append(qmodels.FieldCondition(
                key="brand", match=qmodels.MatchValue(value=brand)
            ))
        if fuel_type:
            must.append(qmodels.FieldCondition(
                key="fuel_type", match=qmodels.MatchValue(value=fuel_type)
            ))
        if transmission:
            must.append(qmodels.FieldCondition(
                key="transmission", match=qmodels.MatchValue(value=transmission)
            ))
        if body_types:
            must.append(qmodels.FieldCondition(
                key="body_type", match=qmodels.MatchAny(any=body_types)
            ))
        if excluded_body_types:
            must_not.append(qmodels.FieldCondition(
                key="body_type", match=qmodels.MatchAny(any=excluded_body_types)
            ))
        if excluded_brands:
            must_not.append(qmodels.FieldCondition(
                key="brand", match=qmodels.MatchAny(any=excluded_brands)
            ))
        if excluded_models:
            must_not.append(qmodels.FieldCondition(
                key="model", match=qmodels.MatchAny(any=excluded_models)
            ))
        if year_min is not None:
            must.append(qmodels.FieldCondition(
                key="year", range=qmodels.Range(gte=year_min)
            ))
        if year_max is not None:
            must.append(qmodels.FieldCondition(
                key="year", range=qmodels.Range(lte=year_max)
            ))

        if not must and not must_not:
            return None
        return qmodels.Filter(must=must, must_not=must_not) if must_not else (
            qmodels.Filter(must=must) if must else qmodels.Filter(must_not=must_not)
        )

    def search(
        self,
        vector: list[float],
        limit: int = 5,
        price_min: Optional[float] = None,
        price_max: Optional[float] = None,
        city: Optional[str] = None,
        brand: Optional[str] = None,
        brands: Optional[List[str]] = None,
        fuel_type: Optional[str] = None,
        transmission: Optional[str] = None,
        body_types: Optional[List[str]] = None,
        excluded_body_types: Optional[List[str]] = None,
        excluded_brands: Optional[List[str]] = None,
        excluded_models: Optional[List[str]] = None,
        year_min: Optional[int] = None,
        year_max: Optional[int] = None,
        exclude_ad_id: Optional[str] = None,
    ) -> list[dict]:
        query_filter = self._build_filter(
            price_min=price_min, price_max=price_max, city=city,
            brand=brand, brands=brands, fuel_type=fuel_type,
            transmission=transmission, body_types=body_types,
            excluded_body_types=excluded_body_types,
            excluded_brands=excluded_brands,
            excluded_models=excluded_models,
            year_min=year_min, year_max=year_max,
        )

        results = self.client.query_points(
            collection_name=self.collection,
            query=vector,
            query_filter=query_filter,
            limit=limit,
            with_payload=True,
        ).points

        points = []
        for r in results:
            p = dict(r.payload or {})
            p["score"] = r.score
            p["id"] = str(r.id)
            points.append(p)

        if exclude_ad_id:
            points = [p for p in points if p.get("ad_id") != exclude_ad_id]

        return points

    def hybrid_search(
        self,
        query_text: str,
        vector: list[float],
        limit: int = 10,
        price_min: Optional[float] = None,
        price_max: Optional[float] = None,
        city: Optional[str] = None,
        brand: Optional[str] = None,
        brands: Optional[List[str]] = None,
        fuel_type: Optional[str] = None,
        transmission: Optional[str] = None,
        body_types: Optional[List[str]] = None,
        excluded_body_types: Optional[List[str]] = None,
        excluded_brands: Optional[List[str]] = None,
        excluded_models: Optional[List[str]] = None,
        year_min: Optional[int] = None,
        year_max: Optional[int] = None,
        exclude_ad_id: Optional[str] = None,
        fusion: str = "rrf",
    ) -> list[dict]:
        """Hybrid search — tries BM25 + vector fusion, falls back to vector-only."""
        query_filter = self._build_filter(
            price_min=price_min, price_max=price_max, city=city,
            brand=brand, brands=brands, fuel_type=fuel_type,
            transmission=transmission, body_types=body_types,
            excluded_body_types=excluded_body_types,
            excluded_brands=excluded_brands,
            excluded_models=excluded_models,
            year_min=year_min, year_max=year_max,
        )

        try:
            prefetch = [
                qmodels.Prefetch(
                    query=query_text,
                    using="text",
                    limit=limit,
                    filter=query_filter,
                ),
                qmodels.Prefetch(
                    query=vector,
                    using="default",
                    limit=limit,
                    filter=query_filter,
                ),
            ]

            results = self.client.query_points(
                collection_name=self.collection,
                prefetch=prefetch,
                query=qmodels.FusionQuery(fusion=fusion),
                limit=limit,
                with_payload=True,
            ).points
        except Exception:
            logger.warning("Hybrid (BM25+vector) query failed — falling back to vector-only search")
            results = self.client.query_points(
                collection_name=self.collection,
                query=vector,
                query_filter=query_filter,
                limit=limit,
                with_payload=True,
            ).points

        points = []
        for r in results:
            p = dict(r.payload or {})
            p["score"] = r.score
            p["id"] = str(r.id)
            points.append(p)

        if exclude_ad_id:
            points = [p for p in points if p.get("ad_id") != exclude_ad_id]

        return points
