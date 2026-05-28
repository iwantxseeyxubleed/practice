import sqlite3
from pathlib import Path
from tkinter import *
from tkinter import ttk, messagebox, filedialog

from config import BG, SECOND_BG, ACCENT, FONT, TITLE_FONT
from repository import fetch_names, fetch_product, save_product
from utils import save_product_image


class ProductForm(Toplevel):
    def __init__(self, app, article=None):
        super().__init__(app)
        self.app = app
        self.article = article
        self.selected_image = None
        self.old_image_path = None
        self.title("Редактирование товара" if article else "Добавление товара")
        self.geometry("620x650")
        self.configure(bg=BG)
        self.protocol("WM_DELETE_WINDOW", self.close)
        self.build()
        if article:
            self.load_product(article)

    def build(self):
        Label(self, text=self.title(), bg=BG, font=TITLE_FONT).pack(pady=8)
        form = Frame(self, bg=BG, padx=15, pady=10)
        form.pack(fill=BOTH, expand=True)
        self.vars = {}
        fields = [
            ("article", "Артикул"), ("name", "Наименование"), ("unit", "Единица измерения"),
            ("price", "Цена"), ("supplier", "Поставщик"), ("manufacturer", "Производитель"),
            ("category", "Категория"), ("discount", "Скидка"), ("stock_quantity", "Количество на складе"),
        ]
        for key, label_text in fields:
            Label(form, text=label_text, bg=BG, font=FONT).pack(anchor=W)
            var = StringVar()
            self.vars[key] = var
            if key in ("supplier", "manufacturer", "category"):
                table = {"supplier": "suppliers", "manufacturer": "manufacturers", "category": "categories"}[key]
                combo = ttk.Combobox(form, textvariable=var, values=fetch_names(table), font=FONT)
                combo.pack(fill=X, pady=2)
            else:
                entry = Entry(form, textvariable=var, font=FONT)
                if key == "article" and self.article:
                    entry.configure(state="readonly")
                entry.pack(fill=X, pady=2)
        Label(form, text="Описание", bg=BG, font=FONT).pack(anchor=W)
        self.description_text = Text(form, height=4, font=FONT)
        self.description_text.pack(fill=X, pady=2)
        self.image_label = Label(form, text="Изображение не выбрано", bg=BG, font=FONT)
        self.image_label.pack(anchor=W, pady=4)
        Button(form, text="Выбрать изображение", bg=SECOND_BG, font=FONT, command=self.choose_image).pack(anchor=W)
        Button(form, text="Сохранить", bg=ACCENT, font=FONT, command=self.save).pack(pady=10)

    def load_product(self, article):
        row = fetch_product(article)
        if not row:
            messagebox.showerror("Ошибка", "Товар не найден")
            self.close()
            return
        for key in self.vars:
            self.vars[key].set(str(row[key] if row[key] is not None else ""))
        self.description_text.insert("1.0", row["description"] or "")
        self.selected_image = row["image_path"]
        self.old_image_path = row["image_path"]
        self.image_label.config(text=Path(self.selected_image or "").name or "Изображение не выбрано")

    def choose_image(self):
        path = filedialog.askopenfilename(filetypes=[("Images", "*.png *.jpg *.jpeg *.bmp")])
        if path:
            self.selected_image = path
            self.image_label.config(text=Path(path).name)

    def validate(self):
        data = {key: var.get().strip() for key, var in self.vars.items()}
        required = ["article", "name", "unit", "price", "supplier", "manufacturer", "category", "discount", "stock_quantity"]
        if any(not data[key] for key in required):
            messagebox.showerror("Ошибка", "Заполните все обязательные поля")
            return None
        try:
            data["price"] = float(data["price"].replace(",", "."))
            data["discount"] = int(data["discount"])
            data["stock_quantity"] = int(data["stock_quantity"])
        except ValueError:
            messagebox.showerror("Ошибка", "Цена, скидка и количество должны быть числами")
            return None
        if data["price"] < 0 or data["discount"] < 0 or data["stock_quantity"] < 0:
            messagebox.showerror("Ошибка", "Цена, скидка и количество не могут быть отрицательными")
            return None
        data["description"] = self.description_text.get("1.0", END).strip()
        return data

    def save(self):
        data = self.validate()
        if not data:
            return
        image_path = save_product_image(self.selected_image, self.old_image_path)
        try:
            save_product(data, image_path, self.article)
        except sqlite3.IntegrityError as exc:
            messagebox.showerror("Ошибка БД", f"Не удалось сохранить товар: {exc}")
            return
        self.app.refresh_products()
        self.close()

    def close(self):
        self.app.edit_window_open = False
        self.destroy()
