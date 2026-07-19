"""
Music Recommender Simulation - core logic.

My "Algorithm Recipe" (designed in Phase 2):
  +2.0  genre match (biggest signal, genre is how I actually browse music)
  +1.0  mood match
  +1.0  energy similarity (closer to my target = more points, not just higher)
  +0.5  valence / danceability similarity (if the user cares about them)
  +0.5  acoustic bonus if the user likes acoustic stuff
  +0.5  small popularity nudge (stretch feature)
  +0.5  decade match (stretch feature)
  +0.25 per matching detailed mood tag, capped (stretch feature)

Recommending = scoring every song with score_song(), then sorting.
I also added a diversity penalty so one artist can't take over the top 5.
"""

from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, field, asdict
import csv


# ---------------------------------------------------------------------------
# Scoring modes (Strategy pattern, stretch feature)
# Each mode is just a different set of weights, so switching strategies is
# switching dictionaries instead of rewriting the scoring function.
# ---------------------------------------------------------------------------
SCORING_MODES: Dict[str, Dict[str, float]] = {
    # my default recipe from Phase 2
    "balanced": {
        "genre": 2.0,
        "mood": 1.0,
        "energy": 1.0,
        "valence": 0.5,
        "danceability": 0.5,
        "acoustic": 0.5,
        "popularity": 0.5,
        "decade": 0.5,
        "mood_tag": 0.25,
    },
    # "just give me my genre" mode
    "genre_first": {
        "genre": 3.5,
        "mood": 0.5,
        "energy": 0.5,
        "valence": 0.25,
        "danceability": 0.25,
        "acoustic": 0.25,
        "popularity": 0.25,
        "decade": 0.25,
        "mood_tag": 0.1,
    },
    # vibe over genre labels
    "mood_first": {
        "genre": 0.75,
        "mood": 2.5,
        "energy": 1.0,
        "valence": 0.75,
        "danceability": 0.25,
        "acoustic": 0.5,
        "popularity": 0.25,
        "decade": 0.25,
        "mood_tag": 0.5,
    },
    # workout-playlist mode: intensity matters most
    "energy_focused": {
        "genre": 0.5,
        "mood": 0.5,
        "energy": 3.0,
        "valence": 0.25,
        "danceability": 1.0,
        "acoustic": 0.25,
        "popularity": 0.25,
        "decade": 0.1,
        "mood_tag": 0.1,
    },
}

# Diversity penalty settings (stretch feature).
# If an artist/genre is already in the picked list, later songs by them lose
# points so the top-k doesn't turn into one artist's discography.
ARTIST_PENALTY = 0.75
GENRE_PENALTY = 0.4  # only kicks in after a genre already appears twice


@dataclass
class Song:
    """Represents a song and its attributes (one row of songs.csv)."""
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
    # stretch-feature attributes (defaults so old code/tests still work)
    popularity: int = 50
    release_decade: int = 2010
    mood_tags: List[str] = field(default_factory=list)
    instrumentalness: float = 0.5
    explicit: bool = False


@dataclass
class UserProfile:
    """Represents a user's taste preferences."""
    favorite_genre: str
    favorite_mood: str
    target_energy: float
    likes_acoustic: bool


def load_songs(csv_path: str) -> List[Dict]:
    """Load songs from a CSV file into a list of dicts with real numeric types."""
    songs = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # csv gives us strings for everything, so convert the numeric
            # columns or the math in score_song silently breaks
            row["id"] = int(row["id"])
            for col in ("energy", "tempo_bpm", "valence", "danceability",
                        "acousticness", "instrumentalness"):
                row[col] = float(row[col])
            row["popularity"] = int(row["popularity"])
            row["release_decade"] = int(row["release_decade"])
            row["mood_tags"] = row["mood_tags"].split(";") if row["mood_tags"] else []
            row["explicit"] = row["explicit"].strip().lower() == "yes"
            songs.append(row)
    return songs


def _similarity(target: float, actual: float) -> float:
    """Turn the gap between two 0-1 values into a closeness score (1 = perfect)."""
    return 1.0 - abs(target - actual)


def _genre_points(user_prefs: Dict, song: Dict,
                  weights: Dict[str, float]) -> Tuple[float, List[str]]:
    """Genre points: exact match = full, partial ("indie pop" vs "pop") = half."""
    want = user_prefs.get("genre", "").lower()
    have = song["genre"].lower()
    if want and want == have:
        return weights["genre"], [f"genre match ({have}, +{weights['genre']:.1f})"]
    if want and (want in have or have in want):
        half = weights["genre"] / 2
        return half, [f"related genre ({have}, +{half:.1f})"]
    return 0.0, []


def _stretch_points(user_prefs: Dict, song: Dict,
                    weights: Dict[str, float]) -> Tuple[float, List[str]]:
    """Points from the stretch attributes: popularity, decade, tags, explicit."""
    score = 0.0
    reasons = []
    if "popularity" in song:
        pts = weights["popularity"] * (song["popularity"] / 100.0)
        score += pts
        reasons.append(f"popularity {song['popularity']}/100 (+{pts:.2f})")
    if user_prefs.get("decade") and user_prefs["decade"] == song.get("release_decade"):
        score += weights["decade"]
        reasons.append(f"{song['release_decade']}s era match (+{weights['decade']:.1f})")
    if user_prefs.get("tags"):
        overlap = {t.lower() for t in user_prefs["tags"]} & \
                  {t.lower() for t in song.get("mood_tags", [])}
        if overlap:
            pts = min(weights["mood_tag"] * len(overlap), weights["mood_tag"] * 2)
            score += pts
            reasons.append(f"vibe tags {sorted(overlap)} (+{pts:.2f})")
    # respect the explicit filter if the user set one
    if user_prefs.get("allow_explicit") is False and song.get("explicit"):
        score -= 2.0
        reasons.append("explicit content (-2.0)")
    return score, reasons


def score_song(user_prefs: Dict, song: Dict,
               weights: Optional[Dict[str, float]] = None) -> Tuple[float, List[str]]:
    """Score one song against user prefs; returns (score, list of reasons)."""
    if weights is None:
        weights = SCORING_MODES["balanced"]

    # genre is the biggest signal, so it gets its own helper
    score, reasons = _genre_points(user_prefs, song, weights)

    # --- mood ---
    if user_prefs.get("mood") and user_prefs["mood"].lower() == song["mood"].lower():
        score += weights["mood"]
        reasons.append(f"mood match ({song['mood']}, +{weights['mood']:.1f})")

    # --- energy: closeness, NOT "more is better". A chill user should not
    # get metal just because metal has a big energy number. ---
    if "energy" in user_prefs:
        sim = _similarity(user_prefs["energy"], song["energy"])
        pts = weights["energy"] * sim
        score += pts
        reasons.append(f"energy fit ({song['energy']:.2f} vs target "
                       f"{user_prefs['energy']:.2f}, +{pts:.2f})")

    # --- optional numeric closeness features ---
    if "valence" in user_prefs:
        pts = weights["valence"] * _similarity(user_prefs["valence"], song["valence"])
        score += pts
        reasons.append(f"positivity fit (+{pts:.2f})")
    if "danceability" in user_prefs:
        pts = weights["danceability"] * _similarity(user_prefs["danceability"],
                                                    song["danceability"])
        score += pts
        reasons.append(f"danceability fit (+{pts:.2f})")

    # --- acoustic taste ---
    if user_prefs.get("likes_acoustic") and song["acousticness"] >= 0.6:
        score += weights["acoustic"]
        reasons.append(f"acoustic vibe (+{weights['acoustic']:.1f})")

    # --- stretch features: popularity, decade, mood tags, explicit filter ---
    stretch_score, stretch_reasons = _stretch_points(user_prefs, song, weights)
    score += stretch_score
    reasons.extend(stretch_reasons)

    return score, reasons


def recommend_songs(user_prefs: Dict, songs: List[Dict], k: int = 5,
                    mode: str = "balanced",
                    diversity: bool = True) -> List[Tuple[Dict, float, List[str]]]:
    """Score every song, rank them, and return the top k as (song, score, reasons)."""
    weights = SCORING_MODES[mode]

    # step 1: judge every single song in the catalog
    scored = []
    for song in songs:
        score, reasons = score_song(user_prefs, song, weights)
        scored.append((song, score, reasons))

    # step 2: rank. sorted() gives me a new list instead of mutating (the AI
    # explained .sort() changes the list in place, sorted() copies it)
    scored = sorted(scored, key=lambda item: item[1], reverse=True)

    if not diversity:
        return scored[:k]

    # step 3 (stretch): greedy re-pick with a diversity penalty so the top-k
    # isn't 5 songs from the same artist/genre bubble
    picked: List[Tuple[Dict, float, List[str]]] = []
    remaining = list(scored)
    while remaining and len(picked) < k:
        artists_used = [p[0]["artist"] for p in picked]
        genres_used = [p[0]["genre"] for p in picked]

        best = None
        best_adjusted = float("-inf")
        for song, score, reasons in remaining:
            adjusted = score
            notes = []
            if song["artist"] in artists_used:
                adjusted -= ARTIST_PENALTY
                notes.append(f"artist repeat (-{ARTIST_PENALTY})")
            if genres_used.count(song["genre"]) >= 2:
                adjusted -= GENRE_PENALTY
                notes.append(f"genre saturated (-{GENRE_PENALTY})")
            if adjusted > best_adjusted:
                best_adjusted = adjusted
                best = (song, adjusted, reasons + notes)
        picked.append(best)
        remaining = [r for r in remaining if r[0]["id"] != best[0]["id"]]

    return picked


class Recommender:
    """OOP wrapper around the scoring logic (kept so the starter tests pass)."""

    def __init__(self, songs: List[Song]):
        self.songs = songs

    def _prefs(self, user: UserProfile) -> Dict:
        """Convert a UserProfile object into the prefs dict score_song expects."""
        return {
            "genre": user.favorite_genre,
            "mood": user.favorite_mood,
            "energy": user.target_energy,
            "likes_acoustic": user.likes_acoustic,
        }

    def recommend(self, user: UserProfile, k: int = 5) -> List[Song]:
        """Return the top k Song objects for this user, best first."""
        song_dicts = [asdict(s) for s in self.songs]
        ranked = recommend_songs(self._prefs(user), song_dicts, k=k)
        by_id = {s.id: s for s in self.songs}
        return [by_id[song["id"]] for song, _score, _reasons in ranked]

    def explain_recommendation(self, user: UserProfile, song: Song) -> str:
        """Explain in one line why this song scored what it did for this user."""
        score, reasons = score_song(self._prefs(user), asdict(song))
        return f"{song.title} scored {score:.2f}: " + ", ".join(reasons)
