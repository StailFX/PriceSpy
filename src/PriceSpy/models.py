from sqlalchemy import Table, Column, Integer, String, Float, Date, ForeignKey, MetaData

metadata = MetaData()

products = Table(
    "products", metadata,
    Column("id", Integer, primary_key=True),
    Column("name", String, nullable=False, unique=True),
    Column("sku", String, nullable=True, unique=True),
)

users = Table(
    "users", metadata,
    Column("id", Integer, primary_key=True),
    Column("username", String(50), unique=True, nullable=False),
    Column("hashed_password", String(128), nullable=False),
    Column("role", String(20), nullable=False),
)

competitors = Table(
    "competitors", metadata,
    Column("id", Integer, primary_key=True),
    Column("name", String, nullable=False, unique=True),
)

price_records = Table(
    "price_records", metadata,
    Column("id", Integer, primary_key=True),
    Column("product_id", Integer, ForeignKey("products.id"), nullable=False),
    Column("competitor_id", Integer, ForeignKey("competitors.id"), nullable=False),
    Column("price", Float, nullable=False),
    Column("url", String, nullable=False),      # ← новый столбец для ссылки
    Column("date", Date, nullable=False),
)