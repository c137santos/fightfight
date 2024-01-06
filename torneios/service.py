import math
import random
from sqlalchemy.exc import SQLAlchemyError

from . import db  # from __init__.py
from . import models_pydantic
from .models import Chave, Torneio, Competidor

CHAVEAMENTO = {16: "OITAVAS", 8: "QUARTAS", 4: "SEMI-FINAL", 2: "FINAL"}


class TorneioService:
    @staticmethod
    def criar_torneio(torneio: models_pydantic.Torneio) -> str:
        try:
            obj = Torneio(nome_torneio=torneio.nome_torneio)
            db.session.add(obj)
            db.session.commit()
            return obj.id
        except SQLAlchemyError as exc:
            raise CreateError from exc

    @staticmethod
    def buscar_torneio(filtros):
        return Torneio.query.all()

    @staticmethod
    def atualizar_qtd_competidores(torneio):
        torneio.qtd_competidores = len(torneio.competidores)
        db.session.add(torneio)
        db.session.commit()


class CompetidorService:
    @staticmethod
    def cadastrar_competidor(
        competidor: models_pydantic.CompetidorRequest, id_torneio: int
    ) -> int:
        torneio = Torneio.query.get(id_torneio)

        if not torneio:
            return "TorneioNotFoundError"
        if torneio.is_chaveado:
            return "TorneioClosed"
        try:
            nova_equipe = Competidor(
                nome_competidor=competidor.nome_competidor, torneio_id=id_torneio
            )
            db.session.add(nova_equipe)
            db.session.commit()

        except SQLAlchemyError as exc:
            db.session.rollback()
            raise CreateError from exc

        TorneioService.atualizar_qtd_competidores(torneio)
        return nova_equipe.id

    @staticmethod
    def buscar_competidores(torneio_id):
        return Competidor.query.filter_by(torneio_id=torneio_id)


class ChaveamentoService:
    @staticmethod
    def get_chavemaneto_sorteado(id_torneio):
        return Chave.query.filter_by(torneio_id=id_torneio).all()

    @staticmethod
    def busca_chaveamento(id_torneio: int) -> int:
        torneio = Torneio.query.get(id_torneio)
        if not torneio.is_chaveado:
            (
                numero_primeira_rodada,
                lista_geral_primeira_rodada,
            ) = ChaveamentoService.sorteia_chaveamento_primeira_fase(torneio)
            ChaveamentoService.criar_rodadas_subsequentes(
                numero_primeira_rodada, len(lista_geral_primeira_rodada), torneio
            )
            torneio.is_chaveado = True
            db.session.add(torneio)
            db.session.commit()
        lista_chaveada = ChaveamentoService.get_chavemaneto_sorteado(id_torneio)
        return lista_chaveada

    @staticmethod
    def sorteia_chaveamento_primeira_fase(torneio):
        competidores_torneio = Competidor.query.filter(
            Competidor.torneio_id == torneio.id
        ).all()
        meio = int(len(competidores_torneio) / 2)
        grupo_a = competidores_torneio[:meio]
        grupo_b = competidores_torneio[meio:]
        numero_primeira_rodada = ChaveamentoService.rodada_por_qtd_competidores(
            len(competidores_torneio)
        )
        if len(grupo_a) % 2 != 0:
            grupo_a.append(None)
        if len(grupo_b) % 2 != 0:
            grupo_b.append(None)
        duplas_ga = ChaveamentoService.sortea_duplas_grupo(grupo_a)
        duplas_gb = ChaveamentoService.sortea_duplas_grupo(grupo_b)
        lista_grupo_a = ChaveamentoService.inserir_duplas_primeira_rodada(
            duplas=duplas_ga,
            torneio_id=torneio.id,
            rodada=numero_primeira_rodada,
            grupo="a",
        )
        lista_grupo_b = ChaveamentoService.inserir_duplas_primeira_rodada(
            duplas=duplas_gb,
            torneio_id=torneio.id,
            rodada=numero_primeira_rodada,
            grupo="b",
        )
        lista_geral_primeira_rodada = lista_grupo_a + lista_grupo_b
        return (
            numero_primeira_rodada,
            lista_geral_primeira_rodada,
        )  # 16 disputas, um chaveamento de 8

    @staticmethod
    def rodada_por_qtd_competidores(total_competidores):
        return math.ceil(math.log2(total_competidores))

    @staticmethod
    def sortea_duplas_grupo(grupo):
        duplas = []
        random.shuffle(grupo)
        for i in range(0, len(grupo), 2):
            dupla = [grupo[i], grupo[i + 1]]
            duplas.append(dupla)

        return duplas

    @staticmethod
    def inserir_duplas_primeira_rodada(duplas, torneio_id, rodada, grupo):
        lista_primeira_partida = []
        for dupla in duplas:
            chave_obj = Chave(
                torneio_id=torneio_id,
                rodada=rodada,
                grupo=grupo,
            )
            if dupla[0]:
                chave_obj.competidor_a_id = dupla[0].id
            if dupla[1]:
                chave_obj.competidor_b_id = dupla[1].id
            if dupla[0] is None or dupla[1] is None:
                chave_obj.vencedor = db.session.merge(dupla[0] or dupla[1])
            db.session.add(chave_obj)
            lista_primeira_partida.append(chave_obj)
        db.session.commit()
        return lista_primeira_partida

    @staticmethod
    def criar_rodadas_subsequentes(rodada, total_disputas_primeira_fase, torneio):
        total_ultimas_disputas = total_disputas_primeira_fase
        rodada_atual = rodada - 1  # Rodada subsequente a que foi informada
        lista_chaves_criadas = []
        while rodada_atual > 1:
            vagas = math.ceil(total_ultimas_disputas / 4)
            chaveamento_atual = []
            for _ in range(vagas):
                for grupo in ["a", "b"]:
                    nova_chave = Chave(
                        torneio_id=torneio.id, rodada=rodada_atual, grupo=grupo
                    )
                    db.session.add(nova_chave)
                    chaveamento_atual.append(nova_chave)
            lista_chaves_criadas.append(chaveamento_atual)
            db.session.commit()
            rodada_atual -= 1
            total_ultimas_disputas = vagas * 2

        chave_final = Chave(torneio_id=torneio.id, rodada=rodada_atual, grupo="f")
        lista_chaves_criadas.append(chave_final)

        chave_terceiro = Chave(torneio_id=torneio.id, rodada=0, grupo="f")
        lista_chaves_criadas.append(chave_terceiro)

        db.session.add(chave_final)
        db.session.add(chave_terceiro)
        db.session.commit()

        return lista_chaves_criadas


class ResultadoService:
    @classmethod
    def cadastrar_resultado(
        cls,
        resultado: models_pydantic.ResultadoPartidaRequest,
        id_torneio: int,
        id_partida: int,
    ) -> int:
        chaveamento_obj = Chave.query.get(id_partida)
        if not chaveamento_obj.torneio_id == id_torneio:
            return "ChaveRaise"
        if not chaveamento_obj:
            return "ChaveamentoNotFound"
        if chaveamento_obj.vencedor:
            return "ChaveamentoComResultado"
        if not chaveamento_obj.competidor_a_id or not chaveamento_obj.competidor_b_id:
            return "ChaveamentoNoDisponivel"
        vencedor_id = (
            chaveamento_obj.competidor_a_id
            if resultado.resultado_comp_a > resultado.resultado_comp_b
            else chaveamento_obj.competidor_b_id
        )
        perdedor_id = (
            chaveamento_obj.competidor_a_id
            if resultado.resultado_comp_a < resultado.resultado_comp_b
            else chaveamento_obj.competidor_b_id
        )

        chaveamento_obj.resultado_comp_a = resultado.resultado_comp_a
        chaveamento_obj.resultado_comp_b = resultado.resultado_comp_b
        chaveamento_obj.vencedor_id = vencedor_id
        db.session.commit()
        ResultadoService.classificar_proxima_rodada(
            vencedor_id, perdedor_id, chaveamento_obj, id_torneio
        )
        return chaveamento_obj

    @classmethod
    def classificar_proxima_rodada(
        cls, vencedor_id, perdedor_id, chaveamento_obj, id_torneio
    ):
        torneio = Torneio.query.get(id_torneio)
        proxima_rodada = chaveamento_obj.rodada - 1
        aviso_classificao_terceiro = "."
        if proxima_rodada == 1:
            return ResultadoService.classificao_das_finais(
                chaveamento_obj, vencedor_id, perdedor_id, torneio
            )

        proxima_chave_grupo = "a" if chaveamento_obj.grupo == "a" else "b"
        proxima_chave = Chave.query.filter_by(
            rodada=proxima_rodada, grupo=proxima_chave_grupo
        ).first()
        setattr(proxima_chave, f"competidor_{chaveamento_obj.grupo}_id", vencedor_id)

        db.session.add(proxima_chave)
        db.session.commit()

        return f"Classificado vencedor para próxima chave {proxima_chave}{aviso_classificao_terceiro}"

    @classmethod
    def classificao_das_finais(cls, chaveamento_obj, vencedor_id, perdedor_id, torneio):
        chave_final = Chave.query.filter_by(rodada=1).first()
        disputa_terceiro = Chave.query.filter_by(rodada=0).first()
        if chaveamento_obj.grupo == "a":
            chave_final.competidor_a_id = vencedor_id
            disputa_terceiro.competidor_a_id = perdedor_id
        else:
            chave_final.competidor_b_id = vencedor_id
            disputa_terceiro.competidor_a_id = perdedor_id
        db.session.commit()
        return "Classificação das finais"


class CreateError(RuntimeError):
    ...


class TorneioNotFoundError(Exception):
    ...


class TorneioClosed(Exception):
    ...
