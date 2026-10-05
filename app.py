import html
import json
from itertools import combinations

import streamlit as st
from openai import OpenAI

from config import (
    CHAT_MODERATOR_NAME,
    CHAT_TARGET_ALL,
    CHAT_TARGET_LABELS,
    CHAT_TARGET_OPPONENT,
    CHAT_TARGET_PRIMARY,
    MODE_DILEMMA,
    MODE_PHENOMENA,
    PHENOMENON_BADGE_CLASSES,
    PHENOMENON_PRESETS,
    PHILOSOPHER_FRAMEWORKS,
    chat_target_label,
)
from prompts import DilemmaChatTurn, PhenomenonChatTurn, build_system_prompt
from utils.llm import (
    OpenAIError,
    answer_dilemma_followup,
    analyze_phenomenon,
    answer_phenomenon_followup,
    request_json,
)
from utils.assets import portrait_data_uri


APP_NAME = "Dialectica AI"
PERSPECTIVE_FIELDS = ("position", "reasoning", "conclusion")
CONSENSUS_FIELDS = ("agreement_score", "conflict_summary", "comparison_matrix")
DILEMMA_ANALYSIS_STATE_KEYS = (
    "debate",
    "debate_selection",
    "debate_dilemma",
    "challenge_responses",
    "dilemma_chat_history",
    "dilemma_chat_target",
    "consensus",
    "consensus_selection",
    "consensus_dilemma",
    "_pending_dilemma",
)
ASSISTANT_CLICHES = (
    "als ki",
    "als künstliche intelligenz",
    "als sprachmodell",
    "hier ist meine analyse",
    "hier ist die analyse",
    "gerne helfe ich",
    "ich kann dir dabei helfen",
)


def reset_dilemma_state(*, clear_input: bool = False) -> None:
    """Clear the active dilemma analysis and its dependent chat state."""
    for key in DILEMMA_ANALYSIS_STATE_KEYS:
        st.session_state.pop(key, None)
    if clear_input:
        st.session_state["dilemma_input"] = ""


PHILOSOPHERS = {
    "Immanuel Kant": {
        "key": "immanuel-kant",
        "school": "Pflichtethik",
        "core_view": "Handle nach verallgemeinerbaren Prinzipien und behandle Menschen stets als Zweck an sich.",
        "portrait": "immanuel-kant.jpg",
        "portrait_source": "https://commons.wikimedia.org/wiki/File:Immanuel_Kant_-_Gemaelde_1.jpg",
        "alt": "Historisches Ölgemälde von Immanuel Kant",
        "voice": "Pflichtbewusst und präzise; prüfe die Maxime auf Allgemeingültigkeit und Menschenwürde.",
        "analysis_lens": "Prüfe die Handlungsmaxime auf widerspruchsfreie Verallgemeinerbarkeit und behandle jede Person als Zweck an sich; eine gute Folge kann eine verbotene Handlung nicht rechtfertigen.",
    },
    "Friedrich Nietzsche": {
        "key": "friedrich-nietzsche",
        "school": "Wille zur Macht",
        "core_view": "Hinterfrage überlieferte Werte und bejahe die schöpferische Selbstgestaltung des Lebens.",
        "portrait": "friedrich-nietzsche.jpg",
        "portrait_source": "https://commons.wikimedia.org/wiki/File:Nietzsche187a.jpg",
        "alt": "Historisches Schwarz-Weiß-Porträt von Friedrich Nietzsche",
        "voice": "Pointiert und genealogisch; entlarve bequeme Moral und prüfe, welche Kräfte und Werte sie hervorbringen.",
        "analysis_lens": "Untersuche Herkunft, Machtwirkung und lebensbejahenden oder lebensverneinenden Charakter der geltenden Werte; moralische Pflicht und Mehrheitsnutzen sind keine letzten Maßstäbe.",
    },
    "Marc Aurel": {
        "key": "marc-aurel",
        "school": "Stoizismus",
        "core_view": "Unterscheide das Beeinflussbare vom Unverfügbaren und handle besonnen zum Wohl der Gemeinschaft.",
        "portrait": "marc-aurel.jpg",
        "portrait_source": "https://commons.wikimedia.org/wiki/File:MSR-ra-61-b-1-DM.jpg",
        "alt": "Fotografie einer antiken Marmorbüste von Marc Aurel",
        "voice": "Ruhig und selbstprüfend; unterscheide Kontrolle von Unverfügbarem und stelle Gerechtigkeit ins Zentrum.",
        "analysis_lens": "Trenne Urteil und Absicht von äußeren Umständen, die niemand vollständig beherrscht; prüfe vernünftige Selbstregierung, Gerechtigkeit und die soziale Natur des Menschen statt Nutzenmaximierung.",
    },
    "Hannah Arendt": {
        "key": "hannah-arendt",
        "school": "Politische Theorie",
        "core_view": "Freiheit entsteht, wenn Verschiedene gemeinsam öffentlich handeln und Verantwortung für die gemeinsame Welt übernehmen.",
        "portrait": "hannah-arendt.jpg",
        "portrait_source": "https://commons.wikimedia.org/wiki/File:Hannah_Arendt_auf_dem_1._Kulturkritikerkongress,_Barbara_Niggl_Radloff,_FM-2019-1-5-9-16_(cropped).jpg",
        "alt": "Fotografisches Porträt von Hannah Arendt",
        "voice": "Politisch konkret und urteilsstark; betone Pluralität, öffentliches Handeln und persönliche Verantwortung.",
        "analysis_lens": "Frage, ob die Entscheidung gemeinsames öffentliches Handeln, Pluralität und eine geteilte Welt ermöglicht oder zerstört; analysiere politische Verantwortung und institutionelle Macht statt privater Tugend oder Nutzenrechnung.",
    },
    "John Stuart Mill": {
        "key": "john-stuart-mill",
        "school": "Utilitarismus",
        "core_view": "Wäge das Wohlergehen aller Betroffenen ab und schütze individuelle Freiheit vor vermeidbarem Schaden.",
        "portrait": "john-stuart-mill.jpg",
        "portrait_source": "https://commons.wikimedia.org/wiki/File:John_Stuart_Mill_by_London_Stereoscopic_Company,_c1870.jpg",
        "alt": "Historisches fotografisches Porträt von John Stuart Mill",
        "voice": "Analytisch und freiheitssensibel; wäge Folgen für alle Betroffenen ab und prüfe die Schadensgrenze.",
        "analysis_lens": "Vergleiche absehbares Wohlergehen und Leid aller Betroffenen, berücksichtige die Qualität von Freuden und wende das Schadensprinzip auf individuelle Freiheit an; keine Handlung ist allein wegen einer abstrakten Pflicht geboten.",
    },
    "Simone de Beauvoir": {
        "key": "simone-de-beauvoir",
        "school": "Feministischer Existenzialismus",
        "core_view": "Freiheit ist situiert und wird ethisch, wenn wir zugleich die Freiheit anderer ermöglichen.",
        "portrait": "simone-de-beauvoir.jpg",
        "portrait_source": "https://commons.wikimedia.org/wiki/File:Simone_De_Beauvoir_(cropped).jpg",
        "alt": "Fotografisches Porträt von Simone de Beauvoir",
        "voice": "Freiheitsbewusst und relational; untersuche konkrete Machtverhältnisse und Verantwortung für die Freiheit anderer.",
        "analysis_lens": "Untersuche die konkrete, verkörperte Situation und ob die eigene Freiheit die Freiheit anderer anerkennt oder zur Unterwerfung macht; vermeide abstrakte Universalregeln und bloße Gesamtnutzenrechnung.",
    },
    "Karl Marx": {
        "key": "karl-marx",
        "school": "Historischer Materialismus",
        "core_view": "Untersuche, wie materielle Verhältnisse und Klassenmacht das Leben prägen und Ausbeutung fortschreiben.",
        "portrait": "karl-marx.png",
        "portrait_source": "https://commons.wikimedia.org/wiki/File:Karl_Marx_by_John_Jabez_Edwin_Mayall_1875_-_Restored.png",
        "alt": "Historisches Schwarz-Weiß-Porträt von Karl Marx",
        "voice": "Materiell und strukturell; frage nach Eigentum, Klasseninteressen und den Bedingungen hinter moralischen Ansprüchen.",
        "analysis_lens": "Lege Eigentumsverhältnisse, Klasseninteressen, Arbeit und materielle Abhängigkeiten offen; frage, wer über Ressourcen verfügt und wer die Kosten trägt, statt das Problem als individuelles Pflicht- oder Nutzenkalkül zu behandeln.",
    },
    "Aristoteles": {
        "key": "aristoteles",
        "school": "Tugendethik",
        "core_view": "Ein gelingendes Leben entsteht durch Tugend, praktische Klugheit und das rechte Maß im konkreten Fall.",
        "portrait": "aristoteles.jpg",
        "portrait_source": "https://commons.wikimedia.org/wiki/File:Aristotle_Altemps_Inv8575.jpg",
        "alt": "Fotografie einer antiken Marmorbüste des Aristoteles",
        "voice": "Praktisch und maßvoll; prüfe Charakter, Tugenden, Umstände und das gelingende Leben.",
        "analysis_lens": "Beurteile, welche Handlung ein tugendhafter und praktisch kluger Mensch unter diesen konkreten Umständen wählen würde und ob sie Eudaimonie und das Gemeinwesen fördert; rechne nicht bloß Folgen zusammen.",
    },
    "Sokrates": {
        "key": "sokrates",
        "school": "Mäutik",
        "core_view": "Prüfendes Fragen legt vorschnelle Annahmen offen und führt zu besser begründeten Urteilen.",
        "portrait": "sokrates.jpg",
        "portrait_source": "https://commons.wikimedia.org/wiki/File:Socrates_Louvre.jpg",
        "alt": "Fotografie einer antiken Marmorbüste des Sokrates",
        "voice": "Fragend und prüfend; lege Widersprüche offen und führe vom konkreten Fall zur begründeten Einsicht.",
        "analysis_lens": "Beginne mit präzisen Rückfragen zu Definitionen und Annahmen, prüfe Antworten auf Widerspruch und lege offen, was die Beteiligten tatsächlich wissen; liefere kein vorgefertigtes Nutzen- oder Pflichturteil.",
    },
    "Thomas Hobbes": {
        "key": "thomas-hobbes",
        "school": "Vertragstheorie",
        "core_view": "Verbindliche Regeln und eine gemeinsame Autorität können Sicherheit und Frieden gewährleisten.",
        "portrait": "thomas-hobbes.jpg",
        "portrait_source": "https://commons.wikimedia.org/wiki/File:Thomas_Hobbes_by_John_Michael_Wright_(colour)_(3x4_cropped).jpg",
        "alt": "Historisches gemaltes Porträt von Thomas Hobbes",
        "voice": "Nüchtern und sicherheitsorientiert; prüfe Konflikt, Schutz, Regeln und die Legitimität gemeinsamer Autorität.",
        "analysis_lens": "Analysiere Gefahren, wechselseitige Unsicherheit, verbindliche Vereinbarungen und die Fähigkeit einer souveränen Autorität, Frieden zu sichern; Stabilität und Schutz stehen vor altruistischen Maximen.",
    },
    "René Descartes": {
        "key": "rene-descartes",
        "school": "Rationalismus",
        "core_view": "Methodischer Zweifel und klare Gründe sollen Überzeugungen von bloßen Annahmen trennen.",
        "portrait": "rene-descartes.jpg",
        "portrait_source": "https://commons.wikimedia.org/wiki/File:Frans_Hals_-_Portret_van_René_Descartes.jpg",
        "alt": "Historisches Ölgemälde von René Descartes",
        "voice": "Methodisch und klar; trenne Annahmen von Gründen und prüfe, was sich vernünftig begründen lässt.",
        "analysis_lens": "Zerlege das Urteil in klare Begriffe und prüfe, welche Prämissen verlässlich begründet sind; unterscheide Gewissheit, Vermutung und Schlussfolgerung, ohne moralische Pflichten oder Folgenabwägung zu importieren.",
    },
    "Niccolò Machiavelli": {
        "key": "niccolo-machiavelli",
        "school": "Politischer Realismus",
        "core_view": "Beurteile Politik nüchtern nach Machtverhältnissen, Folgen und den Bedingungen politischer Stabilität.",
        "portrait": "niccolo-machiavelli.jpg",
        "portrait_source": "https://commons.wikimedia.org/wiki/File:Portrait_of_Niccolò_Machiavelli_by_Santi_di_Tito.jpg",
        "alt": "Historisches gemaltes Porträt von Niccolò Machiavelli",
        "voice": "Machtbewusst und realistisch; beurteile Mittel, Folgen, Stabilität und politische Zwänge ohne Wunschdenken.",
        "analysis_lens": "Prüfe Machtverteilung, Zwangsmittel, politische Notwendigkeit, Stabilität und die realen Folgen für den Staat; urteile aus Sicht verantwortlicher Staatskunst und nicht nach privater Moral oder Nutzenmaximierung.",
    },
}

def contains_assistant_cliche(text: str) -> bool:
    normalized = text.casefold()
    return any(phrase in normalized for phrase in ASSISTANT_CLICHES)


def escape_text(value: str) -> str:
    return html.escape(value).replace("\n", "<br>")


def get_philosopher_details(name: str) -> dict[str, str]:
    """Return UI metadata for selectable and routing-only philosophers."""
    details = PHILOSOPHERS.get(name)
    if details is not None:
        return details
    framework = PHILOSOPHER_FRAMEWORKS.get(name)
    if framework is None:
        raise ValueError(f"Unbekannter Philosoph: {name}")
    slug = "-".join(name.casefold().split())
    return {
        "key": slug,
        "school": framework["school"],
        "alt": f"Porträt für {name} ist nicht im lokalen Bildbestand vorhanden.",
    }


def render_philosopher_identity(
    name: str,
    badge_label: str | None = None,
    badge_class: str | None = None,
) -> None:
    """Render the shared portrait, name, and school header used by both modes."""
    details = get_philosopher_details(name)
    if badge_label and badge_class:
        st.markdown(
            f'<span class="{badge_class}">{html.escape(badge_label)}</span>',
            unsafe_allow_html=True,
        )
    if "portrait" in details:
        st.markdown(
            f'<div class="portrait-stage"><a href="{html.escape(details["portrait_source"], quote=True)}" '
            f'target="_blank" rel="noopener noreferrer">'
            f'<img src="{portrait_data_uri(details["portrait"])}" '
            f'alt="{html.escape(details["alt"], quote=True)}" '
            f'class="portrait-image" decoding="async"></a></div>',
            unsafe_allow_html=True,
        )
    else:
        initials = "".join(part[0] for part in name.split() if part)
        st.markdown(
            '<div class="portrait-stage">'
            f'<div class="portrait-fallback" role="img" '
            f'aria-label="{html.escape(details["alt"], quote=True)}">'
            f'{html.escape(initials)}</div></div>',
            unsafe_allow_html=True,
        )
    st.markdown(
        f'<h3 class="philosopher-heading">{html.escape(name)}</h3>'
        f'<p class="school-label">{html.escape(details["school"])}</p>',
        unsafe_allow_html=True,
    )


def render_perspective_card(
    column: st.delta_generator.DeltaGenerator,
    name: str,
    perspective: dict[str, str],
) -> None:
    details = PHILOSOPHERS[name]
    slug = details["key"]
    with column:
        with st.container(key=f"perspective-{slug}"):
            render_philosopher_identity(name)
            for title, field in (
                ("Position", "position"),
                ("Begründung", "reasoning"),
                ("Fazit", "conclusion"),
            ):
                st.markdown(
                    '<div class="argument-block">'
                    f'<span class="argument-label">{title}</span>'
                    f'<p>{escape_text(perspective[field])}</p></div>',
                    unsafe_allow_html=True,
                )


def render_phenomenon_card(
    column: st.delta_generator.DeltaGenerator,
    name: str,
    role_label: str,
    badge_class: str,
    explanation: str,
) -> None:
    """Render an exploration result with the same card and portrait as the audit."""
    details = get_philosopher_details(name)
    with column:
        with st.container(key=f"perspective-{details['key']}"):
            render_philosopher_identity(name, role_label, badge_class)
            st.markdown(
                '<div class="argument-block">'
                '<span class="argument-label">Philosophische Einordnung</span>'
                f'<p>{escape_text(explanation)}</p></div>',
                unsafe_allow_html=True,
            )


def render_phenomenon_chat_turn(
    turn: dict[str, object],
    primary_name: str,
    opponent_name: str,
) -> None:
    """Show each question's chosen audience and the responses it produced."""
    target = turn.get("target")
    if not isinstance(target, str) or target not in CHAT_TARGET_LABELS:
        target = CHAT_TARGET_ALL
    target_label = chat_target_label(target, primary_name, opponent_name)
    with st.chat_message("user"):
        st.markdown(
            '<span class="chat-target-label">'
            f"Frage an: {html.escape(target_label)}</span>",
            unsafe_allow_html=True,
        )
        st.write(turn["question"])

    responses = turn.get("responses")
    if not isinstance(responses, dict):
        return
    badge_classes = {
        primary_name: PHENOMENON_BADGE_CLASSES["primary"],
        opponent_name: PHENOMENON_BADGE_CLASSES["opponent"],
        CHAT_MODERATOR_NAME: PHENOMENON_BADGE_CLASSES["moderator"],
    }
    with st.chat_message("assistant"):
        for responder in (primary_name, opponent_name, CHAT_MODERATOR_NAME):
            response = responses.get(responder)
            if isinstance(response, str) and response.strip():
                responder_label = (
                    "Dialektische Synthese"
                    if responder == CHAT_MODERATOR_NAME
                    else f"Antwort von {responder}"
                )
                st.markdown(
                    f'<span class="chat-response-label {badge_classes[responder]}">'
                    f'{html.escape(responder_label)}</span>',
                    unsafe_allow_html=True,
                )
                st.write(response)


def render_dilemma_chat_turn(turn: DilemmaChatTurn) -> None:
    """Render a dilemma objection and clearly badge every thinker reply."""
    target = turn["target"]
    addressed_label = (
        "⚡ Alle 3 (Diskurs & Synthese)"
        if target == CHAT_TARGET_ALL
        else f"👤 {target}"
    )
    with st.chat_message("user"):
        st.markdown(
            '<span class="chat-target-label">'
            f"Einwand an: {html.escape(addressed_label)}</span>",
            unsafe_allow_html=True,
        )
        st.write(turn["question"])

    badge_classes = {
        name: (
            PHENOMENON_BADGE_CLASSES["primary"]
            if index == 0
            else PHENOMENON_BADGE_CLASSES["opponent"]
        )
        for index, name in enumerate(
            name for name in turn["responses"] if name != CHAT_MODERATOR_NAME
        )
    }
    badge_classes[CHAT_MODERATOR_NAME] = PHENOMENON_BADGE_CLASSES["moderator"]
    with st.chat_message("assistant"):
        for name, response in turn["responses"].items():
            responder_label = (
                "Dialektische Synthese"
                if name == CHAT_MODERATOR_NAME
                else f"Antwort von {name}"
            )
            st.markdown(
                f'<span class="chat-response-label {badge_classes.get(name, PHENOMENON_BADGE_CLASSES["primary"])}">'
                f'{html.escape(responder_label)}</span>',
                unsafe_allow_html=True,
            )
            st.write(response)


def render_consensus(consensus: dict[str, object]) -> None:
    score = consensus["agreement_score"]
    st.markdown(
        '<section class="consensus-board">'
        '<p class="eyebrow">Synthese der Positionen</p>'
        '<h2>Gemeinsames Urteil &amp; Konsens</h2>'
        "</section>",
        unsafe_allow_html=True,
    )
    metric_column, conflict_column = st.columns([1, 2])
    with metric_column:
        st.metric("Einigkeits-Score", f"{score}%")
        st.progress(score, text=f"Übereinstimmung: {score}%")
    with conflict_column:
        st.markdown("**Zentraler philosophischer Streitpunkt**")
        st.write(consensus["conflict_summary"])
    st.subheader("Konsens- vs. Konflikt-Matrix")
    matrix_rows = [
        {
            "Philosoph:innen": " ↔ ".join(comparison["philosophers"]),
            "Gemeinsamer Boden": comparison["shared_ground"],
            "Unüberbrückbarer Konflikt": comparison["irreconcilable_difference"],
        }
        for comparison in consensus["comparison_matrix"]
    ]
    st.table(matrix_rows)


st.set_page_config(
    page_title=APP_NAME,
    page_icon="D",
    layout="wide",
)

st.markdown(
    """
    <style>
    :root {
        color-scheme: light;
        --paper: #faf8f3;
        --white: #ffffff;
        --ink: #201e1a;
        --muted: #514d45;
        --line: #d7d0c4;
        --accent: #876a3f;
    }

    html, body, [data-testid="stAppViewContainer"], [data-testid="stMain"],
    [data-testid="stHeader"] {
        background: var(--paper) !important;
        color: var(--ink) !important;
    }

    html, body, [class*="st-"], [data-testid="stMarkdownContainer"] {
        font-family: Inter, "Helvetica Neue", Helvetica, system-ui, sans-serif !important;
        font-size: 16px;
        line-height: 1.65;
    }

    h1, h2, h3, [data-testid="stMarkdownContainer"] h1,
    [data-testid="stMarkdownContainer"] h2,
    [data-testid="stMarkdownContainer"] h3 {
        color: var(--ink) !important;
        font-family: Georgia, "Times New Roman", serif !important;
        letter-spacing: -0.025em;
        line-height: 1.2 !important;
    }

    .block-container {
        max-width: 1500px;
        padding: 2.5rem 2rem 8rem;
    }

    [data-testid="stSidebar"] {
        background: #f4f1ea !important;
        border-right: 1px solid var(--line);
    }

    .st-key-app_mode [data-testid="stWidgetLabel"] p {
        color: var(--ink) !important;
        font-family: Georgia, "Times New Roman", serif !important;
        font-size: 1.15rem !important;
        font-weight: 700 !important;
    }

    .st-key-app_mode [data-testid="stRadioGroup"] {
        gap: 0.55rem;
    }

    .st-key-app_mode [data-testid="stRadioOption"] {
        background: #ffffff;
        border: 1px solid #bdb5a8;
        border-radius: 8px;
        color: var(--ink);
        padding: 0.72rem 0.8rem;
        transition: background 150ms ease, border-color 150ms ease;
    }

    .st-key-app_mode [data-testid="stRadioOption"][data-selected="true"] {
        background: #24211d;
        border-color: #24211d;
        color: #ffffff;
    }

    .st-key-app_mode [data-testid="stRadioOption"][data-selected="true"]
    [data-testid="stMarkdownContainer"] p {
        color: #ffffff !important;
    }

    .masthead {
        border-bottom: 1px solid var(--line);
        margin: 0 auto 2.3rem;
        max-width: 1000px;
        padding: 0 0 1.65rem;
        text-align: center;
    }

    .masthead-mark {
        color: var(--accent);
        font-family: Georgia, "Times New Roman", serif;
        font-size: 0.9rem;
        font-weight: 700;
        letter-spacing: 0.24em;
        text-transform: uppercase;
    }

    .masthead h1 {
        font-size: clamp(2.8rem, 6vw, 4.7rem);
        font-weight: 500;
        line-height: 1.05 !important;
        margin: 0.55rem 0 0.35rem;
    }

    .masthead p {
        color: var(--muted);
        font-size: 0.98rem;
        letter-spacing: 0.055em;
        margin: 0;
    }

    .section-kicker, .eyebrow {
        color: var(--accent);
        font-size: 0.78rem;
        font-weight: 800;
        letter-spacing: 0.13em;
        text-transform: uppercase;
    }

    .input-panel {
        background: var(--white);
        border: 1px solid var(--line);
        border-radius: 14px;
        box-shadow: 0 8px 28px rgba(42, 35, 25, 0.045);
        margin: 0 auto 2.2rem;
        max-width: 1100px;
        padding: 1.7rem 2rem 1.2rem;
    }

    .st-key-input-panel {
        background: var(--white);
        border: 1px solid var(--line);
        border-radius: 14px;
        box-shadow: 0 8px 28px rgba(42, 35, 25, 0.045);
        margin: 0 auto 2.2rem;
        max-width: 1100px;
        padding: 1.7rem 2rem 1.2rem;
    }

    [data-testid="stTextArea"] textarea {
        background: #ffffff !important;
        border: 2px solid #625e56 !important;
        border-radius: 8px !important;
        color: var(--ink) !important;
        font-size: 1.05rem !important;
        line-height: 1.65 !important;
        min-height: 155px;
        padding: 0.85rem 1rem !important;
    }

    [data-testid="stTextArea"] textarea::placeholder {
        color: #514d45 !important;
        opacity: 1;
    }

    [data-testid="stTextInput"] input,
    [data-testid="stChatInput"] textarea {
        background: #ffffff !important;
        border: 1.5px solid #625e56 !important;
        border-radius: 8px !important;
        color: var(--ink) !important;
        font-size: 1rem !important;
        line-height: 1.55 !important;
        min-height: 2.9rem;
    }

    [data-testid="stTextArea"] textarea:focus,
    [data-testid="stCheckbox"] input:focus-visible,
    button:focus-visible {
        border-color: #171612 !important;
        box-shadow: 0 0 0 3px #ffffff, 0 0 0 6px #171612 !important;
        outline: 2px solid #171612 !important;
        outline-offset: 3px !important;
    }

    [data-testid="stWidgetLabel"] p {
        color: var(--ink) !important;
        font-size: 1rem !important;
        font-weight: 700 !important;
    }

    [data-testid="stFormSubmitButton"] button {
        background: #24211d !important;
        border: 2px solid #24211d !important;
        border-radius: 7px !important;
        color: #ffffff !important;
        font-size: 1rem !important;
        font-weight: 750 !important;
        min-height: 3.2rem;
        padding: 0.55rem 1.4rem !important;
        transition: background 150ms ease, transform 150ms ease;
    }

    [data-testid="stFormSubmitButton"] button:hover {
        background: #ffffff !important;
        color: #24211d !important;
    }

    [data-testid="stFormSubmitButton"] button:active {
        transform: translateY(1px);
    }

    [class*="st-key-perspective-"] {
        background: #ffffff;
        border: 1px solid #c9c1b5;
        border-radius: 14px;
        box-sizing: border-box;
        height: 100%;
        min-height: 100%;
        overflow: visible;
        padding: 1.25rem;
        position: relative;
        transition: border-color 220ms ease, box-shadow 220ms ease, transform 220ms ease;
    }

    .portrait-stage {
        align-items: center;
        display: flex;
        height: 205px;
        justify-content: center;
        margin: 0 auto 0.75rem;
        max-width: 100%;
        overflow: hidden;
    }

    .portrait-fallback {
        align-items: center;
        background: #f2eee5;
        border: 1px solid #d7d0c4;
        border-radius: 50%;
        color: #292722;
        display: flex;
        font-family: Georgia, "Times New Roman", serif;
        font-size: 2.5rem;
        font-weight: 700;
        height: 170px;
        justify-content: center;
        width: 170px;
    }

    .portrait-image {
        filter: drop-shadow(0 12px 10px rgba(37, 31, 23, 0.24));
        height: 100%;
        max-width: 100%;
        object-fit: contain;
        transition: filter 220ms ease, transform 220ms ease;
        width: 100%;
    }

    .portrait-stage > a {
        height: 100%;
    }

    .philosopher-heading {
        font-size: 1.45rem;
        margin: 0.35rem 0 0.1rem;
        text-align: center;
    }

    .school-label {
        color: var(--accent);
        font-size: 0.82rem;
        font-weight: 800;
        letter-spacing: 0.06em;
        margin: 0 0 1rem;
        text-align: center;
        text-transform: uppercase;
    }

    .argument-block, .challenge-block {
        background: #f8f6f1;
        border: 1px solid #e1dbd0;
        border-radius: 8px;
        color: #25231f;
        margin: 0.7rem 0;
        overflow-wrap: anywhere;
        padding: 0.8rem 0.9rem;
    }

    .argument-block p, .challenge-block p {
        font-size: 0.96rem;
        line-height: 1.65;
        margin: 0.15rem 0 0;
    }

    .argument-label {
        color: #54452e;
        display: block;
        font-size: 0.74rem;
        font-weight: 850;
        letter-spacing: 0.1em;
        text-transform: uppercase;
    }

    .challenge-block {
        background: #f2eee5;
        border-left: 4px solid var(--accent);
    }

    [data-testid="stButton"] button {
        background: #ffffff !important;
        border: 2px solid #302c26 !important;
        border-radius: 7px !important;
        color: #201e1a !important;
        font-weight: 750 !important;
        min-height: 2.7rem;
        width: 100%;
    }

    [data-testid="stButton"] button:hover {
        background: #24211d !important;
        color: #ffffff !important;
    }

    .consensus-board {
        border-top: 1px solid var(--line);
        margin: 2.4rem 0 1rem;
        padding-top: 1.7rem;
    }

    .st-key-dilemma-chat-panel {
        border-top: 1px solid var(--line);
        margin-top: 2.2rem;
        padding-bottom: 6rem;
        padding-top: 1.5rem;
    }

    .consensus-board h2 {
        font-size: 2rem;
        margin: 0.2rem 0 0.8rem;
    }

    .phenomenon-card {
        background: #ffffff;
        border: 1px solid var(--line);
        border-radius: 14px;
        box-shadow: 0 8px 28px rgba(42, 35, 25, 0.045);
        height: 100%;
        padding: 1.35rem;
    }

    .phenomenon-badge {
        border-radius: 999px;
        display: table;
        font-size: 0.73rem;
        font-weight: 800;
        letter-spacing: 0.08em;
        margin: 0 auto 0.9rem;
        padding: 0.35rem 0.7rem;
        text-transform: uppercase;
    }

    .phenomenon-badge-primary {
        background: #292722;
        color: #ffffff;
    }

    .phenomenon-badge-opponent {
        background: #e9e3d8;
        border: 1px solid #68533b;
        color: #292722;
    }

    .phenomenon-badge-moderator {
        background: #efe9dd;
        border: 1px solid #876a3f;
        color: #292722;
    }

    .chat-target-label {
        background: #f2eee5;
        border: 1px solid #c9c1b5;
        border-radius: 999px;
        color: #292722;
        display: inline-block;
        font-size: 0.74rem;
        font-weight: 800;
        letter-spacing: 0.04em;
        margin-bottom: 0.45rem;
        padding: 0.25rem 0.65rem;
    }

    .chat-response-label {
        display: inline-block;
        margin: 0.5rem 0 0.15rem;
    }

    .phenomenon-card h3 {
        margin-top: 0.2rem;
    }

    [data-testid="stProgress"] > div > div > div {
        background-color: #876a3f !important;
    }

    .grid-heading {
        border-top: 1px solid var(--line);
        margin-top: 3rem;
        padding-top: 2rem;
    }

    [class*="st-key-choice-"] {
        align-items: stretch;
        background: #ffffff;
        border: 1px solid #bdb5a8;
        border-radius: 12px;
        box-sizing: border-box;
        display: flex;
        flex-direction: column;
        height: 420px;
        max-height: 420px;
        min-height: 420px;
        overflow: hidden;
        padding: 0.8rem;
        position: relative;
        transition: border-color 160ms ease, box-shadow 160ms ease;
    }

    [class*="st-key-choice-"]:has(input[type="checkbox"]:checked) {
        border: 3px solid #24211d;
        box-shadow: 0 0 0 3px #e7dfd0, 0 12px 26px rgba(42, 35, 25, 0.1);
    }

    [class*="st-key-choice-"]:focus-within {
        outline: 3px solid #24211d;
        outline-offset: 3px;
    }

    .choice-portrait-stage {
        align-items: center;
        display: flex;
        flex: 0 0 205px;
        height: 205px;
        justify-content: center;
        overflow: hidden;
        width: 100%;
    }

    .choice-portrait {
        filter: drop-shadow(0 8px 8px rgba(37, 31, 23, 0.23));
        height: 195px;
        max-width: 100%;
        object-fit: contain;
        width: 100%;
    }

    .choice-portrait-stage > a {
        align-items: center;
        display: flex;
        height: 100%;
        justify-content: center;
        width: 100%;
    }

    .choice-name {
        color: var(--ink);
        flex: 0 0 2.8rem;
        font-size: 1rem;
        font-weight: 850;
        line-height: 1.4;
        margin: 0.2rem 0 0;
        overflow: hidden;
        text-align: center;
        text-overflow: ellipsis;
        white-space: nowrap;
    }

    .choice-school {
        color: var(--accent);
        flex: 0 0 2.5rem;
        font-size: 0.79rem;
        font-weight: 800;
        line-height: 1.35;
        overflow: hidden;
        text-align: center;
        text-overflow: ellipsis;
    }

    .choice-view {
        color: #33302b;
        flex: 1 1 auto;
        font-size: 0.84rem;
        line-height: 1.42;
        margin: 0.25rem 0 0.4rem;
        overflow: hidden;
        text-align: center;
    }

    [data-testid="stCheckbox"] {
        flex: 0 0 auto;
        margin-top: auto;
    }

    [data-testid="stCheckbox"] label {
        color: var(--ink) !important;
        font-size: 0.84rem !important;
        font-weight: 700 !important;
    }

    [data-testid="stCheckbox"] input {
        accent-color: #24211d;
    }

    .stHorizontalBlock:has([class*="st-key-choice-"]) {
        display: grid !important;
        gap: 1rem !important;
        grid-template-columns: repeat(4, minmax(0, 1fr)) !important;
    }

    .stHorizontalBlock:has([class*="st-key-choice-"]) > [data-testid="stColumn"] {
        flex: initial !important;
        min-width: 0 !important;
        width: auto !important;
    }

    .stHorizontalBlock:has([class*="st-key-perspective-"]) {
        align-items: stretch;
        gap: 1rem !important;
    }

    .stHorizontalBlock:has([class*="st-key-perspective-"]) > [data-testid="stColumn"] {
        min-width: 0 !important;
    }

    @media (max-width: 1000px) {
        .stHorizontalBlock:has([class*="st-key-choice-"]) {
            grid-template-columns: repeat(3, minmax(0, 1fr)) !important;
        }
    }

    @media (max-width: 768px) {
        .block-container { padding: 1.5rem 1rem 8rem; }
        .st-key-input-panel { padding: 1.1rem 1rem 0.8rem; }
        .stHorizontalBlock:not(:has([class*="st-key-choice-"])) {
            align-items: stretch !important;
            flex-direction: column !important;
            gap: 0.85rem !important;
        }
        .stHorizontalBlock:not(:has([class*="st-key-choice-"])) > [data-testid="stColumn"] {
            flex: 1 1 100% !important;
            max-width: 100% !important;
            min-width: 0 !important;
            width: 100% !important;
        }
        .stHorizontalBlock:has([class*="st-key-choice-"]) {
            grid-template-columns: repeat(2, minmax(0, 1fr)) !important;
        }
        [class*="st-key-choice-"] {
            height: 390px !important;
            max-height: 390px !important;
            min-height: 390px !important;
            padding: 0.65rem !important;
        }
        .choice-portrait-stage {
            flex-basis: 175px !important;
            height: 175px !important;
            margin: 0 auto 0.4rem;
            max-width: 100%;
            padding: 0;
        }
        .choice-portrait {
            height: auto !important;
            max-height: 165px;
            max-width: 100%;
            object-fit: contain;
            width: auto !important;
        }
        .stHorizontalBlock:has([class*="st-key-perspective-"]) > [data-testid="stColumn"] {
            flex: 1 1 100% !important;
            max-width: 100% !important;
            width: 100% !important;
        }
        [class*="st-key-perspective-"] { margin-bottom: 1rem; }
        .portrait-stage {
            height: 190px;
            max-width: 100%;
        }
        .portrait-image {
            height: auto;
            max-height: 185px;
            max-width: 100%;
            object-fit: contain;
            width: auto;
        }
        .consensus-board + div [data-testid="stTable"] {
            overflow-x: auto;
        }
    }

    @media (prefers-reduced-motion: reduce) {
        *, *::before, *::after {
            animation-duration: 0.01ms !important;
            animation-iteration-count: 1 !important;
            scroll-behavior: auto !important;
            transition-duration: 0.01ms !important;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    f"""
    <header class="masthead">
      <div class="masthead-mark">Dialectica</div>
      <h1>{APP_NAME}</h1>
      <p>A Comparative Philosophical Analysis &amp; Ethics Engine</p>
    </header>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.markdown("### Dialectica AI")
    app_mode = st.radio(
        "Arbeitsmodus",
        options=(MODE_DILEMMA, MODE_PHENOMENA),
        key="app_mode",
    )
    if app_mode == MODE_DILEMMA and st.button(
        "🔄 Neues Dilemma / Chat zurücksetzen",
        key="reset-dilemma-chat",
        use_container_width=True,
    ):
        reset_dilemma_state(clear_input=True)
        st.rerun()

if app_mode == MODE_PHENOMENA:
    st.markdown('<div class="section-kicker">A concept in dialogue</div>', unsafe_allow_html=True)
    st.header("Philosophische Phänomene & Konzepte erkunden")
    st.write(
        "Lass den Hauptvertreter eine Idee entfalten und fordere anschließend "
        "einen systematischen Gegendenker heraus."
    )

    st.markdown("**Schnelleinstieg**")
    preset_columns = st.columns(4)
    for column, preset in zip(preset_columns, PHENOMENON_PRESETS):
        with column:
            if st.button(
                preset,
                key=f"phenomenon-preset-{PHENOMENON_PRESETS.index(preset)}",
                use_container_width=True,
            ):
                st.session_state["phenomenon_query"] = preset
                st.rerun()

    with st.form("phenomenon_form"):
        concept = st.text_input(
            "Begriff, Experiment oder Theorie",
            key="phenomenon_query",
            placeholder="z. B. Schleier des Nichtwissens",
        )
        explore_submitted = st.form_submit_button(
            "Phänomen erkunden",
            type="primary",
            use_container_width=True,
        )

    if explore_submitted:
        if not concept.strip():
            st.warning("Bitte gib einen Begriff oder ein Phänomen ein.")
        else:
            st.session_state["phenomenon_result"] = None
            st.session_state["phenomenon_chat"] = []
            try:
                with st.spinner("Hauptdenker und Kontrahent analysieren das Phänomen ..."):
                    phenomenon_result = analyze_phenomenon(concept)
            except (OpenAIError, ValueError, json.JSONDecodeError) as exc:
                st.error(f"Die Phänomenanalyse ist fehlgeschlagen: {exc}")
            else:
                st.session_state["phenomenon_result"] = phenomenon_result
                st.session_state["phenomenon_chat"] = []

    phenomenon_result = st.session_state.get("phenomenon_result")
    if (
        isinstance(phenomenon_result, dict)
        and phenomenon_result.get("concept") == concept.strip()
        and isinstance(phenomenon_result.get("primary_philosopher"), str)
        and phenomenon_result["primary_philosopher"] in PHILOSOPHER_FRAMEWORKS
        and isinstance(phenomenon_result.get("opponent_philosopher"), str)
        and phenomenon_result["opponent_philosopher"] in PHILOSOPHER_FRAMEWORKS
        and phenomenon_result.get("primary_philosopher")
        != phenomenon_result.get("opponent_philosopher")
        and isinstance(phenomenon_result.get("primary_explanation"), str)
        and isinstance(phenomenon_result.get("opponent_explanation"), str)
    ):
        primary_name = phenomenon_result["primary_philosopher"]
        opponent_name = phenomenon_result["opponent_philosopher"]
        st.session_state["current_hauptdenker"] = primary_name
        st.session_state["current_kontrahent"] = opponent_name
        primary_badge = PHENOMENON_BADGE_CLASSES["primary"]
        opponent_badge = PHENOMENON_BADGE_CLASSES["opponent"]
        primary_column, opponent_column = st.columns(2)
        render_phenomenon_card(
            primary_column,
            primary_name,
            "Urheber / Hauptvertreter",
            primary_badge,
            phenomenon_result["primary_explanation"],
        )
        render_phenomenon_card(
            opponent_column,
            opponent_name,
            "Kontrahent",
            opponent_badge,
            phenomenon_result["opponent_explanation"],
        )

        st.subheader("Im Gespräch weiterdenken")
        raw_chat_history = st.session_state.get("phenomenon_chat")
        chat_history = (
            raw_chat_history if isinstance(raw_chat_history, list) else []
        )
        if chat_history is not raw_chat_history:
            st.session_state["phenomenon_chat"] = chat_history
        valid_chat_history = [
            turn
            for turn in chat_history
            if isinstance(turn, dict)
            and isinstance(turn.get("question"), str)
            and isinstance(turn.get("responses"), dict)
            and any(
                isinstance(turn["responses"].get(responder), str)
                for responder in (
                    primary_name,
                    opponent_name,
                    CHAT_MODERATOR_NAME,
                )
            )
        ]
        for turn in valid_chat_history:
            render_phenomenon_chat_turn(turn, primary_name, opponent_name)

        current_target = st.session_state.get("phenomenon_chat_target")
        if (
            not isinstance(current_target, str)
            or current_target not in CHAT_TARGET_LABELS
        ):
            st.session_state["phenomenon_chat_target"] = CHAT_TARGET_ALL
        selected_target = st.segmented_control(
            "Antwortziel",
            options=(
                CHAT_TARGET_PRIMARY,
                CHAT_TARGET_OPPONENT,
                CHAT_TARGET_ALL,
            ),
            format_func=lambda target: chat_target_label(
                target, primary_name, opponent_name
            ),
            key="phenomenon_chat_target",
            help=(
                "Wähle einen einzelnen Denker oder lasse beide und die "
                "dialektische Moderation antworten."
            ),
            width="stretch",
        )
        followup = st.chat_input(
            "Formuliere eine Frage oder einen Einwand",
            key="phenomenon-followup",
        )
        if followup:
            if (
                not isinstance(selected_target, str)
                or selected_target not in CHAT_TARGET_LABELS
            ):
                selected_target = CHAT_TARGET_ALL
            try:
                target_label = chat_target_label(
                    selected_target, primary_name, opponent_name
                )
                with st.spinner(f"{target_label} formuliert eine Antwort ..."):
                    previous_turns: list[PhenomenonChatTurn] = [
                        {
                            "question": turn["question"],
                            "primary_response": turn["responses"].get(primary_name),
                            "opponent_response": turn["responses"].get(opponent_name),
                            "moderator_response": turn["responses"].get(
                                CHAT_MODERATOR_NAME
                            ),
                        }
                        for turn in valid_chat_history
                    ]
                    responses = answer_phenomenon_followup(
                        concept=phenomenon_result["concept"],
                        primary_name=primary_name,
                        opponent_name=opponent_name,
                        primary_explanation=phenomenon_result["primary_explanation"],
                        opponent_explanation=phenomenon_result["opponent_explanation"],
                        question=followup,
                        target=selected_target,
                        history=previous_turns,
                    )
            except (OpenAIError, ValueError, json.JSONDecodeError) as exc:
                st.error(f"Die Rückfrage konnte nicht beantwortet werden: {exc}")
            else:
                chat_history.append(
                    {
                        "question": followup,
                        "target": selected_target,
                        "responses": responses,
                    }
                )
                st.rerun()
    st.stop()

selection = tuple(
    name
    for name, details in PHILOSOPHERS.items()
    if st.session_state.get(f"select-{details['key']}", False)
)

with st.container(key="input-panel"):
    st.markdown(
        '<p class="section-kicker">Begin with the question</p>',
        unsafe_allow_html=True,
    )
    st.header("Ethisches Dilemma eingeben")
    dilemma = st.text_area(
        "Ethisches Dilemma eingeben",
        placeholder=(
            "Beschreibe das Szenario, die Betroffenen und die Entscheidung, "
            "vor der sie stehen."
        ),
        height=165,
        label_visibility="collapsed",
        key="dilemma_input",
    )
    debate_started = st.button(
        "Debatte & Analyse starten",
        type="primary",
        disabled=len(selection) != 3,
        use_container_width=True,
    )

pending_dilemma = st.session_state.pop("_pending_dilemma", None)
if debate_started and not dilemma.strip():
    st.warning("Bitte gib zuerst ein ethisches Dilemma ein.")
elif debate_started and len(selection) != 3:
    st.error("Wähle unten genau drei Philosophen aus.")
elif debate_started:
    reset_dilemma_state()
    st.session_state["_pending_dilemma"] = dilemma.strip()
    st.rerun()

if isinstance(pending_dilemma, str) and pending_dilemma:
    analysis_dilemma = pending_dilemma
    try:
        api_key = st.secrets["OPENAI_API_KEY"]
    except KeyError:
        st.error("OPENAI_API_KEY fehlt in den Streamlit-Secrets.")
    else:
        client = OpenAI(api_key=api_key)
        ethos_context = "\n".join(
            f"- {name} ({PHILOSOPHERS[name]['school']}): "
            f"{PHILOSOPHERS[name]['core_view']}"
            for name in selection
        )
        debate: dict[str, dict[str, str]] = {}
        request_failed = False
        progress = st.status("Die Perspektiven werden entwickelt ...", expanded=True)
        live_column_set = st.columns(3)

        for name in selection:
            details = PHILOSOPHERS[name]
            progress.update(label=f"{name} entwickelt eine Position ...")
            prompt = f"""
Analysiere das ethische Dilemma ausschließlich aus der Perspektive von {name}.
Philosophische Schule: {details['school']}.
Kernansicht: {details['core_view']}.
Stil: {details['voice']}.

Formuliere prägnant, eigenständig, scharf argumentiert und in-character.
Analysiere AUSSCHLIESSLICH durch die folgende philosophische Brille:
{details['analysis_lens']}
Vermeide allgemeine Moralformeln sowie Begriffe oder Argumentationsmuster
anderer Denkschulen. Insbesondere darfst du keine fremde Theorie als Stütze
verwenden. Zeige, wie genau diese Denkschule aus dem Dilemma zu ihrem Urteil
gelangt, und benenne einen konkreten Entscheidungstest.
Kein Chatbot-Einstieg, keine Selbstbeschreibung, kein Hilfsangebot und kein
Meta-Kommentar. Keine Formeln wie "Als KI", "Hier ist meine Analyse" oder
"Gerne helfe ich". Erfinde keine historischen Zitate.

Antworte ausschließlich als JSON-Objekt mit genau einem Schlüssel
{json.dumps(name, ensure_ascii=False)}. Dessen Wert ist ein Objekt mit den
String-Feldern "position", "reasoning" und "conclusion".

Ethisches Dilemma:
{analysis_dilemma}
"""
            system_prompt = (
                build_system_prompt(name, details["analysis_lens"])
                + "\nAntworte auf Deutsch."
            )
            try:
                with st.spinner(f"{name} argumentiert ..."):
                    answer = request_json(client, prompt, system_prompt)
            except (OpenAIError, ValueError, json.JSONDecodeError) as exc:
                st.error(f"Die Analyse für {name} ist fehlgeschlagen: {exc}")
                request_failed = True
                break

            perspective = answer.get(name)
            valid_perspective = (
                set(answer) == {name}
                and isinstance(perspective, dict)
                and all(
                    isinstance(perspective.get(field), str)
                    and bool(perspective[field].strip())
                    for field in PERSPECTIVE_FIELDS
                )
            )
            if not valid_perspective:
                st.error(f"Die Analyse für {name} hatte nicht das erwartete JSON-Format.")
                request_failed = True
                break
            if any(
                contains_assistant_cliche(perspective[field])
                for field in PERSPECTIVE_FIELDS
            ):
                st.error(
                    f"Die Analyse für {name} enthielt eine Chatbot-Floskel "
                    "und wurde nicht übernommen."
                )
                request_failed = True
                break
            debate[name] = perspective

        if not request_failed and len(debate) == 3:
            st.session_state["debate"] = debate
            st.session_state["debate_selection"] = selection
            st.session_state["debate_dilemma"] = analysis_dilemma
            st.session_state["challenge_responses"] = {}
            st.session_state["dilemma_chat_history"] = []
            st.session_state["dilemma_chat_target"] = CHAT_TARGET_ALL

            consensus_prompt = f"""
Vergleiche die drei folgenden Analysen dieses ethischen Dilemmas.
Bestimme, wie stark die grundlegenden Urteile und Begründungen übereinstimmen.
Gib einen Einigkeits-Score als ganze Prozentzahl von 0 bis 100 an und benenne
den zentralen Konflikt. Erzeuge zusätzlich für jedes Philosophenpaar einen
Matrix-Eintrag: erst die tatsächlich geteilte Prämisse oder das gemeinsame Ziel,
danach die normative Differenz, die sich nicht durch bloße Faktenklärung
auflöst. Erfinde keinen Konsens, wenn die Analysen einander widersprechen.

Ausgewählte Schulen und Kernansichten:
{ethos_context}

Analysen:
{json.dumps(debate, ensure_ascii=False)}

Dilemma:
{analysis_dilemma}

Antworte ausschließlich als JSON-Objekt mit genau diesen Feldern:
{{"agreement_score": 0, "conflict_summary": "Kurze Konfliktbeschreibung",
"comparison_matrix": [
  {{"philosophers": ["Name A", "Name B"], "shared_ground": "Gemeinsamer Boden",
   "irreconcilable_difference": "Unüberbrückbarer normativer Konflikt"}}
]}}
Die comparison_matrix muss exakt diese drei Paare in dieser Reihenfolge enthalten:
{json.dumps([list(pair) for pair in combinations(selection, 2)], ensure_ascii=False)}
"""
            try:
                progress.update(label="Gemeinsamkeiten und Konflikt werden verglichen ...")
                consensus = request_json(
                    client,
                    consensus_prompt,
                    "Vergleiche philosophische Argumente präzise und fair. "
                    "Keine Chatbot-Floskeln, Selbstbezüge oder Meta-Kommentare. "
                    "Antworte ausschließlich mit gültigem JSON.",
                )
            except (OpenAIError, ValueError, json.JSONDecodeError) as exc:
                st.error(f"Die Konsens-Analyse ist fehlgeschlagen: {exc}")
                progress.update(label="Die Einzelanalysen sind fertig.", state="complete")
            else:
                score = consensus.get("agreement_score")
                conflict = consensus.get("conflict_summary")
                valid_consensus = (
                    set(consensus) == set(CONSENSUS_FIELDS)
                    and type(score) is int
                    and 0 <= score <= 100
                    and isinstance(conflict, str)
                    and bool(conflict.strip())
                    and not contains_assistant_cliche(conflict)
                    and isinstance(consensus.get("comparison_matrix"), list)
                    and len(consensus["comparison_matrix"]) == 3
                    and all(
                        isinstance(comparison, dict)
                        and set(comparison)
                        == {
                            "philosophers",
                            "shared_ground",
                            "irreconcilable_difference",
                        }
                        and comparison.get("philosophers") == list(pair)
                        and isinstance(comparison.get("shared_ground"), str)
                        and bool(comparison["shared_ground"].strip())
                        and isinstance(
                            comparison.get("irreconcilable_difference"), str
                        )
                        and bool(comparison["irreconcilable_difference"].strip())
                        and not contains_assistant_cliche(comparison["shared_ground"])
                        and not contains_assistant_cliche(
                            comparison["irreconcilable_difference"]
                        )
                        for comparison, pair in zip(
                            consensus["comparison_matrix"],
                            combinations(selection, 2),
                        )
                    )
                )
                if not valid_consensus:
                    st.error("Die Konsens-Antwort hatte nicht das erwartete JSON-Format.")
                else:
                    st.session_state["consensus"] = consensus
                    st.session_state["consensus_selection"] = selection
                    st.session_state["consensus_dilemma"] = analysis_dilemma
                    progress.update(label="Analyse und Konsens sind abgeschlossen.", state="complete")
        else:
            progress.update(label="Die Analyse wurde wegen einer fehlerhaften Antwort beendet.", state="error")

st.markdown('<div class="section-kicker">Three selected perspectives</div>', unsafe_allow_html=True)
st.header("Die philosophischen Perspektiven")

saved_debate = st.session_state.get("debate")
saved_selection = st.session_state.get("debate_selection")
saved_dilemma = st.session_state.get("debate_dilemma")
matching_debate = (
    isinstance(saved_debate, dict)
    and saved_selection == selection
    and saved_dilemma == dilemma.strip()
)

if len(selection) == 3:
    if matching_debate:
        result_columns = st.columns(3)
        for column, name in zip(result_columns, selection):
            render_perspective_card(
                column,
                name,
                saved_debate[name],
            )
        saved_consensus = st.session_state.get("consensus")
        if (
            isinstance(saved_consensus, dict)
            and st.session_state.get("consensus_selection") == selection
            and st.session_state.get("consensus_dilemma") == saved_dilemma
        ):
            render_consensus(saved_consensus)

        with st.container(key="dilemma-chat-panel"):
            st.subheader("Hinterfragen / Sokratischer Dialog")
            st.markdown(
                "Formuliere deine eigene Position oder einen konkreten Einwand. "
                "Wähle einen Denker oder eröffne einen gemeinsamen Diskurs."
            )
            raw_dialogue_history = st.session_state.get("dilemma_chat_history")
            dialogue_history = (
                raw_dialogue_history
                if isinstance(raw_dialogue_history, list)
                else []
            )
            valid_dialogue_history: list[DilemmaChatTurn] = [
                turn
                for turn in dialogue_history
                if isinstance(turn, dict)
                and isinstance(turn.get("question"), str)
                and isinstance(turn.get("target"), str)
                and isinstance(turn.get("responses"), dict)
                and bool(turn["responses"])
                and all(
                    isinstance(name, str) and isinstance(response, str)
                    for name, response in turn["responses"].items()
                )
            ]
            current_dilemma_target = st.session_state.get("dilemma_chat_target")
            if current_dilemma_target not in (*selection, CHAT_TARGET_ALL):
                st.session_state["dilemma_chat_target"] = CHAT_TARGET_ALL
            dilemma_chat_target = st.segmented_control(
                "Antwortziel",
                options=(*selection, CHAT_TARGET_ALL),
                format_func=lambda target: (
                    "⚡ Alle 3 (Diskurs & Synthese)"
                    if target == CHAT_TARGET_ALL
                    else f"👤 {target}"
                ),
                key="dilemma_chat_target",
                help="Wähle einen der drei aktiven Denker oder lasse alle antworten.",
                width="stretch",
            )
            with st.container(key="dilemma-chat-history"):
                for turn in valid_dialogue_history:
                    render_dilemma_chat_turn(turn)
            user_argument = st.chat_input(
                "Formuliere deine Position oder einen konkreten Einwand",
                key="dilemma-chat-input",
            )

        if user_argument:
            try:
                if (
                    not isinstance(dilemma_chat_target, str)
                    or dilemma_chat_target not in (*selection, CHAT_TARGET_ALL)
                ):
                    raise ValueError("Das ausgewählte Antwortziel ist ungültig.")
                with st.spinner("Die ausgewählten Denker prüfen deinen Einwand ..."):
                    responses = answer_dilemma_followup(
                        dilemma=saved_dilemma,
                        philosophers={
                            name: PHILOSOPHERS[name] for name in selection
                        },
                        analyses=saved_debate,
                        question=user_argument,
                        target=dilemma_chat_target,
                        history=valid_dialogue_history,
                    )
                if any(contains_assistant_cliche(text) for text in responses.values()):
                    raise ValueError(
                        "Eine Dialogantwort enthielt eine Chatbot-Floskel."
                    )
            except (OpenAIError, ValueError, json.JSONDecodeError) as exc:
                    st.error(f"Der sokratische Dialog ist fehlgeschlagen: {exc}")
            else:
                    dialogue_history.append({
                        "question": user_argument.strip(),
                        "target": dilemma_chat_target,
                        "responses": responses,
                    })
                    st.session_state["dilemma_chat_history"] = dialogue_history
                    st.rerun()

st.markdown('<div class="grid-heading">', unsafe_allow_html=True)
st.markdown('<p class="section-kicker">The philosophical library</p>', unsafe_allow_html=True)
st.header("Wähle genau drei Philosophen")
st.markdown(
    "Hier siehst du historische Gemälde, Fotografien und antike Büsten. "
    "Ein Klick auf ein Porträt öffnet dessen Bildquelle mit Lizenzangaben."
)
st.markdown("</div>", unsafe_allow_html=True)

philosopher_items = list(PHILOSOPHERS.items())
for row_start in range(0, len(philosopher_items), 4):
    grid_columns = st.columns(4)
    for column, (name, details) in zip(
        grid_columns, philosopher_items[row_start : row_start + 4]
    ):
        slug = details["key"]
        with column:
            with st.container(key=f"choice-{slug}"):
                st.markdown(
                    f'<div class="choice-portrait-stage"><a '
                    f'href="{html.escape(details["portrait_source"], quote=True)}" '
                    f'target="_blank" rel="noopener noreferrer">'
                    f'<img class="choice-portrait" decoding="async" '
                    f'src="{portrait_data_uri(details["portrait"])}" '
                    f'alt="{html.escape(details["alt"], quote=True)}"></a></div>'
                    f'<div class="choice-name">{html.escape(name)}</div>'
                    f'<div class="choice-school">{html.escape(details["school"])}</div>'
                    f'<div class="choice-view">{html.escape(details["core_view"])}</div>',
                    unsafe_allow_html=True,
                )
                st.checkbox(
                    f"{name} auswählen",
                    key=f"select-{slug}",
                    disabled=(
                        len(selection) >= 3
                        and name not in selection
                    ),
                )

st.caption(f"{len(selection)} von 3 Philosophen ausgewählt")
