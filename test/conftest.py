import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from torneios import db, create_app


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:////tmp/matamata.db")
    Session = sessionmaker(bind=engine)
    db.metadata.create_all(engine)
    session = Session()
    yield session
    session.close()
    db.metadata.drop_all(engine)


@pytest.fixture(scope="module")
def app():
    """Instância o flask app para test"""
    app = create_app("testing")
    yield app


@pytest.fixture()
def client(app):
    return app.test_client()
