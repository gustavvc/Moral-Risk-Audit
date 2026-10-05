"""OpenAI-backed analysis routines used by the Streamlit application."""

import json
from collections.abc import Sequence

import streamlit as st
from openai import OpenAI, OpenAIError

from config import (
    CHAT_MODERATOR_NAME,
    CHAT_TARGET_ALL,
    CHAT_TARGET_OPPONENT,
    CHAT_TARGET_PRIMARY,
    MODEL,
    MODEL_TEMPERATURE,
    PHILOSOPHER_ALIASES,
    PHILOSOPHER_FRAMEWORKS,
)
from prompts import (
    ChatMessage,
    PhenomenonChatTurn,
    build_phenomenon_explanation_prompt,
    build_phenomenon_followup_prompt,
    build_phenomenon_moderator_prompt,
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
    if not response.choices:
        raise ValueError("OpenAI lieferte keine Antwortauswahl.")
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
    if not response.choices:
        raise ValueError("OpenAI lieferte keine Antwortauswahl.")
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
    required_routing_fields = {"primary_philosopher", "opponent_philosopher"}
    if not required_routing_fields.issubset(routing):
        raise ValueError("Das philosophische Routing lieferte ein ungültiges JSON-Format.")

    primary_name = routing.get("primary_philosopher")
    opponent_name = routing.get("opponent_philosopher")
    valid_names = set(PHILOSOPHER_FRAMEWORKS)
    if isinstance(primary_name, str):
        primary_name = _canonical_philosopher_name(primary_name, valid_names)
    if isinstance(opponent_name, str):
        opponent_name = _canonical_philosopher_name(opponent_name, valid_names)
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
    st.session_state["current_hauptdenker"] = primary_name
    st.session_state["current_kontrahent"] = opponent_name
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
    target: str = CHAT_TARGET_ALL,
    history: Sequence[PhenomenonChatTurn] = (),
    client: OpenAI | None = None,
) -> dict[str, str]:
    """Return the selected thinker replies and, for all, a dialectical synthesis."""
    cleaned_question = question.strip()
    if not cleaned_question:
        raise ValueError("Bitte gib eine Rückfrage ein.")
    if target not in {CHAT_TARGET_PRIMARY, CHAT_TARGET_OPPONENT, CHAT_TARGET_ALL}:
        raise ValueError("Unbekanntes Antwortziel für den Phänomen-Dialog.")
    active_client = _get_client(client)
    results: dict[str, str] = {}
    responders: tuple[tuple[str, str, str], ...]
    if target == CHAT_TARGET_PRIMARY:
        responders = ((primary_name, "primary", primary_explanation),)
    elif target == CHAT_TARGET_OPPONENT:
        responders = ((opponent_name, "opponent", opponent_explanation),)
    else:
        responders = (
            (primary_name, "primary", primary_explanation),
            (opponent_name, "opponent", opponent_explanation),
        )

    for name, role, explanation in responders:
        if target == CHAT_TARGET_ALL:
            persona_history = history
            context_opponent_name = (
                opponent_name if name == primary_name else primary_name
            )
            context_opponent_explanation = (
                opponent_explanation if name == primary_name else primary_explanation
            )
        else:
            own_response_key = (
                "primary_response" if role == "primary" else "opponent_response"
            )
            persona_history = tuple(
                {
                    "question": turn["question"],
                    "primary_response": (
                        turn.get(own_response_key) if role == "primary" else None
                    ),
                    "opponent_response": (
                        turn.get(own_response_key) if role == "opponent" else None
                    ),
                    "moderator_response": None,
                }
                for turn in history
            )
            context_opponent_name = ""
            context_opponent_explanation = ""
        messages = build_phenomenon_followup_prompt(
            name,
            concept,
            role,
            explanation,
            cleaned_question,
            persona_history,
            opponent_name=context_opponent_name,
            opponent_explanation=context_opponent_explanation,
        )
        results[name] = _request_text(active_client, messages)

    if target == CHAT_TARGET_ALL:
        moderator_messages = build_phenomenon_moderator_prompt(
            primary_name=primary_name,
            opponent_name=opponent_name,
            concept=concept,
            primary_explanation=primary_explanation,
            opponent_explanation=opponent_explanation,
            question=cleaned_question,
            primary_response=results[primary_name],
            opponent_response=results[opponent_name],
            history=history,
        )
        results[CHAT_MODERATOR_NAME] = _request_text(
            active_client, moderator_messages
        )
    return results


def _canonical_philosopher_name(
    value: str,
    valid_names: set[str],
) -> str | None:
    """Resolve case and incidental surrounding whitespace in routed names."""
    cleaned = value.strip()
    canonical = next(
        (name for name in valid_names if name.casefold() == cleaned.casefold()),
        None,
    )
    if canonical is not None:
        return canonical
    alias_target = PHILOSOPHER_ALIASES.get(cleaned)
    if alias_target is not None and alias_target in valid_names:
        return alias_target
    return None


__all__ = [
    "OpenAIError",
    "analyze_phenomenon",
    "answer_phenomenon_followup",
    "request_json",
]
