from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
import jwt
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from controler import getEmployerByReparticao,getEmployerBySector,getById
import re
from models.models import*
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from groq import Groq
import json

# Inicializar a aplicação FastAPI
app = FastAPI()

# Configurar a conexão com o banco de dados
DATABASE_URL = "sqlite:///database/hospital.db"
engine = create_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Criar as tabelas do banco de dados
def create_base():
    Base.metadata.create_all(bind=engine)


def getAllEmployersByName(nome):
    
   return get_db().query(Employer).filter(Employer.nome.like(f"%{nome}%")).all()

# Dependência para obter a sessão do banco de dados
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Configurações de segurança e criptografia
SECRET_KEY = "a very secret key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 1036800

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def authenticate_user(db, contact: str, password: str):
    user = db.query(User).filter(User.contact == contact).first()
    if not user or user.password != password:
        return False
    return user



def validate_contact(contact: str):
    # verificar se o contato começa com 87, 86, 84, 85, 82 ou 83 e tem exatamente 9 dígitos
    if not re.match(r'^(87|86|84|85|82|83)\d{7}$', contact):
        raise HTTPException(status_code=400, detail="numero invalido 87, 86, 84, 85, 82, or 83 ou nao chegara  9  digitos.")





def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# Rota para login e geração de token
@app.post("/token", response_model=dict)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=400,
            detail="Incorrect contact or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.contact}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

# Dependência para obter o usuário atual a partir do token
def get_current_user(db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        contact: str = payload.get("sub")
        if contact is None:
            raise credentials_exception
    except jwt.PyJWTError:
        raise credentials_exception
    user = db.query(User).filter(User.contact == contact).first()
    if user is None:
        raise credentials_exception
    return user

# Exemplo de rota protegida que requer autenticação
@app.get("/users/me", response_model=dict)
def read_users_me(current_user: User = Depends(get_current_user)):
    return {"username": current_user.name, "contact": current_user.contact}


@app.post("/users/")
def add_user(user: UserCreate, db: Session = Depends(get_db)):
    validate_contact(user.contact)
    new_user = User(
        name=user.name,
        contact=user.contact,
        password=user.password
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user




# Rota para adicionar um funcionário
@app.post("/employers/")
def add_ereparticaomployer(employer: EmployerCreate, db: Session = Depends(get_db)):
    new_employer = Employer(
        nome=employer.nome,
        apelido=employer.apelido,
        nascimento=employer.nascimento,
        bi=employer.bi,
        provincia=employer.provincia,
        naturalidade=employer.naturalidade,
        residencia=employer.residencia,
        sexo=employer.sexo,
        inicio_funcoes=employer.inicio_funcoes,
        sector=employer.sector,
        reparticao=employer.reparticao
    )
    db.add(new_employer)
    db.commit()
    db.refresh(new_employer)
    return new_employer

# Rota para listar todos os funcionários
@app.get("/employers/")
def read_employers(search:str=None,db: Session = Depends(get_db)):
    print(search)
    if(search !=None):
        return db.query(Employer).filter(Employer.nome.like(f"%{search}%")).all()

    else:
        return db.query(Employer).all()

@app.get("/employer/{id}")
def get_by_id(id):
    d= getById(id)
    return d
    


# Rota para contar todos os usuários
@app.get("/employer/count")
def count_users(db: Session = Depends(get_db)):
    count = db.query(Employer).count()
    return {"total_users": count}





def getLen(db: Session):
    maternidade = db.query(Employer).filter_by(sector="Maternidade").all()
    laboratorio = db.query(Employer).filter_by(sector="Laboratório").all()
    psiquiatria = db.query(Employer).filter_by(sector="Psiquiatria").all()
    medicina1 = db.query(Employer).filter_by(sector="Medicina 1").all()
    return {
        "maternidade": maternidade,
        "laboratorio": laboratorio,
        "psiquiatria": psiquiatria,
        "medicina1": medicina1
    }

# Rota para obter funcionários por setores específicos
@app.get("/employers/sectors")
def read_employers_by_sectors(db: Session = Depends(get_db)):
    sectors = getLen(db)
    return sectors









# Rota para listar funcionários por gênero
@app.get("/employers/genre/{genre}")
def read_employers_by_genre(genre: str, db: Session = Depends(get_db),current_user: User = Depends(get_current_user)):
    employers = db.query(Employer).filter_by(sexo=genre).all()
    return employers

# Rota para listar funcionários por ano de início
@app.get("/employers/year/{year}")
def read_employers_by_year(year: int, db: Session = Depends(get_db),current_user: User = Depends(get_current_user)):
    employers = db.query(Employer).filter_by(ano_inicio=year).all()
    return employers

# Rota para listar funcionários por setor
@app.get("/employers/sector/{sector}")
def read_employers_by_sector(sector: str, db: Session = Depends(get_db)):
    return getEmployerBySector(sector)

# Rota para listar funcionários por naturalidade
@app.get("/employers/naturality/{naturality}")
def read_employers_by_naturality(naturality: str, db: Session = Depends(get_db),current_user: User = Depends(get_current_user)):
    employers = db.query(Employer).filter_by(naturalidade=naturality).all()
    return employers

# Rota para listar funcionários por província
@app.get("/employers/province/{province}")
def read_employers_by_province(province: str, db: Session = Depends(get_db),current_user: User = Depends(get_current_user)):
    employers = db.query(Employer).filter_by(provincia=province).all()
    return employers

# Rota para listar funcionários por nome

@app.get("/employers/reparticao/{reparticao}")
def read_employers_by_reparticao(reparticao: str, db: Session = Depends(get_db),current_user: User = Depends(get_current_user)):
    return getEmployerByReparticao(reparticao)




@app.get("/employers/name/{name}")
def read_employers_by_name(name: str, surename: str = None, db: Session = Depends(get_db),current_user: User = Depends(get_current_user)):
    if surename:
        employers = db.query(Employer).filter_by(nome=name, apelido=surename).all()
    else:
        employers = db.query(Employer).filter_by(nome=name).all()
    return employers




# Rota para deletar um funcionário
@app.delete("/employers/{id_employer}")
def delete_employer(id_employer: int, db: Session = Depends(get_db),current_user: User = Depends(get_current_user)):
    employer = db.query(Employer).filter_by(id=id_employer).first()
    if not employer:
        raise HTTPException(status_code=404, detail="Employer not found")
    db.delete(employer)
    db.commit()
    return {"message": "Employer deleted successfully"}

# Rota para atualizar um usuário
@app.put("/users/{id_user}")
def update_user(id_user: int, name: str, db: Session = Depends(get_db),current_user: User = Depends(get_current_user)):
    user = db.query(User).filter_by(id=id_user).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.name = name
    db.commit()
    db.refresh(user)
    return user


# Rota para atualizar um funcionário
@app.put("/employers/{id_employer}")
def update_employer(id_employer: int, employer_update: EmployerUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    employer = db.query(Employer).filter_by(id=id_employer).first()
    if not employer:
        raise HTTPException(status_code=404, detail="Employer not found")
    
    for key, value in employer_update.dict(exclude_unset=True).items():
        setattr(employer, key, value)

    db.commit()
    db.refresh(employer)
    return employer



# Rota para deletar um usuário
@app.delete("/users/{id_user}")
def delete_user(id_user: int, db: Session = Depends(get_db),current_user: User = Depends(get_current_user)):
    user = db.query(User).filter_by(id=id_user).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    db.delete(user)
    db.commit()
    return {"message": "User deleted successfully"}


client = Groq(api_key="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")

# Classe para a entrada de texto
class TextInput(BaseModel):
    text: str

def employer_to_dict(employer):
    # Converte o objeto Employer para um dicionário, excluindo atributos não serializáveis
    return {
        "id": employer.id,
        "nome": employer.nome,
        "apelido": employer.apelido,
        "nascimento": employer.nascimento.isoformat() if employer.nascimento else None,
        "bi": employer.bi,
        "provincia": employer.provincia,
        "naturalidade": employer.naturalidade,
        "residencia": employer.residencia,
        "sexo": employer.sexo,
        "inicio_funcoes": employer.inicio_funcoes.isoformat() if employer.inicio_funcoes else None,
        "ano_inicio": employer.ano_inicio,
        "careira": employer.careira,
        "sector": employer.sector,
        "reparticao": employer.reparticao,
    }

message_history = []

@app.post('/dina')
def dina(text_input: TextInput, db: Session = Depends(get_db)):
    users = db.query(Employer).all()
    text = text_input.text
    
    # Converte os objetos Employer para um formato serializável
    treino_dina = f"""
    OLa eu sou assistente IA criado e integrado no sistema de gestao de recursos humanos do hospital de lichinga, fui criada pela a BlueSpark
    
    
    Dados do hospital:
    {[employer_to_dict(user) for user in users]}

    ao mencionar dados nao posso retornar em json nao , deve ser dados claros, sempre ignorar o id do funcionario nao pode ser retornado

    Criado pela Electro Gulamo , 
    os principais programadores, Diqui Joaquim, Jorge Sebastiao , Zelote francisco e Alvarinho Luis, esses pertencen na equipe BlueSpark Da ElectroGulamo
    
    Hospital de lichinga:

    Hospital Provincial de Lichinga: Informação Atualizada (8 de Julho de 2024)
    O Hospital Provincial de Lichinga, na província de Niassa, Moçambique, foi recentemente inaugurado após extensas obras de reabilitação, ampliação e requalificação.
    Serviços Disponíveis:
    Serviços de Urgência: Atendimento médico imediato para casos graves.
    Maternidade: Cuidados de saúde pré, durante e pós-parto para mães e recém-nascidos.
    Bloco Operatório: Realização de cirurgias de diversas especialidades.
    Consulta Externa: Consultas médicas em diversas áreas da medicina.
    Fisioterapia: Reabilitação física para pacientes com diversos tipos de lesões.
    Pediatria: Cuidados de saúde para crianças.
    Tomografia TAC: Exames de imagem avançados para diagnóstico de doenças.
    Produção e Canalização de Oxigénio: Garantia de oxigénio para pacientes que necessitem.
    Outras Informações:

    Localização: Lichinga, Niassa, Moçambique.
    """
    # Adiciona a mensagem do sistema ao histórico, se for a primeira interação
    if not message_history:
        message_history.append({"role": "system", "content": treino_dina})

    # Adiciona a mensagem do usuário ao histórico
    message_history.append({"role": "user", "content": text})

    response = client.chat.completions.create(
        messages=message_history,
        model="llama3-70b-8192",
    )
    return response.choices[0].message.content


# Rodar o servidor com Uvicorn
if __name__ == "__main__":
    import uvicorn
    create_base()  # Criar as tabelas
    uvicorn.run(app, host="192.168.1.62", port=8000)
