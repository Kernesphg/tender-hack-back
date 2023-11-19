

'''
import databases
import ormar
import sqlalchemy
import uvicorn
'''

from sqlalchemy import Column, String, Float, Integer, Boolean
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker


from typing import Union

from pydantic import BaseModel
from fastapi import FastAPI, APIRouter

from fastapi_crudrouter import SQLAlchemyCRUDRouter as CRUDRouter # SQLAlchemyCRUDRouter as CRUDRouter






app = FastAPI(
    title="tenderhack noname", openapi_url=f"/openapi.json" # settings.PROJECT_NAME # settings.API_V1_STR
)


engine = create_engine(
    #"postgresql://ezz:ezz@localhost:5432/ezz"
    "sqlite:///./app.db",
    connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()


def get_db():
    session = SessionLocal()
    try:
        yield session
        session.commit()
    finally:
        session.close()









class Users(BaseModel):
    
    id: int
    name: str
    inn: int
    kpp: int

    class Config:
        orm_mode = True
#Users.update_forward_refs()

class UsersModel(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    inn = Column(Integer)
    kpp = Column(Integer)




class Items(BaseModel):
    id: int
    name: str

    class Config:
        orm_mode = True

class ItemsModel(Base):
    __tablename__ = 'items'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)

class KSessions(BaseModel): #Participants
    id: int
    participant_inn: int
    participant_kpp: int
    is_winner: int
    id_ks: int
    publish_date: int
    price: int
    customer_inn: int
    customer_kpp: int
    kpgs: int
    name: int
    items: int
    region_code: int
    violations: int

    class Config:
        orm_mode = True

class KSessionsModel(Base):
    __tablename__ = 'ksessions'
    id = Column(Integer, primary_key=True, index=True)
    participant_inn: Column(Integer) #ormar.ForeignKey(Users, related_name="sessions")
    participant_kpp: Column(Integer)
    is_winner: Column(Integer)
    id_ks: Column(Integer)
    publish_date: Column(Integer)
    price: Column(Integer)
    customer_inn: Column(Integer)
    customer_kpp: Column(Integer)
    kpgs: Column(Integer)
    name: Column(Integer)
    items: Column(Integer)
    region_code: Column(Integer)
    violations: Column(Boolean)

class Contracts(BaseModel):
    id: int
    Id_ks: int # fk KSessions id
    Contract_id: int
    Conclusion_date: int
    Price: int
    Customer_inn: int
    Customer_kpp: int
    Supplier_inn: int
    Supplier_kpp: int
    Violations: int
    Status: int

    class Config:
        orm_mode = True

class ContractsModel(Base):
    __tablename__ = 'contracts'
    id = Column(Integer, primary_key=True, index=True)
    Id_ks: Column(Integer) # fk KSessions id
    Contract_id: Column(Integer)
    Conclusion_date: Column(Integer)
    Price: Column(Integer)
    Customer_inn: Column(Integer)
    Customer_kpp: Column(Integer)
    Supplier_inn: Column(Integer)
    Supplier_kpp: Column(Integer)
    Violations: Column(Integer)
    Status: Column(Integer)

class Blocking(BaseModel):
    id: int
    Supplier_inn: int
    Supplier_kpp: int
    Reason: int
    Blocking_start_date: int
    Blocking_end_date: int

    class Config:
        orm_mode = True

class BlockingModel(Base):
    __tablename__ = 'blocking'
    id = Column(Integer, primary_key=True, index=True)
    Supplier_inn: Column(Integer)
    Supplier_kpp: Column(Integer)
    Reason: Column(Integer)
    Blocking_start_date: Column(Integer)
    Blocking_end_date: Column(Integer)



class Contract_executionCreate(BaseModel):
    Contract_id: int
    Upd_id: int
    Scheduled_delivery_date: int
    Actual_delivery_date: int
    Supplier_inn: int
    Supplier_kpp: int
    Customer_inn: int
    Customer_kpp: int

class Contract_execution(Contract_executionCreate):
    id: int

    class Config:
        orm_mode = True

class Contract_executionModel(Base):
    __tablename__ = 'contract_execution'
    id = Column(Integer, primary_key=True, index=True)
    Contract_id: Column(Integer)
    Upd_id: Column(Integer)
    Scheduled_delivery_date: Column(Integer)
    Actual_delivery_date: Column(Integer)
    Supplier_inn: Column(Integer)
    Supplier_kpp: Column(Integer)
    Customer_inn: Column(Integer)
    Customer_kpp: Column(Integer)





Base.metadata.create_all(bind=engine)




#app.include_router(APIRouter())



app.include_router(CRUDRouter(schema=Users,db_model=UsersModel,
    db=get_db,
    prefix='users', paginate=20))
app.include_router(CRUDRouter(schema=Items,db_model=ItemsModel,
    db=get_db,
    prefix='items', paginate=20))


app.include_router(CRUDRouter(schema=KSessions,db_model=KSessionsModel,
    db=get_db,
    prefix='ksessions', paginate=20))

app.include_router(CRUDRouter(schema=Contracts,db_model=ContractsModel,
    db=get_db,
    prefix='contracts', paginate=20))

app.include_router(CRUDRouter(schema=Blocking,db_model=BlockingModel,
    db=get_db,
    prefix='blocking', paginate=20))

app.include_router(CRUDRouter(schema=Contract_execution,create_schema=Contract_executionCreate,db_model=Contract_executionModel,
    db=get_db,
    prefix='contract_execution', paginate=20))




@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.get("/test_items/{test_item_id}")
def read_item(test_item_id: int, q: Union[str, None] = None):
    return {"test_item_id": test_item_id, "q": q}


#if __name__ == "__main__":
#    uvicorn.run("main:app", host="127.0.0.1", port=5000, log_level="info")


