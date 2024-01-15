import pytest
from torneios import db, create_app


# @pytest.fixture(scope="module")
# def app():
#     app = create_app("testing")
#     yield app

# @pytest.fixture(autouse=True)
# def app_context(app):
#     with app.app_context():
#         yield


@pytest.fixture(scope="module")
def app():
    app = create_app("testing")
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()


@pytest.fixture()
def client(app):
    with app.test_client() as client:
        yield client
