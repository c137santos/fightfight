from . import db  # from __init__.py
from sqlalchemy.orm import relationship


class Torneio(db.Model):
    __tablename__ = "torneio"
    id = db.Column(db.Integer, primary_key=True)
    nome_torneio = db.Column(db.String())
    qtd_competidores = db.Column(db.Integer, default=0)
    is_chaveado = db.Column(db.Boolean, default=False)
    is_finalizado = db.Column(db.Boolean, default=False)

    competidores = relationship("Competidor", back_populates="torneio")
    chaves = relationship("Chave", back_populates="torneio")

    def __init__(self, nome_torneio):
        self.nome_torneio = nome_torneio

    def __repr__(self):
        return f"<id {self.id}>"


class Competidor(db.Model):
    __tablename__ = "competidor"
    id = db.Column(db.Integer, primary_key=True)
    nome_competidor = db.Column(db.String())
    torneio_id = db.Column(db.Integer, db.ForeignKey("torneio.id"))

    # Adicionando relação entre Equipe e Torneio
    torneio = relationship("Torneio", back_populates="competidores")

    def __init__(self, nome_competidor, torneio_id):
        self.nome_competidor = nome_competidor
        self.torneio_id = torneio_id

    def __repr__(self):
        return f"<id {self.id}, {self.nome_competidor}>"

    def to_dict(self):
        return {"id": self.id, "nome": self.nome_competidor}


class Chave(db.Model):
    __tablename__ = "chave"
    id = db.Column(db.Integer, primary_key=True)
    torneio_id = db.Column(db.Integer, db.ForeignKey("torneio.id"))
    competidor_a_id = db.Column(db.Integer, db.ForeignKey("competidor.id"))
    competidor_b_id = db.Column(db.Integer, db.ForeignKey("competidor.id"))
    rodada = db.Column(db.Integer)
    grupo = db.Column(db.String(), default="s")
    resultado_comp_a = db.Column(db.Integer)
    resultado_comp_b = db.Column(db.Integer)
    vencedor_id = db.Column(db.Integer, db.ForeignKey("competidor.id"))

    competidor_a = relationship("Competidor", foreign_keys=[competidor_a_id])
    competidor_b = relationship("Competidor", foreign_keys=[competidor_b_id])
    vencedor = relationship("Competidor", foreign_keys=[vencedor_id])
    torneio = relationship("Torneio", back_populates="chaves")

    def __init__(
        self, torneio_id, rodada, grupo, competidor_a_id=None, competidor_b_id=None
    ):
        self.torneio_id = torneio_id
        self.competidor_a_id = competidor_a_id
        self.competidor_b_id = competidor_b_id
        self.rodada = rodada
        self.grupo = grupo

    def __repr__(self):
        return (
            f"<Chave(id={self.id}, torneio_id={self.torneio_id}, rodada={self.rodada})>"
        )
