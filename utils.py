import re
import shutil
from pathlib import Path
from config import PLACEHOLDER, IMAGES_DIR

try:
    from PIL import Image, ImageTk
except ImportError:
    Image = None
    ImageTk = None


def load_product_image(path, size=(120, 80)):
    image_file = Path(path or "")
    if not image_file.exists():
        image_file = PLACEHOLDER
    if Image and ImageTk:
        img = Image.open(image_file).convert("RGB")
        img.thumbnail(size)
        return ImageTk.PhotoImage(img)
    return None


def save_product_image(selected_image, old_path=None):
    if not selected_image:
        return str(PLACEHOLDER)
    source = Path(selected_image)
    if not source.exists():
        return old_path or str(PLACEHOLDER)
    IMAGES_DIR.mkdir(exist_ok=True)
    safe_name = re.sub(r"[^A-Za-zА-Яа-я0-9_.-]", "_", source.name)
    target = IMAGES_DIR / safe_name
    if Image:
        img = Image.open(source).convert("RGB")
        img.thumbnail((300, 200))
        img.save(target)
    else:
        shutil.copy(source, target)
    if old_path and Path(old_path).exists() and Path(old_path) != target and Path(old_path).parent == IMAGES_DIR:
        try:
            Path(old_path).unlink()
        except OSError:
            pass
    return str(target)
