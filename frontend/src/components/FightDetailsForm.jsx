/**
 * FightDetailsForm.jsx
 *
 * Collects the fight-context details (weight class, title bout status, number
 * of rounds) that aren't available from the odds API, but are required by the
 * backend to build a prediction. Shown after a fight is selected, before the
 * actual prediction request is made.
 */
import { useState } from "react";
import "./FightDetailsForm.css";

// Matches the ordinal encoding order used when the model was trained
const WEIGHT_CLASSES = [
  "Flyweight",
  "Bantamweight",
  "Featherweight",
  "Lightweight",
  "Welterweight",
  "Middleweight",
  "Light Heavyweight",
  "Heavyweight",
  "Women's Strawweight",
  "Women's Flyweight",
  "Women's Bantamweight",
  "Women's Featherweight",
  "Catch Weight",
];

/**
 * @param {Object} props
 * @param {Object} props.fight - The selected fight (fighter_a, fighter_b, etc.)
 * @param {Function} props.onSubmit - Called with the fight object plus the
 *   collected details (weight_class_encoded, title_bout, num_rounds).
 * @param {Function} props.onBack - Called if the user wants to return to the fight list.
 */
function FightDetailsForm({ fight, onSubmit, onBack }) {
  const [weightClassEncoded, setWeightClassEncoded] = useState(0);
  const [titleBout, setTitleBout] = useState(false);
  const [numRounds, setNumRounds] = useState(3);

  const handleSubmit = (e) => {
    e.preventDefault();
    onSubmit({
      ...fight,
      weight_class_encoded: weightClassEncoded,
      title_bout: titleBout,
      num_rounds: numRounds,
    });
  };

  // Title bouts are always 5 rounds - keep num_rounds in sync automatically
  const handleTitleBoutChange = (checked) => {
    setTitleBout(checked);
    setNumRounds(checked ? 5 : 3);
  };

  return (
    <form className="fight-details-form" onSubmit={handleSubmit}>
      <h2>
        {fight.fighter_a} vs {fight.fighter_b}
      </h2>

      <label>
        Weight Class
        <select
          value={weightClassEncoded}
          onChange={(e) => setWeightClassEncoded(Number(e.target.value))}
        >
          {WEIGHT_CLASSES.map((name, index) => (
            <option key={name} value={index}>
              {name}
            </option>
          ))}
        </select>
      </label>

      <label className="checkbox-label">
        <input
          type="checkbox"
          checked={titleBout}
          onChange={(e) => handleTitleBoutChange(e.target.checked)}
        />
        Title Bout
      </label>

      <label>
        Number of Rounds
        <select
          value={numRounds}
          onChange={(e) => setNumRounds(Number(e.target.value))}
        >
          <option value={3}>3</option>
          <option value={5}>5</option>
        </select>
      </label>

      <div className="form-buttons">
        <button type="button" onClick={onBack}>
          Back
        </button>
        <button type="submit">Predict Winner</button>
      </div>
    </form>
  );
}

export default FightDetailsForm;