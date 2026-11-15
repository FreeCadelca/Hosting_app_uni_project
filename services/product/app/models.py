from sqlalchemy import Column, Integer, String, DateTime, Numeric, ForeignKey, Table
from sqlalchemy.orm import declarative_base
from datetime import datetime

Base = declarative_base()


class Plan(Base):
    __tablename__ = "plans"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    cpu = Column(Integer, nullable=False)
    ram_mb = Column(Integer, nullable=False)
    disk_gb = Column(Integer, nullable=False)
    price_monthly = Column(Numeric(10, 2), nullable=False)


class Server(Base):
    __tablename__ = "servers"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    plan_id = Column(Integer, ForeignKey("plans.id"))
    hostname = Column(String(255))
    ip_address = Column(String(45))
    root_password = Column(String(255))
    os = Column(String(100), default="Ubuntu 22.04")
    status = Column(String(50), default="pending")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)


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
