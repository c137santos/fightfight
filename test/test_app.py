from torneios.models import Torneio


def test_view_torneio_simples(client):
    response = client.get("/tournament")
    assert response.status_code == 200


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


def test_cadastrar_competidor_torneio_not_found(client):
    response = client.post(
        "/tournament/60/competidor", json={"nome_competidor": "Competidor 1"}
    )
    assert response.status_code == 500
    assert response.json["message"] == "Torneio não encontrado"


# TODO: organizar erros da forma que o flask merece https://flask.palletsprojects.com/en/2.3.x/errorhandling/
