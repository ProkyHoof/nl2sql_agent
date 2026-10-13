import sqlite3

connection = sqlite3.connect("shop.db")
cursor = connection.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    category TEXT,
    price REAL,
    stock INTEGER
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY,
    product_id INTEGER,
    quantity INTEGER,
    order_date TEXT,
    FOREIGN KEY (product_id) REFERENCES products(id)
)
""")

cursor.executemany("INSERT OR IGNORE INTO products VALUES (?,?,?,?,?)", [
    (1, "iPhone 15", "电子产品", 5999.0, 100),
    (2, "MacBook Pro", "电子产品", 12999.0, 50),
    (3, "Python编程书", "图书", 89.0, 200),
    (4, "机械键盘", "配件", 399.0, 80),
])

cursor.executemany("INSERT OR IGNORE INTO orders VALUES (?,?,?,?)", [
    (1, 1, 2, "2025-01-15"),
    (2, 2, 1, "2025-01-20"),
    (3, 3, 5, "2025-02-01"),
    (4, 4, 3, "2025-02-10"),
])

connection.commit()
connection.close()
print("创建数据库: shop.db")