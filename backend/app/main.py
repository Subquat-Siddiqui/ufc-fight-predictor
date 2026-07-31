"""
Entry point for the UFC Fight Predictor API. Registers all routes and starts the app.
"""
from fastapi import FastAPI
from backend.app.routes import predict_route

app = FastAPI(title="UFC Fight Predictor API")

app.include_router(predict_route.router)

@app.get("/")
def root():
    return {"message": "UFC Fight Predictor API is running"}