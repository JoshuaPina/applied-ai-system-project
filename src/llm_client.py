"""
LLM Client for generating personalized song recommendations.

Supports both offline (MockClient) and online modes (OpenAI, Gemini).
Includes error handling and fallback logic for reliability.
"""

import os
import json
import logging
from typing import Optional, Dict, Any
from datetime import datetime


logger = logging.getLogger(__name__)


class MockClient:
    """
    Offline mock LLM for demos and testing without API keys.
    Returns plausible but templated explanations.
    """

    def __init__(self):
        self.model_name = "mock"
        logger.info("Initialized MockClient (offline mode)")

    def complete(self, system_prompt: str, user_prompt: str) -> str:
        """
        Returns a mock explanation based on detected keywords.
        """
        if "genre" in user_prompt.lower() and "mood" in user_prompt.lower():
            return (
                "These songs match your taste profile because they share your preferred genre and mood. "
                "They also have similar energy and acoustic characteristics to what you're looking for. "
                "Combined, these factors make them strong recommendations."
            )
        elif "adversarial" in user_prompt.lower():
            return (
                "This profile tests edge cases in the recommendation system. "
                "The system handles it by falling back to numeric features when categorical matches fail."
            )
        else:
            return (
                "The recommender selected these songs based on weighted feature matching. "
                "Genre and mood preferences are the strongest signals, followed by energy and acousticness."
            )


class OpenAIClient:
    """
    OpenAI API client for LLM-powered explanations.

    Requirements:
    - openai library installed
    - OPENAI_API_KEY set in environment
    """

    def __init__(
        self,
        model_name: str = "gpt-4o-mini",
        temperature: float = 0.7,
        max_tokens: int = 300,
    ):
        api_key = os.getenv("OPENAI_API_KEY", "").strip()
        if not api_key:
            raise RuntimeError(
                "Missing OPENAI_API_KEY. Set it in your .env file or environment."
            )

        try:
            from openai import OpenAI
        except ImportError:
            raise RuntimeError(
                "openai library not installed. Run: pip install openai"
            )

        self.client = OpenAI(api_key=api_key)
        self.model_name = model_name
        self.temperature = float(temperature)
        self.max_tokens = max_tokens
        logger.info(f"Initialized OpenAIClient with model {model_name}")

    def complete(self, system_prompt: str, user_prompt: str) -> str:
        """
        Sends a request to OpenAI.
        Returns empty string on failure (triggers fallback logic).
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens,
            )

            result = response.choices[0].message.content or ""
            logger.debug(f"OpenAI response: {result[:100]}...")
            return result

        except Exception as e:
            logger.warning(f"OpenAI API error: {e}")
            return ""


class GeminiClient:
    """
    Google Gemini API client for LLM-powered explanations.

    Requirements:
    - google-genai library installed
    - GEMINI_API_KEY set in environment
    """

    def __init__(
        self,
        model_name: str = "gemini-2.0-flash",
        temperature: float = 0.7,
    ):
        api_key = os.getenv("GEMINI_API_KEY", "").strip()
        if not api_key:
            raise RuntimeError(
                "Missing GEMINI_API_KEY. Set it in your .env file or environment."
            )

        try:
            import google.genai as genai
        except ImportError:
            raise RuntimeError(
                "google-genai library not installed. Run: pip install google-genai"
            )

        genai.configure(api_key=api_key)
        self.model_name = model_name
        self.temperature = float(temperature)
        self.client = genai.GenerativeModel(model_name, generation_config={"temperature": temperature})
        logger.info(f"Initialized GeminiClient with model {model_name}")

    def complete(self, system_prompt: str, user_prompt: str) -> str:
        """
        Sends a request to Gemini.
        Returns empty string on failure (triggers fallback logic).
        """
        try:
            merged_prompt = f"{system_prompt}\n\n{user_prompt}".strip()
            response = self.client.generate_content(merged_prompt)
            result = response.text or ""
            logger.debug(f"Gemini response: {result[:100]}...")
            return result

        except Exception as e:
            logger.warning(f"Gemini API error: {e}")
            return ""


class LLMExplainer:
    """
    Wraps LLM client with system prompts and fallback logic.
    Logs all LLM calls for debugging and reliability analysis.
    """

    def __init__(self, client):
        self.client = client
        self.call_log = []

    def explain_recommendations(
        self,
        user_prefs: Dict[str, Any],
        recommendations: list,
        use_mock: bool = False,
    ) -> str:
        """
        Generate a personalized explanation for why these songs are recommended.

        Args:
            user_prefs: User preference dictionary
            recommendations: List of (song, score, explanation) tuples
            use_mock: If True, force MockClient regardless of configured client

        Returns:
            Natural language explanation of recommendations
        """
        client = MockClient() if use_mock else self.client

        system_prompt = (
            "You are a friendly music recommendation expert. "
            "Explain in 2-3 sentences why the given recommendations match the user's taste. "
            "Be specific about how their preferences (genre, mood, energy, acousticness) align with the songs. "
            "Keep explanations concise and personable."
        )

        song_list = "\n".join(
            [f"  {i + 1}. {song['title']} by {song['artist']} (score: {score:.2f})"
             for i, (song, score, _) in enumerate(recommendations[:5])]
        )

        user_prompt = (
            f"User preferences:\n"
            f"  - Favorite genre: {user_prefs.get('genre', 'N/A')}\n"
            f"  - Favorite mood: {user_prefs.get('mood', 'N/A')}\n"
            f"  - Target energy: {user_prefs.get('energy', 'N/A')}\n"
            f"  - Likes acoustic: {user_prefs.get('likes_acoustic', 'N/A')}\n\n"
            f"Top 5 recommendations:\n{song_list}\n\n"
            f"Why should they listen to these?"
        )

        # Log the call
        call_entry = {
            "timestamp": datetime.now().isoformat(),
            "client": client.model_name if hasattr(client, "model_name") else "unknown",
            "user_prefs": user_prefs,
            "num_recommendations": len(recommendations),
        }

        # Get response
        response = client.complete(system_prompt, user_prompt)

        # Fallback to heuristic if LLM fails
        if not response.strip():
            logger.info("LLM returned empty response, using heuristic fallback")
            response = self._fallback_explanation(user_prefs, recommendations)
            call_entry["used_fallback"] = True
        else:
            call_entry["used_fallback"] = False

        call_entry["response_length"] = len(response)
        self.call_log.append(call_entry)

        return response

    def _fallback_explanation(self, user_prefs: Dict, recommendations: list) -> str:
        """
        Heuristic fallback when LLM unavailable.
        """
        genre = user_prefs.get("genre", "your favorite genre")
        mood = user_prefs.get("mood", "your mood")
        energy = user_prefs.get("energy", 0.5)

        if recommendations:
            top_song = recommendations[0][0]["title"]
            return (
                f"These recommendations match your taste for {genre} music with a {mood} vibe. "
                f"Top pick '{top_song}' especially aligns with your energy preference ({energy:.1f}). "
                f"Explore these songs based on feature similarity to your profile."
            )
        return (
            f"Your taste profile prefers {genre} genre and {mood} mood. "
            "The recommender scored each song based on how closely it matches these preferences."
        )

    def get_call_log(self) -> list:
        """Return log of all LLM calls for debugging."""
        return self.call_log
