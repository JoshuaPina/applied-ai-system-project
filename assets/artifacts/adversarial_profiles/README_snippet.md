## Adversarial and Edge-Case Profile Runs

These profiles were designed to stress-test the scoring logic and surface unexpected behavior.

### 1) Case-Sensitivity Attack
Input: genre=Pop, mood=HAPPY, energy=0.90, likes_acoustic=False

![Case-Sensitivity Attack](case-sensitivity-attack.svg)

### 2) Out-of-Range Energy High
Input: genre=pop, mood=happy, energy=2.50, likes_acoustic=False

![Out-of-Range Energy High](out-of-range-energy-high.svg)

### 3) Out-of-Range Energy Low
Input: genre=rock, mood=intense, energy=-1.20, likes_acoustic=True

![Out-of-Range Energy Low](out-of-range-energy-low.svg)

### 4) Unknown Labels + Numeric Only
Input: genre=nonexistent-genre, mood=nonexistent-mood, energy=0.55, likes_acoustic=True

![Unknown Labels + Numeric Only](unknown-labels-plus-numeric-only.svg)

### 5) Sparse Profile (No Genre/Mood)
Input: energy=0.80, likes_acoustic=False

![Sparse Profile](sparse-profile-no-genre-mood.svg)
