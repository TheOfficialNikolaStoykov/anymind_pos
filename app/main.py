from contextlib import asynccontextmanager
from fastapi import FastAPI
from strawberry.fastapi import GraphQLRouter

from app.database import init_db
from app.schema import schema


graphql_app = GraphQLRouter(schema)

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield
    

app = FastAPI(lifespan=lifespan)
app.include_router(graphql_app, prefix="/graphql")