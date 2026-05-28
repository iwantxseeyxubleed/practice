from pathlib import Path

APP_DIR = Path(__file__).resolve().parent
IMPORT_DIR = APP_DIR / "import"
IMAGES_DIR = APP_DIR / "images"
DB_PATH = APP_DIR / "electroservice.db"
PLACEHOLDER = IMPORT_DIR / "picture.png"

BG = "#FFFFFF"
SECOND_BG = "#7FFF00"
ACCENT = "#00FA9A"
DISCOUNT_BG = "#2E8B57"
EMPTY_STOCK_BG = "#ADD8E6"
FONT = ("Times New Roman", 12)
TITLE_FONT = ("Times New Roman", 18, "bold")
