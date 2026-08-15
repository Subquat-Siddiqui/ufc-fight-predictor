/**
 * predictApi.js
 * 
 * This file contains the logic for communicating with external data sources
 * needed by the frontend: the backend prediction API, and Wikipedia's public
 * API for fetching fighter photos.
 */

/**
 * Sends a fight matchup to the backend's /predict endpoint and returns the
 * predicted winner and confidence score.
 *
 * @param {Object} fightDetails - The fight details to send for prediction.
 * @param {string} fightDetails.fighter_a - Name of the first fighter.
 * @param {string} fightDetails.fighter_b - Name of the second fighter.
 * @param {number} fightDetails.weight_class_encoded - Encoded weight class of the fight.
 * @param {boolean} fightDetails.title_bout - Whether this fight is a title bout.
 * @param {number} fightDetails.num_rounds - Number of rounds scheduled for the fight.
 * @returns {Promise<Object>} Resolves to { winner, confidence } on success.
 * @throws {Error} If the backend returns a non-OK response (e.g. fighter not found).
 */
export async function predictWinner(fightDetails) {
    const response = await fetch('http://localhost:8000/predict', {
        method: 'POST',
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify(fightDetails)
    });

    // Parse the response body first, since both success and error responses
    // from the backend come back as valid JSON
    const data = await response.json();

    // If the backend returned an error (e.g. 404 for fighter/matchup not found),
    // surface that error message rather than returning invalid prediction data
    if (!response.ok) {
        throw new Error(data.detail || "Prediction request failed");
    }

    return data;
}

/**
 * Looks up a fighter's photo via Wikipedia's public API.
 *
 * @param {string} fighterName - Full name of the fighter (e.g. "Islam Makhachev").
 * @returns {Promise<string|null>} Resolves to the image URL if found, otherwise null.
 *   Never throws - a failed or missing lookup just resolves to null so the UI
 *   can instead use default image.
 */
export async function getFighterImage(fighterName) {
    // encodeURIComponent ensures spaces/special characters in the name don't break the URL
    const url = `https://en.wikipedia.org/w/api.php?action=query&titles=${encodeURIComponent(fighterName)}&prop=pageimages&format=json&pithumbsize=300&origin=*`;

    try {
        const response = await fetch(url);
        const data = await response.json();

        // The page object is keyed by an unknown numeric page ID, so grab
        // whatever single page comes back rather than accessing it by key
        const page = Object.values(data.query.pages)[0];

        // Chaining (?.) safely handles fighters with no thumbnail at all
        return page.thumbnail?.source || null;
    } catch (error) {
        // A missing/failed photo lookup shouldn't break the app - log it and use null
        console.error(`Failed to fetch image for ${fighterName}:`, error);
        return null;
    }
}

/**
 * Retrieves the list of currently scheduled upcoming UFC fights from the backend.
 *
 * @returns {Promise<Array>} Resolves to a list of { fighter_a, fighter_b, commence_time } objects.
 * @throws {Error} If the backend request fails.
 */
export async function getUpcomingFights() {
    const response = await fetch('http://localhost:8000/upcoming-fights');
    const data = await response.json();

    if (!response.ok) {
        throw new Error(data.detail || "Failed to fetch upcoming fights");
    }

    return data;
}