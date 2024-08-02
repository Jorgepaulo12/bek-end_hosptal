import sqlalchemy
from models.models import *  # Importa a Base e Employer do arquivo correto
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine,or_
# Configurar a conexão com o banco de dados
DATABASE_URI = 'link'
engine = create_engine(DATABASE_URI, echo=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Session = sessionmaker(bind=engine)
# Criar as tabelas do banco de dados se não existirem
def create_base():
    Base.metadata.create_all(bind=engine)

# Criação da sessão
db = Session()

def getEmployerByReparticao(r):
    """Retorna a lista de empregados filtrados pela repartição"""
    return db.query(Employer).filter_by(reparticao=r).all()

def getEmployerBySector(s):
    """Retorna a lista de empregados filtrados pelo setor"""
    return db.query(Employer).filter_by(sector=s).all()

def getById(id):
    """Retorna um empregado com base no ID"""
    return db.query(Employer).filter_by(id=id).first()

def getLen():
    """Retorna o número de empregados em setores específicos"""
    setores = ["Maternidade", "Laboratorio", "Psiquiatria", "Medicina 1"]
    contagem = {}
    for setor in setores:
        contagem[setor] = db.query(Employer).filter_by(sector=setor).count()
    return contagem
def addFerias(id,start=datetime.now(),end=datetime.now()):
    nova_feria = Feria(
        funcionario_id=id,
        data_inicio_ferias = start,
        data_fim_ferias = end

    )
    funcionario=db.query(Employer).filter_by(id=id).first()
    funcionario.status="LICENCA"
    db.commit()

    db.add(nova_feria)
    db.commit()

    return nova_feria

def getFerias():
    # Recupera todas as férias e seus respectivos funcionários
    feria = db.query(Feria).join(Employer).first()
    
    return feria

