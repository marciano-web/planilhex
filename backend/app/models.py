from sqlalchemy import String, Integer, DateTime, ForeignKey, LargeBinary, Text, Boolean, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from .db import Base

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(50), default="operator")  # admin|operator
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class Template(Base):
    __tablename__ = "templates"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    original_filename: Mapped[str] = mapped_column(String(255))
    mime_type: Mapped[str] = mapped_column(String(120))
    file_bytes: Mapped[bytes] = mapped_column(LargeBinary)
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    mapped_cells: Mapped[list["TemplateCell"]] = relationship(back_populates="template", cascade="all, delete-orphan")

class TemplateCell(Base):
    __tablename__ = "template_cells"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    template_id: Mapped[int] = mapped_column(ForeignKey("templates.id"), index=True)
    sheet_name: Mapped[str] = mapped_column(String(255), default="Sheet1")
    cell_ref: Mapped[str] = mapped_column(String(20))  # e.g. A1
    label: Mapped[str] = mapped_column(String(255), default="")
    data_type: Mapped[str] = mapped_column(String(50), default="text")  # text|number|date
    template: Mapped["Template"] = relationship(back_populates="mapped_cells")

    __table_args__ = (UniqueConstraint("template_id", "sheet_name", "cell_ref", name="uq_template_cell"),)

class Instance(Base):
    __tablename__ = "instances"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    template_id: Mapped[int] = mapped_column(ForeignKey("templates.id"), index=True)
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    title: Mapped[str] = mapped_column(String(255), default="")

class InstanceValue(Base):
    __tablename__ = "instance_values"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    instance_id: Mapped[int] = mapped_column(ForeignKey("instances.id"), index=True)
    sheet_name: Mapped[str] = mapped_column(String(255))
    cell_ref: Mapped[str] = mapped_column(String(20))
    value: Mapped[str] = mapped_column(Text)

    __table_args__ = (UniqueConstraint("instance_id", "sheet_name", "cell_ref", name="uq_instance_value"),)

class AuditEvent(Base):
    __tablename__ = "audit_events"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    instance_id: Mapped[int] = mapped_column(ForeignKey("instances.id"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    event_type: Mapped[str] = mapped_column(String(50))  # edit|save|export|login
    sheet_name: Mapped[str] = mapped_column(String(255), default="")
    cell_ref: Mapped[str] = mapped_column(String(20), default="")
    old_value: Mapped[str] = mapped_column(Text, default="")
    new_value: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    meta_json: Mapped[str] = mapped_column(Text, default="{}")
