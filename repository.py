from database import connect_db, create_schema, get_or_create
from import_data import import_from_excel


def init_database():
    con = connect_db()
    create_schema(con)
    import_from_excel(con)
    con.close()


def authorize_user(login, password):
    con = connect_db()
    row = con.execute(
        """
        SELECT u.*, r.name AS role_name FROM users u
        JOIN roles r ON r.id = u.role_id
        WHERE u.login=? AND u.password=?
        """,
        (login, password),
    ).fetchone()
    con.close()
    return row


def fetch_products(search="", supplier="Все поставщики", sort_mode="Без сортировки"):
    con = connect_db()
    query = """
        SELECT p.*, c.name AS category, m.name AS manufacturer, s.name AS supplier
        FROM products p
        JOIN categories c ON c.id = p.category_id
        JOIN manufacturers m ON m.id = p.manufacturer_id
        JOIN suppliers s ON s.id = p.supplier_id
    """
    conditions = []
    params = []
    if supplier and supplier != "Все поставщики":
        conditions.append("s.name = ?")
        params.append(supplier)
    if search:
        like = f"%{search.lower()}%"
        fields = ["LOWER(p.article)", "LOWER(p.name)", "LOWER(p.unit)", "LOWER(p.description)",
                  "LOWER(c.name)", "LOWER(m.name)", "LOWER(s.name)"]
        conditions.append("(" + " OR ".join([f"{f} LIKE ?" for f in fields]) + ")")
        params.extend([like] * len(fields))
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    if sort_mode == "Остаток по возрастанию":
        query += " ORDER BY p.stock_quantity ASC"
    elif sort_mode == "Остаток по убыванию":
        query += " ORDER BY p.stock_quantity DESC"
    else:
        query += " ORDER BY p.article"
    rows = con.execute(query, params).fetchall()
    con.close()
    return rows


def fetch_names(table):
    con = connect_db()
    rows = [r["name"] for r in con.execute(f"SELECT name FROM {table} ORDER BY name").fetchall()]
    con.close()
    return rows


def fetch_product(article):
    con = connect_db()
    row = con.execute(
        """
        SELECT p.*, c.name AS category, m.name AS manufacturer, s.name AS supplier
        FROM products p
        JOIN categories c ON c.id = p.category_id
        JOIN manufacturers m ON m.id = p.manufacturer_id
        JOIN suppliers s ON s.id = p.supplier_id
        WHERE p.article=?
        """,
        (article,),
    ).fetchone()
    con.close()
    return row


def product_exists_in_orders(article):
    con = connect_db()
    row = con.execute("SELECT 1 FROM order_items WHERE product_article=? LIMIT 1", (article,)).fetchone()
    con.close()
    return row is not None


def delete_product(article):
    con = connect_db()
    con.execute("DELETE FROM products WHERE article=?", (article,))
    con.commit()
    con.close()


def save_product(data, image_path, old_article=None):
    con = connect_db()
    supplier_id = get_or_create(con, "suppliers", data["supplier"])
    manufacturer_id = get_or_create(con, "manufacturers", data["manufacturer"])
    category_id = get_or_create(con, "categories", data["category"])
    if old_article:
        con.execute(
            """
            UPDATE products SET name=?, unit=?, price=?, supplier_id=?, manufacturer_id=?, category_id=?,
            discount=?, stock_quantity=?, description=?, image_path=? WHERE article=?
            """,
            (data["name"], data["unit"], data["price"], supplier_id, manufacturer_id, category_id,
             data["discount"], data["stock_quantity"], data["description"], image_path, old_article),
        )
    else:
        con.execute(
            """
            INSERT INTO products(article, name, unit, price, supplier_id, manufacturer_id, category_id,
            discount, stock_quantity, description, image_path) VALUES(?,?,?,?,?,?,?,?,?,?,?)
            """,
            (data["article"], data["name"], data["unit"], data["price"], supplier_id, manufacturer_id,
             category_id, data["discount"], data["stock_quantity"], data["description"], image_path),
        )
    con.commit()
    con.close()
