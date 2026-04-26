from pathlib import Path
import sys

if __package__ in {None, ""}:
    sys.path.append(str(Path(__file__).resolve().parents[2]))

from src.recommender import load_songs, recommend_songs

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SONGS_PATH = PROJECT_ROOT / 'data' / 'songs.csv'

songs = load_songs(str(SONGS_PATH))
profiles = {
    'High-Energy Pop': {'genre':'pop','mood':'happy','energy':0.9,'likes_acoustic':False},
    'Chill Lofi': {'genre':'lofi','mood':'chill','energy':0.35,'likes_acoustic':True},
    'Deep Intense Rock': {'genre':'rock','mood':'intense','energy':0.92,'likes_acoustic':False},
}

for name, prefs in profiles.items():
    print(f'PROFILE: {name}')
    recs = recommend_songs(prefs, songs, k=5)
    for i, (song, score, explanation) in enumerate(recs, 1):
        print(f'  {i}. {song["title"]} | {score:.2f} | {explanation}')
    print()
