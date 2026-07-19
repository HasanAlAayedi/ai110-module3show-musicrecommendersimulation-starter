"""
Command line runner for the Music Recommender Simulation.

Runs my recommender against several different "taste profiles" (including one
adversarial profile with conflicting preferences) and prints a formatted table
of the top picks with the reasons behind each score.

Run with:  python -m src.main
"""

from src.recommender import load_songs, recommend_songs, SCORING_MODES

try:
    from tabulate import tabulate
    HAVE_TABULATE = True
except ImportError:
    # fall back to plain printing if tabulate isn't installed
    HAVE_TABULATE = False


# ---------------------------------------------------------------------------
# My test profiles (Phase 4). The last one is the "adversarial" profile the
# AI suggested: sad mood but very high energy — the prefs fight each other.
# ---------------------------------------------------------------------------
PROFILES = {
    "High-Energy Pop Fan": {
        "genre": "pop", "mood": "happy", "energy": 0.9,
        "danceability": 0.85, "tags": ["euphoric", "summery"],
    },
    "Chill Lofi Studier": {
        "genre": "lofi", "mood": "chill", "energy": 0.3,
        "likes_acoustic": True, "tags": ["cozy"], "allow_explicit": False,
    },
    "Deep Intense Rock Head": {
        "genre": "rock", "mood": "intense", "energy": 0.95,
        "tags": ["aggressive"], "decade": 2010,
    },
    "Conflicted (adversarial)": {
        # sad + high energy + acoustic: no song in my catalog is all three
        "genre": "metal", "mood": "sad", "energy": 0.9,
        "likes_acoustic": True,
    },
}

# which scoring strategy to use — change this to switch modes!
# options: "balanced", "genre_first", "mood_first", "energy_focused"
MODE = "balanced"


def print_recommendations(title: str, results) -> None:
    """Print one profile's top picks as a table (with reasons for each score)."""
    print(f"\n=== {title} ===")
    rows = []
    for rank, (song, score, reasons) in enumerate(results, start=1):
        rows.append([rank, song["title"], song["artist"], song["genre"],
                     f"{score:.2f}", "\n".join(reasons)])
    headers = ["#", "Title", "Artist", "Genre", "Score", "Why it was picked"]
    if HAVE_TABULATE:
        print(tabulate(rows, headers=headers, tablefmt="grid"))
    else:
        for row in rows:
            print(f"{row[0]}. {row[1]} by {row[2]} [{row[3]}] - score {row[4]}")
            print(f"   because: {row[5].replace(chr(10), ', ')}")


def main() -> None:
    songs = load_songs("data/songs.csv")
    print(f"Loaded songs: {len(songs)}")
    print(f"Scoring mode: {MODE}  (available: {', '.join(SCORING_MODES)})")

    for name, prefs in PROFILES.items():
        results = recommend_songs(prefs, songs, k=5, mode=MODE)
        print_recommendations(f"{name}  |  prefs: {prefs}", results)

    # quick demo of switching strategies for the same user (stretch feature):
    # same person, very different lists depending on what the algorithm values
    demo_prefs = PROFILES["High-Energy Pop Fan"]
    for mode in ("genre_first", "energy_focused"):
        results = recommend_songs(demo_prefs, songs, k=3, mode=mode)
        print_recommendations(f"High-Energy Pop Fan in '{mode}' mode", results)


if __name__ == "__main__":
    main()
