from qdrant_client import QdrantClient
from qdrant_client.http import models as qmodels
from typing import Optional
from app.config import settings


class QdrantSearch:
    def __init__(self, client: QdrantClient):
        self.client = client
        self.collection = settings.qdrant_collection

    def search(
        self,
        vector: list[float],
        limit: int = 5,
        price_min: Optional[float] = None,
        price_max: Optional[float] = None,
        city: Optional[str] = None,
        brand: Optional[str] = None,
        fuel_type: Optional[str] = None,
        transmission: Optional[str] = None,
        body_type: Optional[str] = None,
        year_min: Optional[int] = None,
        year_max: Optional[int] = None,
        exclude_ad_id: Optional[str] = None,
    ) -> list[dict]:
        must = [qmodels.FieldCondition(
            key="is_active", match=qmodels.MatchValue(value=True)
        )]
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
        if brand:
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
        if body_type:
            must.append(qmodels.FieldCondition(
                key="body_type", match=qmodels.MatchValue(value=body_type)
            ))
        if year_min is not None:
            must.append(qmodels.FieldCondition(
                key="year", range=qmodels.Range(gte=year_min)
            ))
        if year_max is not None:
            must.append(qmodels.FieldCondition(
                key="year", range=qmodels.Range(lte=year_max)
            ))

        query_filter = qmodels.Filter(must=must) if must else None

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
