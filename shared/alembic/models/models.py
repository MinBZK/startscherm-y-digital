from sqlalchemy import (
    Column,
    Integer,
    String,
)

from shared.alembic.database import Base


class Law(Base):
    __tablename__ = "law"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String)
    url = Column(String)


class ChatMessage(Base):
    __tablename__ = "chat_message"

    id = Column(Integer, primary_key=True, autoincrement=True)
    message = Column(String)


class SelectieLijsten(Base):
    __tablename__ = "selectielijsten"

    id = Column(Integer, primary_key=True, autoincrement=True)
    selectielijsten = Column(String)
    procescategorie = Column(String)
    process_number = Column(String)
    process_description = Column(String)
    waardering = Column(String)
    proces_komt_voor_bij = Column(String)
    toelichting = Column(String)
    voorbeelden = Column(String)
    voorbeelden_werkdoc_bsd = Column(String)
    persoonsgegevens_aanwezig = Column(String)
