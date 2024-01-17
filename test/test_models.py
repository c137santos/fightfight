from torneios.models import Torneio, Competidor
from torneios import db


def test_new_tournament(app):
    torneio = Torneio(nome_torneio="Primeiro torneio")
    db.session.add(torneio)
    db.session.commit()
    torneio_adicionado = Torneio.query.filter_by(
        nome_torneio="Primeiro torneio"
    ).first()
    assert torneio_adicionado is not None
    assert torneio_adicionado.nome_torneio == "Primeiro torneio"
    assert torneio_adicionado.qtd_competidores == 0
    assert torneio_adicionado.id == torneio.id
    assert torneio_adicionado.is_chaveado is False


def test_new_competidor(app):
    nome = "Competidor Super"
    torneio = Torneio(nome_torneio="Primeiro torneio")
    db.session.add(torneio)
    db.session.commit()

    competidor = Competidor(nome_competidor=nome, torneio_id=torneio.id)
    competidor.torneio = torneio
    db.session.add(competidor)
    db.session.commit()
    competidor_add = Competidor.query.filter_by(nome_competidor=nome).first()
    assert competidor_add.nome_competidor == nome
    assert competidor_add.id == competidor.id
    assert competidor_add.torneio_id == torneio.id
    assert competidor_add.nome_competidor == nome
