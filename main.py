from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import jwt
import re
from models.models import *  # Certifique-se de importar corretamente seus modelos e classes Pydantic
from sqlalchemy import create_engine,or_
import uvicorn
from sqlalchemy.orm import sessionmaker
from controler import addFerias,getFerias,getLen
from groq import Groq
# Inicializar a aplicação FastAPI
app = FastAPI()

# Configurar a conexão com o banco de dados
DATABASE_URI = 'limk'
engine = create_engine(DATABASE_URI, echo=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Criar as tabelas do banco de dados
def create_base():
    Base.metadata.create_all(bind=engine)

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

# Validação de usuário
def authenticate_user(db, contact: str, password: str):
    user = db.query(User).filter(User.contact == contact).first()
    if not user or user.password != password:
        return False
    return user

def validate_contact(contact: str):
    if not re.match(r'^(87|86|84|85|82|83)\d{7}$', contact):
        raise HTTPException(status_code=400, detail="Número inválido. Deve começar com 87, 86, 84, 85, 82, ou 83 e ter 9 dígitos.")

def create_access_token(data: dict, expires_delta: timedelta = None):
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
def add_employer(employer: EmployerCreate, db: Session = Depends(get_db)):
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
        reparticao=employer.reparticao,
        especialidade=employer.especialidade,
        categoria=employer.categoria,
        nuit=employer.nuit
    )
    db.add(new_employer)
    db.commit()
    db.refresh(new_employer)
    return new_employer

@app.post('/add_ferias')
def feria(feria:FeriaModel):
    f=addFerias(id=feria.funcionario_id)
    return f
@app.get('/ferias')
def get_ferias():
    return getFerias()

@app.get("/employers/")
def funcionarios(search: str = None, db: Session = Depends(get_db)):
    employers = db.query(Employer).join(Feria).filter(
    or_(
        Employer.status == "ACTIVO",
        Employer.status == "DISPENSA",
        Employer.status == "LICENCA"
    )
).all()
    return employers

@app.get("/employers/passados")
def funcionarios_passados(search: str = None, db: Session = Depends(get_db)):
    employers = db.query(Employer).filter(
    or_(
        
        Employer.status == "TRASFERIDO",
        Employer.status == "SUSPENSO",
        Employer.status == "FALECIDO",
        
    )
).all()
    return employers



#ROTAS PARA ESTATUS



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



@app.get("/employers/status/transferido")
def read_employers_by_transferido(db: Session = Depends(get_db)):
    employers = db.query(Employer).filter(Employer.status == "TRANSFERIDO").all()
    return employers


@app.get("/employers/status/suspenso")
def read_employers_by_suspenso(db: Session = Depends(get_db)):
    employers = db.query(Employer).filter(Employer.status == "SUSPENSO").all()
    return employers

@app.get("/employers/status/aposentado")
def read_employers_by_aposentado(db: Session = Depends(get_db)):
    employers = db.query(Employer).filter(Employer.status == "APOSENTADO").all()
    result = [
        {
            "id": emp.id,
            "nome": emp.nome,
            "total_dias": emp.calculate_days("APOSENTADO")
        }
        for emp in employers
    ]
    return result

# Rota para listar funcionários com status "DISPENSA" e calcular total de dias
@app.get("/employers/status/dispensa")
def read_employers_by_dispensa(db: Session = Depends(get_db)):
    employers = db.query(Employer).filter(Employer.status == "DISPENSA").all()
    result = [
        {
            "id": emp.id,
            "nome": emp.nome,
            "total_dias": emp.calculate_days("DISPENSA")
        }
        for emp in employers
    ]
    return result




@app.get("/employers/status/{status}")
def read_employers_by_status(status: str, db: Session = Depends(get_db)):
    valid_statuses = {"ACTIVO", "TRANSFERIDO", "SUSPENSO", "APOSENTADO", "FALECIDO","DISPENSA","LICENCA"}
    if status not in valid_statuses:
        raise HTTPException(status_code=400, detail="Status inválido")
    employers = db.query(Employer).filter(Employer.status == status).all()
    return employers



@app.get("/employers/status/falecido")
def read_employers_by_aposentado(db: Session = Depends(get_db)):
    employers = db.query(Employer).filter(Employer.status == "FALECIDO").all()
    return employers




@app.get("/employers/status/licenca")
def read_employers_by_licenca(db: Session = Depends(get_db)):
    employers = db.query(Employer).filter(Employer.status == "LICENCA").all()
    result = [
        {
            "id": emp.id,
            "nome": emp.nome,
            "total_dias": emp.calculate_days("LICENCA")
        }
        for emp in employers
    ]
    return result




# Rota para listar funcionários por setor
@app.get("/employers/sector/{sector}")
def read_employers_by_sector(sector: str, db: Session = Depends(get_db)):
    return db.query(Employer).filter(Employer.sector == sector).all()




@app.get("/employers/sectors")
def read_employers_by_sectors(db: Session = Depends(get_db)):
    sectors = getLen()
    return sectors




# Rota para listar funcionários por naturalidade
@app.get("/employers/naturality/{naturality}")
def read_employers_by_naturality(naturality: str, db: Session = Depends(get_db)):
    return db.query(Employer).filter(Employer.naturalidade == naturality).all()

# Rota para listar funcionários por província
@app.get("/employers/province/{province}")
def read_employers_by_province(province: str, db: Session = Depends(get_db)):
    return db.query(Employer).filter(Employer.provincia == province).all()

# Rota para listar funcionários por nome
@app.get("/employers/name/{name}")
def read_employers_by_name(name: str, surename: str = None, db: Session = Depends(get_db)):
    if surename:
        return db.query(Employer).filter_by(nome=name, apelido=surename).all()
    else:
        return db.query(Employer).filter_by(nome=name).all()

# Rota para listar funcionários por gênero
@app.get("/employers/genre/{genre}")
def read_employers_by_genre(genre: str, db: Session = Depends(get_db)):
    return db.query(Employer).filter(Employer.sexo == genre).all()

# Rota para listar funcionários por ano de início
@app.get("/employers/year/{year}")
def read_employers_by_year(year: int, db: Session = Depends(get_db)):
    return db.query(Employer).filter(Employer.ano_inicio == year).all()

# Rota para atualizar o status de um funcionário

def calculate_days(start_date: datetime, end_date: datetime):
    return (end_date - start_date).days if start_date and end_date else None

@app.put("/employers/{id_employer}/status")
def update_employer_status(id_employer: int, status_update: EmployerUpdateStatus, db: Session = Depends(get_db)):
    employer = db.query(Employer).filter(Employer.id == id_employer).first()
    if not employer:
        raise HTTPException(status_code=404, detail="Employer not found")

    # Atualizar o status e outros campos
    employer.status = status_update.status
    employer.data_remocao = status_update.data_remocao
    employer.razao_remocao = status_update.razao_remocao
    employer.nova_localizacao = status_update.nova_localizacao

    # Calcular dias baseados no status e nas datas fornecidas
    if status_update.status == "APOSENTADO":
        if status_update.data_inicio_aposentadoria and status_update.data_fim_aposentadoria:
            employer.total_dias_aposentadoria = calculate_days(status_update.data_inicio_aposentadoria, status_update.data_fim_aposentadoria)
    elif status_update.status == "LICENÇA":
        if status_update.data_inicio_licenca and status_update.data_fim_licenca:
            employer.total_dias_licenca = calculate_days(status_update.data_inicio_licenca, status_update.data_fim_licenca)
    elif status_update.status == "DISPENSADO":
        if status_update.data_inicio_dispensa and status_update.data_fim_dispensa:
            employer.total_dias_dispensa = calculate_days(status_update.data_inicio_dispensa, status_update.data_fim_dispensa)

    db.commit()
    db.refresh(employer)
    return employer


# Rota para deletar um funcionário
@app.delete("/employers/{id_employer}")
def delete_employer(id_employer: int, db: Session = Depends(get_db)):
    employer = db.query(Employer).filter(Employer.id == id_employer).first()
    if not employer:
        raise HTTPException(status_code=404, detail="Employer not found")
    employer.status = "Removido"
    employer.data_remocao = datetime.utcnow()
    db.commit()
    return {"message": "Employer status updated to 'Removido'"}

















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
        "categoria": employer.categoria,
        "especialidade":employer.especialidade,
        "nuit":employer.nuit

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
