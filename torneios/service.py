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
        query = Torneio.query
        if filtros.id:
            if query.filter(Torneio.id == filtros.id).count():
                return query.filter(Torneio.id == filtros.id).all()
            else:
                raise TorneioNotFoundError
        if filtros.nome_torneio:
            query = query.filter(
                Torneio.nome_torneio.ilike(f"%{filtros.nome_torneio}%")
            )
        result = query.all()
        if not result:
            return []
        return result

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
            raise TorneioNotFoundError
        if torneio.is_chaveado:
            raise TorneioClosedError
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
        filtro = models_pydantic.FiltroTorneio(id=torneio_id)
        TorneioService.buscar_torneio(filtro)
        competidores = Competidor.query.filter_by(torneio_id=torneio_id)
        if not competidores:
            raise CompetidoresNotFoundError
        return competidores


class ChaveamentoService:
    @staticmethod
    def get_chavemaneto_sorteado(id_torneio):  # se é get, pega só um
        return Chave.query.filter_by(torneio_id=id_torneio).all()

    @staticmethod
    def busca_chaveamento(id_torneio: int) -> int:
        torneio = Torneio.query.get(id_torneio)
        if torneio is None:
            raise TorneioNotFoundError
        if not torneio.is_chaveado:
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
        ResultadoService.classifica_proxima_rodada_bybye(torneio.id)
        lista_chaveamentos_torneio = ChaveamentoService.get_chavemaneto_sorteado(
            id_torneio
        )
        return lista_chaveamentos_torneio

    @staticmethod
    def marca_rodadas_bye(n_primeira_rodada, qtd_comps_ga, qtd_comps_gb, torneio_id):
        count = 0
        rodada_atual = n_primeira_rodada - 1
        while rodada_atual > 1:
            qtd_comps_ga = math.ceil(qtd_comps_ga / 2)
            qtd_comps_gb = math.ceil(qtd_comps_gb / 2)
            if qtd_comps_ga % 2 != 0:
                ChaveamentoService.sorteia_rodada_como_bye(
                    torneio_id, rodada_atual, "a"
                )
                count += 1
            if qtd_comps_gb % 2 != 0:
                ChaveamentoService.sorteia_rodada_como_bye(
                    torneio_id, rodada_atual, "b"
                )
                count += 1
            rodada_atual -= 1

        return count

    @staticmethod
    def sorteia_rodada_como_bye(torneio_id, n_rodada, grupo):
        filtros = models_pydantic.FiltroChave(
            torneio_id=torneio_id, rodada=n_rodada, grupo=grupo
        )
        rodadas = ChaveamentoService.filtra_chaves_rodada(filtros)
        random.shuffle(rodadas)
        rodada_bye = rodadas[0]
        rodada_bye.bye = True
        db.session.commit()

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
        qtd_comps_ga = len(grupo_a)
        qtd_comps_gb = len(grupo_b)
        if qtd_comps_ga % 2 != 0:
            grupo_a.append(None)
        if qtd_comps_gb % 2 != 0:
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
            qtd_comps_ga,
            qtd_comps_gb,
        )

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
                chave_obj.bye = True
            db.session.add(chave_obj)
            lista_primeira_partida.append(chave_obj)
        db.session.commit()
        return lista_primeira_partida

    @staticmethod
    def criar_rodadas_subsequentes(rodada, total_disputas_primeira_fase, torneio):
        total_disputas_ultimas_rodada = total_disputas_primeira_fase
        rodada_atual = rodada - 1
        lista_chaves_criadas = []
        while rodada_atual > 1:
            duplas_por_grupo = total_disputas_ultimas_rodada / 4
            vagas_duplas_por_grupo = math.ceil(duplas_por_grupo)
            chaveamento_atual = []
            for _ in range(vagas_duplas_por_grupo):
                for grupo in ["a", "b"]:
                    nova_chave = Chave(
                        torneio_id=torneio.id, rodada=rodada_atual, grupo=grupo
                    )
                    db.session.add(nova_chave)
                    chaveamento_atual.append(nova_chave)
            lista_chaves_criadas.append(chaveamento_atual)
            db.session.commit()
            rodada_atual -= 1
            total_disputas_ultimas_rodada = vagas_duplas_por_grupo * 2

        chave_final = Chave(torneio_id=torneio.id, rodada=rodada_atual, grupo="f")
        lista_chaves_criadas.append(chave_final)

        chave_terceiro = Chave(torneio_id=torneio.id, rodada=0, grupo="f")
        lista_chaves_criadas.append(chave_terceiro)

        db.session.add(chave_final)
        db.session.add(chave_terceiro)
        db.session.commit()

        return lista_chaves_criadas

    @staticmethod
    def filtra_chaves_rodada(filtros):
        query = Chave.query
        if filtros.torneio_id:
            chaveamentos_torneios = query.filter(
                Chave.torneio_id == filtros.torneio_id
            ).count()
            if not chaveamentos_torneios:
                raise TorneioNotClosedError
            query = query.filter(Chave.torneio_id == filtros.torneio_id)
        if filtros.rodada:
            query = query.filter(Chave.rodada == filtros.rodada)
        if filtros.grupo:
            query = query.filter(Chave.grupo == filtros.grupo)
        return query.all()


class ResultadoService:
    @staticmethod
    def cadastrar_resultado(
        resultado: models_pydantic.ResultadoPartidaRequest,
        id_torneio: int,
        id_partida: int,
    ) -> int:
        chaveamento_obj = Chave.query.get(id_partida)
        if not chaveamento_obj:
            raise ChaveamentoNotFoundError
        if not chaveamento_obj.torneio_id == id_torneio:
            raise ChaveRaiseError
        if chaveamento_obj.vencedor:
            raise BracketingWithResultError
        if not chaveamento_obj.competidor_a_id or not chaveamento_obj.competidor_b_id:
            raise ChaveamentoNotAvailableError
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

    @staticmethod
    def classificar_proxima_rodada(
        vencedor_id, perdedor_id, chaveamento_obj, id_torneio
    ):
        torneio = Torneio.query.get(id_torneio)
        proxima_rodada = chaveamento_obj.rodada - 1
        if proxima_rodada == 1:
            return ResultadoService.classificao_das_finais(
                chaveamento_obj, vencedor_id, perdedor_id, torneio
            )
        if proxima_rodada == 0:
            return

        proxima_chave = (
            Chave.query.filter_by(rodada=proxima_rodada, grupo=chaveamento_obj.grupo)
            .filter(
                (Chave.competidor_a_id.is_(None)) | (Chave.competidor_b_id.is_(None))
            )
            .first()
        )
        if not proxima_chave.competidor_a_id:
            proxima_chave.competidor_a_id = vencedor_id
        else:
            proxima_chave.competidor_b_id = vencedor_id
        db.session.commit()

        return proxima_chave

    @staticmethod
    def classifica_proxima_rodada_bybye(torneio_id):
        lista_chaveamentos_torneio = ChaveamentoService.get_chavemaneto_sorteado(
            torneio_id
        )
        for chave in lista_chaveamentos_torneio.copy():
            if chave.bye and chave.rodada > 1 and not chave.classificado_bye:
                if not chave.competidor_a and not chave.competidor_b:
                    continue
                vencedor_bye = chave.competidor_a or chave.competidor_b
                chave.vencedor = vencedor_bye
                chave.classificado_bye = True
                db.session.commit()
                proxima_rodada = chave.rodada - 1
                proxima_chave = Chave.query.filter_by(
                    rodada=proxima_rodada,
                    grupo=chave.grupo,
                    bye=False,
                    torneio_id=torneio_id,
                ).first()
                if chave.grupo == "a":
                    proxima_chave.competidor_a = vencedor_bye
                else:
                    proxima_chave.competidor_b = vencedor_bye
                db.session.commit()
        return lista_chaveamentos_torneio

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

    @staticmethod
    def buscar_resultado_top(torneio_id):
        torneio = Torneio.query.get(torneio_id)
        if not torneio:
            raise TorneioNotFoundError
        if torneio.is_chaveado is False:
            raise TorneioNotClosedError
        chaves = (
            Chave.query.filter_by(torneio_id=torneio_id)
            .filter(Chave.rodada.in_([1, 0]))
            .order_by(Chave.rodada.asc())
            .all()
        )
        dict_classificacao = {}
        for chave in chaves:
            if chave.rodada == 1:
                dict_classificacao["Primeiro"] = chave.vencedor
                dict_classificacao["Segundo"] = (
                    chave.competidor_a
                    if chave.vencedor != chave.competidor_a
                    else chave.competidor_b
                )
            else:
                dict_classificacao["Terceiro"] = chave.vencedor
                dict_classificacao["Quarto"] = (
                    chave.competidor_a
                    if chave.vencedor != chave.competidor_a
                    else chave.competidor_b
                )
        if all(value is None for value in dict_classificacao.values()):
            raise PendingClassification
        return dict_classificacao


class CreateError(RuntimeError):
    ...


class TorneioNotFoundError(Exception):
    message = "Torneio não encontrado"
    status_code = 404


class TorneioClosedError(Exception):
    message = "Torneio está fechado"
    status_code = 403


class TorneioNotClosedError(Exception):
    message = "Torneio ainda não foi chaveado"
    status_code = 401


class PendingClassification(Exception):
    message = "Classificação não está disponível, pois não houve chaveamento"
    status_code = 401


class ChaveRaiseError(Exception):
    message = "Essa chave não pertence a esse torneio"
    status_code = 401


class BracketingWithResultError(Exception):
    message = "Resultado já existente. Não pode ser substituido"
    status_code = 422


class ChaveamentoNotFoundError(Exception):
    message = "O Chaveamento não existe"
    status_code = 401


class ChaveamentoNotAvailableError(Exception):
    message = "O chaveamento não contém dados suficientes para receber um resultado"
    status_code = 422


class CompetidoresNotFoundError(Exception):
    message = "Não foram encontrados competidores nesse torneio"
    status_code = 401
