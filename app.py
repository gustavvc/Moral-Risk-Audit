import json

import streamlit as st
from openai import OpenAI, OpenAIError


PHILOSOPHERS = ("Kant", "Nietzsche", "Marc Aurel")

st.set_page_config(
    page_title="The Policy & Ethics Simulator",
    page_icon="⚖️",
    layout="wide",
)

st.title("The Policy & Ethics Simulator")
st.write(
    "Untersuche ein politisches Dilemma aus drei philosophischen Perspektiven."
)

with st.form("dilemma_form"):
    dilemma = st.text_area(
        "Politisches Dilemma",
        placeholder="Beschreibe das Dilemma, die Beteiligten und die schwierige Entscheidung ...",
        height=160,
    )
    debate_started = st.form_submit_button("Debatte starten", type="primary")

if debate_started:
    if not dilemma.strip():
        st.warning("Bitte beschreibe zuerst ein politisches Dilemma.")
    else:
        try:
            api_key = st.secrets["OPENAI_API_KEY"]
        except KeyError:
            st.error(
                "Der API-Schlüssel fehlt. Lege OPENAI_API_KEY in "
                "`.streamlit/secrets.toml` oder in den Streamlit-Secrets fest."
            )
        else:
            prompt = f"""
Analysiere das folgende politische Dilemma aus den Perspektiven von Kant,
Nietzsche und Marc Aurel. Gib für jede Perspektive eine eigenständige,
nuancierte und verständliche Analyse. Kennzeichne Interpretationen als solche
und behaupte nicht, eine historische Person könne das konkrete Dilemma
wörtlich beurteilt haben.

Antworte ausschließlich mit einem gültigen JSON-Objekt. Verwende genau die
Schlüssel "Kant", "Nietzsche" und "Marc Aurel". Der Wert jedes Schlüssels muss
ein Objekt mit genau den String-Feldern "position", "reasoning" und
"conclusion" sein.

Dilemma:
{dilemma.strip()}
"""
            with st.spinner("Die philosophische Debatte wird vorbereitet ..."):
                try:
                    client = OpenAI(api_key=api_key)
                    response = client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=[
                            {
                                "role": "system",
                                "content": (
                                    "Du bist ein sorgfältiger, sachlicher "
                                    "Philosophie- und Politikassistent. "
                                    "Befolge das verlangte JSON-Format."
                                ),
                            },
                            {"role": "user", "content": prompt},
                        ],
                        response_format={"type": "json_object"},
                    )
                except OpenAIError as exc:
                    st.error(f"Die Anfrage an OpenAI ist fehlgeschlagen: {exc}")
                else:
                    content = response.choices[0].message.content
                    if not content:
                        st.error("OpenAI hat keine auswertbare Antwort geliefert.")
                    else:
                        try:
                            debate = json.loads(content)
                        except json.JSONDecodeError:
                            st.error("Die Antwort von OpenAI war kein gültiges JSON.")
                        else:
                            valid_response = isinstance(debate, dict) and all(
                                isinstance(debate.get(philosopher), dict)
                                and all(
                                    isinstance(debate[philosopher].get(field), str)
                                    for field in (
                                        "position",
                                        "reasoning",
                                        "conclusion",
                                    )
                                )
                                for philosopher in PHILOSOPHERS
                            )
                            if not valid_response:
                                st.error(
                                    "Die Antwort hatte nicht das erwartete Format "
                                    "für alle drei Philosophen."
                                )
                            else:
                                columns = st.columns(3)
                                for column, philosopher in zip(
                                    columns, PHILOSOPHERS
                                ):
                                    perspective = debate[philosopher]
                                    with column:
                                        st.subheader(philosopher)
                                        st.markdown("**Position**")
                                        st.write(perspective["position"])
                                        st.markdown("**Begründung**")
                                        st.write(perspective["reasoning"])
                                        st.markdown("**Fazit**")
                                        st.write(perspective["conclusion"])