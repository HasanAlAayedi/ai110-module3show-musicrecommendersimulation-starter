# 🎧 Model Card: Music Recommender Simulation

## 1. Model Name

**VibeJudge 1.0** — because all it really does is judge every song against your vibe and rank the verdicts.

---

## 2. Intended Use

VibeJudge is a classroom simulation of a content-based music recommender. Given a stated taste profile (favorite genre, mood, target energy, and a few optional preferences), it ranks a small catalog and returns a top-5 list with a plain-English reason for every score. It assumes the user can honestly *state* their taste up front — real users usually can't, which is why real systems learn from behavior instead of asking.

**Intended use:** learning how data + preferences + a ranking rule become a "prediction"; experimenting with weights and bias.
**Not intended for:** real users, production playlists, or any decision that matters. 22 songs and hand-picked weights cannot represent actual musical taste, and the popularity term would actively amplify mainstream bias at scale.

---

## 3. How the Model Works

Think of it as a judge with a scorecard. For every song in the catalog it hands out points: a big bonus if the genre matches what you asked for (a smaller one if it's just related, like "indie pop" for a pop fan), a medium bonus for the right mood, and points for *closeness* on energy — a song slightly calmer than your target still scores well, while one far off scores badly, in either direction. Smaller nudges come from popularity, matching your favorite decade, shared "vibe tags" like *cozy* or *euphoric*, and an acoustic bonus if that's your thing. Explicit songs lose points if you turned the family filter on.

Once every song has a number, recommending is just sorting the numbers and taking the top five — with one twist I added: if an artist already made the list, their next song gets docked points, and so does a third song from the same genre. Compared to the starter, everything past the empty function signatures is mine: the recipe, the reasons attached to every score, four switchable weighting modes, and the diversity penalty.

---

## 4. Data

- **22 songs** in `data/songs.csv` — the 10 starter tracks plus 12 I added (with AI help) to cover hip-hop, EDM, country, classical, metal, R&B, folk, reggaeton, punk, soul, and indie rock.
- **15 attributes per song**, including 5 stretch-feature additions: `popularity` (0–100), `release_decade`, `mood_tags`, `instrumentalness`, `explicit`.
- Known gaps: no songs with mood "sad" (discovered the hard way, see §6), moods are single labels I assigned by feel, the catalog skews 2020s, and huge parts of taste (lyrics, language, nostalgia, artist loyalty) simply aren't in the data.

---

## 5. Strengths

- For "coherent" users — pop/happy, lofi/chill, rock/intense — the top 3 matched my intuition every time, and the closeness rule correctly kept metal away from the chill listener even though metal has big energy numbers.
- Every recommendation is fully explainable: the reasons column shows exactly which rule fired and for how many points, so nothing is a black box.
- The diversity penalty visibly works (Focus Flow shows `artist repeat (-0.75)` under the lofi profile instead of the list becoming all-LoRoom).
- Partial genre matching ("indie pop" ≈ "pop") catches neighbors a strict string match would miss.

---

## 6. Limitations and Bias

The clearest weakness I found: **users whose mood isn't in the catalog's vocabulary become invisible, and the system fills the gap with popular party music.** My adversarial profile asked for sad, high-energy, acoustic metal; since zero songs are tagged "sad", that entire preference contributed nothing, and slots 2–4 went to reggaeton, EDM, and pop purely on energy + popularity. The system never signals "I can't serve this request" — it just answers confidently with something else. On top of that, the +2.0 exact-genre bonus means labels beat vibes (Fiesta Neon fits a pop fan perfectly but starts 2 points behind anything labeled "pop"), and the popularity nudge is a small rich-get-richer loop: already-popular songs get bonus points for *every* user, which at scale is exactly how filter bubbles and mainstream bias compound.

**Diversity/fairness feature (stretch):** to push against the bubble effect, `recommend_songs()` applies an artist penalty (−0.75) and a genre-saturation penalty (−0.4 after two songs of the same genre) during a greedy re-pick. This improves fairness in a concrete way: exposure in the top-5 gets spread across more artists and genres instead of letting one popular artist monopolize the list, and the penalty is printed in the reasons so the trade-off is transparent to the user.

---

## 7. Evaluation

I tested four profiles (full commands in `src/main.py`, first profile's output in the README):

**Chill Lofi Studier** (`genre=lofi, mood=chill, energy=0.3, likes_acoustic=True, allow_explicit=False`):

```
=== Chill Lofi Studier ===
+-----+--------------------+----------------+---------+---------+-----------------------------------------+
|   # | Title              | Artist         | Genre   |   Score | Why it was picked                       |
+=====+====================+================+=========+=========+=========================================+
|   1 | Library Rain       | Paper Lanterns | lofi    |    4.98 | genre match (lofi, +2.0)                |
|     |                    |                |         |         | mood match (chill, +1.0)                |
|     |                    |                |         |         | energy fit (0.35 vs target 0.30, +0.95) |
|     |                    |                |         |         | acoustic vibe (+0.5)                    |
|     |                    |                |         |         | popularity 55/100 (+0.28)               |
|     |                    |                |         |         | vibe tags ['cozy'] (+0.25)              |
+-----+--------------------+----------------+---------+---------+-----------------------------------------+
|   2 | Midnight Coding    | LoRoom         | lofi    |    4.95 | genre match (lofi, +2.0)                |
|     |                    |                |         |         | mood match (chill, +1.0)                |
|     |                    |                |         |         | energy fit (0.42 vs target 0.30, +0.88) |
|     |                    |                |         |         | acoustic vibe (+0.5)                    |
|     |                    |                |         |         | popularity 64/100 (+0.32)               |
|     |                    |                |         |         | vibe tags ['cozy'] (+0.25)              |
+-----+--------------------+----------------+---------+---------+-----------------------------------------+
|   3 | Focus Flow         | LoRoom         | lofi    |    2.81 | genre match (lofi, +2.0)                |
|     |                    |                |         |         | energy fit (0.40 vs target 0.30, +0.90) |
|     |                    |                |         |         | acoustic vibe (+0.5)                    |
|     |                    |                |         |         | vibe tags ['cozy'] (+0.25)              |
|     |                    |                |         |         | artist repeat (-0.75)                   |
|     |                    |                |         |         | genre saturated (-0.4)                  |
+-----+--------------------+----------------+---------+---------+-----------------------------------------+
|   4 | Spacewalk Thoughts | Orbit Bloom    | ambient |    2.72 | mood match (chill, +1.0)                |
|     |                    |                |         |         | energy fit (0.28 vs target 0.30, +0.98) |
|     |                    |                |         |         | acoustic vibe (+0.5)                    |
+-----+--------------------+----------------+---------+---------+-----------------------------------------+
|   5 | Tokyo Rain Level   | Pixel Monk     | edm     |    2.15 | mood match (chill, +1.0)                |
|     |                    |                |         |         | energy fit (0.52 vs target 0.30, +0.78) |
+-----+--------------------+----------------+---------+---------+-----------------------------------------+
```

**Deep Intense Rock Head** (`genre=rock, mood=intense, energy=0.95, decade=2010`):

```
=== Deep Intense Rock Head ===
+-----+------------------+------------+------------+---------+-----------------------------------------+
|   # | Title            | Artist     | Genre      |   Score | Why it was picked                       |
+=====+==================+============+============+=========+=========================================+
|   1 | Storm Runner     | Voltline   | rock       |    5.06 | genre match (rock, +2.0)                |
|     |                  |            |            |         | mood match (intense, +1.0)              |
|     |                  |            |            |         | energy fit (0.91 vs target 0.95, +0.96) |
|     |                  |            |            |         | 2010s era match (+0.5)                  |
|     |                  |            |            |         | vibe tags ['aggressive'] (+0.25)        |
+-----+------------------+------------+------------+---------+-----------------------------------------+
|   2 | Iron Bloom       | Graveshift | metal      |    3.05 | mood match (intense, +1.0)              |
|     |                  |            |            |         | energy fit (0.98 vs target 0.95, +0.97) |
|     |                  |            |            |         | 2010s era match (+0.5)                  |
+-----+------------------+------------+------------+---------+-----------------------------------------+
|   3 | Gym Hero         | Max Pulse  | pop        |    2.66 | mood match (intense, +1.0)              |
|     |                  |            |            |         | energy fit (0.93 vs target 0.95, +0.98) |
|     |                  |            |            |         | popularity 85/100 (+0.42)               |
+-----+------------------+------------+------------+---------+-----------------------------------------+
|   4 | Glass Mountains  | Echo Atlas | indie rock |    2.52 | related genre (indie rock, +1.0)        |
|     |                  |            |            |         | energy fit (0.68 vs target 0.95, +0.73) |
+-----+------------------+------------+------------+---------+-----------------------------------------+
|   5 | Night Drive Loop | Neon Echo  | synthwave  |    1.65 | energy fit (0.75 vs target 0.95, +0.80) |
+-----+------------------+------------+------------+---------+-----------------------------------------+
```

**Conflicted adversarial profile** (`genre=metal, mood=sad, energy=0.9, likes_acoustic=True`):

```
=== Conflicted (adversarial) ===
+-----+------------------+----------------+-----------+---------+-----------------------------------------+
|   # | Title            | Artist         | Genre     |   Score | Why it was picked                       |
+=====+==================+================+===========+=========+=========================================+
|   1 | Iron Bloom       | Graveshift     | metal     |    3.25 | genre match (metal, +2.0)               |
|     |                  |                |           |         | energy fit (0.98 vs target 0.90, +0.92) |
+-----+------------------+----------------+-----------+---------+-----------------------------------------+
|   2 | Fiesta Neon      | Los Brillantes | reggaeton |    1.43 | energy fit (0.88 vs target 0.90, +0.98) |
|     |                  |                |           |         | popularity 90/100 (+0.45)               |
+-----+------------------+----------------+-----------+---------+-----------------------------------------+
|   3 | Bass Cathedral   | DJ Nova        | edm       |    1.40 | energy fit (0.96 vs target 0.90, +0.94) |
|     |                  |                |           |         | popularity 92/100 (+0.46)               |
+-----+------------------+----------------+-----------+---------+-----------------------------------------+
|   4 | Gym Hero         | Max Pulse      | pop       |    1.40 | energy fit (0.93 vs target 0.90, +0.97) |
+-----+------------------+----------------+-----------+---------+-----------------------------------------+
|   5 | Golden Hour Slow | Marigold Tape  | soul      |    1.38 | energy fit (0.44 vs target 0.90, +0.54) |
|     |                  |                |           |         | acoustic vibe (+0.5)                    |
+-----+------------------+----------------+-----------+---------+-----------------------------------------+
```

**Comparing the outputs:**

- **Pop fan vs. Lofi studier:** the lists share zero songs. The pop fan's list is all energy 0.76–0.96 dance-adjacent tracks; the studier's is energy 0.28–0.52 with the acoustic bonus firing on four of five. That's exactly what the profiles test for — the energy *closeness* rule is steering, not just genre labels.
- **Lofi studier vs. Rock head:** both lists are dominated by their genre at #1, but the rock list degrades more gracefully — with only one true "rock" song in the catalog, mood=intense and 2010s-era matches pull in metal and synthwave neighbors. Makes sense: when the genre signal runs out, the secondary weights take over.
- **Rock head vs. Adversarial:** Iron Bloom appears in both, but for different reasons — the rock head gets it via mood+energy, the conflicted user via the genre label alone. And below #1 the adversarial list collapses into pure popularity/energy picks (party tracks for a "sad" user), which is the mood-vocabulary blind spot in action.
- **What surprised me:** Gym Hero showed up in *three* of four lists (pop, rock, adversarial). It's the catalog's stealth over-recommendation — high energy + high popularity + "intense" mood makes it score decently for almost everyone, a mini version of how one viral song colonizes everyone's real-world recommendations.

I also ran a weight-shift experiment (`genre_first` vs `energy_focused` on the same user — details in the README): same person, visibly different list, so the weights are as much of an editorial choice as the data.

---

## 8. Future Work

1. **Handle vocabulary gaps honestly** — if a requested mood/genre has zero matches in the catalog, say so (or fall back to mood *tags*) instead of silently recommending party music to sad users.
2. **Learn weights from feedback** — simulate likes/skips and nudge the weights up or down instead of me hand-picking 2.0 vs 1.0.
3. **Genre similarity instead of string matching** — a tiny genre-relatedness map (lofi ≈ ambient ≈ jazz) so neighbors score partial credit by design, not by substring luck.

---

## 9. Personal Reflection

My biggest learning moment was the adversarial profile. I expected "conflicting preferences" to produce weird scores; instead it produced *confident* scores for the wrong songs, because a preference the data can't express just silently disappears from the math. That reframed how I think about Spotify recommendations that feel "off" — the system probably isn't wrong about the songs, it's blind to a dimension of what I asked for.

AI tools were genuinely useful and genuinely fallible in the same session. The assistant generated my 12 extra songs and the strategy-pattern refactor quickly, but I caught it once suggesting a genre bonus proportional to song energy (which would have broken the closeness principle) and its first CSV draft reused a duplicate id — both caught by actually running the code and reading the output, not by trusting the diff. What surprised me most is how little machinery it takes for output to *feel* personalized: score, sort, top-k, plus a reasons column, and suddenly it reads like taste. If I extended this, I'd add the simulated feedback loop first — that's the piece that separates my static scorecard from a system that actually learns you.
