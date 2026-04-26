from csv import DictReader
from typing import Any, List, Dict, Tuple, Optional
from dataclasses import dataclass


# Weighting is tuned for a small catalog where genre and mood are the clearest
# indicators of taste, and numeric features fine-tune the ranking.
GENRE_MATCH_POINTS = 4.0
MOOD_MATCH_POINTS = 3.0
ENERGY_MATCH_POINTS = 2.5
ACOUSTIC_MATCH_POINTS = 1.0
POPULARITY_MATCH_POINTS = 1.5
DECADE_MATCH_POINTS = 1.25
MOOD_TAG_MATCH_POINTS = 1.75
INSTRUMENTAL_MATCH_POINTS = 1.0
EXPLICIT_ALIGNMENT_POINTS = 1.0

@dataclass
class Song:
    """
    Represents a song and its attributes.
    Required by tests/test_recommender.py
    """
    id: int
    title: str
    artist: str
    genre: str
    mood: str
    energy: float
    tempo_bpm: float
    valence: float
    danceability: float
    acousticness: float
    popularity: int = 50
    release_decade: int = 2000
    mood_tags: str = ""
    instrumentalness: float = 0.0
    explicit_lyrics: bool = False

@dataclass
class UserProfile:
    """
    Represents a user's taste preferences.
    Required by tests/test_recommender.py
    """
    favorite_genre: str
    favorite_mood: str
    target_energy: float
    likes_acoustic: bool

class Recommender:
    """
    OOP implementation of the recommendation logic.
    Required by tests/test_recommender.py
    """
    def __init__(self, songs: List[Song]):
        self.songs = songs

    def recommend(self, user: UserProfile, k: int = 5) -> List[Song]:
        scored_songs = []
        user_prefs = {
            "genre": user.favorite_genre,
            "mood": user.favorite_mood,
            "energy": user.target_energy,
            "likes_acoustic": user.likes_acoustic,
        }

        for song in self.songs:
            score, _ = score_song(user_prefs, song.__dict__)
            scored_songs.append((song, score))

        scored_songs.sort(key=lambda item: item[1], reverse=True)
        return [song for song, _ in scored_songs[:k]]

    def explain_recommendation(self, user: UserProfile, song: Song) -> str:
        user_prefs = {
            "genre": user.favorite_genre,
            "mood": user.favorite_mood,
            "energy": user.target_energy,
            "likes_acoustic": user.likes_acoustic,
        }
        _, reasons = score_song(user_prefs, song.__dict__)
        return "; ".join(reasons) if reasons else "This song is a reasonable match for the user's taste profile."

def _get_value(item: Any, key: str, default: Any = None) -> Any:
    if isinstance(item, dict):
        return item.get(key, default)
    return getattr(item, key, default)


def _clamp(value: float, minimum: float = 0.0, maximum: float = 1.0) -> float:
    return max(minimum, min(maximum, value))


def _normalized_distance_score(value: float, target: float) -> float:
    return _clamp(1.0 - abs(value - target))


def load_songs(csv_path: str) -> List[Dict]:
    """
    Loads songs from a CSV file.
    Required by src/main.py
    """
    songs: List[Dict[str, Any]] = []
    with open(csv_path, newline="", encoding="utf-8") as csv_file:
        reader = DictReader(csv_file)
        for row in reader:
            songs.append(
                {
                    "id": int(row["id"]),
                    "title": row["title"],
                    "artist": row["artist"],
                    "genre": row["genre"],
                    "mood": row["mood"],
                    "energy": float(row["energy"]),
                    "tempo_bpm": float(row["tempo_bpm"]),
                    "valence": float(row["valence"]),
                    "danceability": float(row["danceability"]),
                    "acousticness": float(row["acousticness"]),
                    "popularity": int(row.get("popularity", 50)),
                    "release_decade": int(row.get("release_decade", 2000)),
                    "mood_tags": row.get("mood_tags", ""),
                    "instrumentalness": float(row.get("instrumentalness", 0.0)),
                    "explicit_lyrics": bool(int(row.get("explicit_lyrics", 0))),
                }
            )
    return songs

def score_song(user_prefs: Dict, song: Dict) -> Tuple[float, List[str]]:
    """
    Scores a single song against user preferences.
    Required by recommend_songs() and src/main.py
    """
    genre = _get_value(song, "genre", "")
    mood = _get_value(song, "mood", "")
    energy = float(_get_value(song, "energy", 0.0) or 0.0)
    acousticness = float(_get_value(song, "acousticness", 0.0) or 0.0)
    popularity = float(_get_value(song, "popularity", 50.0) or 50.0)
    release_decade = int(_get_value(song, "release_decade", 2000) or 2000)
    mood_tags = str(_get_value(song, "mood_tags", "") or "")
    instrumentalness = float(_get_value(song, "instrumentalness", 0.0) or 0.0)
    explicit_lyrics = bool(_get_value(song, "explicit_lyrics", False))

    preferred_genre = user_prefs.get("genre") or user_prefs.get("favorite_genre")
    preferred_mood = user_prefs.get("mood") or user_prefs.get("favorite_mood")
    target_energy = user_prefs.get("energy", user_prefs.get("target_energy", 0.0))
    likes_acoustic = bool(user_prefs.get("likes_acoustic", False))
    target_popularity = float(user_prefs.get("target_popularity", 50.0))
    preferred_decade = int(user_prefs.get("preferred_decade", release_decade))
    likes_instrumental = bool(user_prefs.get("likes_instrumental", False))
    preferred_tags_raw = user_prefs.get("preferred_mood_tags", [])
    if isinstance(preferred_tags_raw, str):
        preferred_tags = [tag.strip().lower() for tag in preferred_tags_raw.split("|") if tag.strip()]
    else:
        preferred_tags = [str(tag).strip().lower() for tag in preferred_tags_raw if str(tag).strip()]
    song_tag_set = {tag.strip().lower() for tag in mood_tags.split("|") if tag.strip()}

    score = 0.0
    reasons: List[str] = []

    # Strong categorical matches.
    if preferred_genre and genre == preferred_genre:
        score += GENRE_MATCH_POINTS
        reasons.append(f"genre matches {preferred_genre}")

    if preferred_mood and mood == preferred_mood:
        score += MOOD_MATCH_POINTS
        reasons.append(f"mood matches {preferred_mood}")

    # Distance-based numeric scoring rewards songs that are close to the user's target.
    energy_match = _normalized_distance_score(energy, float(target_energy))
    score += energy_match * ENERGY_MATCH_POINTS
    reasons.append(f"energy is close to the target ({energy:.2f} vs {float(target_energy):.2f})")

    preferred_acousticness = 1.0 if likes_acoustic else 0.0
    acoustic_match = _normalized_distance_score(acousticness, preferred_acousticness)
    score += acoustic_match * ACOUSTIC_MATCH_POINTS
    if likes_acoustic:
        reasons.append("higher acousticness fits the user's preference")
    else:
        reasons.append("lower acousticness fits the user's preference")

    # Popularity similarity: normalize to [0, 1] and reward closeness.
    popularity_match = _normalized_distance_score(popularity / 100.0, target_popularity / 100.0)
    popularity_points = popularity_match * POPULARITY_MATCH_POINTS
    score += popularity_points
    reasons.append(
        f"popularity is close to target (+{popularity_points:.2f}) [song={int(popularity)}, target={int(target_popularity)}]"
    )

    # Decade preference: full points for exact decade, smoothly reduced by distance.
    decade_gap = abs(release_decade - preferred_decade)
    decade_match = _clamp(1.0 - (decade_gap / 40.0))
    decade_points = decade_match * DECADE_MATCH_POINTS
    score += decade_points
    reasons.append(
        f"era alignment (+{decade_points:.2f}) [song decade={release_decade}, preferred={preferred_decade}]"
    )

    # Detailed mood-tag overlap: intersection ratio against preferred tags.
    if preferred_tags:
        overlap_count = len(song_tag_set.intersection(preferred_tags))
        tag_match_ratio = overlap_count / len(preferred_tags)
        tag_points = tag_match_ratio * MOOD_TAG_MATCH_POINTS
        score += tag_points
        reasons.append(
            f"mood-tag overlap (+{tag_points:.2f}) [matched {overlap_count}/{len(preferred_tags)} tags]"
        )

    # Instrumentalness preference works like a distance-based soft target.
    preferred_instrumentalness = 1.0 if likes_instrumental else 0.0
    instrumental_match = _normalized_distance_score(instrumentalness, preferred_instrumentalness)
    instrumental_points = instrumental_match * INSTRUMENTAL_MATCH_POINTS
    score += instrumental_points
    reasons.append(f"instrumentalness alignment (+{instrumental_points:.2f})")

    # Explicit lyric preference is optional; only score when preference is provided.
    if "avoids_explicit" in user_prefs:
        avoids_explicit = bool(user_prefs.get("avoids_explicit", False))
        preferred_explicitness = 0.0 if avoids_explicit else 1.0
        explicit_match = _normalized_distance_score(float(int(explicit_lyrics)), preferred_explicitness)
        explicit_points = explicit_match * EXPLICIT_ALIGNMENT_POINTS
        score += explicit_points
        reasons.append(f"explicit-content alignment (+{explicit_points:.2f})")

    return score, reasons

def recommend_songs(user_prefs: Dict, songs: List[Dict], k: int = 5) -> List[Tuple[Dict, float, str]]:
    """
    Functional implementation of the recommendation logic.
    Required by src/main.py
    """
    scored_songs = []

    for song in songs:
        score, reasons = score_song(user_prefs, song)
        explanation = "; ".join(reasons)
        scored_songs.append((song, score, explanation))

    scored_songs.sort(key=lambda item: item[1], reverse=True)
    return scored_songs[:k]
