"""Series definitions — canonical reading order for each named series.

The archive grid uses this to render "Part X of N" badges and to sort rows
within each series so a reader can click through in order. Add a new
playbook to the end of its series list to extend that series.

Slugs match `playbook_registry.SLUG_TO_FILE` keys.
"""

# series_slug -> ordered list of playbook slugs (narrative reading order)
SERIES_SEQUENCE: dict[str, list[str]] = {
    "the-attending": [
        "attend",
        "done-before-you-started",
    ],
    "manna": [
        "given",
        "returning",
    ],
    "eden-pattern": [
        "before-the-garden-returns",
        "the-source",
        "the-soil",
        "the-fruit",
        "tending-the-garden",
    ],
    "lay-it-down": [
        "lay-it-down",
        "lay-it-down-pride",
        "lay-it-down-envy",
        "lay-it-down-wrath",
        "lay-it-down-sloth",
        "lay-it-down-greed",
        "lay-it-down-gluttony",
        "lay-it-down-lust",
    ],
    "dad-talks": [
        "dad-talks-the-dopamine-drought",
        "dad-talks-the-mirror-test",
        "dad-talks-the-flinch",
        "dad-talks-the-invisible-contract",
        "dad-talks-the-scoreboard-lie",
        "dad-talks-the-first-punch",
    ],
    "how-ai-works": [
        "the-mockingbirds-song",
        "the-cuttlefishs-canvas",
        "the-centipedes-march",
        "the-lyrebirds-echo",
        "the-ravens-trial",
    ],
    "ai-economy": [
        "conductors-playbook",
        "the-lifted-ceiling",
        "the-new-earning",
    ],
    "a-process-model": [
        "the-tide-pools-echo",
        "the-whales-breath",
        "the-butterflys-crossing",
        "the-elephants-ground",
        "the-bees-dance",
        "the-otters-play",
    ],
    "the-mirror-series": [
        "the-hermit-crabs-shell",
        "the-scorpions-molt",
        "the-vampire-squids-light",
    ],
    "the-shield-series": [
        "the-mantis-shrimps-eye",
        "the-porcupines-quills",
        "the-tardigrade-protocol",
    ],
}


def get_series_position(slug: str) -> tuple[str, int, int] | None:
    """Return (series_slug, position_1indexed, total) for slug, or None.

    Position is 1-indexed so it can be shown directly in UI ("3 of 6").
    """
    for series_slug, seq in SERIES_SEQUENCE.items():
        if slug in seq:
            return series_slug, seq.index(slug) + 1, len(seq)
    return None


SERIES_DISPLAY_NAME: dict[str, str] = {
    "the-attending": "The Attending",
    "manna": "Manna",
    "eden-pattern": "Eden Pattern",
    "lay-it-down": "Lay It Down",
    "dad-talks": "Dad Talks",
    "how-ai-works": "How AI Works",
    "ai-economy": "AI Economy",
    "a-process-model": "A Process Model",
    "the-mirror-series": "Mirror Series",
    "the-shield-series": "Shield Series",
}


# Short clarifier shown beside the series name. Mirror and Shield are the
# inverse-paired narcissism series — Mirror is the inward examination
# (am I the narcissist?), Shield is the outward defense (someone in my life
# is). Stating both halves makes the structural relationship readable
# without opening either playbook.
SERIES_DESCRIPTION: dict[str, str] = {
    "the-attending": "The practice of staying with the work when you want to leave.",
    "manna": "The faith pattern that converts heavy work back into given work.",
    "eden-pattern": "The post scarcity blueprint hidden in the first garden.",
    "lay-it-down": "The seven deadly sins decoded as modern behavior patterns.",
    "dad-talks": "The hard conversations a father should have with his sons.",
    "how-ai-works": "Mental models for the machinery underneath modern AI.",
    "ai-economy": "How wealth moves in an economy where AI does the work.",
    "a-process-model": "Six animals that map the phases of any transformation.",
    "the-mirror-series": "Narcissism examined from the inside. For the reader who suspects the pattern lives in them and wants to heal it.",
    "the-shield-series": "Narcissism examined from the outside. For the reader being targeted by a narcissist who needs sight, armor, and a way to outlast them.",
}
