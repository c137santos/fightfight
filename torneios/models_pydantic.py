from typing import List, Optional, Union

from pydantic import BaseModel


class Message(BaseModel):
    message: str


class IdResponse(BaseModel):
    id: str


class Torneio(BaseModel):
    nome_torneio: str


class FiltroTorneio(BaseModel):
    id: Optional[str] = None
    nome_torneio: Optional[str] = "nome"


class TorneioResponse(BaseModel):
    torneios: List[Torneio]


class CompetidorRequest(BaseModel):
    nome_competidor: str


class CompetidorR(BaseModel):
    id: int
    nome: str


class CompetidoresResponse(BaseModel):
    competidores: List[CompetidorR]


class ChaveCreate(BaseModel):
    competidor_a_id: Optional[str]
    competidor_b_id: Optional[str]
    rodada: int
    torneio_id: int


class ChaveSerializada(BaseModel):
    id: int
    adversario_a: Optional[CompetidorR] = None
    adversario_b: Optional[CompetidorR] = None
    rodada: Union[int, str]
    grupo: str
    vencedor: Optional[CompetidorR] = None


class ChaveamentoResponse(BaseModel):
    chaveamentos: List[ChaveSerializada]


class ResultadoResponse(BaseModel):
    message: str


class ResultadoPartidaRequest(BaseModel):
    resultado_comp_a: int
    resultado_comp_b: int


class ResultadoCreate(BaseModel):
    resultado_comp_a: int
    resultado_comp_b: int
    vencedor_id: int


class NotImplementedResponse(BaseModel):
    message: str
