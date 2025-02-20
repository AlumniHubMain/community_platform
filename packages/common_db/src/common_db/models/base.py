from datetime import datetime

from sqlalchemy import text
from sqlalchemy.orm import DeclarativeBase, mapped_column, Mapped

from common_db.config import schema


class Base(DeclarativeBase):
    """
    The basic model of the table. Here we prescribe the properties common to all tables.
    """

    __abstract__ = True
    __table_args__ = {
        "schema": f"{schema}",
        "extend_existing": True
    }


class ObjectTable(Base):
    """
    A table model (template) for objects.
    """

    __abstract__ = True
    __allow_unmapped__ = True

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    created_at: Mapped[datetime] = mapped_column(
        server_default=text("TIMEZONE('utc', now())")
    )
    updated_at: Mapped[datetime] = mapped_column(
        server_default=text("TIMEZONE('utc', now())"),
        onupdate=text("TIMEZONE('utc', now())"),
    )


class PropertyTable(ObjectTable):
    """
    A table model (template) for the properties (characteristics) of objects.
    """
    __abstract__ = True

    label: Mapped[str]
    description: Mapped[str | None]
    is_custom: Mapped[bool] = mapped_column(default=False)
