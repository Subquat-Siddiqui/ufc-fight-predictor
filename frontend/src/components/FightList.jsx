/**
 * FightList.jsx
 *
 * Fetches the list of currently scheduled upcoming UFC fights from the backend,
 * resolves each fighter's photo via Wikipedia, and renders one FightCard per
 * matchup, grouped into confirmed and rumored sections. Notifies its parent
 * (via onSelectFight) when the user picks a fight.
 */
import { useState, useEffect } from "react";
import FightCard from "./FightCard";
import { getFighterImage, getUpcomingFights } from "../api/predictApi";
import "./FightList.css";

/**
 * @param {Object} props
 * @param {Function} props.onSelectFight - Called with the selected fight's data
 *   when the user clicks a FightCard.
 */
function FightList({ onSelectFight }) {
    // Holds the fully-assembled list of fights, including resolved fighter images.
    // Starts empty until the fetch in useEffect below completes.
    const [fights, setFights] = useState([]);

    // Runs once, when this component first mounts (empty dependency array),
    // to fetch the fight list and each fighter's image before rendering anything.
    useEffect(() => {
        const loadFights = async () => {
            const fightData = await getUpcomingFights();

            // For each fight, fetch both fighters' images concurrently via Promise.all,
            // rather than one fight/fighter at a time, since sequential fetching
            // would be noticeably slower with multiple fights on the card
            const fightsWithImages = await Promise.all(
                fightData.map(async (fight) => {
                    const [fighterAImage, fighterBImage] = await Promise.all([
                        getFighterImage(fight.fighter_a),
                        getFighterImage(fight.fighter_b),
                    ]);

                    return {
                        ...fight,
                        fighterAImage,
                        fighterBImage,
                    };
                })
            );

            setFights(fightsWithImages);
        };

        loadFights();
    }, []);

    // Simple loading state while the fetch above is still in progress
    if (fights.length === 0) {
        return <p>Loading fights...</p>;
    }

    // Split into two groups based on the status tagged by the backend
    const confirmedFights = fights.filter((fight) => fight.status === "confirmed");
    const rumoredFights = fights.filter((fight) => fight.status === "rumored");

    const renderFightCard = (fight) => (
        <FightCard
            key={`${fight.fighter_a}-${fight.fighter_b}`}
            fighterAName={fight.fighter_a}
            fighterBName={fight.fighter_b}
            fighterAImage={fight.fighterAImage}
            fighterBImage={fight.fighterBImage}
            status={fight.status}
            onSelect={() => onSelectFight(fight)}
        />
    );

    return (
        <div className="fight-list">
            <h2>Confirmed Upcoming Fights</h2>
            {confirmedFights.length > 0 ? (
                confirmedFights.map(renderFightCard)
            ) : (
                <p>No confirmed fights currently scheduled.</p>
            )}

            {rumoredFights.length > 0 && (
                <>
                    <h2>Rumoured & Potential Matchups</h2>
                    {rumoredFights.map(renderFightCard)}
                </>
            )}
        </div>
    );
}

export default FightList;