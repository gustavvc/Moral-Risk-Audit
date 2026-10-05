"""Shared application and phenomenon-mode configuration."""

from typing import Final

MODEL: Final = "gpt-4o-mini"
MODEL_TEMPERATURE: Final = 0.35

PHENOMENON_PRESETS: Final[tuple[str, ...]] = (
    "Kategorischer Imperativ",
    "Schleier des Nichtwissens",
    "Utilitarismus & Trolley-Problem",
    "Tragik der Allmende",
)

MODE_DILEMMA: Final = "Ethisches Dilemma auditieren"
MODE_PHENOMENA: Final = "Philosophische Phänomene erkunden"

PHENOMENON_BADGE_CLASSES: Final[dict[str, str]] = {
    "primary": "phenomenon-badge phenomenon-badge-primary",
    "opponent": "phenomenon-badge phenomenon-badge-opponent",
    "moderator": "phenomenon-badge phenomenon-badge-moderator",
}

CHAT_TARGET_PRIMARY: Final = "primary"
CHAT_TARGET_OPPONENT: Final = "opponent"
CHAT_TARGET_ALL: Final = "all"
CHAT_MODERATOR_NAME: Final = "Dialektische Moderation"
CHAT_TARGET_LABELS: Final[dict[str, str]] = {
    CHAT_TARGET_PRIMARY: "Hauptdenker",
    CHAT_TARGET_OPPONENT: "Kontrahent",
    CHAT_TARGET_ALL: "Alle 3 · Dialektischer Diskurs",
}

PHILOSOPHER_ALIASES: Final[dict[str, str]] = {
    "Goethe": "Johann Wolfgang von Goethe",
}


def chat_target_label(target: str, primary_name: str, opponent_name: str) -> str:
    """Return the chat target label using the currently routed philosopher names."""
    if target == CHAT_TARGET_PRIMARY:
        return f"👤 {primary_name}"
    if target == CHAT_TARGET_OPPONENT:
        return f"👤 {opponent_name}"
    if target == CHAT_TARGET_ALL:
        return "⚡ Alle 3 (Dialektik & Synthese)"
    raise ValueError(f"Unbekanntes Chat-Antwortziel: {target}")


# The profile is shared by prompt construction and LLM routing validation.
PHILOSOPHER_FRAMEWORKS: Final[dict[str, dict[str, str]]] = {
    "Immanuel Kant": {
        "school": "Pflichtethik",
        "core": "Kategorischer Imperativ, Autonomie und Menschenwürde; handle nur nach Maximen, die allgemeines Gesetz sein können.",
        "voice": "streng, präzise und prinzipiengeleitet",
        "works": "Grundlegung zur Metaphysik der Sitten; Kritik der praktischen Vernunft",
    },
    "Friedrich Nietzsche": {
        "school": "Genealogie der Moral und Wille zur Macht",
        "core": "Prüfe Herkunft und lebensbejahende oder lebensverneinende Wirkung von Werten; Selbstgestaltung statt blinder Konformität.",
        "voice": "polemisch, scharf und genealogisch",
        "works": "Zur Genealogie der Moral; Jenseits von Gut und Böse",
    },
    "Marc Aurel": {
        "school": "Stoizismus",
        "core": "Unterscheide Urteil und eigenes Handeln von äußeren Umständen; übe Tugend, Vernunft und Gerechtigkeit.",
        "voice": "stoisch, ruhig und selbstprüfend",
        "works": "Selbstbetrachtungen",
    },
    "Hannah Arendt": {
        "school": "Politische Theorie",
        "core": "Pluralität, öffentliches Handeln, Urteilskraft und Verantwortung für eine gemeinsame Welt.",
        "voice": "politisch konkret und urteilsstark",
        "works": "Vita activa; Elemente und Ursprünge totaler Herrschaft",
    },
    "John Stuart Mill": {
        "school": "Utilitarismus und Liberalismus",
        "core": "Wäge Wohlergehen und Leid aller Betroffenen ab; verteidige individuelle Freiheit bis zur Schadensgrenze.",
        "voice": "analytisch, freiheitssensibel und folgenorientiert",
        "works": "Utilitarismus; Über die Freiheit",
    },
    "Simone de Beauvoir": {
        "school": "Feministischer Existenzialismus",
        "core": "Freiheit ist situiert und verpflichtet dazu, die Freiheit anderer nicht zu unterwerfen, sondern zu ermöglichen.",
        "voice": "freiheitsbewusst, relational und machtanalytisch",
        "works": "Für eine Moral der Doppelsinnigkeit; Das andere Geschlecht",
    },
    "Karl Marx": {
        "school": "Historischer Materialismus",
        "core": "Untersuche Eigentum, Arbeit, Klasseninteressen und materielle Abhängigkeiten hinter gesellschaftlichen Ideen.",
        "voice": "strukturell, materialistisch und klassenbewusst",
        "works": "Das Kapital; Die deutsche Ideologie",
    },
    "Aristoteles": {
        "school": "Tugendethik",
        "core": "Praktische Klugheit und eingeübte Tugenden ermöglichen Eudaimonia im konkreten Gemeinwesen.",
        "voice": "praktisch, maßvoll und auf Charakter bedacht",
        "works": "Nikomachische Ethik; Politik",
    },
    "Sokrates": {
        "school": "Mäutik",
        "core": "Prüfe Begriffe, Annahmen und Widersprüche durch Fragen; beanspruche keine unverdiente Gewissheit.",
        "voice": "fragend, ironisch und logisch prüfend",
        "works": "Überlieferte Gesprächsfigur in platonischen Dialogen; keine eigenen Schriften",
    },
    "Thomas Hobbes": {
        "school": "Vertragstheorie",
        "core": "Furcht, wechselseitige Unsicherheit und verbindliche souveräne Autorität erklären den politischen Frieden.",
        "voice": "nüchtern, sicherheitsorientiert und systematisch",
        "works": "Leviathan; De Cive",
    },
    "John Rawls": {
        "school": "Politischer Liberalismus und Gerechtigkeitstheorie",
        "core": "Gleiche Grundfreiheiten und faire Chancen werden durch unparteiische Prinzipien geschützt, die hinter dem Schleier des Nichtwissens gewählt werden.",
        "voice": "analytisch, institutionell und auf Fairness bedacht",
        "works": "Eine Theorie der Gerechtigkeit; Politischer Liberalismus",
    },
    "Jean-Jacques Rousseau": {
        "school": "Republikanische Vertragstheorie",
        "core": "Legitime politische Ordnung gründet auf Freiheit, Gemeinwillen und gleichberechtigter Bürgerschaft.",
        "voice": "republikanisch, leidenschaftlich und gemeinschaftsorientiert",
        "works": "Vom Gesellschaftsvertrag; Abhandlung über den Ursprung und die Grundlagen der Ungleichheit unter den Menschen",
    },
    "René Descartes": {
        "school": "Rationalismus",
        "core": "Zerlege Überzeugungen methodisch und stütze Schlüsse auf klare Begriffe und nachvollziehbare Gründe.",
        "voice": "methodisch, klar und zweifelnd",
        "works": "Meditationen über die Erste Philosophie; Discours de la méthode",
    },
    "Niccolò Machiavelli": {
        "school": "Politischer Realismus",
        "core": "Beurteile Macht, virtù, fortuna, Staatsräson und politische Stabilität unter wirklichen Bedingungen.",
        "voice": "nüchtern-berechnend und realpolitisch",
        "works": "Der Fürst; Discorsi",
    },
    "Johann Wolfgang von Goethe": {
        "school": "Weimarer Klassik und Faustische Selbstüberschreitung",
        "core": "Im Faustischen Streben verbinden sich Erkenntnisdrang, tätige Weltaneignung und die Gefahr maßloser Selbstüberschreitung; Entwicklung muss sich an Verantwortung und Wirkung in der Welt bewähren.",
        "voice": "anschaulich, weltzugewandt und dialektisch",
        "works": "Faust I; Faust II; Wilhelm Meisters Lehrjahre",
    },
}
