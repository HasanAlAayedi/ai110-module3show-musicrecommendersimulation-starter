from src.recommender import (
    Song,
    UserProfile,
    Recommender,
    load_songs,
    score_song,
    recommend_songs,
)

def make_small_recommender() -> Recommender:
    songs = [
        Song(
            id=1,
            title="Test Pop Track",
            artist="Test Artist",
            genre="pop",
            mood="happy",
            energy=0.8,
            tempo_bpm=120,
            valence=0.9,
            danceability=0.8,
            acousticness=0.2,
        ),
        Song(
            id=2,
            title="Chill Lofi Loop",
            artist="Test Artist",
            genre="lofi",
            mood="chill",
            energy=0.4,
            tempo_bpm=80,
            valence=0.6,
            danceability=0.5,
            acousticness=0.9,
        ),
    ]
    return Recommender(songs)


def test_recommend_returns_songs_sorted_by_score():
    user = UserProfile(
        favorite_genre="pop",
        favorite_mood="happy",
        target_energy=0.8,
        likes_acoustic=False,
    )
    rec = make_small_recommender()
    results = rec.recommend(user, k=2)

    assert len(results) == 2
    # Starter expectation: the pop, happy, high energy song should score higher
    assert results[0].genre == "pop"
    assert results[0].mood == "happy"


def test_explain_recommendation_returns_non_empty_string():
    user = UserProfile(
        favorite_genre="pop",
        favorite_mood="happy",
        target_energy=0.8,
        likes_acoustic=False,
    )
    rec = make_small_recommender()
    song = rec.songs[0]

    explanation = rec.explain_recommendation(user, song)
    assert isinstance(explanation, str)
    assert explanation.strip() != ""


# ---------------------------------------------------------------------------
# My own tests for the functional API (load_songs / score_song / recommend_songs)
# ---------------------------------------------------------------------------

def test_load_songs_converts_numeric_types():
    songs = load_songs("data/songs.csv")
    assert len(songs) >= 15  # rubric wants at least 15-20 songs
    first = songs[0]
    # if these stayed strings, all the scoring math would silently break
    assert isinstance(first["energy"], float)
    assert isinstance(first["popularity"], int)
    assert isinstance(first["mood_tags"], list)
    assert isinstance(first["explicit"], bool)


def test_score_song_rewards_genre_and_mood_match():
    prefs = {"genre": "pop", "mood": "happy", "energy": 0.8}
    match = {"genre": "pop", "mood": "happy", "energy": 0.8, "acousticness": 0.1}
    miss = {"genre": "metal", "mood": "sad", "energy": 0.1, "acousticness": 0.1}

    match_score, match_reasons = score_song(prefs, match)
    miss_score, _ = score_song(prefs, miss)

    assert match_score > miss_score
    # the reasons should actually mention the rules that fired
    assert any("genre match" in r for r in match_reasons)
    assert any("mood match" in r for r in match_reasons)


def test_energy_scoring_uses_closeness_not_magnitude():
    # a chill user should prefer a 0.35-energy song over a 0.95-energy one,
    # even though 0.95 is the "bigger" number
    prefs = {"energy": 0.3}
    close = {"genre": "x", "mood": "x", "energy": 0.35, "acousticness": 0.0}
    loud = {"genre": "x", "mood": "x", "energy": 0.95, "acousticness": 0.0}
    assert score_song(prefs, close)[0] > score_song(prefs, loud)[0]


def test_recommend_songs_returns_top_k_sorted():
    songs = load_songs("data/songs.csv")
    prefs = {"genre": "pop", "mood": "happy", "energy": 0.9}
    results = recommend_songs(prefs, songs, k=3, diversity=False)

    assert len(results) == 3
    scores = [score for _song, score, _reasons in results]
    assert scores == sorted(scores, reverse=True)


def test_diversity_penalty_limits_artist_repeats():
    songs = load_songs("data/songs.csv")
    # LoRoom has multiple lofi tracks, so this profile would stack them
    prefs = {"genre": "lofi", "mood": "chill", "energy": 0.4}
    results = recommend_songs(prefs, songs, k=5, diversity=True)

    artists = [song["artist"] for song, _score, _reasons in results]
    # no artist should appear more than twice in the top 5
    assert all(artists.count(a) <= 2 for a in set(artists))
