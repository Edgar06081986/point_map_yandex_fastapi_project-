from typing import List, Optional
import json
from pathlib import Path
from playwright.sync_api import sync_playwright, BrowserContext, Page
from main import Point


MAPS_URL = "https://yandex.ru/maps/"


def _load_cookies(cookies_path: str) -> list:
    data = json.loads(Path(cookies_path).read_text(encoding="utf-8"))
    # Accept either a list of cookie dicts or a dict with "cookies"
    if isinstance(data, dict) and "cookies" in data:
        return data["cookies"]
    if isinstance(data, list):
        return data
    raise ValueError("Unsupported cookies format: expected list or {cookies: [...]} dict")


def _search_coordinates(page: Page, latitude: float, longitude: float) -> None:
    query = f"{latitude}, {longitude}"
    search_box = page.get_by_role("searchbox").first
    if search_box.count() == 0:
        search_box = page.get_by_placeholder("Поиск мест и адресов").first
    if search_box.count() > 0:
        search_box.fill(query)
        search_box.press("Enter")
        page.wait_for_timeout(1500)
    else:
        # Fallback: type to body
        page.keyboard.type(query)
        page.keyboard.press("Enter")
        page.wait_for_timeout(1500)


def build_collection_in_maps(points: List[Point], cookies_path: str, collection_name: str, headless: bool = True) -> Optional[str]:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        context: BrowserContext = browser.new_context(locale="ru-RU")

        # Inject cookies to be authenticated
        cookies = _load_cookies(cookies_path)
        try:
            context.add_cookies(cookies)
        except Exception:
            # Try to map Chrome JSON format fields to Playwright
            mapped = []
            for c in cookies:
                mapped.append({
                    "name": c.get("name"),
                    "value": c.get("value"),
                    "domain": c.get("domain", ".yandex.ru"),
                    "path": c.get("path", "/"),
                    "httpOnly": c.get("httpOnly", False),
                    "secure": c.get("secure", True),
                    "sameSite": c.get("sameSite", "Lax"),
                })
            context.add_cookies(mapped)

        page = context.new_page()
        page.goto(MAPS_URL, wait_until="domcontentloaded")

        # Open Collections panel
        try:
            page.get_by_role("button", name="Коллекции").click(timeout=3000)
        except Exception:
            try:
                page.get_by_text("Коллекции").first.click(timeout=3000)
            except Exception:
                pass

        # Create new collection
        try:
            page.get_by_role("button", name="Новая коллекция").click(timeout=3000)
        except Exception:
            try:
                page.get_by_text("Создать коллекцию").first.click(timeout=3000)
            except Exception:
                pass

        # Set collection name
        try:
            name_input = page.get_by_placeholder("Название коллекции").first
            if name_input.count() > 0:
                name_input.fill(collection_name)
                try:
                    page.get_by_role("button", name="Сохранить").click(timeout=2000)
                except Exception:
                    pass
        except Exception:
            pass

        # Add points into the collection
        for pt in points:
            _search_coordinates(page, pt.latitude, pt.longitude)
            # Open place card menu and save to collection
            try:
                page.get_by_role("button", name="Сохранить").first.click(timeout=2000)
            except Exception:
                try:
                    page.get_by_text("Сохранить").first.click(timeout=2000)
                except Exception:
                    pass
            # Choose our collection
            try:
                page.get_by_text(collection_name).first.click(timeout=2000)
            except Exception:
                pass

        # Open collection and copy public link
        share_url: Optional[str] = None
        try:
            # Open Collections panel again and select our collection
            try:
                page.get_by_role("button", name="Коллекции").click(timeout=2000)
            except Exception:
                pass
            page.get_by_text(collection_name).first.click(timeout=3000)
            # Open share dialog
            try:
                page.get_by_role("button", name="Поделиться").click(timeout=2000)
            except Exception:
                page.get_by_text("Поделиться").first.click(timeout=2000)
            # Read link
            link_el = page.locator("input[type='text']").first
            if link_el.count() > 0:
                share_url = link_el.input_value()
        except Exception:
            pass

        context.close()
        browser.close()
        return share_url

