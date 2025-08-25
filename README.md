## point_map_yandex_fastapi_project

- Вход: JSON со списком точек `{id, latitude, longitude, title?}`
- Скрипт создаёт публичную карту с метками через веб-автоматизацию и отдаёт ссылку

### Задача
- **Вход**: JSON с точками `[{id, latitude, longitude, title?}, ...]`
- **Выход**: публичная карта Яндекса или коллекция с метками, видимая в другой сессии/на другом устройстве (через общий URL или в аккаунте).

### Подходы (оба реализованы)
- **Map Constructor (официальный конструктор карт)**: создаёт публичную карту и возвращает ссылку. Видно всем по ссылке, без авторизации.
- **Коллекции в аккаунте**: добавляет точки в коллекцию авторизованного пользователя, можно поделиться ссылкой на коллекцию. Видно на всех устройствах при входе в аккаунт; по ссылке — всем.

### Быстрый старт
1) Установите Python 3.12+ и создайте окружение:
```
python3 -m venv .venv
. .venv/bin/activate
pip install -U pip
pip install -e .
python -m playwright install chromium
```

2) Проверьте входные данные:
```
python cli.py to_geojson samples/points.json
```

3a) Опубликовать карту через Конструктор:
```
python cli.py constructor samples/points.json --title "Демо точки" --headless False
```
На выходе получите URL опубликованной карты. Откройте на другом устройстве/в другом браузере — метки видны.

3б) Добавить в Коллекции (нужны cookie авторизованной сессии):
- В браузере откройте `yandex.ru`, войдите.
- В DevTools Application/Storage экспортируйте cookies в JSON (см. `samples/cookies.sample.json`).
```
python cli.py collections samples/points.json cookies.json --collection-name "Демо коллекция" --headless False
```
Скрипт распечатает ссылку на коллекцию. Откройте на другом устройстве (вошли в аккаунт — появится в Коллекциях; либо по ссылке).

### Формат входа
`samples/points.json`:
```
[
  {"id": "p1", "latitude": 55.751244, "longitude": 37.618423, "title": "Москва"},
  {"id": "p2", "latitude": 59.938732, "longitude": 30.316229, "title": "СПб"}
]
```

### Ключевые файлы
- `main.py` — модели `Point`, валидация, экспорт в GeoJSON
- `cli.py` — команды: `to_geojson`, `constructor`, `collections`
- `automation/constructor.py` — автоматизация Конструктора карт (публикация, ссылка)
- `automation/collections.py` — автоматизация Коллекций (создание, шаринг)

### Обработка ошибок (кратко)
- Валидация входа через Pydantic (диапазоны широты/долготы, пустые заголовки).
- Веб-автоматизация использует несколько селекторов и таймаутов; при провале шаг пропускается, продолжается выполнение.
- Явное сообщение об ошибках в формате CLI exit code 1, читаемые trace/log.

### Доказательство видимости
- Конструктор: откройте напечатанную ссылку в инкогнито/на другом устройстве.
- Коллекции: откройте ссылку коллекции или зайдите в аккаунт на другом устройстве и откройте `Коллекции`.

### Примечания
- UI Яндекс.Карт меняется; селекторы в Playwright подобраны с запасом (несколько вариантов, русские/роле-селекторы).
- При необходимости используйте `--headless False` для наглядности и скриншотов.

### FastAPI сервер

Запуск сервера:
```
uvicorn server:app --host 0.0.0.0 --port 8000
```

Проверка здоровья:
```
GET http://localhost:8000/health
```

Преобразование точек в GeoJSON:
```
POST http://localhost:8000/to-geojson
Body (json): [
  {"id":"p1","latitude":55.751244,"longitude":37.618423,"title":"Москва"}
]
```

Публикация через Конструктор карт (вернёт публичную ссылку):
```
POST http://localhost:8000/publish/constructor
Body (json): {
  "title": "Демо точки",
  "points": [
    {"id":"p1","latitude":55.751244,"longitude":37.618423,"title":"Москва"}
  ],
  "headless": false
}
```
Ответ:
```
{"url": "https://yandex.ru/map-..."}
```

Публикация в Коллекции (нужны cookies авторизованной сессии):
```
POST http://localhost:8000/publish/collections
Body (json): {
  "cookies_path": "samples/cookies.sample.json",
  "collection_name": "Демо коллекция",
  "points": [
    {"id":"p1","latitude":55.751244,"longitude":37.618423,"title":"Москва"}
  ],
  "headless": false
}
```

Упрощённые эндпоинты из файлов:
```
POST http://localhost:8000/publish/constructor/from-file?path=samples/points.json&title=Демо&headless=false
POST http://localhost:8000/publish/collections/from-file?points_path=samples/points.json&cookies_path=samples/cookies.sample.json&collection_name=Демо&headless=false
```

Где взять ссылку для открытия карты?
- Эндпоинты публикации возвращают поле `url`. Это и есть ссылка, которую можно открыть на любом устройстве и увидеть метки на карте.
