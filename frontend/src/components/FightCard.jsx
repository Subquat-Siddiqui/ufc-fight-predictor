import './FightCard.css';

// Builds initials from a fighter's full name (e.g. "Islam Makhachev" -> "IM"),
// used as a fallback when no photo is available
function getInitials(name) {
  return name
    .split(' ')
    .map(word => word[0])
    .join('')
    .toUpperCase();
}

// Displays one matchup as a clickable card. Purely presentational - receives
// all data (names, images, click handler) as props and doesn't fetch anything itself.
function FightCard({ fighterAName, fighterBName, fighterAImage, fighterBImage, onSelect }) {
  return (
    <div className="fight-card" onClick={onSelect}>
      <div className="fighter">
        {fighterAImage ? (
          <img src={fighterAImage} alt={fighterAName} className="fighter-image" />
        ) : (
          <div className="fighter-placeholder">{getInitials(fighterAName)}</div>
        )}
        <p>{fighterAName}</p>
      </div>

      <span className="vs">VS</span>

      <div className="fighter">
        {fighterBImage ? (
          <img src={fighterBImage} alt={fighterBName} className="fighter-image" />
        ) : (
          <div className="fighter-placeholder">{getInitials(fighterBName)}</div>
        )}
        <p>{fighterBName}</p>
      </div>
    </div>
  );
}

export default FightCard;