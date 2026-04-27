"""
Robustness and reliability testing for the music recommender.

Provides utilities to:
- Test consistency (same input → same output)
- Analyze sensitivity (how much do rankings change with input tweaks)
- Run edge-case adversarial profiles
- Detect bias in recommendations
"""

import logging
from typing import Dict, List, Tuple, Any
from src.recommender import recommend_songs


logger = logging.getLogger(__name__)


def check_consistency(songs: List[Dict], user_prefs: Dict, num_runs: int = 10) -> float:
    """
    Test if the same input produces identical output (consistency).

    Args:
        songs: Catalog of songs
        user_prefs: User preference dict
        num_runs: Number of runs to test

    Returns:
        Consistency score (1.0 = perfect, 0.0 = no consistency)
    """
    logger.info(f"Starting consistency test with {num_runs} runs")

    results = []
    for i in range(num_runs):
        recs = recommend_songs(user_prefs, songs, k=5)
        results.append([song["title"] for song, _, _ in recs])

    # Check if all runs produced identical rankings
    first_result = results[0]
    consistency_count = sum(1 for r in results if r == first_result)
    consistency_score = consistency_count / num_runs

    logger.info(f"Consistency score: {consistency_score:.2%} ({consistency_count}/{num_runs} runs identical)")
    return consistency_score


def compute_sensitivity(songs: List[Dict], user_prefs: Dict, perturbation: float = 0.1) -> Dict[str, float]:
    """
    Measure how sensitive rankings are to small input changes (sensitivity analysis).

    Args:
        songs: Catalog of songs
        user_prefs: User preference dict
        perturbation: Magnitude of parameter change (0.1 = ±10%)

    Returns:
        Dict mapping parameter names to ranking change percentages
    """
    logger.info("Starting sensitivity analysis")

    baseline = recommend_songs(user_prefs, songs, k=5)
    baseline_titles = {song["title"] for song, _, _ in baseline}

    sensitivity = {}

    # Test energy sensitivity
    perturbed_prefs = user_prefs.copy()
    perturbed_prefs["energy"] = max(0, min(1, user_prefs.get("energy", 0.5) + perturbation))
    perturbed = recommend_songs(perturbed_prefs, songs, k=5)
    perturbed_titles = {song["title"] for song, _, _ in perturbed}
    energy_change = len(baseline_titles - perturbed_titles) / 5
    sensitivity["energy"] = energy_change
    logger.debug(f"Energy perturbation caused {energy_change:.2%} ranking change")

    # Test acousticness sensitivity
    perturbed_prefs = user_prefs.copy()
    perturbed_prefs["likes_acoustic"] = not user_prefs.get("likes_acoustic", True)
    perturbed = recommend_songs(perturbed_prefs, songs, k=5)
    perturbed_titles = {song["title"] for song, _, _ in perturbed}
    acoustic_change = len(baseline_titles - perturbed_titles) / 5
    sensitivity["acousticness"] = acoustic_change
    logger.debug(f"Acousticness flip caused {acoustic_change:.2%} ranking change")

    # Test popularity sensitivity
    if "target_popularity" in user_prefs:
        perturbed_prefs = user_prefs.copy()
        perturbed_prefs["target_popularity"] = max(0, min(100, user_prefs["target_popularity"] + 20))
        perturbed = recommend_songs(perturbed_prefs, songs, k=5)
        perturbed_titles = {song["title"] for song, _, _ in perturbed}
        pop_change = len(baseline_titles - perturbed_titles) / 5
        sensitivity["popularity"] = pop_change
        logger.debug(f"Popularity change caused {pop_change:.2%} ranking change")

    logger.info(f"Sensitivity analysis complete: {sensitivity}")
    return sensitivity


def run_adversarial_profiles(songs: List[Dict]) -> Dict[str, Any]:
    """
    Test the recommender with edge-case and adversarial profiles.

    Returns:
        Dict with results for each adversarial profile
    """
    logger.info("Running adversarial profile tests")

    adversarial_profiles = {
        "case-sensitivity-attack": {
            "genre": "Pop",  # Wrong case
            "mood": "HAPPY",
            "energy": 0.9,
            "likes_acoustic": False,
        },
        "out-of-range-energy-high": {
            "genre": "pop",
            "mood": "happy",
            "energy": 2.5,  # Out of range
            "likes_acoustic": False,
        },
        "out-of-range-energy-low": {
            "genre": "rock",
            "mood": "intense",
            "energy": -1.2,  # Out of range
            "likes_acoustic": True,
        },
        "unknown-labels": {
            "genre": "nonexistent-genre",
            "mood": "nonexistent-mood",
            "energy": 0.55,
            "likes_acoustic": True,
        },
        "sparse-profile": {
            "energy": 0.8,
            "likes_acoustic": False,
            # Missing genre and mood
        },
    }

    results = {}
    for profile_name, prefs in adversarial_profiles.items():
        try:
            recs = recommend_songs(prefs, songs, k=5)
            results[profile_name] = {
                "status": "success",
                "num_recs": len(recs),
                "top_song": recs[0][0]["title"] if recs else None,
                "avg_score": sum(score for _, score, _ in recs) / len(recs) if recs else 0,
            }
            logger.info(f"Adversarial profile '{profile_name}': returned {len(recs)} recommendations")
        except Exception as e:
            results[profile_name] = {
                "status": "error",
                "error": str(e),
            }
            logger.warning(f"Adversarial profile '{profile_name}' failed: {e}")

    return results


def check_genre_bias(songs: List[Dict]) -> Dict[str, float]:
    """
    Detect if the recommender is biased toward certain genres.

    Returns:
        Dict mapping genres to frequency in top-5 recommendations
    """
    logger.info("Checking for genre bias")

    genre_frequencies = {}
    num_tests = 10

    for genre in set(s.get("genre", "") for s in songs if "genre" in s):
        top_5_count = 0
        for _ in range(num_tests):
            prefs = {"genre": genre, "mood": "happy", "energy": 0.7, "likes_acoustic": False}
            recs = recommend_songs(prefs, songs, k=5)
            # Count if the preferred genre appears in top 5
            top_5_count += sum(1 for song, _, _ in recs if song.get("genre") == genre)

        genre_frequencies[genre] = top_5_count / (num_tests * 5)
        logger.debug(f"Genre '{genre}' appears in top-5: {genre_frequencies[genre]:.2%} of the time")

    logger.info(f"Genre bias analysis complete: {genre_frequencies}")
    return genre_frequencies


def run_robustness_tests(songs: List[Dict]) -> Dict[str, Any]:
    """
    Run the full robustness testing suite.

    Returns:
        Comprehensive dict with all test results
    """
    logger.info("Starting full robustness test suite")

    results = {
        "consistency": {
            "score": check_consistency(songs, {"genre": "pop", "mood": "happy", "energy": 0.7, "likes_acoustic": False}),
            "description": "1.0 = always consistent, 0.0 = never consistent",
        },
        "sensitivity": {
            "results": compute_sensitivity(songs, {"genre": "pop", "mood": "happy", "energy": 0.7, "likes_acoustic": False}),
            "description": "Ranking change when inputs are perturbed",
        },
        "adversarial": {
            "results": run_adversarial_profiles(songs),
            "description": "Edge-case profile handling",
        },
        "genre_bias": {
            "results": check_genre_bias(songs),
            "description": "Frequency of each genre appearing in top-5",
        },
    }

    logger.info("Full robustness suite complete")
    return results
