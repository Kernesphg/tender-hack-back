

from typing import Union

from pydantic import BaseModel
from fastapi import FastAPI, APIRouter

from fastapi_crudrouter import MemoryCRUDRouter as CRUDRouter



app = FastAPI(
    title="tenderhack noname", openapi_url=f"/openapi.json" # settings.PROJECT_NAME # settings.API_V1_STR
)


class Users(BaseModel):
    id: int
    name: str
    inn: int
    kpp: int

class Items(BaseModel):
    id: int
    name: str

class KSessions(BaseModel): #Participants
    id: int
    Participant_inn: int
    Participant_kpp: int
    Is_winner: int
    Id_ks: int
    Publish_date: int
    Price: int
    Customer_inn: int
    Customer_kpp: int
    Kpgs: int
    name: str
    Item: int
    Region_code: int
    Violations: bool


class Contracts(BaseModel):
    id: int
    Id_ks: str # fk KSessions id
    Contract_id: str
    Conclusion_date: str
    Price: str
    Customer_inn: str
    Customer_kpp: str
    Supplier_inn: str
    Supplier_kpp: str
    Violations: str
    Status: str

class Blocking(BaseModel):
    id: int
    Supplier_inn: str
    Supplier_kpp: str
    Reason: str
    Blocking_start_date: str
    Blocking_end_date: str

class Contract_execution(BaseModel):
    id: int
    Contract_id: str
    Upd_id: str
    Scheduled_delivery_date: str
    Actual_delivery_date: str
    Supplier_inn: str
    Supplier_kpp: str
    Customer_inn: str
    Customer_kpp: str




#app.include_router(APIRouter())

app.include_router(CRUDRouter(schema=KSessions))

app.include_router(CRUDRouter(schema=Contracts))

app.include_router(CRUDRouter(schema=Blocking))

app.include_router(CRUDRouter(schema=Contract_execution))

app.include_router(CRUDRouter(schema=Users))
app.include_router(CRUDRouter(schema=Items))




@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.get("/items/{item_id}")
def read_item(item_id: int, q: Union[str, None] = None):
    return {"item_id": item_id, "q": q}





