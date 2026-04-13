from fastapi import FastAPI
from sqlalchemy import text

from endpoints import router
from models import Base, engine

with engine.connect() as conn:
    conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
    conn.commit()

Base.metadata.create_all(bind=engine)


app = FastAPI()
app.include_router(router)
