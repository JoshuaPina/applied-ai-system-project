from __future__ import annotations

import json
from pathlib import Path
import sys
from typing import Any, Dict, List

if __package__ in {None, ""}:
    sys.path.append(str(Path(__file__).resolve().parents[2]))

from src.recommender import load_songs, recommend_songs
from src.reliability import check_consistency, run_adversarial_profiles
from src.llm_client import LLMExplainer, MockClient


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SONGS_PATH = PROJECT_ROOT / "data" / "songs.csv"
REPORT_PATH = PROJECT_ROOT / "assets" / "results" / "evaluation_harness_report.json"


PROFILE_CASES: List[Dict[str, Any]] = [
    {
        "name": "pop-happy-high-energy",
        "prefs": {
            "genre": "pop",
            "mood": "happy",
            "energy": 0.82,
            "likes_acoustic": False,
        },
        "k": 5,
    },
    {
        "name": "lofi-chill-acoustic",
        "prefs": {
            "genre": "lofi",
            "mood": "chill",
            "energy": 0.35,
            "likes_acoustic": True,
        },
        "k": 5,
    },
    {
        "name": "unknown-labels-numeric-only",
        "prefs": {
            "genre": "nonexistent-genre",
            "mood": "nonexistent-mood",
            "energy": 0.55,
            "likes_acoustic": True,
        },
        "k": 5,
    },
]


def clamp(value: float, min_value: float = 0.0, max_value: float = 1.0) -> float:
    return max(min_value, min(max_value, value))


def confidence_from_scores(scores: List[float]) -> float:
    if not scores:
        return 0.0

    top_score = float(scores[0])
    second_score = float(scores[1]) if len(scores) > 1 else float(scores[0])

    normalized_strength = clamp(top_score / 16.0)
    normalized_margin = clamp((top_score - second_score) / 4.0)

    return round(0.65 * normalized_strength + 0.35 * normalized_margin, 3)


def evaluate_profile_case(songs: List[Dict[str, Any]], case: Dict[str, Any], explainer: LLMExplainer) -> Dict[str, Any]:
    prefs = case["prefs"]
    k = int(case.get("k", 5))

    recs = recommend_songs(prefs, songs, k=k)
    scores = [float(score) for _, score, _ in recs]
    confidence = confidence_from_scores(scores)

    generated_explanation = explainer.explain_recommendations(prefs, recs, use_mock=True)

    checks = {
        "returns_k_recommendations": len(recs) == k,
        "scores_sorted_desc": scores == sorted(scores, reverse=True),
        "top_score_positive": (scores[0] if scores else 0.0) > 0.0,
        "llm_explanation_non_empty": bool(generated_explanation.strip()),
        "confidence_in_range": 0.0 <= confidence <= 1.0,
    }

    passed = all(checks.values())

    return {
        "name": case["name"],
        "passed": passed,
        "checks": checks,
        "top_song": recs[0][0]["title"] if recs else None,
        "top_score": round(scores[0], 3) if scores else 0.0,
        "confidence": confidence,
    }


def run_harness() -> Dict[str, Any]:
    songs = load_songs(str(SONGS_PATH))
    explainer = LLMExplainer(MockClient())

    profile_results = [evaluate_profile_case(songs, case, explainer) for case in PROFILE_CASES]

    reliability_checks = {
        "consistency_ge_0_95": check_consistency(
            songs,
            {"genre": "pop", "mood": "happy", "energy": 0.7, "likes_acoustic": False},
            num_runs=10,
        ) >= 0.95,
        "adversarial_profiles_all_success": all(
            result.get("status") == "success"
            for result in run_adversarial_profiles(songs).values()
        ),
    }

    reliability_result = {
        "checks": reliability_checks,
        "passed": all(reliability_checks.values()),
    }

    all_test_units = [item["passed"] for item in profile_results] + [reliability_result["passed"]]
    passed_count = sum(1 for status in all_test_units if status)
    total_count = len(all_test_units)

    avg_confidence = round(
        sum(item["confidence"] for item in profile_results) / len(profile_results),
        3,
    )

    summary = {
        "passed": passed_count,
        "total": total_count,
        "pass_rate": round(passed_count / total_count, 3) if total_count else 0.0,
        "avg_confidence": avg_confidence,
    }

    report = {
        "summary": summary,
        "profiles": profile_results,
        "reliability": reliability_result,
        "llm_call_log_entries": len(explainer.get_call_log()),
    }

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")

    return report


def print_report(report: Dict[str, Any]) -> None:
    summary = report["summary"]

    print("=== Evaluation Harness Summary ===")
    print(f"Passed: {summary['passed']}/{summary['total']}")
    print(f"Pass rate: {summary['pass_rate']:.1%}")
    print(f"Average confidence: {summary['avg_confidence']:.3f}")
    print()

    print("Profile checks:")
    for item in report["profiles"]:
        status = "PASS" if item["passed"] else "FAIL"
        print(
            f"- [{status}] {item['name']} | top_song={item['top_song']} "
            f"| top_score={item['top_score']:.3f} | confidence={item['confidence']:.3f}"
        )

    reliability_status = "PASS" if report["reliability"]["passed"] else "FAIL"
    print()
    print(f"Reliability suite: {reliability_status}")
    for check_name, check_status in report["reliability"]["checks"].items():
        label = "PASS" if check_status else "FAIL"
        print(f"- [{label}] {check_name}")

    print()
    print(f"Saved report: {REPORT_PATH}")


if __name__ == "__main__":
    final_report = run_harness()
    print_report(final_report)
