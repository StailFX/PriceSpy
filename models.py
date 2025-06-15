# price_spy-main/models.py

from sqlalchemy import Table, Column, Integer, String, Float, Date, ForeignKey, MetaData

metadata = MetaData()

products = Table(
    "products",
    metadata,
    Column("id",      Integer, primary_key=True),
    Column("name",    String,  nullable=False),
    # оставляем sku в БД, но не требуем при создании
    Column("sku",     String,  nullable=True),
)

competitors = Table(
    "competitors",
    metadata,
    Column("id",   Integer, primary_key=True),
    Column("name", String,  nullable=False, unique=True),
)

price_records = Table(
    "price_records",
    metadata,
    Column("id",            Integer, primary_key=True),
    Column("product_id",    Integer, ForeignKey("products.id"),   nullable=False),
    Column("competitor_id", Integer, ForeignKey("competitors.id"), nullable=False),
    Column("price",         Float,   nullable=False),
    Column("date",          Date,    nullable=False),
)
