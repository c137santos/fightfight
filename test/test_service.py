from collections import defaultdict
from torneios import models_pydantic
from torneios.models import Chave, Torneio, Competidor
from torneios.service import (
    CompetidorService,
    ChaveamentoService,
    ResultadoService,
)
import pytest


def test_new_competidor_atualiza_qtd_competidores_em_Torneio(db_session, app):
    nome_torneio = "Aumenta qtd competidores"

    with app.app_context():
        torneio = Torneio(nome_torneio=nome_torneio)
        db_session.add(torneio)
        db_session.commit()
        assert torneio.qtd_competidores == 0
        competidor = Competidor(nome_competidor="Competidor1", torneio_id=torneio.id)
        CompetidorService.cadastrar_competidor(competidor, torneio.id)
        db_session.commit()
        torneio_modificado = db_session.query(Torneio).get(torneio.id)
        assert torneio_modificado.qtd_competidores == 1


@pytest.mark.parametrize(
    "compt, rodadas_esperadas",
    [(4, 2), (8, 3), (16, 4), (32, 5), (64, 6), (128, 7), (3, 2), (70, 7)],
    "",
)
def test_qtd_rodada_por_duplas(compt, rodadas_esperadas):
    rodadas = ChaveamentoService.rodada_por_qtd_competidores(compt)
    assert rodadas == rodadas_esperadas


def test_cadastrar_resultado_classificacao(db_session, app):
    nome_torneio = "Rankeia"

    with app.app_context():
        torneio = Torneio(nome_torneio=nome_torneio)
        competidor_a = Competidor(nome_competidor="Clara", torneio_id=torneio.id)
        competidor_b = Competidor(nome_competidor="Santos", torneio_id=torneio.id)
        resultado_partida = models_pydantic.ResultadoPartidaRequest(
            resultado_comp_a=2, resultado_comp_b=1
        )
        chavinha = Chave(
            torneio_id=torneio.id,
            rodada=4,
            competidor_a_id=competidor_a.id,
            competidor_b_id=competidor_b.id,
            grupo="a",
        )

        db_session.add(chavinha)
        db_session.commit()
        result = ResultadoService.cadastrar_resultado(
            resultado_partida, torneio.id, chavinha.id
        )
        assert result == "ChaveamentoNoDisponivel"


def criar_sublista_em_pares(lista):
    sublista_em_pares = [lista[i : i + 2] for i in range(0, len(lista), 2)]
    meio = int(len(sublista_em_pares) / 2)
    dupla_ga = sublista_em_pares[:meio]
    dupla_gb = sublista_em_pares[meio:]
    return dupla_ga, dupla_gb


def test_inserir_duplas_primeira_rodada_chave_perfeita(db_session, app):
    nome_torneio = "Rankeia"
    with app.app_context():
        torneio = Torneio(nome_torneio=nome_torneio)
        db_session.add(torneio)
        db_session.commit()
        lista_de_competidores = []
        for nome in "abcdefghijklmnop":
            i = Competidor(nome_competidor=nome, torneio_id=torneio.id)
            lista_de_competidores.append(i)
            db_session.add(i)
        db_session.commit()
        dupla_ga, _ = criar_sublista_em_pares(lista_de_competidores)
        response = ChaveamentoService.inserir_duplas_primeira_rodada(
            dupla_ga, torneio.id, 4, "a"
        )
        assert len(response) == 4
        assert all(isinstance(chave, Chave) for chave in response)
        for chave in response:
            assert chave.torneio_id == torneio.id
            assert chave.rodada == 4
            assert chave.grupo == "a"


def test_criar_primeira_comp_impar(db_session, app):
    nome_torneio = "Rankeia"
    with app.app_context():
        torneio = Torneio(nome_torneio=nome_torneio)
        db_session.add(torneio)
        db_session.commit()
        lista_de_competidores = []
        competidor = Competidor(nome_competidor="nome", torneio_id=torneio.id)
        db_session.add(competidor)
        db_session.commit()
        lista_de_competidores.append(competidor)
        lista_de_competidores.append(None)
        _, duplas_gb = criar_sublista_em_pares(lista_de_competidores)
        response = ChaveamentoService.inserir_duplas_primeira_rodada(
            duplas_gb, torneio.id, 1, "a"
        )
        assert len(response) == 1
        chave = response[0]
        assert isinstance(chave, Chave)
        assert chave.torneio_id == torneio.id
        assert chave.rodada == 1
        assert chave.grupo != "f"
        assert chave.vencedor.id == competidor.id


def criar_torneio_e_competidores(db_session, app):
    nome_torneio = "Rankeia"
    with app.app_context():
        torneio = Torneio(nome_torneio=nome_torneio)
        db_session.add(torneio)
        db_session.commit()

        lista_de_competidores = []
        for nome in "abcdefghijklmnop":
            competidor = Competidor(nome_competidor=nome)
            lista_de_competidores.append(competidor)
            db_session.add(competidor)
        db_session.commit()

    return torneio, lista_de_competidores


def test_criar_rodadas_subsequentes_chave_perfeita(db_session, app):
    with app.app_context():
        torneio = Torneio(nome_torneio="Perola")
        db_session.add(torneio)
        db_session.commit()
        response = ChaveamentoService.criar_rodadas_subsequentes(5, 32, torneio)
        rodada_4 = response[0]  # chaveamento 3 oitavas
        rodada_3 = response[1]  # chaveamento 3 quartas
        rodada_2 = response[2]  # chaveamento 2 semi-final
        rodada_1 = response[3]  # chaveamento 1 final
        rodada_terceiro_lugar = response[4]
        assert len(rodada_4) == 16
        assert len(rodada_3) == 8
        assert len(rodada_2) == 4
        assert rodada_1
        assert rodada_1.grupo == "f"
        assert rodada_terceiro_lugar.grupo == "f"


def test_criar_rodadas_subsequentes_sem_potencia_dois(db_session, app):
    with app.app_context():
        torneio = Torneio(nome_torneio="Perola")
        db_session.add(torneio)
        db_session.commit()
        response = ChaveamentoService.criar_rodadas_subsequentes(5, 20, torneio)
        rodada_4 = response[0]  # chaveamento 3 oitavas
        rodada_3 = response[1]  # chaveamento 3 quartas
        rodada_2 = response[2]  # chaveamento 2 semi-final
        rodada_1 = response[3]  # chaveamento 1 final
        rodada_terceiro_lugar = response[4]
        assert len(rodada_4) == 10
        assert len(rodada_3) == 6
        assert len(rodada_2) == 4
        assert rodada_1
        assert rodada_1.grupo == "f"
        assert rodada_terceiro_lugar.grupo == "f"


def test_busca_chaveamento_dispara_chaveamento(db_session, app):
    with app.app_context():
        torneio = Torneio(nome_torneio="Perola")
        db_session.add(torneio)
        db_session.commit()
        for nome in "abcdefghijklmnop":
            i = Competidor(nome_competidor=nome, torneio_id=torneio.id)
            db_session.add(i)
        db_session.commit()
        response = ChaveamentoService.busca_chaveamento(torneio.id)
        contagem_por_rodada = defaultdict(int)
        contagem_por_rodada = defaultdict(int)
        for chave in response:
            contagem_por_rodada[chave.rodada] += 1
        grupo = any(chave.grupo == "f" for chave in response)
        assert contagem_por_rodada[4] == 8
        assert contagem_por_rodada[3] == 4
        assert contagem_por_rodada[2] == 2
        assert contagem_por_rodada[1] == 1
        assert contagem_por_rodada[0] == 1
        assert grupo is True


def test_sorteia_chaveamento_primeira_fase(db_session, app):
    with app.app_context():
        torneio = Torneio(nome_torneio="Perola")
        db_session.add(torneio)
        db_session.commit()
        for nome in "abcdefghijklmnop":
            i = Competidor(nome_competidor=nome, torneio_id=torneio.id)
            db_session.add(i)
        db_session.commit()
        (
            numero_primeira_rodada,
            lista_geral_primeira_rodada,
        ) = ChaveamentoService.sorteia_chaveamento_primeira_fase(torneio)
        assert len(lista_geral_primeira_rodada) == 8
        assert all(isinstance(chave, Chave) for chave in lista_geral_primeira_rodada)
        lista_a = []
        lista_b = []
        for chave in lista_geral_primeira_rodada:
            assert chave.torneio_id == torneio.id
            assert chave.rodada == numero_primeira_rodada
            lista_a.append(chave) if chave.grupo == "a" else lista_b.append(chave)
        assert len(lista_a) == 4
        assert len(lista_b) == 4


def test_cadastrar_resultado(db_session, app):
    with app.app_context():
        torneio = Torneio(nome_torneio="Perola")
        db_session.add(torneio)
        db_session.commit()
        competidor_a = Competidor(nome_competidor="Clara", torneio_id=torneio.id)
        competidor_b = Competidor(nome_competidor="Santos", torneio_id=torneio.id)
        db_session.add(competidor_a)
        db_session.add(competidor_b)
        db_session.commit()
        partida = Chave(torneio.id, 4, "a", competidor_a.id, competidor_b.id)
        proxima_chave = Chave(torneio.id, 3, "a")
        db_session.add(partida)
        db_session.add(proxima_chave)
        db_session.commit()
        resultado_partida = models_pydantic.ResultadoPartidaRequest(
            resultado_comp_a=2, resultado_comp_b=1
        )
        partida_atualizada = ResultadoService.cadastrar_resultado(
            resultado_partida, torneio.id, partida.id
        )
        assert partida_atualizada.id == partida.id
        assert partida_atualizada.resultado_comp_a == resultado_partida.resultado_comp_a
        assert partida_atualizada.resultado_comp_b == resultado_partida.resultado_comp_b
        assert partida_atualizada.vencedor.id == competidor_a.id


def test_cadastrar_resultado_sem_comp(db_session, app):
    with app.app_context():
        torneio = Torneio(nome_torneio="Perola")
        db_session.add(torneio)
        db_session.commit()
        competidor_a = Competidor(nome_competidor="Clara", torneio_id=torneio.id)
        db_session.add(competidor_a)
        db_session.commit()
        partida = Chave(torneio.id, 4, "a", competidor_a.id)
        db_session.add(partida)
        db_session.commit()
        resultado_partida = models_pydantic.ResultadoPartidaRequest(
            resultado_comp_a=2, resultado_comp_b=1
        )
        partida_atualizada = ResultadoService.cadastrar_resultado(
            resultado_partida, torneio.id, partida.id
        )
        assert partida_atualizada == "ChaveamentoNoDisponivel"


def test_classificacao_das_finais(db_session, app):
    nome_torneio = "Rankeia"
    with app.app_context():
        torneio = Torneio(nome_torneio=nome_torneio)
        db_session.add(torneio)
        db_session.commit()

        competidor_a = Competidor(nome_competidor="Clara", torneio_id=torneio.id)
        competidor_b = Competidor(nome_competidor="Santos", torneio_id=torneio.id)
        db_session.add(competidor_a)
        chaveFinal = Chave(
            torneio_id=torneio.id,
            rodada=1,
            grupo="f",
        )
        chaveTerceira = Chave(
            torneio_id=torneio.id,
            rodada=0,
            grupo="f",
        )
        db_session.add(chaveFinal)
        db_session.add(chaveTerceira)
        db_session.add(competidor_b)
        db_session.commit()

        chavinha = Chave(
            torneio_id=torneio.id,
            rodada=2,
            competidor_a_id=competidor_a.id,
            competidor_b_id=competidor_b.id,
            grupo="a",
        )
        chavinha.vencedor_id = competidor_a.id
        db_session.add(chavinha)
        db_session.commit()

        vencedor_id = competidor_a.id
        perdedor_id = competidor_b.id

        resultado = ResultadoService.classificao_das_finais(
            chavinha, vencedor_id, perdedor_id, torneio
        )

        assert resultado == "Classificação das finais"


def test_buscar_topquatro_com_classificacao(client, db_session, app):
    nome_torneio = "Rankeia"
    with app.app_context():
        torneio = Torneio(nome_torneio=nome_torneio)
        torneio.is_chaveado = True
        db_session.add(torneio)
        db_session.commit()

        competidor_primeiro_lugar = Competidor(
            nome_competidor="Segundo Lugar", torneio_id=torneio.id
        )
        competidor_segundo_lugar = Competidor(
            nome_competidor="Primeiro Lugar", torneio_id=torneio.id
        )
        competidor_terceiro = Competidor(
            nome_competidor="Terceiro", torneio_id=torneio.id
        )
        competidor_quarto = Competidor(nome_competidor="Quarto", torneio_id=torneio.id)
        db_session.add(competidor_primeiro_lugar)
        db_session.add(competidor_segundo_lugar)
        db_session.add(competidor_terceiro)
        db_session.add(competidor_quarto)
        db_session.commit()

        chaveFinal = Chave(
            torneio_id=torneio.id,
            rodada=1,
            grupo="f",
            competidor_a_id=competidor_primeiro_lugar.id,
            competidor_b_id=competidor_segundo_lugar.id,
        )
        chaveFinal.resultado_comp_a = 1
        chaveFinal.resultado_comp_b = 2
        db_session.add(chaveFinal)
        db_session.commit()
        chaveFinal.vencedor_id = competidor_segundo_lugar.id
        db_session.commit()

        chaveTerceira = Chave(
            torneio_id=torneio.id,
            rodada=0,
            grupo="f",
            competidor_a_id=competidor_terceiro.id,
            competidor_b_id=competidor_quarto.id,
        )
        chaveTerceira.resultado_comp_a = 1
        chaveTerceira.resultado_comp_b = 0
        chaveTerceira.vencedor_id = competidor_terceiro.id
        db_session.add(chaveTerceira)
        db_session.commit()
        dict_classificacao = ResultadoService.buscar_resultado_top(torneio.id)
        assert "Terceiro" in dict_classificacao
        assert competidor_terceiro.id == dict_classificacao["Terceiro"].id
        assert "Quarto" in dict_classificacao
        assert competidor_quarto.id == dict_classificacao["Quarto"].id
        assert "Primeiro" in dict_classificacao
        assert dict_classificacao["Primeiro"].id == competidor_segundo_lugar.id
        assert "Segundo" in dict_classificacao
        assert dict_classificacao["Segundo"].id == competidor_primeiro_lugar.id
