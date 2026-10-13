import sqlite3

# 链接数据库，如果文件不存在，就创建 shop.db
conn = sqlite3.connect("shop.db")
# 通过 cursor 执行 SQL 语句
cursor = conn.cursor()

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

# 查询所有商品
for row in cursor.execute("SELECT * FROM products"):
    print(row)

# 查询价格大于 5000 的商品
for row in cursor.execute("SELECT name, price FROM products WHERE price > 5000"):
    print(row)

# 查询电子产品的分类的商品数量
for row in cursor.execute("SELECT COUNT(*) FROM products WHERE category = '电子产品'"):
    print(row)

# 查询每个分类的平均价格
for row in cursor.execute("SELECT category, AVG(price) FROM products GROUP BY category"):
    print(row)

# 关联查询：每个订单对应的商品名和数量
for row in cursor.execute(
    """
    SELECT p.name, o.quantity, o.order_date
    FROM orders o
    JOIN products p ON o.product_id = p.id
    """
):
    print(row)

conn.commit()
conn.close()
print("Database created: shop.db")