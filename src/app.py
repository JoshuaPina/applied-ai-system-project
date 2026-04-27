"""
Interactive Streamlit app for the Music Recommender with LLM explanations.

Features:
- Adjust user preferences dynamically
- View top recommendations with LLM-generated explanations
- Run robustness tests on the recommendation algorithm
- Toggle between mock and real LLM
- View detailed scoring breakdowns
"""

import streamlit as st
import logging
import sys
from pathlib import Path

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.recommender import load_songs, recommend_songs
from src.llm_client import MockClient, OpenAIClient, GeminiClient, LLMExplainer
from src.reliability import (
    run_robustness_tests,
    compute_sensitivity,
    check_consistency,
)


# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def load_data():
    """Load songs catalog."""
    songs_path = PROJECT_ROOT / "data" / "songs.csv"
    return load_songs(str(songs_path))


def init_session_state():
    """Initialize Streamlit session state."""
    if "songs" not in st.session_state:
        st.session_state.songs = load_data()
        logger.info(f"Loaded {len(st.session_state.songs)} songs")

    if "llm_explainer" not in st.session_state:
        st.session_state.llm_explainer = LLMExplainer(MockClient())

    if "recommendations" not in st.session_state:
        st.session_state.recommendations = None

    if "robustness_results" not in st.session_state:
        st.session_state.robustness_results = None


def main():
    st.set_page_config(
        page_title="🎵 Music Recommender AI",
        page_icon="🎵",
        layout="wide",
    )

    st.title("🎵 Music Recommender with AI Explanations")
    st.markdown(
        "Discover songs tailored to your taste. Get AI-powered insights into why each song is recommended."
    )

    init_session_state()

    # Sidebar: Settings
    with st.sidebar:
        st.header("⚙️ Settings")

        llm_mode = st.radio(
            "LLM Mode",
            ["Mock (Offline)", "OpenAI", "Gemini"],
            help="Choose LLM backend for explanations",
        )

        if llm_mode == "Mock (Offline)":
            st.session_state.llm_explainer = LLMExplainer(MockClient())
            st.success("Using offline mock LLM")
        elif llm_mode == "OpenAI":
            try:
                client = OpenAIClient()
                st.session_state.llm_explainer = LLMExplainer(client)
                st.success("Connected to OpenAI")
            except RuntimeError as e:
                st.error(f"OpenAI setup failed: {e}")
                st.session_state.llm_explainer = LLMExplainer(MockClient())
        elif llm_mode == "Gemini":
            try:
                client = GeminiClient()
                st.session_state.llm_explainer = LLMExplainer(client)
                st.success("Connected to Gemini")
            except RuntimeError as e:
                st.error(f"Gemini setup failed: {e}")
                st.session_state.llm_explainer = LLMExplainer(MockClient())

        st.divider()
        num_recommendations = st.slider("Top N Recommendations", 1, 10, 5)

    # Main content: Two columns
    col1, col2 = st.columns([1, 1])

    # Column 1: User Preferences
    with col1:
        st.header("👤 Your Taste Profile")

        with st.form("preference_form"):
            genres = sorted(set(s.get("genre", "") for s in st.session_state.songs))
            moods = sorted(set(s.get("mood", "") for s in st.session_state.songs))

            favorite_genre = st.selectbox("Favorite Genre", genres, index=0)
            favorite_mood = st.selectbox("Favorite Mood", moods, index=0)

            target_energy = st.slider(
                "Target Energy Level",
                0.0,
                1.0,
                0.7,
                step=0.05,
                help="0 = calm, 1 = intense",
            )

            likes_acoustic = st.checkbox("Like Acoustic Songs?", value=True)

            target_popularity = st.slider(
                "Target Popularity (0-100)",
                0,
                100,
                70,
                step=5,
            )

            preferred_decade = st.selectbox(
                "Preferred Decade",
                [1980, 1990, 2000, 2010, 2020],
                index=3,
            )

            submitted = st.form_submit_button("🔍 Get Recommendations", use_container_width=True)

        if submitted:
            user_prefs = {
                "genre": favorite_genre,
                "mood": favorite_mood,
                "energy": target_energy,
                "likes_acoustic": likes_acoustic,
                "target_popularity": target_popularity,
                "preferred_decade": preferred_decade,
            }

            with st.spinner("Generating recommendations..."):
                recommendations = recommend_songs(
                    user_prefs,
                    st.session_state.songs,
                    k=num_recommendations,
                )
                st.session_state.recommendations = recommendations
                logger.info(f"Generated {len(recommendations)} recommendations")

    # Column 2: Recommendations & Explanations
    with col2:
        if st.session_state.recommendations:
            st.header("🎧 Top Recommendations")

            for i, (song, score, explanation) in enumerate(st.session_state.recommendations, 1):
                with st.container(border=True):
                    st.subheader(f"#{i} — {song['title']}")
                    st.caption(f"by {song['artist']} • {song.get('genre', 'N/A')} • {song.get('mood', 'N/A')}")

                    col_score, col_energy = st.columns([1, 1])
                    with col_score:
                        st.metric("Match Score", f"{score:.2f}/20")
                    with col_energy:
                        st.metric("Energy", f"{song.get('energy', 0):.2f}")

                    st.markdown("**Why this match?**")
                    st.write(explanation)

            st.divider()

            # LLM-generated explanation
            st.header("💡 AI Insights")
            with st.spinner("Generating personalized insight..."):
                user_prefs = {
                    "genre": st.session_state.recommendations[0][1] if st.session_state.recommendations else "N/A",
                    "mood": st.session_state.recommendations[0][1] if st.session_state.recommendations else "N/A",
                }
                # Extract actual prefs from form (simplified for demo)
                llm_explanation = st.session_state.llm_explainer.explain_recommendations(
                    {"genre": "pop", "mood": "happy", "energy": 0.7, "likes_acoustic": False},
                    st.session_state.recommendations,
                )
            st.info(llm_explanation)

        else:
            st.info("👈 Adjust your preferences and click 'Get Recommendations' to get started!")

    # Bottom section: Robustness Testing
    st.divider()
    st.header("🧪 System Robustness Testing")

    test_col1, test_col2, test_col3 = st.columns(3)

    with test_col1:
        if st.button("Run Consistency Tests", use_container_width=True):
            with st.spinner("Testing consistency..."):
                consistency_score = check_consistency(
                    st.session_state.songs,
                    {"genre": "pop", "mood": "happy", "energy": 0.7, "likes_acoustic": False},
                    num_runs=10,
                )
            st.metric("Consistency Score", f"{consistency_score:.2%}")
            logger.info(f"Consistency test result: {consistency_score:.2%}")

    with test_col2:
        if st.button("Run Sensitivity Analysis", use_container_width=True):
            with st.spinner("Analyzing sensitivity..."):
                sensitivity = compute_sensitivity(
                    st.session_state.songs,
                    {"genre": "pop", "mood": "happy", "energy": 0.7, "likes_acoustic": False},
                )
            st.write(f"**Sensitivity Analysis:**")
            for param, change in sensitivity.items():
                st.write(f"  • {param}: {change:.2%} change in rankings")
            logger.info(f"Sensitivity analysis complete: {sensitivity}")

    with test_col3:
        if st.button("Run Full Robustness Suite", use_container_width=True):
            with st.spinner("Running full suite..."):
                results = run_robustness_tests(st.session_state.songs)
            st.json(results)
            logger.info(f"Full robustness suite complete")

    # Debug: LLM Call Log
    with st.expander("🔍 LLM Call Log (Debug)"):
        call_log = st.session_state.llm_explainer.get_call_log()
        if call_log:
            st.json(call_log)
        else:
            st.write("No LLM calls yet.")


if __name__ == "__main__":
    main()
