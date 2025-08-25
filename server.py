from typing import List, Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from main import Point, points_to_geojson, load_points_from_json
from automation.constructor import build_map_in_constructor
from automation.collections import build_collection_in_maps


app = FastAPI(title="Yandex Map Publisher")


class PublishConstructorRequest(BaseModel):
    title: str
    points: List[Point]
    headless: Optional[bool] = True


class PublishCollectionsRequest(BaseModel):
    cookies_path: str
    collection_name: str
    points: List[Point]
    headless: Optional[bool] = True


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/to-geojson")
def to_geojson(payload: List[Point]) -> dict:
    return points_to_geojson(payload)


@app.post("/publish/constructor")
def publish_constructor(body: PublishConstructorRequest) -> dict:
    url = build_map_in_constructor(points=body.points, map_title=body.title, headless=body.headless)
    if not url:
        raise HTTPException(status_code=500, detail="Не удалось получить публичную ссылку из Конструктора")
    return {"url": url}


@app.post("/publish/collections")
def publish_collections(body: PublishCollectionsRequest) -> dict:
    url = build_collection_in_maps(points=body.points, cookies_path=body.cookies_path, collection_name=body.collection_name, headless=body.headless)
    if not url:
        raise HTTPException(status_code=500, detail="Не удалось получить ссылку коллекции")
    return {"url": url}


@app.post("/publish/constructor/from-file")
def publish_constructor_from_file(path: str, title: str, headless: bool = True) -> dict:
    points = load_points_from_json(path)
    url = build_map_in_constructor(points=points, map_title=title, headless=headless)
    if not url:
        raise HTTPException(status_code=500, detail="Не удалось получить публичную ссылку из Конструктора")
    return {"url": url}


@app.post("/publish/collections/from-file")
def publish_collections_from_file(points_path: str, cookies_path: str, collection_name: str, headless: bool = True) -> dict:
    points = load_points_from_json(points_path)
    url = build_collection_in_maps(points=points, cookies_path=cookies_path, collection_name=collection_name, headless=headless)
    if not url:
        raise HTTPException(status_code=500, detail="Не удалось получить ссылку коллекции")
    return {"url": url}

