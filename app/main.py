from fastapi import FastAPI
from app.database import Base, engine
from app.routes import auth_routes

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Encrypto Backend API")

app.include_router(auth_routes.router)

@app.get("/")
def root():
    return {"message": "Encrypto backend is running"}