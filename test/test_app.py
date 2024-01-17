import os
from torneios.models import Torneio
from unittest.mock import patch
from torneios import db
from torneios.service import PendingClassification, ResultadoService


def test_view_torneio_analisando_isolamento_testes(client):
    response = client.get("/tournament")
    assert response.status_code == 200
    assert len(response.json["torneios"]) == 0


def test_view_torneio_return_201(client):
    payload = {"nome_torneio": "Torneio return 201"}
    response = client.post("/tournament", json=payload)
    assert response.status_code == 201
    assert response.json["id"] is not None


def test_view_criar_return_201(client, app):
    torneio = Torneio(nome_torneio="Torneio criação com return 201")
    db.session.add(torneio)
    db.session.commit()
    payload = {"nome_competidor": "Competidor um!!!"}
    response = client.post(f"/tournament/{torneio.id}/competidor", json=payload)
    assert response.status_code == 201


def test_cadastrar_competidor_torneio_not_found(client, app):
    with app.app_context():
        response = client.post(
            "/tournament/60/competidor", json={"nome_competidor": "Competidor 1"}
        )
        assert response.status_code == 404
        assert response.json["message"] == "Torneio não encontrado"


def test_buscar_topquatro_torneio_not_closed(client, app):
    with app.app_context():
        torneio = Torneio(nome_torneio="Torneio not Closed")
        torneio.is_chaveado = True
        db.session.add(torneio)
        db.session.commit()
        response = client.get(f"/tournament/{torneio.id}/result")
        assert response.status_code == 401
        assert (
            response.json["message"]
            == "Classificação não está disponível, pois não houve chaveamento"
        )


def test_buscar_topquatro_torneio_pending_classification(client, app):
    with app.app_context():
        torneio = Torneio(nome_torneio="Torneio topquatro peding")
        torneio.is_chaveado = True
        db.session.add(torneio)
        db.session.commit()
        with patch.object(
            ResultadoService, "buscar_resultado_top", side_effect=PendingClassification
        ):
            response = client.get(f"/tournament/{torneio.id}/result")
        response = client.get(f"/tournament/{torneio.id}/result")
        assert response.status_code == 401
        assert (
            response.json["message"]
            == "Classificação não está disponível, pois não houve chaveamento"
        )


def test_listar_torneios_torneio_not_found(client, app):
    with app.app_context():
        response = client.get("/tournament?id=1")
        assert response.status_code == 200
        assert response.json == {"torneios": []}


def test_testing_config(app):
    assert app.config["DEBUG"]
    assert app.config["TESTING"]
    assert app.config["SQLALCHEMY_DATABASE_URI"] == os.environ.get("TEST_DATABASE_URL")
