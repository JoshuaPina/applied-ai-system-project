from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from src.recommender import load_songs, recommend_songs

OUTPUT_DIR = Path("artifacts/adversarial_profiles")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

profiles = {
    "Case-Sensitivity Attack": {
        "genre": "Pop",
        "mood": "HAPPY",
        "energy": 0.90,
        "likes_acoustic": False,
    },
    "Out-of-Range Energy High": {
        "genre": "pop",
        "mood": "happy",
        "energy": 2.50,
        "likes_acoustic": False,
    },
    "Out-of-Range Energy Low": {
        "genre": "rock",
        "mood": "intense",
        "energy": -1.20,
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


def slugify(name: str) -> str:
    return (
        name.lower()
        .replace("+", "plus")
        .replace("/", "-")
        .replace("(", "")
        .replace(")", "")
        .replace(" ", "-")
    )


def render_profile(name: str, prefs: dict, songs: list[dict]) -> str:
    console = Console(record=True, width=120)

    recommendations = recommend_songs(prefs, songs, k=5)

    console.rule(f"Adversarial Profile: {name}", style="bright_blue")
    console.print(f"Input preferences: {prefs}", style="cyan")

    table = Table(show_header=True, header_style="bold magenta", expand=True)
    table.add_column("Rank", justify="right", style="bold cyan", width=6)
    table.add_column("Title", style="white", min_width=22)
    table.add_column("Score", justify="right")
    table.add_column("Reasons", style="white")

    for i, (song, score, explanation) in enumerate(recommendations, start=1):
        reasons = "\n".join(
            f"- {part.strip()}" for part in explanation.split(";") if part.strip()
        )
        table.add_row(str(i), song["title"], f"{score:.2f}", reasons)

    console.print(
        Panel.fit(
            f"Top 5 recommendations for: {name}",
            style="cyan",
            border_style="bright_blue",
        )
    )
    console.print(table)

    out_path = OUTPUT_DIR / f"{slugify(name)}.svg"
    out_path.write_text(console.export_svg(title=name), encoding="utf-8")

    return str(out_path)


def main() -> None:
    songs = load_songs("data/songs.csv")
    summary = []

    for name, prefs in profiles.items():
        out_file = render_profile(name, prefs, songs)
        summary.append((name, out_file))

    print("Generated adversarial profile screenshots:")
    for name, out_file in summary:
        print(f"- {name}: {out_file}")


if __name__ == "__main__":
    main()
