from sqlalchemy import Column, Integer, String, DateTime, Numeric, ForeignKey, Table
from sqlalchemy.orm import declarative_base
from datetime import datetime

Base = declarative_base()


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


# Reference-only metadata for foreign keys; these services do not manage these tables.
Table("users", Base.metadata, Column("id", Integer, primary_key=True))
Table("plans", Base.metadata, Column("id", Integer, primary_key=True))
