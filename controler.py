import sqlalchemy
from models.models import *
from sqlalchemy.orm import sessionmaker

engine=sqlalchemy.create_engine("sqlite:///database/hospital.db",echo=True)

Session=sessionmaker(bind=engine)
# Criar as tabelas do banco de dados
def create_base():
    Base.metadata.create_all(bind=engine)

db=Session()


def getEmployerByReparticao(r):
    return db.query(Employer).filter_by(reparticao=r).all()

def getEmployerBySector(s):
    return db.query(Employer).filter_by(sector=s).all()

def getById(id):
    return db.query(Employer).filter_by(id=id).first()

def getLen():
    laboratorio=db.query(Employer).filter_by(sector="Maternidade").all()
    laboratorio=db.query(Employer).filter_by(sector="Laboratorio").all()
    laboratorio=db.query(Employer).filter_by(sector="Psiquiatria").all()
    laboratorio=db.query(Employer).filter_by(sector="Medicina 1").all()
    



