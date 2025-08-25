from typing import List, Optional
import time
from playwright.sync_api import sync_playwright, Page, BrowserContext
from main import Point


CONSTRUCTOR_URL = "https://yandex.ru/map-constructor/"


def _click_add_marker_tool(page: Page) -> None:
    # Try several selectors as the UI may vary
    candidates = [
        "[aria-label='Добавить метку']",
        "button[title*='метк']",
        "[data-key='add-placemark']",
    ]
    for sel in candidates:
        try:
            el = page.locator(sel).first
            if el.count() > 0:
                el.click(timeout=2000)
                return
        except Exception:
            pass
    # Fallback: open toolbar by keyboard and pick placemark (if available)
    try:
        page.keyboard.press("KeyM")
    except Exception:
        pass


def _search_coordinates(page: Page, latitude: float, longitude: float) -> None:
    # Search input can be found by role or placeholder
    query = f"{latitude}, {longitude}"
    input_candidates = [
        page.get_by_placeholder("Поиск"),
        page.locator("input[type='search']"),
        page.locator("input"),
    ]
    for inp in input_candidates:
        try:
            if inp.count() > 0:
                box = inp.first
                box.fill("")
                box.type(query, delay=20)
                box.press("Enter")
                page.wait_for_timeout(1200)
                return
        except Exception:
            continue
    # As a last resort, focus body and type
    page.keyboard.type(query)
    page.keyboard.press("Enter")
    page.wait_for_timeout(1200)


def build_map_in_constructor(points: List[Point], map_title: str, headless: bool = True) -> Optional[str]:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        context: BrowserContext = browser.new_context(locale="ru-RU")
        page = context.new_page()
        page.goto(CONSTRUCTOR_URL, wait_until="domcontentloaded")

        # Create a new map if the landing suggests it
        try:
            page.get_by_role("button", name="Создать карту").click(timeout=3000)
        except Exception:
            pass

        # Set map title if possible
        try:
            title_input = page.get_by_placeholder("Название карты").first
            if title_input.count() > 0:
                title_input.fill(map_title)
        except Exception:
            pass

        # For each point: search by coordinates, add placemark at center, set title
        for pt in points:
            _search_coordinates(page, pt.latitude, pt.longitude)
            page.wait_for_timeout(1000)
            _click_add_marker_tool(page)
            # Click at center of the map to place the placemark
            try:
                viewport = page.viewport_size
                if viewport:
                    x = viewport["width"] // 2
                    y = viewport["height"] // 2
                    page.mouse.click(x, y)
            except Exception:
                pass
            # Set marker title/label if a sidebar/input appears
            try:
                name_inp = page.get_by_placeholder("Название метки").first
                if name_inp.count() > 0 and (pt.title or pt.id):
                    name_inp.fill(pt.title or pt.id)
                    # Save changes if save button exists
                    try:
                        page.get_by_role("button", name="Сохранить").click(timeout=1000)
                    except Exception:
                        pass
            except Exception:
                pass

        # Publish and grab share link
        share_url: Optional[str] = None
        try:
            # Try open publish/share dialog
            candidates = [
                page.get_by_role("button", name="Публикация"),
                page.get_by_role("button", name="Опубликовать"),
                page.get_by_text("Опубликовать"),
            ]
            clicked = False
            for c in candidates:
                try:
                    c.click(timeout=2000)
                    clicked = True
                    break
                except Exception:
                    continue
            if clicked:
                # Look for a direct link in the dialog
                link_el = page.locator("a[href*='map-']").first
                if link_el.count() > 0:
                    share_url = link_el.get_attribute("href")
        except Exception:
            pass

        # Fallback: grab preview link if present
        if not share_url:
            try:
                preview = page.locator("a[href*='constructor']").first
                if preview.count() > 0:
                    share_url = preview.get_attribute("href")
            except Exception:
                pass

        context.close()
        browser.close()
        return share_url

