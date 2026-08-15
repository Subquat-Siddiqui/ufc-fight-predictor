"""
Entry point for the UFC Fight Predictor API. Registers all routes and starts the app.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.routes import predict_route

app = FastAPI(title="UFC Fight Predictor API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # For when frontend is implemented and running on a different port
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(predict_route.router)

@app.get("/")
def root():
    return {"message": "UFC Fight Predictor API is running"}