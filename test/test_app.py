from torneios.models import Torneio
from unittest.mock import patch

from torneios.service import PendingClassification, ResultadoService


def test_view_torneio_simples(client):
    response = client.get("/tournament")
    assert response.status_code == 404


def test_view_torneio_return_201(client, db_session):
    payload = {"nome_torneio": "Primeiro torneio"}
    response = client.post("/tournament", json=payload)
    assert response.status_code == 201
    assert response.json["id"] is not None


def test_view_criar_return_201(client, db_session):
    torneio = Torneio(nome_torneio="Primeiro torneio")
    db_session.add(torneio)
    db_session.commit()
    payload = {"nome_competidor": "Competidor um!!!"}
    response = client.post(f"/tournament/{torneio.id}/competidor", json=payload)
    assert response.status_code == 201


def test_cadastrar_competidor_torneio_not_found(client, db_session, app):
    with app.app_context():
        response = client.post(
            "/tournament/60/competidor", json={"nome_competidor": "Competidor 1"}
        )
        assert response.status_code == 404
        assert response.json["message"] == "Torneio não encontrado"


def test_buscar_topquatro_torneio_not_closed(client, db_session, app):
    with app.app_context():
        torneio = Torneio(nome_torneio="Primeiro torneio")
        torneio.is_chaveado = True
        db_session.add(torneio)
        db_session.commit()
        response = client.get(f"/tournament/{torneio.id}/result")
        assert response.status_code == 401
        assert (
            response.json["message"]
            == "Classificação não está disponível, pois não houve chaveamento"
        )


def test_buscar_topquatro_torneio_pending_classification(client, db_session, app):
    with app.app_context():
        torneio = Torneio(nome_torneio="Primeiro torneio")
        torneio.is_chaveado = True
        db_session.add(torneio)
        db_session.commit()
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


def test_listar_torneios_torneio_not_found(client, db_session, app):
    with app.app_context():
        response = client.get("/tournament", json={"id": 1})
        assert response.status_code == 404
        assert response.json["message"] == "Torneio não encontrado"
