/**
 * PredictionResult.jsx
 *
 * Given a selected fight, calls the backend's /predict endpoint and displays
 * the predicted winner and confidence score. Handles its own loading and
 * error states, and lets the user go back to the fight list.
 */
import { useState, useEffect } from "react";
import { predictWinner } from "../api/predictApi";
import "./PredictionResult.css";


/**
 * @param {Object} props
 * @param {Object} props.fight - The selected fight, including fighter_a, fighter_b,
 *   fighterAImage, fighterBImage, and status.
 * @param {Function} props.onBack - Called when the user wants to return to the fight list.
 */
function PredictionResult({ fight, onBack }) {
    const [result, setResult] = useState(null);
    const [error, setError] = useState(null);

    // Runs once when this component mounts, using the selected fight to
    // actually request a prediction from the backend
    useEffect(() => {
        const runPrediction = async () => {
            try {
                const fightDetails = {
                    fighter_a: fight.fighter_a,
                    fighter_b: fight.fighter_b,
                    weight_class_encoded: fight.weight_class_encoded,
                    title_bout: fight.title_bout,
                    num_rounds: fight.num_rounds,
                };

                const prediction = await predictWinner(fightDetails);
                setResult(prediction);
            } catch (err) {
                setError(err.message);
            }
        };

        runPrediction();
    }, [fight]);

    if (error) {
        return (
            <div className="prediction-result">
                <p className="error-message">Couldn't get a prediction: {error}</p>
                <button onClick={onBack}>Back to fights</button>
            </div>
        );
    }

    if (!result) {
        return <p>Predicting winner...</p>;
    }

    // Figure out which fighter's image to show alongside the winner's name
    const winnerImage =
        result.winner === fight.fighter_a ? fight.fighterAImage : fight.fighterBImage;

    return (
        <div className="prediction-result">
            <h2>Predicted Winner</h2>

            {winnerImage && (
                <img src={winnerImage} alt={result.winner} className="winner-image" />
            )}

            <p className="winner-name">{result.winner}</p>
            <p className="confidence">{(result.confidence * 100).toFixed(1)}% confidence</p>

            <button onClick={onBack}>Predict another fight</button>
        </div>
    );
}

export default PredictionResult;