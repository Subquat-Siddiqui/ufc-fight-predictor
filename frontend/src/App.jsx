/**
 * App.jsx
 *
 * Top-level component managing the UFC Fight Predictor's three-step flow:
 * 1. FightList - browse and pick an upcoming fight
 * 2. FightDetailsForm - fill in weight class, title bout, and rounds
 * 3. PredictionResult - see the predicted winner
 *
 * No routing library is used - which step is shown is just tracked in state,
 * since this is a single-page app with no need for separate URLs.
 */
import { useState } from "react";
import FightList from "./components/FightList";
import FightDetailsForm from "./components/FightDetailsForm";
import PredictionResult from "./components/PredictionResult";
import "./App.css";

function App() {
  // Tracks which step of the flow is currently showing
  const [step, setStep] = useState("list"); // "list" | "form" | "result"

  // Holds the fight data as it moves through the flow - starts as just
  // { fighter_a, fighter_b, fighterAImage, fighterBImage, status } from
  // FightList, then gets weight_class_encoded/title_bout/num_rounds added
  // once FightDetailsForm is submitted
  const [selectedFight, setSelectedFight] = useState(null);

  const handleSelectFight = (fight) => {
    setSelectedFight(fight);
    setStep("form");
  };

  const handleSubmitDetails = (fightWithDetails) => {
    setSelectedFight(fightWithDetails);
    setStep("result");
  };

  const handleBackToList = () => {
    setSelectedFight(null);
    setStep("list");
  };

  const handleBackToForm = () => {
    setStep("form");
  };

  return (
    <div className="app">
      <header className="app-header">
        <h1>UFC Fight Predictor</h1>
        <p>Pick an upcoming fight and see who the model favours to win.</p>
      </header>

      <main>
        {step === "list" && <FightList onSelectFight={handleSelectFight} />}

        {step === "form" && (
          <FightDetailsForm
            fight={selectedFight}
            onSubmit={handleSubmitDetails}
            onBack={handleBackToList}
          />
        )}

        {step === "result" && (
          <PredictionResult fight={selectedFight} onBack={handleBackToForm} />
        )}
      </main>
    </div>
  );
}

export default App;