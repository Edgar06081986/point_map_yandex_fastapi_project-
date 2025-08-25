from typing import List, Optional
from pydantic import BaseModel, Field, ValidationError, field_validator
import json


class Point(BaseModel):
    id: str
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    title: Optional[str] = None

    @field_validator("title")
    @classmethod
    def normalize_title(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        trimmed = value.strip()
        return trimmed if trimmed else None


def points_to_geojson(points: List[Point]) -> dict:
    features = []
    for p in points:
        features.append(
            {
                "type": "Feature",
                "id": p.id,
                "geometry": {"type": "Point", "coordinates": [p.longitude, p.latitude]},
                "properties": {"name": p.title or p.id},
            }
        )
    return {"type": "FeatureCollection", "features": features}


def load_points_from_json(path: str) -> List[Point]:
    with open(path, "r", encoding="utf-8") as f:
        raw = json.load(f)
    if not isinstance(raw, list):
        raise ValueError("Input JSON must be a list of points")
    points: List[Point] = []
    errors = []
    for idx, item in enumerate(raw):
        try:
            points.append(Point(**item))
        except ValidationError as ve:
            errors.append(f"index {idx}: {ve}")
    if errors:
        joined = "\n".join(errors)
        raise ValueError(f"Invalid points in input JSON:\n{joined}")
    return points


def main():
    print("OK: models and converters loaded")


if __name__ == "__main__":
    main()
