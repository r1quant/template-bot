from sqlmodel import Session, SQLModel, create_engine

from app.core.settings import settings

# ---------------------------------------------------------
# Connection
# ---------------------------------------------------------

connect_args = {"check_same_thread": False}
engine = create_engine(settings.database_path, connect_args=connect_args)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session
