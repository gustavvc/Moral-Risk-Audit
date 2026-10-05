"""OpenAI-backed analysis routines used by the Streamlit application."""

import json
from collections.abc import Sequence

import streamlit as st
from openai import OpenAI, OpenAIError

from config import MODEL, MODEL_TEMPERATURE, PHILOSOPHER_FRAMEWORKS
from prompts import (
    ChatMessage,
    PhenomenonChatTurn,
    build_phenomenon_explanation_prompt,
    build_phenomenon_followup_prompt,
    build_phenomenon_routing_prompt,
)


def _get_client(client: OpenAI | None = None) -> OpenAI:
    if client is not None:
        return client
    api_key = st.secrets.get("OPENAI_API_KEY")
    if not api_key:
        raise ValueError(
            "OPENAI_API_KEY fehlt in den Streamlit-Secrets. "
            "Hinterlege den Schlüssel unter [secrets]."
        )
    return OpenAI(api_key=api_key)


def request_json(
    client: OpenAI,
    prompt: str,
    system_prompt: str,
) -> dict[str, object]:
    """Send a JSON-mode chat completion at the app's standard temperature."""
    response = client.chat.completions.create(
        model=MODEL,
        temperature=MODEL_TEMPERATURE,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ],
        response_format={"type": "json_object"},
    )
    content = response.choices[0].message.content
    if not content:
        raise ValueError("OpenAI lieferte eine leere Antwort.")
    result = json.loads(content)
    if not isinstance(result, dict):
        raise ValueError("Die OpenAI-Antwort ist kein JSON-Objekt.")
    return result


def _request_text(
    client: OpenAI,
    messages: Sequence[ChatMessage],
) -> str:
    response = client.chat.completions.create(
        model=MODEL,
        temperature=MODEL_TEMPERATURE,
        messages=list(messages),
    )
    content = response.choices[0].message.content
    if not content or not content.strip():
        raise ValueError("OpenAI lieferte eine leere Erklärung.")
    return content.strip()


def analyze_phenomenon(
    concept: str,
    client: OpenAI | None = None,
) -> dict[str, str]:
    """Route a concept and return the primary explanation and opposing critique."""
    cleaned_concept = concept.strip()
    if not cleaned_concept:
        raise ValueError("Bitte gib einen Begriff oder ein Phänomen ein.")
    active_client = _get_client(client)
    routing_prompt = build_phenomenon_routing_prompt(cleaned_concept)
    routing = request_json(
        active_client,
        routing_prompt["user_prompt"],
        routing_prompt["system_prompt"],
    )
    if set(routing) != {"primary_philosopher", "opponent_philosopher"}:
        raise ValueError("Das philosophische Routing lieferte ein ungültiges JSON-Format.")

    primary_name = routing.get("primary_philosopher")
    opponent_name = routing.get("opponent_philosopher")
    valid_names = set(PHILOSOPHER_FRAMEWORKS)
    if (
        not isinstance(primary_name, str)
        or not isinstance(opponent_name, str)
        or primary_name not in valid_names
        or opponent_name not in valid_names
        or primary_name == opponent_name
    ):
        raise ValueError(
            "Das Routing muss zwei verschiedene Denker aus der verfügbaren Liste nennen."
        )

    primary_messages = build_phenomenon_explanation_prompt(
        primary_name, cleaned_concept, "primary"
    )
    opponent_messages = build_phenomenon_explanation_prompt(
        opponent_name, cleaned_concept, "opponent"
    )
    primary_explanation = _request_text(active_client, primary_messages)
    opponent_explanation = _request_text(active_client, opponent_messages)
    return {
        "concept": cleaned_concept,
        "primary_philosopher": primary_name,
        "opponent_philosopher": opponent_name,
        "primary_explanation": primary_explanation,
        "opponent_explanation": opponent_explanation,
    }


def answer_phenomenon_followup(
    concept: str,
    primary_name: str,
    opponent_name: str,
    primary_explanation: str,
    opponent_explanation: str,
    question: str,
    history: Sequence[PhenomenonChatTurn] = (),
    client: OpenAI | None = None,
) -> dict[str, str]:
    """Ask both philosophers to address the same follow-up independently."""
    cleaned_question = question.strip()
    if not cleaned_question:
        raise ValueError("Bitte gib eine Rückfrage ein.")
    active_client = _get_client(client)
    results: dict[str, str] = {}
    for name, role, explanation in (
        (primary_name, "primary", primary_explanation),
        (opponent_name, "opponent", opponent_explanation),
    ):
        messages = build_phenomenon_followup_prompt(
            name, concept, role, explanation, cleaned_question, history
        )
        results[name] = _request_text(active_client, messages)
    return results


__all__ = [
    "OpenAIError",
    "analyze_phenomenon",
    "answer_phenomenon_followup",
    "request_json",
]
