# AI Interactions Log

> **Stretch features only.** Only fill in the sections that apply to stretch features you attempted. If you did not attempt a stretch feature, leave its section blank or delete it. This file is not required for the core project.

---

## Agentic Workflow (SF8)

> Document your experience using an AI agent (e.g., Cursor Agent, Claude, Copilot) to make multi-step changes autonomously.

**What task did you give the agent?**

Expand the dataset from 10 songs / 10 columns to 20+ songs / 15 columns, and wire the 5 new attributes (`popularity`, `release_decade`, `mood_tags`, `instrumentalness`, `explicit`) all the way through the pipeline: CSV → `load_songs()` type conversion → `score_song()` rules → the printed reasons. I wanted one agentic pass rather than editing three files by hand and hoping they stayed consistent.

**Prompts used:**

> "Here's my songs.csv. Add 5 new columns — popularity (0-100 int), release_decade (int like 2010), mood_tags (semicolon-separated detailed tags like 'euphoric;summery'), instrumentalness (0.0-1.0), explicit (yes/no) — fill them in for the existing 10 songs, then add 12 new songs covering genres I don't have yet (hip-hop, EDM, country, classical, metal, r&b, folk, reggaeton, punk, soul). Keep the CSV valid with the exact same header order everywhere."

> "Now update load_songs to convert the new columns to real types (mood_tags should become a list, explicit a bool), and add scoring rules: popularity/100 as a small nudge worth up to 0.5, +0.5 for a decade match, +0.25 per overlapping mood tag capped at 2 tags, and a -2.0 penalty on explicit songs when the user sets allow_explicit=False. Each new rule needs to append to the reasons list like the existing ones."

**What did the agent generate or change?**

- `data/songs.csv`: 12 new rows + 5 new columns on all 22 rows.
- `src/recommender.py`: type conversions in `load_songs()` (int/float casts, `split(";")` for tags, yes→bool for explicit), a `_stretch_points()` helper with the four new rules, new keys in every `SCORING_MODES` weight dict, and matching defaults on the `Song` dataclass so the starter tests kept passing.

**What did you verify or fix manually?**

- The first CSV draft **reused id 11 twice** — caught it because my diversity re-pick removes songs by id, so a duplicate would have made one pick disappear. Renumbered by hand.
- Checked every 0–1 column actually stayed in range and that `explicit` was only yes/no (a stray "true" would have silently become `False` with my `== "yes"` check).
- Re-ran `python -m src.main` and confirmed "Loaded songs: 22", and re-ran `pytest` to confirm the old `Song(...)` constructor calls in the tests still worked thanks to the default values.
- Rejected one agent suggestion: it initially proposed scaling the genre bonus by the song's energy, which would have broken my "closeness, not more-is-better" principle. Kept the rules independent instead.

---

## Design Pattern (SF10)

> Document how AI helped you choose or implement a design pattern.

**Which design pattern did you use?**

Strategy pattern — implemented lightweight, as a dictionary of named weight configurations (`SCORING_MODES`) rather than a class hierarchy.

**How did AI help you brainstorm or implement it?**

I asked: *"I want genre-first, mood-first, and energy-focused ranking modes the user can switch in main.py. What design pattern keeps this modular without me writing three nearly-identical scoring functions?"* The AI suggested the Strategy pattern and showed two versions: the classic one (an abstract `ScoringStrategy` class with subclasses) and a Pythonic one (strategies as data — a dict of weight dicts passed into one scoring function). It made the point that since all my strategies share the exact same *rules* and only differ in *weights*, the data version avoids duplicating the rule logic three times. I picked that one; the class version felt like Java cosplay for what is genuinely just four dictionaries.

**How does the pattern appear in your final code?**

`SCORING_MODES` at the top of `src/recommender.py` holds four named weight dicts (`balanced`, `genre_first`, `mood_first`, `energy_focused`). `score_song(user_prefs, song, weights)` is the single algorithm that any strategy plugs into, and `recommend_songs(..., mode="balanced")` selects the strategy by name. Switching modes in `src/main.py` is changing the `MODE` constant (and the demo at the bottom of `main()` runs the same user through two modes back-to-back to show the lists actually change).
