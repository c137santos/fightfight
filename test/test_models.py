from torneios.models import Torneio, Competidor


def test_new_tournament(db_session):
    torneio = Torneio(nome_torneio="Primeiro torneio")
    db_session.add(torneio)
    db_session.commit()
    torneio_adicionado = (
        db_session.query(Torneio).filter_by(nome_torneio="Primeiro torneio").first()
    )
    assert torneio_adicionado is not None
    assert torneio_adicionado.nome_torneio == "Primeiro torneio"
    assert torneio_adicionado.qtd_competidores == 0
    assert torneio_adicionado.id == torneio.id
    assert torneio_adicionado.is_chaveado is False


def test_new_competidor(db_session):
    nome = "Competidor Super"
    torneio = Torneio(nome_torneio="Primeiro torneio")
    db_session.add(torneio)
    db_session.commit()

    competidor = Competidor(nome_competidor=nome, torneio_id=torneio.id)
    competidor.torneio = torneio
    db_session.add(competidor)
    db_session.commit()
    competidor_add = (
        db_session.query(Competidor).filter_by(nome_competidor=nome).first()
    )

    assert competidor_add.nome_competidor == nome
    assert competidor_add.id == competidor.id
    assert competidor_add.torneio_id == torneio.id
    assert competidor_add.nome_competidor == nome
