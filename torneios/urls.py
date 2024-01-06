from flask import Blueprint, jsonify, request, make_response
from flask_pydantic_spec import Request, Response

from . import spec
from .models_pydantic import (
    ChaveamentoResponse,
    FiltroTorneio,
    NotImplementedResponse,
    ResultadoPartidaRequest,
    ResultadoResponse,
    Torneio,
    CompetidorRequest,
    TorneioResponse,
    IdResponse,
    CompetidoresResponse,
)
from .service import (
    ChaveamentoService,
    CreateError,
    ResultadoService,
    TorneioService,
    CompetidorService,
)

api_blueprint = Blueprint("api", __name__)

CLASSIFICACAO = {0: "Disputa Terceiro Lugar", 1: "Final"}


@api_blueprint.post("/tournament")
@spec.validate(body=Request(Torneio), resp=Response(HTTP_201=IdResponse))
def torneio():
    data: Torneio = request.context.body
    try:
        torneio_id = TorneioService.criar_torneio(data)
        return make_response(jsonify({"id": torneio_id}), 201)
    except CreateError:
        return make_response(jsonify({"message": "Error"}), 500)


@api_blueprint.get("/tournament")
@spec.validate(query=FiltroTorneio, resp=Response(HTTP_200=TorneioResponse))
def liste_torneios():
    lista_torneios_objs = TorneioService.buscar_torneio(dict(request.context.query))
    json_lista_objetos_torneios = [
        {
            "id": torneio.id,
            "nome_torneio": torneio.nome_torneio,
            "qtd_competidores": torneio.qtd_competidores,
            "is_chaveado": torneio.is_chaveado,
        }
        for torneio in lista_torneios_objs
    ]
    return make_response(jsonify({"torneios": json_lista_objetos_torneios}), 200)


@api_blueprint.post("/tournament/<int:id_torneio>/competidor")
@spec.validate(body=Request(CompetidorRequest), resp=Response(HTTP_201=IdResponse))
def cadastrar_competidor(id_torneio: int):
    data: CompetidorRequest = request.context.body
    response = CompetidorService.cadastrar_competidor(data, id_torneio)
    if response == "TorneioNotFoundError":
        return make_response(jsonify({"message": "Torneio não encontrado"}), 500)
    if response == "TorneioClosed":
        return make_response(
            jsonify({"error": "Torneio não pode receber mais competidores"}), 403
        )
    return make_response(jsonify({"id": response}), 201)


@api_blueprint.get("/tournament/<int:id_torneio>/competidores")
@spec.validate(resp=Response(HTTP_200=CompetidoresResponse))
def buscar_competidores_torneio(id_torneio: int):
    lista_competidores_objs = CompetidorService.buscar_competidores(id_torneio)
    if lista_competidores_objs == "TorneioNotFoundError":
        return make_response(jsonify({"message": "Torneio não encontrado"}), 404)

    json_lista_competidores_objs = [
        {"id": competidor.id, "nome": competidor.nome_competidor}
        for competidor in lista_competidores_objs
    ]
    return make_response(jsonify({"competidores": json_lista_competidores_objs}), 200)


@api_blueprint.get("/tournament/<int:id_torneio>/match")
@spec.validate(resp=Response(HTTP_200=ChaveamentoResponse))
def buscar_chaveamento(id_torneio: int):
    chaveamentos_obj = ChaveamentoService.busca_chaveamento(id_torneio)
    if chaveamentos_obj == "NotEnoughCompetitor":
        return make_response(
            jsonify({"Error": "Torneio com menos de 8 competidores cadastrados"}), 404
        )

    json_chaveamentos_obj = [
        {
            "id": chave.id,
            "adversario_a": chave.competidor_a.to_dict()
            if chave.competidor_a
            else None,
            "adversario_b": chave.competidor_b.to_dict()
            if chave.competidor_b
            else None,
            "rodada": (
                CLASSIFICACAO[chave.rodada] if chave.rodada < 2 else chave.rodada
            ),
            "grupo": chave.grupo,
            "vencedor": chave.vencedor.to_dict() if chave.vencedor else None,
        }
        for chave in chaveamentos_obj
    ]
    return make_response(jsonify({"chaveamentos": json_chaveamentos_obj}), 200)


@api_blueprint.post("/tournament/<int:id_torneio>/match/<int:id_partida>")
@spec.validate(
    body=Request(ResultadoPartidaRequest), resp=Response(HTTP_201=ResultadoResponse)
)
def inserir_resultado_partida(id_torneio: int, id_partida: int):
    data: ResultadoPartidaRequest = request.context.body
    try:
        response = ResultadoService.cadastrar_resultado(data, id_torneio, id_partida)
    except Exception as ex:
        return make_response(jsonify({"message": "Error", "detail": str(ex)}), 500)
    if response == "ChaveamentoComResultado":
        return make_response(
            jsonify({"message": "Resultado Já existente. Não pode ser substituido"}),
            401,
        )
    if response == "chaveRaise":
        return make_response(
            jsonify({"message": "Essa chave não pertence a esse torneio"}), 401
        )
    return make_response(jsonify({"message": "Resultado registrado"}), 201)


@api_blueprint.get("/tournament/<int:id_torneio>/result")
@spec.validate(resp=Response(HTTP_501=NotImplementedResponse))
def buscar_topquatro(id_torneio: int):
    return make_response(jsonify({"message": "Método em implementação"}), 501)
