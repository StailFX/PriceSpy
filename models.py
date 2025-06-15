from sqlalchemy import Table, Column, Integer, String, Float, Date, ForeignKey
from database import metadata

products = Table(
    "products",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("name", String(255)),
    Column("sku", String(50), unique=True)
)

competitors = Table(
    "competitors",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("name", String(255)),
    Column("base_url", String(255))
)

price_records = Table(
    "price_records",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("product_id", Integer, ForeignKey("products.id")),
    Column("competitor_id", Integer, ForeignKey("competitors.id")),
    Column("price", Float),
    Column("date", Date)
)