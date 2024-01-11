from flask import Blueprint, jsonify, request, make_response
from flask_pydantic_spec import Request, Response

from . import spec
from .models_pydantic import (
    ChaveamentoResponse,
    ClassificationResponse,
    ErrorResponse,
    FiltroTorneio,
    ResultadoPartidaRequest,
    ResultadoResponse,
    Torneio,
    CompetidorRequest,
    TorneioResponse,
    IdResponse,
    CompetidoresResponse,
)
from .service import (
    BracketingWithResultError,
    ChaveRaiseError,
    ChaveamentoNotAvailableError,
    ChaveamentoNotFoundError,
    ChaveamentoService,
    CompetidoresNotFoundError,
    CreateError,
    PendingClassification,
    ResultadoService,
    TorneioClosedError,
    TorneioNotClosedError,
    TorneioNotFoundError,
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
    except CreateError:
        return make_response(jsonify({"message": "Error"}), 500)
    return make_response(jsonify({"id": torneio_id}), 201)


@api_blueprint.get("/tournament")
@spec.validate(
    query=FiltroTorneio, resp=Response(HTTP_200=TorneioResponse, HTTP_404=ErrorResponse)
)
def liste_torneios():
    try:
        lista_torneios_objs = TorneioService.buscar_torneio(request.context.query)
    except TorneioNotFoundError as exc:
        return make_response(jsonify({"message": exc.message}), exc.status_code)
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
@spec.validate(
    body=Request(CompetidorRequest),
    resp=Response(HTTP_201=IdResponse, HTTP_401=ErrorResponse, HTTP_403=ErrorResponse),
)
def cadastrar_competidor(id_torneio: int):
    data: CompetidorRequest = request.context.body
    try:
        response = CompetidorService.cadastrar_competidor(data, id_torneio)
    except (TorneioClosedError, TorneioNotFoundError) as exc:
        return make_response(jsonify({"message": exc.message}), exc.status_code)
    return make_response(jsonify({"id": response}), 201)


@api_blueprint.get("/tournament/<int:id_torneio>/competidores")
@spec.validate(
    resp=Response(
        HTTP_200=CompetidoresResponse, HTTP_404=ErrorResponse, HTTP_401=ErrorResponse
    )
)
def buscar_competidores_torneio(id_torneio: int):
    try:
        lista_competidores_objs = CompetidorService.buscar_competidores(id_torneio)
    except (TorneioNotFoundError, CompetidoresNotFoundError) as exc:
        return make_response(jsonify({"message": exc.message}), exc.status_code)
    json_lista_competidores_objs = [
        {"id": competidor.id, "nome": competidor.nome_competidor}
        for competidor in lista_competidores_objs
    ]
    return make_response(jsonify({"competidores": json_lista_competidores_objs}), 200)


@api_blueprint.get("/tournament/<int:id_torneio>/match")
@spec.validate(resp=Response(HTTP_200=ChaveamentoResponse, HTTP_404=ErrorResponse))
def buscar_chaveamento(id_torneio: int):
    try:
        chaveamentos_obj = ChaveamentoService.busca_chaveamento(id_torneio)
    except TorneioNotFoundError as exc:
        return make_response(jsonify({"message": exc.message}), exc.status_code)
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
            "is_bye": chave.bye,
            "resultado_a": chave.resultado_comp_a,
            "resultado_b": chave.resultado_comp_b,
        }
        for chave in chaveamentos_obj
    ]
    return make_response(jsonify({"chaveamentos": json_chaveamentos_obj}), 200)


@api_blueprint.post("/tournament/<int:id_torneio>/match/<int:id_partida>")
@spec.validate(
    body=Request(ResultadoPartidaRequest),
    resp=Response(
        HTTP_201=ResultadoResponse, HTTP_422=ErrorResponse, HTTP_401=ErrorResponse
    ),
)
def inserir_resultado_partida(id_torneio: int, id_partida: int):
    data: ResultadoPartidaRequest = request.context.body
    try:
        ResultadoService.cadastrar_resultado(data, id_torneio, id_partida)
    except (
        ChaveRaiseError,
        BracketingWithResultError,
        ChaveamentoNotFoundError,
        ChaveamentoNotAvailableError,
    ) as exc:
        return make_response(jsonify({"message": exc.message}), exc.status_code)
    return make_response(jsonify({"message": "Resultado registrado"}), 201)


@api_blueprint.get("/tournament/<int:id_torneio>/result")
@spec.validate(resp=Response(HTTP_200=ClassificationResponse, HTTP_401=ErrorResponse))
def buscar_topquatro(id_torneio: int):
    try:
        response = ResultadoService.buscar_resultado_top(id_torneio)
    except (PendingClassification, TorneioNotClosedError) as exc:
        return make_response(jsonify({"message": exc.message}), exc.status_code)
    return make_response(jsonify({"message": response}), 200)
