from tkinter import *
from tkinter import ttk, messagebox

from config import BG, SECOND_BG, ACCENT, DISCOUNT_BG, EMPTY_STOCK_BG, FONT, TITLE_FONT, IMPORT_DIR
from repository import authorize_user, fetch_products, fetch_names, product_exists_in_orders, delete_product
from product_form import ProductForm
from utils import load_product_image

try:
    from PIL import Image, ImageTk
except ImportError:
    Image = None
    ImageTk = None


class ElectroServiceApp(Tk):
    def __init__(self):
        super().__init__()
        self.title("ООО ЭлектроСервис")
        self.geometry("1100x720")
        self.configure(bg=BG)
        self.current_user = None
        self.current_role = "Гость"
        self.edit_window_open = False
        icon_path = IMPORT_DIR / "Icon.ico"
        if icon_path.exists():
            try:
                self.iconbitmap(icon_path)
            except TclError:
                pass
        self.show_login()

    def clear(self):
        for widget in self.winfo_children():
            widget.destroy()

    def show_login(self):
        self.clear()
        self.current_user = None
        self.current_role = "Гость"
        frame = Frame(self, bg=BG, padx=30, pady=30)
        frame.pack(expand=True)
        logo_path = IMPORT_DIR / "Icon.png"
        if logo_path.exists() and Image and ImageTk:
            img = Image.open(logo_path)
            img.thumbnail((150, 150))
            self.logo_img = ImageTk.PhotoImage(img)
            Label(frame, image=self.logo_img, bg=BG).pack(pady=5)
        Label(frame, text="Вход в систему", bg=BG, font=TITLE_FONT).pack(pady=10)
        Label(frame, text="Логин", bg=BG, font=FONT).pack(anchor=W)
        login_entry = Entry(frame, font=FONT, width=35)
        login_entry.pack(pady=4)
        Label(frame, text="Пароль", bg=BG, font=FONT).pack(anchor=W)
        password_entry = Entry(frame, font=FONT, width=35, show="*")
        password_entry.pack(pady=4)

        def login():
            row = authorize_user(login_entry.get().strip(), password_entry.get().strip())
            if not row:
                messagebox.showerror("Ошибка", "Неверный логин или пароль")
                return
            self.current_user = dict(row)
            self.current_role = row["role_name"]
            self.show_products()

        Button(frame, text="Войти", bg=ACCENT, font=FONT, width=25, command=login).pack(pady=8)
        Button(frame, text="Войти как гость", bg=SECOND_BG, font=FONT, width=25, command=self.show_products).pack()

    def header(self, parent, title):
        top = Frame(parent, bg=SECOND_BG, padx=10, pady=8)
        top.pack(fill=X)
        Label(top, text=title, bg=SECOND_BG, font=TITLE_FONT).pack(side=LEFT)
        full_name = self.current_user["full_name"] if self.current_user else "Гость"
        Label(top, text=f"{full_name} ({self.current_role})", bg=SECOND_BG, font=FONT).pack(side=RIGHT, padx=10)
        Button(top, text="Выйти", font=FONT, command=self.show_login).pack(side=RIGHT)

    def show_products(self):
        self.clear()
        self.header(self, "Список товаров")
        self.create_controls()
        self.create_products_area()
        self.refresh_products()

    def create_controls(self):
        controls = Frame(self, bg=BG, pady=8)
        controls.pack(fill=X)
        self.search_var = StringVar()
        self.supplier_var = StringVar(value="Все поставщики")
        self.sort_var = StringVar(value="Без сортировки")

        if self.current_role in ("Менеджер", "Администратор"):
            Label(controls, text="Поиск:", bg=BG, font=FONT).pack(side=LEFT, padx=5)
            Entry(controls, textvariable=self.search_var, font=FONT, width=25).pack(side=LEFT, padx=5)
            Label(controls, text="Поставщик:", bg=BG, font=FONT).pack(side=LEFT, padx=5)
            suppliers = ["Все поставщики"] + fetch_names("suppliers")
            ttk.Combobox(controls, textvariable=self.supplier_var, values=suppliers, state="readonly", width=25).pack(side=LEFT, padx=5)
            Label(controls, text="Сортировка:", bg=BG, font=FONT).pack(side=LEFT, padx=5)
            ttk.Combobox(
                controls,
                textvariable=self.sort_var,
                values=["Без сортировки", "Остаток по возрастанию", "Остаток по убыванию"],
                state="readonly",
                width=22,
            ).pack(side=LEFT, padx=5)
            self.search_var.trace_add("write", lambda *_: self.refresh_products())
            self.supplier_var.trace_add("write", lambda *_: self.refresh_products())
            self.sort_var.trace_add("write", lambda *_: self.refresh_products())

        if self.current_role == "Администратор":
            Button(controls, text="Добавить товар", bg=ACCENT, font=FONT, command=lambda: self.open_product_form()).pack(side=RIGHT, padx=10)

    def create_products_area(self):
        self.canvas = Canvas(self, bg=BG, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self, orient=VERTICAL, command=self.canvas.yview)
        self.products_frame = Frame(self.canvas, bg=BG)
        self.products_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.create_window((0, 0), window=self.products_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)
        self.canvas.pack(side=LEFT, fill=BOTH, expand=True)
        scrollbar.pack(side=RIGHT, fill=Y)
        self.product_images = []

    def refresh_products(self):
        for widget in self.products_frame.winfo_children():
            widget.destroy()
        search = self.search_var.get() if hasattr(self, "search_var") else ""
        supplier = self.supplier_var.get() if hasattr(self, "supplier_var") else "Все поставщики"
        sort_mode = self.sort_var.get() if hasattr(self, "sort_var") else "Без сортировки"
        products = fetch_products(search, supplier, sort_mode)
        Label(self.products_frame, text=f"Найдено товаров: {len(products)}", bg=BG, font=FONT).pack(anchor=W, padx=10, pady=5)
        self.product_images = []
        for product in products:
            self.product_card(product)

    def product_card(self, product):
        bg = BG
        if product["stock_quantity"] <= 0:
            bg = EMPTY_STOCK_BG
        elif product["discount"] > 15:
            bg = DISCOUNT_BG

        card = Frame(self.products_frame, bg=bg, bd=1, relief=SOLID, padx=10, pady=10)
        card.pack(fill=X, padx=12, pady=6)
        photo = load_product_image(product["image_path"])
        if photo:
            self.product_images.append(photo)
            Label(card, image=photo, bg=bg, width=130).pack(side=LEFT, padx=5)
        else:
            Label(card, text="Нет фото", bg=bg, font=FONT, width=12).pack(side=LEFT, padx=5)

        info = Frame(card, bg=bg)
        info.pack(side=LEFT, fill=BOTH, expand=True, padx=10)
        Label(info, text=f'{product["article"]} — {product["name"]}', bg=bg, font=("Times New Roman", 14, "bold")).pack(anchor=W)
        Label(info, text=f'Категория: {product["category"]} | Производитель: {product["manufacturer"]} | Поставщик: {product["supplier"]}', bg=bg, font=FONT).pack(anchor=W)
        Label(info, text=f'Ед. изм.: {product["unit"]} | Остаток: {product["stock_quantity"]} | Скидка: {product["discount"]}%', bg=bg, font=FONT).pack(anchor=W)
        Label(info, text=product["description"], bg=bg, font=FONT, wraplength=700, justify=LEFT).pack(anchor=W)

        price_frame = Frame(info, bg=bg)
        price_frame.pack(anchor=W)
        price = float(product["price"])
        discount = int(product["discount"])
        if discount > 0:
            Label(price_frame, text=f"{price:.2f} руб.", fg="red", bg=bg, font=("Times New Roman", 12, "overstrike")).pack(side=LEFT)
            new_price = price * (100 - discount) / 100
            Label(price_frame, text=f"  {new_price:.2f} руб.", fg="black", bg=bg, font=("Times New Roman", 12, "bold")).pack(side=LEFT)
        else:
            Label(price_frame, text=f"Цена: {price:.2f} руб.", bg=bg, font=FONT).pack(side=LEFT)

        if self.current_role == "Администратор":
            buttons = Frame(card, bg=bg)
            buttons.pack(side=RIGHT, padx=5)
            Button(buttons, text="Редактировать", font=FONT, command=lambda: self.open_product_form(product["article"])).pack(pady=3)
            Button(buttons, text="Удалить", font=FONT, command=lambda: self.delete_product(product["article"])).pack(pady=3)

    def open_product_form(self, article=None):
        if self.edit_window_open:
            messagebox.showwarning("Внимание", "Окно редактирования уже открыто")
            return
        self.edit_window_open = True
        ProductForm(self, article)

    def delete_product(self, article):
        if product_exists_in_orders(article):
            messagebox.showerror("Удаление запрещено", "Товар присутствует в заказе, его нельзя удалить")
            return
        if messagebox.askyesno("Подтверждение", "Удалить выбранный товар?"):
            delete_product(article)
            self.refresh_products()
