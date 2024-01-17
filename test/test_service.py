from collections import defaultdict
from torneios import models_pydantic, db
from torneios.models import Chave, Torneio, Competidor
from torneios.service import (
    ChaveamentoNotAvailableError,
    CompetidorService,
    ChaveamentoService,
    ResultadoService,
    TorneioNotClosedError,
    TorneioService,
)
import pytest


def test_new_competidor_atualiza_qtd_competidores_em_Torneio(app):
    nome_torneio = "Aumenta qtd competidores"

    with app.app_context():
        torneio = Torneio(nome_torneio=nome_torneio)
        db.session.add(torneio)
        db.session.commit()
        assert torneio.qtd_competidores == 0
        competidor = Competidor(nome_competidor="Competidor1", torneio_id=torneio.id)
        CompetidorService.cadastrar_competidor(competidor, torneio.id)
        db.session.commit()
        torneio_modificado = db.session.query(Torneio).get(torneio.id)
        assert torneio_modificado.qtd_competidores == 1


@pytest.mark.parametrize(
    "compt, rodadas_esperadas",
    [(4, 2), (8, 3), (16, 4), (32, 5), (64, 6), (128, 7), (3, 2), (70, 7)],
    "",
)
def test_qtd_rodada_por_duplas(compt, rodadas_esperadas):
    rodadas = ChaveamentoService.rodada_por_qtd_competidores(compt)
    assert rodadas == rodadas_esperadas


def test_cadastrar_resultado_classificacao(app):
    nome_torneio = "Rankeia"

    with app.app_context():
        torneio = Torneio(nome_torneio=nome_torneio)
        competidor_a = Competidor(nome_competidor="Clara", torneio_id=torneio.id)
        competidor_b = Competidor(nome_competidor="Santos", torneio_id=torneio.id)
        resultado_partida = models_pydantic.ResultadoPartidaRequest(
            resultado_comp_a=2, resultado_comp_b=1
        )
        db.session.add(competidor_a)
        db.session.add(competidor_b)
        db.session.add(torneio)
        db.session.commit()
        chavinha = Chave(
            torneio_id=torneio.id,
            rodada=4,
            competidor_a_id=competidor_a.id,
            competidor_b_id=competidor_b.id,
            grupo="a",
        )
        proxima_chave = Chave(torneio_id=torneio.id, rodada=3, grupo="a")

        db.session.add(chavinha)
        db.session.add(proxima_chave)
        db.session.commit()
        response = ResultadoService.cadastrar_resultado(
            resultado_partida, torneio.id, chavinha.id
        )
        assert isinstance(response, Chave)
        assert response.torneio_id == torneio.id
        assert response.rodada == 4
        assert response.grupo != "f"
        assert response.grupo == "a"
        assert response.vencedor.id == competidor_a.id


def criar_sublista_em_pares(lista):
    sublista_em_pares = [lista[i : i + 2] for i in range(0, len(lista), 2)]
    meio = int(len(sublista_em_pares) / 2)
    dupla_ga = sublista_em_pares[:meio]
    dupla_gb = sublista_em_pares[meio:]
    return dupla_ga, dupla_gb


def test_inserir_duplas_primeira_rodada_chave_perfeita(app):
    nome_torneio = "Rankeia"
    with app.app_context():
        torneio = Torneio(nome_torneio=nome_torneio)
        db.session.add(torneio)
        db.session.commit()
        lista_de_competidores = []
        for nome in "abcdefghijklmnop":
            i = Competidor(nome_competidor=nome, torneio_id=torneio.id)
            lista_de_competidores.append(i)
            db.session.add(i)
        db.session.commit()
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


def test_criar_primeira_comp_impar(app):
    nome_torneio = "Rankeia"
    with app.app_context():
        torneio = Torneio(nome_torneio=nome_torneio)
        db.session.add(torneio)
        db.session.commit()
        lista_de_competidores = []
        competidor = Competidor(nome_competidor="nome", torneio_id=torneio.id)
        db.session.add(competidor)
        db.session.commit()
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


def criar_torneio_e_competidores(app):
    nome_torneio = "Rankeia"
    with app.app_context():
        torneio = Torneio(nome_torneio=nome_torneio)
        db.session.add(torneio)
        db.session.commit()

        lista_de_competidores = []
        for nome in "abcdefghijklmnop":
            competidor = Competidor(nome_competidor=nome)
            lista_de_competidores.append(competidor)
            db.session.add(competidor)
        db.session.commit()

    return torneio, lista_de_competidores


def test_criar_rodadas_subsequentes_chave_perfeita(app):
    with app.app_context():
        torneio = Torneio(nome_torneio="Perola")
        db.session.add(torneio)
        db.session.commit()
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


def test_criar_rodadas_subsequentes_sem_potencia_dois(app):
    with app.app_context():
        torneio = Torneio(nome_torneio="Perola")
        db.session.add(torneio)
        db.session.commit()
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


def test_busca_chaveamento_dispara_chaveamento(app):
    with app.app_context():
        torneio = Torneio(nome_torneio="Perola")
        db.session.add(torneio)
        db.session.commit()
        for nome in "abcdefghijklmnop":
            i = Competidor(nome_competidor=nome, torneio_id=torneio.id)
            db.session.add(i)
        db.session.commit()
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


def test_sorteia_chaveamento_primeira_fase(app):
    with app.app_context():
        torneio = Torneio(nome_torneio="Perola")
        db.session.add(torneio)
        db.session.commit()
        for nome in "abcdefghijklmnop":
            i = Competidor(nome_competidor=nome, torneio_id=torneio.id)
            db.session.add(i)
        db.session.commit()
        (
            numero_primeira_rodada,
            lista_geral_primeira_rodada,
            _,
            _,
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


def test_cadastrar_resultado(app):
    with app.app_context():
        torneio = Torneio(nome_torneio="Perola")
        db.session.add(torneio)
        db.session.commit()
        competidor_a = Competidor(nome_competidor="Clara", torneio_id=torneio.id)
        competidor_b = Competidor(nome_competidor="Santos", torneio_id=torneio.id)
        db.session.add(competidor_a)
        db.session.add(competidor_b)
        db.session.commit()
        partida = Chave(torneio.id, 4, "a", competidor_a.id, competidor_b.id)
        proxima_chave = Chave(torneio.id, 3, "a")
        db.session.add(partida)
        db.session.add(proxima_chave)
        db.session.commit()
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


def test_tentativa_cadastrar_resultado_sem_comp(app):
    with app.app_context():
        torneio = Torneio(nome_torneio="Perola")
        db.session.add(torneio)
        db.session.commit()
        competidor_a = Competidor(nome_competidor="Clara", torneio_id=torneio.id)
        db.session.add(competidor_a)
        db.session.commit()
        partida = Chave(torneio.id, 4, "a", competidor_a.id)
        db.session.add(partida)
        db.session.commit()
        resultado_partida = models_pydantic.ResultadoPartidaRequest(
            resultado_comp_a=2, resultado_comp_b=1
        )
        with pytest.raises(ChaveamentoNotAvailableError):
            ResultadoService.cadastrar_resultado(
                resultado_partida, torneio.id, partida.id
            )


def test_classificacao_das_finais(app):
    nome_torneio = "Rankeia"
    with app.app_context():
        torneio = Torneio(nome_torneio=nome_torneio)
        db.session.add(torneio)
        db.session.commit()

        competidor_a = Competidor(nome_competidor="Clara", torneio_id=torneio.id)
        competidor_b = Competidor(nome_competidor="Santos", torneio_id=torneio.id)
        db.session.add(competidor_a)
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
        db.session.add(chaveFinal)
        db.session.add(chaveTerceira)
        db.session.add(competidor_b)
        db.session.commit()

        chavinha = Chave(
            torneio_id=torneio.id,
            rodada=2,
            competidor_a_id=competidor_a.id,
            competidor_b_id=competidor_b.id,
            grupo="a",
        )
        chavinha.vencedor_id = competidor_a.id
        db.session.add(chavinha)
        db.session.commit()

        vencedor_id = competidor_a.id
        perdedor_id = competidor_b.id

        resultado = ResultadoService.classificao_das_finais(
            chavinha, vencedor_id, perdedor_id, torneio
        )

        assert resultado == "Classificação das finais"


def test_buscar_topquatro_com_classificacao(client, app):
    nome_torneio = "Rankeia"
    with app.app_context():
        torneio = Torneio(nome_torneio=nome_torneio)
        torneio.is_chaveado = True
        db.session.add(torneio)
        db.session.commit()

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
        db.session.add(competidor_primeiro_lugar)
        db.session.add(competidor_segundo_lugar)
        db.session.add(competidor_terceiro)
        db.session.add(competidor_quarto)
        db.session.commit()

        chaveFinal = Chave(
            torneio_id=torneio.id,
            rodada=1,
            grupo="f",
            competidor_a_id=competidor_primeiro_lugar.id,
            competidor_b_id=competidor_segundo_lugar.id,
        )
        chaveFinal.resultado_comp_a = 1
        chaveFinal.resultado_comp_b = 2
        db.session.add(chaveFinal)
        db.session.commit()
        chaveFinal.vencedor_id = competidor_segundo_lugar.id
        db.session.commit()

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
        db.session.add(chaveTerceira)
        db.session.commit()
        dict_classificacao = ResultadoService.buscar_resultado_top(torneio.id)
        assert "Terceiro" in dict_classificacao
        assert competidor_terceiro.id == dict_classificacao["Terceiro"].id
        assert "Quarto" in dict_classificacao
        assert competidor_quarto.id == dict_classificacao["Quarto"].id
        assert "Primeiro" in dict_classificacao
        assert dict_classificacao["Primeiro"].id == competidor_segundo_lugar.id
        assert "Segundo" in dict_classificacao
        assert dict_classificacao["Segundo"].id == competidor_primeiro_lugar.id


def test_buscar_torneio_por_id(app):
    with app.app_context():
        torneio = Torneio(nome_torneio="Exemplo")
        db.session.add(torneio)
        db.session.commit()
        filtros = models_pydantic.FiltroTorneio(id=torneio.id)
        result = TorneioService.buscar_torneio(filtros)
        assert torneio.id == result[0].id


def test_buscar_torneio_por_nome_torneio(app):
    with app.app_context():
        torneio = Torneio(nome_torneio="Exemplo")
        torneio_com_outro_nome = Torneio(nome_torneio="Outro nome")
        torneio_nome_tres = Torneio(nome_torneio="Nomee outro")
        db.session.add(torneio)
        db.session.add(torneio_com_outro_nome)
        db.session.add(torneio_nome_tres)
        db.session.commit()
        filtros = models_pydantic.FiltroTorneio(nome_torneio="Exemplo")
        result = TorneioService.buscar_torneio(filtros)
        assert torneio.id == result[0].id


def test_buscar_torneio_sem_filtros(app):
    with app.app_context():
        torneio1 = Torneio(nome_torneio="Exemplo1")
        torneio2 = Torneio(nome_torneio="Exemplo2")
        db.session.add(torneio1)
        db.session.add(torneio2)
        db.session.commit()
        result = TorneioService.buscar_torneio(models_pydantic.FiltroTorneio())
        assert torneio1.id in [t.id for t in result]
        assert torneio2.id in [t.id for t in result]


def test_filtra_chaves_rodada_torneio_not_closed(app):
    filtro_pydantic = models_pydantic.FiltroChave(torneio_id=1, rodada=2)
    with app.app_context():
        with pytest.raises(TorneioNotClosedError):
            ChaveamentoService.filtra_chaves_rodada(filtro_pydantic)


def test_filtra_chaves_rodada(app):
    with app.app_context():
        torneio = Torneio(nome_torneio="Torneiozao")
        db.session.add(torneio)
        db.session.commit()
        for i in range(8):
            chave = Chave(torneio_id=torneio.id, rodada=4, grupo="a")
            db.session.add(chave)
            db.session.commit()
        for i in range(4):
            chave = Chave(torneio_id=torneio.id, rodada=3, grupo="a")
            db.session.add(chave)
            db.session.commit()
        for i in range(4):
            chave = Chave(torneio_id=555, rodada=4, grupo="a")
            db.session.add(chave)
            db.session.commit()
        filtro_pydantic = models_pydantic.FiltroChave(
            torneio_id=torneio.id, rodada=4, grupo="a"
        )
        resultado = ChaveamentoService.filtra_chaves_rodada(filtro_pydantic)
        assert len(resultado) == 8
        assert all(torneio.id == t.torneio_id for t in resultado)


def test_filtra_chaves_grupo(app):
    with app.app_context():
        torneio = Torneio(nome_torneio="Torneiozao")
        db.session.add(torneio)
        db.session.commit()
        for i in range(8):
            chave = Chave(torneio_id=torneio.id, rodada=4, grupo="a")
            db.session.add(chave)
            db.session.commit()
        for i in range(4):
            chave = Chave(torneio_id=torneio.id, rodada=4, grupo="b")
            db.session.add(chave)
            db.session.commit()
        filtro_pydantic = models_pydantic.FiltroChave(
            torneio_id=torneio.id, rodada=4, grupo="a"
        )
        resultado = ChaveamentoService.filtra_chaves_rodada(filtro_pydantic)
        assert len(resultado) == 8
        assert torneio.id in [t.torneio_id for t in resultado]
        assert all(elemento == "a" for elemento in [t.grupo for t in resultado])


def test_filtra_chaves_torneio(app):
    with app.app_context():
        torneio = Torneio(nome_torneio="Torneiozao")
        db.session.add(torneio)
        db.session.commit()
        for i in range(8):
            chave = Chave(torneio_id=torneio.id, rodada=4, grupo="a")
            db.session.add(chave)
            db.session.commit()
        for i in range(4):
            chave = Chave(torneio_id=torneio.id, rodada=4, grupo="b")
            db.session.add(chave)
            db.session.commit()
        filtro_pydantic = models_pydantic.FiltroChave(torneio_id=torneio.id)
        resultado = ChaveamentoService.filtra_chaves_rodada(filtro_pydantic)
        assert len(resultado) == 12
        assert torneio.id in [t.torneio_id for t in resultado]


@pytest.mark.parametrize(
    "qtd_comp, byes_esperados",
    [
        (
            4,
            0,
        ),  # Caso com o número mínimo de competidores (caso limite). Potencia de 2 não tem byes.
        (8, 0),  # Caso com 8 competidores. Potência de 2 não tem byes.
        (10, 2),  # Caso com 10 competidores, esperando 2 byes para rodadas subsequentes
        (16, 0),  # Caso com 16 compts. Potência de 2 não tem byes.
        (
            20,
            4,
        ),  # Caso com 20 competidores, par, mas não é potência de 2. 2 byes para rodadas subsequentes
        (25, 2),  # Caso com um número ímpar de competidores.
    ],
)
def test_marca_rodadas_bye(qtd_comp, byes_esperados, app):
    with app.app_context():
        torneio = Torneio(nome_torneio="Torneiozao")
        db.session.add(torneio)
        db.session.commit()
        for i in range(qtd_comp):
            comp = Competidor(nome_competidor=i, torneio_id=torneio.id)
            db.session.add(comp)
            db.session.commit()
        n, lista_g, qa, qb = ChaveamentoService.sorteia_chaveamento_primeira_fase(
            torneio
        )
        ChaveamentoService.criar_rodadas_subsequentes(n, len(lista_g), torneio)
        count_bye = ChaveamentoService.marca_rodadas_bye(n, qa, qb, torneio.id)
        assert count_bye == byes_esperados


@pytest.fixture
def torneio_byes(app):
    with app.app_context():
        torneio = Torneio(nome_torneio="Frida")
        db.session.add(torneio)
        db.session.commit()
        for nome in "abcdefghij":  # 10 competidores
            i = Competidor(nome_competidor=nome, torneio_id=torneio.id)
            db.session.add(i)
        db.session.commit()
        (
            n_primeira_rodada,
            lista_geral_primeira_rodada,
            qtd_comps_ga,
            qtd_comps_gb,
        ) = ChaveamentoService.sorteia_chaveamento_primeira_fase(torneio)
        ChaveamentoService.criar_rodadas_subsequentes(
            n_primeira_rodada, len(lista_geral_primeira_rodada), torneio
        )
        ChaveamentoService.marca_rodadas_bye(
            n_primeira_rodada, qtd_comps_ga, qtd_comps_gb, torneio.id
        )
        torneio.is_chaveado = True
        db.session.add(torneio)
        db.session.commit()
        return torneio.id


def test_busca_verificar_passagem_automatica_byebyes(app, torneio_byes):
    with app.app_context():
        torneio_id = torneio_byes
        lista_chaveada_primeira_rodada = (
            ResultadoService.classifica_proxima_rodada_bybye(torneio_id)
        )
        count = 0
        for chave in lista_chaveada_primeira_rodada:
            if chave.bye and (chave.competidor_a or chave.competidor_b):
                assert chave.vencedor_id is not None
                assert chave.rodada in [
                    3,
                    4,
                ]  # verifica que todos bye=True com competidor e vencedor são da 4 e 3
                assert chave.rodada not in [
                    2,
                    1,
                    0,
                ]  # verifica que não há competidor bye escalados para rodadas 2, 1, 0
                count += 1
            if chave.rodada == 3 and (
                chave.competidor_a or chave.competidor_b
            ):  # verifica terceira rodada de byes
                assert (
                    chave.bye is False
                )  # Verifica se comp vindo de um bye não deve ser chavedo para outro bye
                assert chave.vencedor is None  # Não deve ter vencedor atribuido
        if chave.rodada in [2, 1, 0]:
            assert chave.competidor_a is None
            assert chave.competidor_b is None
            assert chave.vencedor is None
        assert count == 2  # só deve existir 2 byes da oitavas a quartas.
        assert len(lista_chaveada_primeira_rodada) == 14


def test_busca_verificar_passagem_automatica_byebyes_segunda_rodada(app, torneio_byes):
    with app.app_context():
        torneio_id = torneio_byes
        lista_chaveada_primeira_rodada = (
            ResultadoService.classifica_proxima_rodada_bybye(torneio_id)
        )
        competidor_qualquer = Competidor(
            nome_competidor="Qualquer", torneio_id=torneio_id
        )
        for chave in lista_chaveada_primeira_rodada:
            if chave.rodada == 3 and chave.bye is True:  # byes de terceira rodada
                chave.competidor_b is None
                chave.competidor_a is None
                chave.competidor_a = competidor_qualquer
                db.session.commit()
        rechamada = ResultadoService.classifica_proxima_rodada_bybye(torneio_id)
        assert len(rechamada) == 14
        for chave in rechamada:
            if chave.rodada == 2 and chave.bye is False:
                assert chave.competidor_a or chave.competidor_b
                assert chave.vencedor is None


def test_busca_nao_ocorre_passagem_automatica_byebyes_chave_perfeita(app):
    with app.app_context():
        torneio = Torneio(nome_torneio="Frida")
        db.session.add(torneio)
        db.session.commit()
        for nome in "abcdefgh":  # 8 competidores
            i = Competidor(nome_competidor=nome, torneio_id=torneio.id)
            db.session.add(i)
        db.session.commit()
        (
            n_primeira_rodada,
            lista_geral_primeira_rodada,
            qtd_comps_ga,
            qtd_comps_gb,
        ) = ChaveamentoService.sorteia_chaveamento_primeira_fase(torneio)
        ChaveamentoService.criar_rodadas_subsequentes(
            n_primeira_rodada, len(lista_geral_primeira_rodada), torneio
        )
        ChaveamentoService.marca_rodadas_bye(
            n_primeira_rodada, qtd_comps_ga, qtd_comps_gb, torneio.id
        )
        torneio.is_chaveado = True
        db.session.add(torneio)
        db.session.commit()
        lista_chaveada = ResultadoService.classifica_proxima_rodada_bybye(torneio.id)
        for chave in lista_chaveada:
            assert chave.bye is False
            assert chave.vencedor is None
        assert len(lista_chaveada) == 8


def test_classificar_proxima_rodada(app):
    nome_torneio = "Rankeia"

    with app.app_context():
        torneio = Torneio(nome_torneio=nome_torneio)
        competidor_a = Competidor(nome_competidor="Clara", torneio_id=torneio.id)
        competidor_b = Competidor(nome_competidor="Santos", torneio_id=torneio.id)
        competidor_a_ja_classificado = Competidor(
            nome_competidor="Santos", torneio_id=torneio.id
        )
        resultado_partida = models_pydantic.ResultadoPartidaRequest(
            resultado_comp_a=2, resultado_comp_b=1
        )
        db.session.add(competidor_a)
        db.session.add(competidor_b)
        db.session.add(competidor_a_ja_classificado)
        db.session.add(torneio)
        db.session.commit()

        chaveamento_obj = Chave(
            torneio_id=torneio.id,
            rodada=4,
            competidor_a_id=competidor_a.id,
            competidor_b_id=competidor_b.id,
            grupo="a",
        )
        chaveamento_obj.resultado_comp_a = resultado_partida.resultado_comp_a
        chaveamento_obj.resultado_comp_b = resultado_partida.resultado_comp_b
        chaveamento_obj.vencedor_id = competidor_a.id
        proxima_chave_com_compts = Chave(
            torneio_id=torneio.id,
            rodada=3,
            grupo="a",
            competidor_a_id=competidor_a_ja_classificado.id,
            competidor_b_id=competidor_b.id,
        )
        proxima_chave_sem_compts = Chave(
            torneio_id=torneio.id,
            rodada=3,
            grupo="a",
            competidor_a_id=competidor_a_ja_classificado.id,
        )

        db.session.add(chaveamento_obj)
        db.session.add(chaveamento_obj)
        db.session.add(proxima_chave_com_compts)
        db.session.add(proxima_chave_sem_compts)
        db.session.commit()
        response = ResultadoService.classificar_proxima_rodada(
            chaveamento_obj.vencedor_id, competidor_b.id, chaveamento_obj, torneio.id
        )
        assert isinstance(response, Chave)
        assert response.torneio_id == torneio.id
        assert response.id == proxima_chave_sem_compts.id
        assert response.rodada == 3
        assert response.grupo == "a"
        assert response.competidor_a_id == competidor_a_ja_classificado.id
        assert response.competidor_b_id == competidor_a.id
