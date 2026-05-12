from fastapi import FastAPI
from app.database import Base, engine
from app.routes import auth_routes
from app.models import user, file
from app.routes import auth_routes, file_routes
from app.routes import crypto_routes


Base.metadata.create_all(bind=engine)

app = FastAPI(title="Encrypto Backend API")
app.include_router(file_routes.router)
app.include_router(crypto_routes.router)
app.include_router(auth_routes.router)

@app.get("/")
def root():
    return {"message": "Encrypto backend is running"}
