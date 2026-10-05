import html
import json
import base64
from pathlib import Path

import streamlit as st
from openai import OpenAI, OpenAIError


APP_NAME = "Dialectica AI"
MODEL = "gpt-4o-mini"
PERSPECTIVE_FIELDS = ("position", "reasoning", "conclusion")
CONSENSUS_FIELDS = ("agreement_score", "conflict_summary")
ASSISTANT_CLICHES = (
    "als ki",
    "als künstliche intelligenz",
    "als sprachmodell",
    "hier ist meine analyse",
    "hier ist die analyse",
    "gerne helfe ich",
    "ich kann dir dabei helfen",
)

PHILOSOPHERS = {
    "Immanuel Kant": {
        "key": "immanuel-kant",
        "school": "Pflichtethik",
        "core_view": "Handle nach verallgemeinerbaren Prinzipien und behandle Menschen stets als Zweck an sich.",
        "portrait": "immanuel-kant.jpg",
        "portrait_source": "https://commons.wikimedia.org/wiki/File:Immanuel_Kant_-_Gemaelde_1.jpg",
        "alt": "Historisches Ölgemälde von Immanuel Kant",
        "voice": "Pflichtbewusst und präzise; prüfe die Maxime auf Allgemeingültigkeit und Menschenwürde.",
    },
    "Friedrich Nietzsche": {
        "key": "friedrich-nietzsche",
        "school": "Wille zur Macht",
        "core_view": "Hinterfrage überlieferte Werte und bejahe die schöpferische Selbstgestaltung des Lebens.",
        "portrait": "friedrich-nietzsche.jpg",
        "portrait_source": "https://commons.wikimedia.org/wiki/File:Nietzsche187a.jpg",
        "alt": "Historisches Schwarz-Weiß-Porträt von Friedrich Nietzsche",
        "voice": "Pointiert und genealogisch; entlarve bequeme Moral und prüfe, welche Kräfte und Werte sie hervorbringen.",
    },
    "Marc Aurel": {
        "key": "marc-aurel",
        "school": "Stoizismus",
        "core_view": "Unterscheide das Beeinflussbare vom Unverfügbaren und handle besonnen zum Wohl der Gemeinschaft.",
        "portrait": "marc-aurel.jpg",
        "portrait_source": "https://commons.wikimedia.org/wiki/File:MSR-ra-61-b-1-DM.jpg",
        "alt": "Fotografie einer antiken Marmorbüste von Marc Aurel",
        "voice": "Ruhig und selbstprüfend; unterscheide Kontrolle von Unverfügbarem und stelle Gerechtigkeit ins Zentrum.",
    },
    "Hannah Arendt": {
        "key": "hannah-arendt",
        "school": "Politische Theorie",
        "core_view": "Freiheit entsteht, wenn Verschiedene gemeinsam öffentlich handeln und Verantwortung für die gemeinsame Welt übernehmen.",
        "portrait": "hannah-arendt.jpg",
        "portrait_source": "https://commons.wikimedia.org/wiki/File:Hannah_Arendt_auf_dem_1._Kulturkritikerkongress,_Barbara_Niggl_Radloff,_FM-2019-1-5-9-16_(cropped).jpg",
        "alt": "Fotografisches Porträt von Hannah Arendt",
        "voice": "Politisch konkret und urteilsstark; betone Pluralität, öffentliches Handeln und persönliche Verantwortung.",
    },
    "John Stuart Mill": {
        "key": "john-stuart-mill",
        "school": "Utilitarismus",
        "core_view": "Wäge das Wohlergehen aller Betroffenen ab und schütze individuelle Freiheit vor vermeidbarem Schaden.",
        "portrait": "john-stuart-mill.jpg",
        "portrait_source": "https://commons.wikimedia.org/wiki/File:John_Stuart_Mill_by_London_Stereoscopic_Company,_c1870.jpg",
        "alt": "Historisches fotografisches Porträt von John Stuart Mill",
        "voice": "Analytisch und freiheitssensibel; wäge Folgen für alle Betroffenen ab und prüfe die Schadensgrenze.",
    },
    "Simone de Beauvoir": {
        "key": "simone-de-beauvoir",
        "school": "Feministischer Existenzialismus",
        "core_view": "Freiheit ist situiert und wird ethisch, wenn wir zugleich die Freiheit anderer ermöglichen.",
        "portrait": "simone-de-beauvoir.jpg",
        "portrait_source": "https://commons.wikimedia.org/wiki/File:Simone_De_Beauvoir_(cropped).jpg",
        "alt": "Fotografisches Porträt von Simone de Beauvoir",
        "voice": "Freiheitsbewusst und relational; untersuche konkrete Machtverhältnisse und Verantwortung für die Freiheit anderer.",
    },
    "Karl Marx": {
        "key": "karl-marx",
        "school": "Historischer Materialismus",
        "core_view": "Untersuche, wie materielle Verhältnisse und Klassenmacht das Leben prägen und Ausbeutung fortschreiben.",
        "portrait": "karl-marx.png",
        "portrait_source": "https://commons.wikimedia.org/wiki/File:Karl_Marx_by_John_Jabez_Edwin_Mayall_1875_-_Restored.png",
        "alt": "Historisches Schwarz-Weiß-Porträt von Karl Marx",
        "voice": "Materiell und strukturell; frage nach Eigentum, Klasseninteressen und den Bedingungen hinter moralischen Ansprüchen.",
    },
    "Aristoteles": {
        "key": "aristoteles",
        "school": "Tugendethik",
        "core_view": "Ein gelingendes Leben entsteht durch Tugend, praktische Klugheit und das rechte Maß im konkreten Fall.",
        "portrait": "aristoteles.jpg",
        "portrait_source": "https://commons.wikimedia.org/wiki/File:Aristotle_Altemps_Inv8575.jpg",
        "alt": "Fotografie einer antiken Marmorbüste des Aristoteles",
        "voice": "Praktisch und maßvoll; prüfe Charakter, Tugenden, Umstände und das gelingende Leben.",
    },
    "Sokrates": {
        "key": "sokrates",
        "school": "Mäutik",
        "core_view": "Prüfendes Fragen legt vorschnelle Annahmen offen und führt zu besser begründeten Urteilen.",
        "portrait": "sokrates.jpg",
        "portrait_source": "https://commons.wikimedia.org/wiki/File:Socrates_Louvre.jpg",
        "alt": "Fotografie einer antiken Marmorbüste des Sokrates",
        "voice": "Fragend und prüfend; lege Widersprüche offen und führe vom konkreten Fall zur begründeten Einsicht.",
    },
    "Thomas Hobbes": {
        "key": "thomas-hobbes",
        "school": "Vertragstheorie",
        "core_view": "Verbindliche Regeln und eine gemeinsame Autorität können Sicherheit und Frieden gewährleisten.",
        "portrait": "thomas-hobbes.jpg",
        "portrait_source": "https://commons.wikimedia.org/wiki/File:Thomas_Hobbes_by_John_Michael_Wright_(colour)_(3x4_cropped).jpg",
        "alt": "Historisches gemaltes Porträt von Thomas Hobbes",
        "voice": "Nüchtern und sicherheitsorientiert; prüfe Konflikt, Schutz, Regeln und die Legitimität gemeinsamer Autorität.",
    },
    "René Descartes": {
        "key": "rene-descartes",
        "school": "Rationalismus",
        "core_view": "Methodischer Zweifel und klare Gründe sollen Überzeugungen von bloßen Annahmen trennen.",
        "portrait": "rene-descartes.jpg",
        "portrait_source": "https://commons.wikimedia.org/wiki/File:Frans_Hals_-_Portret_van_René_Descartes.jpg",
        "alt": "Historisches Ölgemälde von René Descartes",
        "voice": "Methodisch und klar; trenne Annahmen von Gründen und prüfe, was sich vernünftig begründen lässt.",
    },
    "Niccolò Machiavelli": {
        "key": "niccolo-machiavelli",
        "school": "Politischer Realismus",
        "core_view": "Beurteile Politik nüchtern nach Machtverhältnissen, Folgen und den Bedingungen politischer Stabilität.",
        "portrait": "niccolo-machiavelli.jpg",
        "portrait_source": "https://commons.wikimedia.org/wiki/File:Portrait_of_Niccolò_Machiavelli_by_Santi_di_Tito.jpg",
        "alt": "Historisches gemaltes Porträt von Niccolò Machiavelli",
        "voice": "Machtbewusst und realistisch; beurteile Mittel, Folgen, Stabilität und politische Zwänge ohne Wunschdenken.",
    },
}


@st.cache_data(show_spinner=False)
def portrait_data_uri(name):
    from pathlib import Path
    import base64

    base_dir = Path(__file__).resolve().parent
    slug = str(name).lower().strip().replace(" ", "-").replace("_", "-")
    
    # Prüft sowohl das Hauptverzeichnis als auch den Unterordner "assets/portraits"
    candidates = [
        base_dir / f"{slug}.jpg",
        base_dir / f"{slug}.png",
        base_dir / f"{name}.jpg",
        base_dir / f"{name}.png",
        base_dir / "assets" / "portraits" / f"{slug}.jpg",
        base_dir / "assets" / "portraits" / f"{slug}.png",
    ]
    
    for path in candidates:
        if path.exists():
            encoded = base64.b64encode(path.read_bytes()).decode("ascii")
            mime = "image/png" if path.suffix.lower() == ".png" else "image/jpeg"
            return f"data:{mime};base64,{encoded}"
            
    # Falls ein Bild komplett fehlt, stürzt die App nicht mehr ab
    return ""


def contains_assistant_cliche(text: str) -> bool:
    normalized = text.casefold()
    return any(phrase in normalized for phrase in ASSISTANT_CLICHES)


def request_json(client: OpenAI, prompt: str, system_prompt: str) -> dict[str, object]:
    response = client.chat.completions.create(
        model=MODEL,
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


def escape_text(value: str) -> str:
    return html.escape(value).replace("\n", "<br>")


def render_perspective_card(
    column: st.delta_generator.DeltaGenerator,
    name: str,
    perspective: dict[str, str] | None,
    active: bool,
    challenge: str | None = None,
    interactive: bool = False,
) -> bool:
    details = PHILOSOPHERS[name]
    slug = details["key"]
    with column:
        with st.container(key=f"perspective-{slug}"):
            if active:
                st.markdown(
                    '<div class="speaker-label" role="status" aria-live="polite">'
                    'AKTUELLER BEITRAG</div>',
                    unsafe_allow_html=True,
                )
            st.markdown(
                f'<div class="portrait-stage"><a href="{html.escape(details["portrait_source"], quote=True)}" '
                f'target="_blank" rel="noopener noreferrer">'
                f'<img src="{portrait_data_uri(name)}" '
                f'alt="{html.escape(details["alt"], quote=True)}" '
                f'class="portrait-image" decoding="async"></a></div>',
                unsafe_allow_html=True,
            )
            st.markdown(
                f'<h3 class="philosopher-heading">{html.escape(name)}</h3>'
                f'<p class="school-label">{html.escape(details["school"])}</p>',
                unsafe_allow_html=True,
            )
            if perspective is None:
                st.markdown(
                    '<div class="analysis-placeholder">Die Analyse erscheint '
                    "hier, sobald die Debatte gestartet wurde.</div>",
                    unsafe_allow_html=True,
                )
            else:
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
            if challenge:
                st.markdown(
                    '<div class="challenge-block">'
                    '<span class="argument-label">Kreuzverhör</span>'
                    f'<p>{escape_text(challenge)}</p></div>',
                    unsafe_allow_html=True,
                )
            if interactive and perspective is not None:
                return st.button(
                    "Hinterfragen",
                    key=f"challenge-{slug}",
                    help="Fordere diesen Standpunkt zur direkten Verteidigung heraus.",
                )
    return False


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
        padding: 2.5rem 2rem 4rem;
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

    [class*="st-key-perspective-"]:has(.speaker-label) {
        animation: active-card-glow 1.8s ease-in-out infinite alternate;
        border: 3px solid #211f1b;
        transform: scale(1.08);
        z-index: 2;
    }

    @keyframes active-card-glow {
        from { box-shadow: 0 10px 30px rgba(42, 35, 25, 0.12); }
        to { box-shadow: 0 18px 42px rgba(135, 106, 63, 0.28); }
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

    [class*="st-key-perspective-"]:has(.speaker-label) .portrait-image {
        filter: drop-shadow(0 18px 15px rgba(57, 43, 24, 0.38));
        transform: scale(1.08);
    }

    .speaker-label {
        background: #24211d;
        border: 1px solid #24211d;
        border-radius: 999px;
        color: #ffffff;
        display: table;
        font-family: Inter, sans-serif;
        font-size: 0.74rem;
        font-weight: 800;
        letter-spacing: 0.075em;
        margin: 0 auto 0.9rem;
        padding: 0.4rem 0.7rem;
        text-align: center;
    }

    .speaker-label::after {
        animation: speaking-pulse 1.2s ease-in-out infinite;
        background: #e4c68e;
        border-radius: 50%;
        content: "";
        display: inline-block;
        height: 0.5rem;
        margin-left: 0.5rem;
        width: 0.5rem;
    }

    @keyframes speaking-pulse {
        50% { box-shadow: 0 0 0 5px rgba(228, 198, 142, 0.25); opacity: 0.62; }
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

    .argument-block, .analysis-placeholder, .challenge-block {
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

    .consensus-board h2 {
        font-size: 2rem;
        margin: 0.2rem 0 0.8rem;
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

    @media (max-width: 720px) {
        .block-container { padding: 1.5rem 1rem 3rem; }
        .input-panel { padding: 1.1rem 1rem 0.8rem; }
        .stHorizontalBlock:has([class*="st-key-choice-"]) {
            grid-template-columns: repeat(2, minmax(0, 1fr)) !important;
        }
        .stHorizontalBlock:has([class*="st-key-perspective-"]) {
            flex-direction: column !important;
        }
        [class*="st-key-perspective-"] { margin-bottom: 1rem; }
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
    with st.form("dilemma_form"):
        dilemma = st.text_area(
            "Ethisches Dilemma eingeben",
            placeholder=(
                "Beschreibe das Szenario, die Betroffenen und die Entscheidung, "
                "vor der sie stehen."
            ),
            height=165,
            label_visibility="collapsed",
        )
        debate_started = st.form_submit_button(
            "Debatte & Analyse starten",
            type="primary",
            disabled=len(selection) != 3,
        )

if debate_started and not dilemma.strip():
    st.warning("Bitte gib zuerst ein ethisches Dilemma ein.")
elif debate_started and len(selection) != 3:
    st.error("Wähle unten genau drei Philosophen aus.")
elif debate_started:
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

Die drei ausgewählten Perspektiven:
{ethos_context}

Formuliere prägnant, eigenständig, scharf argumentiert und in-character.
Kein Chatbot-Einstieg, keine Selbstbeschreibung, kein Hilfsangebot und kein
Meta-Kommentar. Keine Formeln wie "Als KI", "Hier ist meine Analyse" oder
"Gerne helfe ich". Erfinde keine historischen Zitate.

Antworte ausschließlich als JSON-Objekt mit genau einem Schlüssel
{json.dumps(name, ensure_ascii=False)}. Dessen Wert ist ein Objekt mit den
String-Feldern "position", "reasoning" und "conclusion".

Ethisches Dilemma:
{dilemma.strip()}
"""
            system_prompt = (
                f"Schreibe ausschließlich in der philosophischen Perspektive von {name}. "
                f"Stil: {details['voice']} Keine Chatbot-Floskeln, Selbstbezüge, "
                "Begrüßung oder Meta-Kommentare. Keine erfundenen Zitate. "
                "Liefere nur das verlangte prägnante JSON."
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
            st.session_state["debate_dilemma"] = dilemma.strip()
            st.session_state["challenge_responses"] = {}

            consensus_prompt = f"""
Vergleiche die drei folgenden Analysen dieses ethischen Dilemmas.
Bestimme, wie stark die grundlegenden Urteile und Begründungen übereinstimmen.
Gib einen Einigkeits-Score als ganze Prozentzahl von 0 bis 100 an. Benenne
außerdem in wenigen Sätzen den zentralen philosophischen Konflikt.

Ausgewählte Schulen und Kernansichten:
{ethos_context}

Analysen:
{json.dumps(debate, ensure_ascii=False)}

Dilemma:
{dilemma.strip()}

Antworte ausschließlich als JSON-Objekt mit genau diesen Feldern:
{{"agreement_score": 0, "conflict_summary": "Kurze Konfliktbeschreibung"}}
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
                )
                if not valid_consensus:
                    st.error("Die Konsens-Antwort hatte nicht das erwartete JSON-Format.")
                else:
                    st.session_state["consensus"] = consensus
                    st.session_state["consensus_selection"] = selection
                    st.session_state["consensus_dilemma"] = dilemma.strip()
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
        active_key = "active_philosopher"
        if st.session_state.get(active_key) not in selection:
            st.session_state[active_key] = selection[0]
        active_name = st.radio(
            "Aktueller Beitrag",
            options=selection,
            key=active_key,
            horizontal=True,
        )
        result_columns = st.columns(3)
        challenge_responses = st.session_state.get("challenge_responses", {})
        challenge_target: str | None = None
        for column, name in zip(result_columns, selection):
            clicked = render_perspective_card(
                column,
                name,
                saved_debate[name],
                active=name == active_name,
                challenge=challenge_responses.get(name),
                interactive=True,
            )
            if clicked:
                challenge_target = name

        if challenge_target:
            name = challenge_target
            details = PHILOSOPHERS[name]
            challenge_prompt = f"""
Verteidige im sokratischen Kreuzverhör deine gerade formulierte Position.
Sprich als {name}; Stil: {details['voice']}.

Deine Analyse:
{json.dumps(saved_debate[name], ensure_ascii=False)}

Dilemma:
{saved_dilemma}

Nenne den stärksten Einwand, antworte mit einem konkreten Grund und benenne
eine Grenze deiner Position. Prägnant, eigenständig, in-character. Keine
Begrüßung, keine KI-Selbstbeschreibung, kein Hilfsangebot, kein Meta-Kommentar
und keine erfundenen historischen Zitate.

Antworte ausschließlich als JSON: {{"defense": "Kurze Verteidigung"}}
"""
            try:
                with st.spinner(f"{name} verteidigt den Standpunkt ..."):
                    defense_data = request_json(
                        OpenAI(api_key=st.secrets["OPENAI_API_KEY"]),
                        challenge_prompt,
                        f"Schreibe ausschließlich als {name}. Stil: {details['voice']} "
                        "Keine Chatbot-Floskeln oder Selbstbezüge. Antworte nur als JSON.",
                    )
            except KeyError:
                st.error("OPENAI_API_KEY fehlt in den Streamlit-Secrets.")
            except (OpenAIError, ValueError, json.JSONDecodeError) as exc:
                st.error(f"Das Kreuzverhör für {name} ist fehlgeschlagen: {exc}")
            else:
                defense = defense_data.get("defense")
                if (
                    set(defense_data) != {"defense"}
                    or not isinstance(defense, str)
                    or not defense.strip()
                    or contains_assistant_cliche(defense)
                ):
                    st.error("Die Verteidigung hatte nicht das erwartete JSON-Format.")
                else:
                    challenge_responses[name] = defense.strip()
                    st.session_state["challenge_responses"] = challenge_responses
                    st.markdown(
                        f'<div class="challenge-block"><strong>Kreuzverhör — '
                        f'{html.escape(name)}</strong><p>{escape_text(defense)}</p></div>',
                        unsafe_allow_html=True,
                    )
    else:
        st.info(
            "Die drei ausgewählten Perspektiven erscheinen hier, sobald du "
            "oben eine Debatte gestartet hast."
        )
        waiting_columns = st.columns(3)
        for column, name in zip(waiting_columns, selection):
            render_perspective_card(
                column,
                name,
                perspective=None,
                active=False,
            )
else:
    st.info("Wähle unten genau drei Philosophen aus, um das Analyse-Panel vorzubereiten.")

saved_consensus = st.session_state.get("consensus")
if (
    isinstance(saved_consensus, dict)
    and st.session_state.get("consensus_selection") == selection
    and st.session_state.get("consensus_dilemma") == dilemma.strip()
):
    render_consensus(saved_consensus)

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
                    f'src="{portrait_data_uri(name)}" '
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
