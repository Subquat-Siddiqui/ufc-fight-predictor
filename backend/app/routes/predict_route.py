from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from backend.app.predict import predict_winner, get_upcoming_fights

router = APIRouter()


# Defines the expected shape of a request to the /predict endpoint
class PredictionRequest(BaseModel):
    fighter_a: str
    fighter_b: str
    weight_class_encoded: int
    title_bout: bool
    num_rounds: int


@router.post("/predict")
def predict(request: PredictionRequest):
    try:
        result = predict_winner(
            request.fighter_a,
            request.fighter_b,
            request.weight_class_encoded,
            request.title_bout,
            request.num_rounds
        )
        return result
    except ValueError as e:
        # Catches known errors from predict.py (e.g. no fighter history, 
        # no scheduled matchup found) and returns a proper 404 instead of a 500
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/upcoming-fights")
def upcoming_fights():
    return get_upcoming_fights()