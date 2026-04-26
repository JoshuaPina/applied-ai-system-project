# 🎧 Model Card: Chune-Boost v1.0.1

## 1. Model Name
Chune-Boost v1.0.1

---

## 2. Goal / Task
This model suggests songs from a small catalog.
It tries to find songs that match a user's genre, mood, energy, and acoustic preference.

---

## 3. Data Used
The dataset has 20 songs in `songs.csv`.
Each song has features like genre, mood, energy, tempo, valence, danceability, and acousticness.
The data is small, so results can repeat often.
The data also does not include lyrics, language, or real listening history.

---

## 4. Algorithm Summary
Each song gets points for matching user preferences.
Genre and mood give strong bonus points when they match exactly.
Energy gives more points when the song energy is close to the target energy.
Acousticness gives points based on whether the user wants more acoustic or less acoustic songs.
Songs are sorted by total score, then the top songs are returned.

---

## 5. Observed Behavior / Biases
The model can create a filter bubble because exact matches get rewarded a lot.
If a user types `Pop` instead of `pop`, genre matching can fail because matching is case-sensitive.
Out-of-range energy values still run, which can create odd rankings.
Because the catalog is small, some songs appear across many profiles.

---

## 6. Evaluation Process
I tested these profiles: High-Energy Pop, Chill Lofi, and Deep Intense Rock.
I compared top-5 results to my own music intuition.
I also ran a sensitivity experiment by halving genre weight and doubling energy weight.
That change made energy matter more and reordered some songs.
Example: for High-Energy Pop, Rooftop Lights moved above Gym Hero after the weight shift.

---

## 7. Intended Use and Non-Intended Use
Intended use: classroom learning and simple demos of recommendation logic.
Intended use: showing how weighted scoring affects outputs.
Non-intended use: real production music apps.
Non-intended use: decisions that require fairness, personalization history, or user safety controls.

---

## 8. Ideas for Improvement
Add input normalization (like lowercasing genre and mood).
Add input validation for energy range (0.0 to 1.0).
Add diversity rules so top results are not too similar.

---

## 9. Personal Reflection
My biggest learning moment was seeing how small weight changes can move songs up or down quickly.
AI tools helped me move faster when creating test profiles and explaining ranking behavior.
I still had to double-check outputs because AI suggestions can sound correct but miss edge cases.
I was surprised that a simple scoring formula can still feel like a real recommender to a user.
If I extend this project, I want to add user feedback so the model can learn over time.
