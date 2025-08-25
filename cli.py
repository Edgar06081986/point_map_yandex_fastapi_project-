import json
import pathlib
import sys
import typer
from rich import print


app = typer.Typer(add_completion=False, help="Create Yandex Maps markers from JSON points")


@app.command()
def to_geojson(points_path: str, out: str = "-"):
    """Convert input JSON points to GeoJSON FeatureCollection."""
    from main import load_points_from_json, points_to_geojson

    points = load_points_from_json(points_path)
    geo = points_to_geojson(points)
    if out == "-":
        json.dump(geo, sys.stdout, ensure_ascii=False, indent=2)
        print()
    else:
        pathlib.Path(out).parent.mkdir(parents=True, exist_ok=True)
        with open(out, "w", encoding="utf-8") as f:
            json.dump(geo, f, ensure_ascii=False, indent=2)
        print(f"[green]Wrote[/green] {out}")


@app.command()
def constructor(points_path: str, title: str = "Auto map", headless: bool = True) -> None:
    """Create a public map via Yandex Map Constructor and print share URL."""
    from main import load_points_from_json
    from automation.constructor import build_map_in_constructor

    points = load_points_from_json(points_path)
    url = build_map_in_constructor(points=points, map_title=title, headless=headless)
    if url:
        print(f"[bold green]Published map:[/bold green] {url}")
    else:
        raise typer.Exit(code=1)


@app.command()
def collections(points_path: str, cookies_path: str, collection_name: str = "Auto collection", headless: bool = True) -> None:
    """Create a Yandex Maps collection in the user account and return its share link.

    Requires cookies for yandex.ru authenticated session (exported JSON from browser devtools).
    """
    from main import load_points_from_json
    from automation.collections import build_collection_in_maps

    points = load_points_from_json(points_path)
    url = build_collection_in_maps(points=points, cookies_path=cookies_path, collection_name=collection_name, headless=headless)
    if url:
        print(f"[bold green]Collection link:[/bold green] {url}")
    else:
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()

