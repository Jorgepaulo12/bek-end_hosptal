from sqlalchemy import Column,String,Integer,Float,Boolean,DateTime
from sqlalchemy.orm import declarative_base
from pydantic import BaseModel
from datetime import *
from typing import Optional

#models.py este arquivo conte os modelos do banco de dados
#para o sistema 

#vamos criar a instancia para que os modelos herdadem desta clase Base
Base=declarative_base()

#modelo para usuario ->login atraves d telefone e senha
class User(Base):
    __tablename__="users"
    id=Column(Integer,primary_key=True)
    name=Column(String(50))
    contact=Column(String(30))
    password=Column(String(64))

class Employer(Base):
    __tablename__="employers"
    id=Column(Integer,primary_key=True)
    nome=Column(String(50))
    apelido=Column(String(50))
    nascimento=Column(DateTime)
    bi=Column(String(50))
    provincia=Column(String(50))
    naturalidade=Column(String(50))
    residencia=Column(String(50))
    sexo=Column(String(50))
    inicio_funcoes=Column(DateTime)
    ano_inicio=Column(Integer,default="2020")
    careira=Column(String(200))
    sector=Column(String(200))
    reparticao=Column(String(100))

class EmployerCreate(BaseModel):
    nome: str
    apelido: str
    nascimento: datetime
    bi: str
    provincia: str
    naturalidade: str
    residencia: str
    sexo: str
    inicio_funcoes: datetime
    sector: str
    reparticao:str

class EmployerUpdate(BaseModel):
    nome: Optional[str]
    apelido: Optional[str]
    bi: Optional[str]
    provincia: Optional[str]
    naturalidade: Optional[str]
    residencia: Optional[str]
    sexo: Optional[str]
    sector: Optional[str]
    reparticao:str

# Modelo para entrada do formulário de adicionar usuário
class UserCreate(BaseModel):
    name: str
    contact: str
    password: str

    