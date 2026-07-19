# 🎵 Music Recommender Simulation

## Project Summary

This project is my simulation of how apps like Spotify or TikTok decide what to play next. I built a small content-based recommender in Python that loads a catalog of 22 songs from a CSV, scores every song against a user's "taste profile" using a weighted recipe (genre, mood, energy closeness, and some stretch attributes like popularity and era), and prints a ranked top-5 list in the terminal with an explanation for every score. It also has four switchable scoring modes and a diversity penalty so one artist can't take over the whole list.

---

## How The System Works

### How real recommenders do it

Real platforms mostly combine two strategies. **Collaborative filtering** looks at other users' behavior: if people who like the same songs as you also love a track you haven't heard, it gets recommended ("users like you also played..."). **Content-based filtering** looks at attributes of the songs themselves — genre, tempo, energy, mood, audio features — and matches them against a profile of what you already listen to. Spotify famously does both: audio analysis of the tracks plus playlist co-occurrence data from millions of users. The important distinction I learned is that there are three separate things in the pipeline: the **input data** (song features and listening history), the **user preferences** (a learned or stated profile of taste), and the **ranking algorithm** (the math that turns the first two into an ordered list). Skips, likes, replays, and playlist adds are the feedback signals that keep updating the preference side.

My version is purely **content-based** since I only have one simulated user and no behavior data from other users.

### My data model

Each `Song` uses these features:

- **Categorical:** `genre`, `mood`, `mood_tags` (detailed tags like "euphoric", "cozy"), `explicit`
- **Numerical (0.0–1.0):** `energy`, `valence`, `danceability`, `acousticness`, `instrumentalness`
- **Other:** `tempo_bpm`, `popularity` (0–100), `release_decade`

The `UserProfile` stores target values for those: a favorite genre and mood, a target energy (and optionally valence/danceability), whether they like acoustic music, favorite decade, vibe tags, and an explicit-content filter.

### My Algorithm Recipe

For each song, `score_song()` adds up:

| Rule | Points |
|---|---|
| Genre exact match | +2.0 |
| Genre partial match (e.g. "indie pop" for a "pop" fan) | +1.0 |
| Mood match | +1.0 |
| Energy **closeness** (`1 - |target - song|`) | up to +1.0 |
| Valence / danceability closeness (if user cares) | up to +0.5 each |
| Acoustic bonus (if user likes acoustic and song is acoustic) | +0.5 |
| Popularity nudge (`popularity / 100`) | up to +0.5 |
| Release decade match | +0.5 |
| Matching detailed mood tag | +0.25 each (capped at +0.5) |
| Explicit song when user's filter is on | **−2.0** |

The key design decision: numerical features use **closeness**, not "bigger is better." A chill user with target energy 0.3 should get points for a 0.35-energy song, not for a 0.98-energy metal track. The AI helped me realize `1 - abs(target - actual)` does exactly that for 0–1 features.

Then `recommend_songs()` is just ranking: it runs `score_song()` as a judge on **every** song in the catalog, sorts by score with `sorted(..., reverse=True)`, and returns the top k. There's also a **diversity penalty** (−0.75 if an artist is already in the picks, −0.4 once a genre appears twice) so the list doesn't become one artist's discography, and four **scoring modes** (`balanced`, `genre_first`, `mood_first`, `energy_focused`) that are just different weight dictionaries — same function, different strategy.

**Bias I expected going in:** genre carries the most weight, so a great song in a neighboring genre can lose to a mediocre song with the right label. Also my catalog leans heavily 2020s and has zero songs with mood = "sad", which turned out to matter (see Experiments).

---

## Getting Started

### Setup

1. Create a virtual environment (optional but recommended):

   ```bash
   python -m venv .venv
   source .venv/bin/activate      # Mac or Linux
   .venv\Scripts\activate         # Windows

2. Install dependencies

```bash
pip install -r requirements.txt
```

3. Run the app:

```bash
python -m src.main
```

### Running Tests

Run the starter tests with:

```bash
pytest
```

You can add more tests in `tests/test_recommender.py`.

---

## Sample Recommendation Output

Real terminal output for the default "High-Energy Pop Fan" profile (`genre=pop, mood=happy, energy=0.9`):

```
Loaded songs: 22
Scoring mode: balanced  (available: balanced, genre_first, mood_first, energy_focused)

=== High-Energy Pop Fan  |  prefs: {'genre': 'pop', 'mood': 'happy', 'energy': 0.9, 'danceability': 0.85, 'tags': ['euphoric', 'summery']} ===
+-----+----------------+----------------+-----------+---------+-------------------------------------------+
|   # | Title          | Artist         | Genre     |   Score | Why it was picked                         |
+=====+================+================+===========+=========+===========================================+
|   1 | Sunrise City   | Neon Echo      | pop       |    5.28 | genre match (pop, +2.0)                   |
|     |                |                |           |         | mood match (happy, +1.0)                  |
|     |                |                |           |         | energy fit (0.82 vs target 0.90, +0.92)   |
|     |                |                |           |         | danceability fit (+0.47)                  |
|     |                |                |           |         | popularity 78/100 (+0.39)                 |
|     |                |                |           |         | vibe tags ['euphoric', 'summery'] (+0.50) |
+-----+----------------+----------------+-----------+---------+-------------------------------------------+
|   2 | Rooftop Lights | Indigo Parade  | indie pop |    4.21 | related genre (indie pop, +1.0)           |
|     |                |                |           |         | mood match (happy, +1.0)                  |
|     |                |                |           |         | energy fit (0.76 vs target 0.90, +0.86)   |
|     |                |                |           |         | danceability fit (+0.48)                  |
|     |                |                |           |         | popularity 73/100 (+0.36)                 |
|     |                |                |           |         | vibe tags ['euphoric', 'summery'] (+0.50) |
+-----+----------------+----------------+-----------+---------+-------------------------------------------+
|   3 | Gym Hero       | Max Pulse      | pop       |    3.88 | genre match (pop, +2.0)                   |
|     |                |                |           |         | energy fit (0.93 vs target 0.90, +0.97)   |
|     |                |                |           |         | danceability fit (+0.48)                  |
|     |                |                |           |         | popularity 85/100 (+0.42)                 |
+-----+----------------+----------------+-----------+---------+-------------------------------------------+
|   4 | Fiesta Neon    | Los Brillantes | reggaeton |    3.13 | mood match (happy, +1.0)                  |
|     |                |                |           |         | energy fit (0.88 vs target 0.90, +0.98)   |
|     |                |                |           |         | danceability fit (+0.45)                  |
|     |                |                |           |         | popularity 90/100 (+0.45)                 |
|     |                |                |           |         | vibe tags ['summery'] (+0.25)             |
+-----+----------------+----------------+-----------+---------+-------------------------------------------+
|   5 | Bass Cathedral | DJ Nova        | edm       |    2.1  | energy fit (0.96 vs target 0.90, +0.94)   |
|     |                |                |           |         | danceability fit (+0.46)                  |
|     |                |                |           |         | popularity 92/100 (+0.46)                 |
+-----+----------------+----------------+-----------+---------+-------------------------------------------+
```

The top results match what I'd expect: the pure pop/happy tracks win, the "indie pop" partial match slots in second, and high-energy dance tracks fill out the list. Outputs for the other three profiles are in [model_card.md](model_card.md).

---

## Experiments You Tried

**1. Mode/weight shift (genre ×~0.25, energy ×3).** I ran the *same* High-Energy Pop Fan through `genre_first` (genre weight 3.5) and `energy_focused` (genre 0.5, energy 3.0). In `genre_first` the top 3 were Sunrise City, Gym Hero, Rooftop Lights — all pop or pop-adjacent, and Gym Hero (mood "intense") jumped to #2 purely off its label. In `energy_focused`, reggaeton track Fiesta Neon broke into the top 3 and Gym Hero fell out of it, because energy closeness suddenly mattered ~6× more than the genre label. Same user, same catalog, meaningfully different list — the "recipe" is doing at least as much work as the data. It wasn't obviously *more accurate*, just different, which taught me weights encode opinions, not truth.

**2. Adversarial profile.** The AI suggested testing a conflicted user: `genre=metal, mood=sad, energy=0.9, likes_acoustic=True`. The system never complains that "sad + high-energy + acoustic metal" basically doesn't exist — it silently drops the impossible constraints. My catalog has **zero** songs with mood "sad", so the sad request contributes nothing and the user gets Iron Bloom followed by... party music (Fiesta Neon, Bass Cathedral) because energy and popularity are the only signals left. A real user would find that tone-deaf.

**3. Diversity penalty on/off.** Without the penalty, the Chill Lofi Studier's top 3 was drifting toward multiple LoRoom lofi tracks. With it on, Focus Flow (same artist as Midnight Coding) takes −0.75 and ambient/jazz tracks get a fair shot at the tail of the list. The visible `artist repeat (-0.75)` reason makes the trade-off transparent.

---

## Limitations and Risks

- **Tiny catalog (22 songs):** rankings are very sensitive to which handful of songs happen to exist; one new song can reshuffle everything.
- **Mood vocabulary gaps fail silently:** asking for "sad" just zeroes out that signal instead of saying "I have nothing sad" — the system hides its own blind spots.
- **Genre labels dominate:** a +2.0 exact-match bonus means labels beat vibes; Fiesta Neon fits a pop fan's energy/mood perfectly but starts 2 points behind every mediocre "pop"-labeled song.
- **Popularity nudge is a rich-get-richer loop:** already-popular songs get extra points for every user, which is exactly how real filter bubbles form.
- It knows nothing about lyrics, language, artists' style, or how tastes change over time.

The model card goes deeper on these: [**Model Card**](model_card.md)

---

## Reflection

The biggest thing I learned is that a "recommendation" is just arithmetic plus sorting — score every item, rank, take the top k — and yet the output genuinely *feels* like the system understands taste. That feeling is doing a lot of hidden work: when my recommender put Sunrise City first for a pop fan, it looked smart, but the exact same code confidently handed a sad metal fan a reggaeton party track, and it looked equally confident doing it. The data → prediction pipeline (features in, preferences as targets, weighted score, rank) has no notion of whether its answer makes sense; only the reasons list I attached to each score let me actually audit it.

On bias: I went in expecting "genre weight too high" to be the main issue, and it was real, but the sneakier problems were in the *data*, not the algorithm — no sad songs means sad users are invisible, 2020s-heavy popularity scores mean older music quietly loses every tie. Unfairness didn't need a malicious rule; it fell out of an unbalanced catalog plus a rich-get-richer popularity term. That's a small-scale version of exactly how real platforms end up over-serving mainstream tastes. AI tools sped me up a lot (the CSV expansion, the strategy-pattern refactor), but I had to double-check them — details in [ai_interactions.md](ai_interactions.md).
