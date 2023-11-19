


import databases
import ormar
import sqlalchemy
import uvicorn

from sqlalchemy import Column, String, Float, Integer
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker


from typing import Union

from pydantic import BaseModel
from fastapi import FastAPI, APIRouter

from fastapi_crudrouter import OrmarCRUDRouter as CRUDRouter # SQLAlchemyCRUDRouter as CRUDRouter


DATABASE_URL = "sqlite:///./test.db"
database = databases.Database(DATABASE_URL)
metadata = sqlalchemy.MetaData()



app = FastAPI(
    title="tenderhack noname", openapi_url=f"/openapi.json" # settings.PROJECT_NAME # settings.API_V1_STR
)

@app.on_event("startup")
async def startup():
    await database.connect()

@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()

class BaseMeta(ormar.ModelMeta):
    metadata = metadata
    database = database

def _setup_database():
    # if you do not have the database run this once
    engine = sqlalchemy.create_engine(DATABASE_URL)
    metadata.drop_all(engine)
    metadata.create_all(engine)
    return engine, database






engine = create_engine(
    "sqlite:///./app.db",
    connect_args={"check_same_thread": False}
)


class Users(ormar.Model):
    class Meta(BaseMeta):
        pass
    id: ormar.Integer(primary_key=True)
    name: ormar.String(max_length=255)
    inn: ormar.Integer()
    kpp: ormar.Integer()

class Items(ormar.Model):
    class Meta(BaseMeta):
        pass
    id: ormar.Integer(primary_key=True)
    name: ormar.String(max_length=255)

class KSessions(ormar.Model): #Participants
    class Meta(BaseMeta):
        pass
    id: ormar.Integer(primary_key=True)
    Participant_inn: ormar.ForeignKey(Users, related_name="sessions")
    Participant_kpp: ormar.Integer()
    Is_winner: ormar.Integer()
    Id_ks: ormar.Integer()
    Publish_date: ormar.Integer()
    Price: ormar.Integer()
    Customer_inn: ormar.Integer()
    Customer_kpp: ormar.Integer()
    Kpgs: ormar.Integer()
    name: ormar.Integer()
    Items: ormar.Integer()
    Region_code: ormar.Integer()
    Violations: ormar.Boolean()


class Contracts(ormar.Model):
    class Meta(BaseMeta):
        pass
    id: ormar.Integer(primary_key=True)
    Id_ks: ormar.Integer() # fk KSessions id
    Contract_id: ormar.Integer()
    Conclusion_date: ormar.Integer()
    Price: ormar.Integer()
    Customer_inn: ormar.Integer()
    Customer_kpp: ormar.Integer()
    Supplier_inn: ormar.Integer()
    Supplier_kpp: ormar.Integer()
    Violations: ormar.Integer()
    Status: ormar.Integer()

class Blocking(ormar.Model):
    class Meta(BaseMeta):
        pass
    id: ormar.Integer(primary_key=True)
    Supplier_inn: ormar.Integer()
    Supplier_kpp: ormar.Integer()
    Reason: ormar.Integer()
    Blocking_start_date: ormar.Integer()
    Blocking_end_date: ormar.Integer()

class Contract_execution(ormar.Model):
    class Meta(BaseMeta):
        pass
    id: ormar.Integer(primary_key=True)
    Contract_id: ormar.Integer()
    Upd_id: ormar.Integer()
    Scheduled_delivery_date: ormar.Integer()
    Actual_delivery_date: ormar.Integer()
    Supplier_inn: ormar.Integer()
    Supplier_kpp: ormar.Integer()
    Customer_inn: ormar.Integer()
    Customer_kpp: ormar.Integer()










#app.include_router(APIRouter())

app.include_router(CRUDRouter(schema=KSessions, paginate=20))

app.include_router(CRUDRouter(schema=Contracts, paginate=20))

app.include_router(CRUDRouter(schema=Blocking, paginate=20))

app.include_router(CRUDRouter(schema=Contract_execution, paginate=20))

app.include_router(CRUDRouter(schema=Users, paginate=20))
app.include_router(CRUDRouter(schema=Items, paginate=20))




@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.get("/test_items/{test_item_id}")
def read_item(test_item_id: int, q: Union[str, None] = None):
    return {"test_item_id": test_item_id, "q": q}





