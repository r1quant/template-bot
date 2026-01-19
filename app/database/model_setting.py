from sqlalchemy import select
from sqlmodel import Field, Session, SQLModel

from app.database.database import engine

# ---------------------------------------------------------
# Model
# ---------------------------------------------------------


class Setting(SQLModel, table=True):
    __tablename__ = "settings"
    key: str = Field(primary_key=True, unique=True, nullable=False)
    value: str = Field(nullable=False)


# ---------------------------------------------------------
# Methods
# ---------------------------------------------------------


class settings_methods:
    def all():
        with Session(engine) as session:
            stmt = select(Setting)
            rows = session.scalars(stmt).all()
            if rows:
                result_dict = {row.key: row.value for row in rows}
                return result_dict

            return {}

    def get(key):
        with Session(engine) as session:
            stmt = select(Setting).where(Setting.key == key)
            row = session.scalars(stmt).first()
            if row:
                return row.value
            return None

    def set(key, value):
        with Session(engine) as session:
            stmt = select(Setting).where(Setting.key == key)
            setting = session.scalars(stmt).first()
            if setting:
                setting.value = value  # update
            else:
                setting = Setting(key=key, value=value)  # create
            session.add(setting)
            session.commit()
            session.refresh(setting)

    def delete(key):
        with Session(engine) as session:
            stmt = select(Setting).where(Setting.key == key)
            setting = session.scalars(stmt).first()
            if setting:
                session.delete(setting)
                session.commit()
            return True
