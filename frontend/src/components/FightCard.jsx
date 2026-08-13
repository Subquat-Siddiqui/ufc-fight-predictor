import './FightCard.css';

function getInitials(name) {
  return name
    .split(' ')
    .map(word => word[0])
    .join('')
    .toUpperCase();
}

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