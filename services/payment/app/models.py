from sqlalchemy import Column, Integer, String, DateTime, Numeric, ForeignKey, Table
from sqlalchemy.orm import declarative_base
from datetime import datetime

Base = declarative_base()


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    plan_id = Column(Integer, ForeignKey("plans.id"))
    server_id = Column(Integer, ForeignKey("servers.id"))
    amount = Column(Numeric(10, 2), nullable=False)
    status = Column(String(50), default="pending")
    created_at = Column(DateTime, default=datetime.utcnow)


# Reference-only metadata for foreign keys; these services do not manage these tables.
Table("users", Base.metadata, Column("id", Integer, primary_key=True))
Table("plans", Base.metadata, Column("id", Integer, primary_key=True))
Table("servers", Base.metadata, Column("id", Integer, primary_key=True))
