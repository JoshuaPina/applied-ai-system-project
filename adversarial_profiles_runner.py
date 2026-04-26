from src.recommender import load_songs, recommend_songs

songs = load_songs('data/songs.csv')

profiles = {
    "Case-Sensitivity Attack": {
        "genre": "Pop",  # intentionally different case
        "mood": "HAPPY",  # intentionally different case
        "energy": 0.90,
        "likes_acoustic": False,
    },
    "Out-of-Range Energy High": {
        "genre": "pop",
        "mood": "happy",
        "energy": 2.50,  # invalid high target
        "likes_acoustic": False,
    },
    "Out-of-Range Energy Low": {
        "genre": "rock",
        "mood": "intense",
        "energy": -1.20,  # invalid low target
        "likes_acoustic": True,
    },
    "Unknown Labels + Numeric Only": {
        "genre": "nonexistent-genre",
        "mood": "nonexistent-mood",
        "energy": 0.55,
        "likes_acoustic": True,
    },
    "Sparse Profile (No Genre/Mood)": {
        "energy": 0.80,
        "likes_acoustic": False,
    },
}

sep = "=" * 90

with open('adversarial_profile_results.txt', 'w', encoding='utf-8') as out:
    out.write('ADVERSARIAL / EDGE-CASE PROFILE RESULTS\\n')
    out.write(sep + '\\n\\n')

    for name, prefs in profiles.items():
        recs = recommend_songs(prefs, songs, k=5)

        out.write(f'PROFILE: {name}\\n')
        out.write(f'INPUT PREFS: {prefs}\\n')
        out.write('-' * 90 + '\\n')
        out.write(f"{'Rank':<6} {'Title':<30} {'Score':>8}  Reason Preview\\n")
        out.write('-' * 90 + '\\n')

        for i, (song, score, explanation) in enumerate(recs, start=1):
            reason_preview = explanation.split(';')[0].strip()
            out.write(f"{i:<6} {song['title'][:30]:<30} {score:>8.2f}  {reason_preview}\\n")

        out.write('\\nTop-5 detailed explanations:\\n')
        for i, (song, score, explanation) in enumerate(recs, start=1):
            out.write(f"{i}. {song['title']} ({score:.2f})\\n")
            out.write(f"   {explanation}\\n")

        out.write('\\n' + sep + '\\n\\n')

print('Wrote adversarial_profile_results.txt')
