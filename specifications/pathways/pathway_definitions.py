"""Pathway definitions for the kingdombuilders.ai/playbooks library.

Each pathway is a curated journey of 5-8 playbooks designed to produce a
specific transformation. Pathways are the primary front-door for new
visitors; the Archive is the secondary surface.

Each archive-only playbook (one not in any pathway's curated sequence) is
tagged with its nearest pathway via NEAREST_PATHWAY, so the archive grid
card can still show a Pathway descriptor badge.

This file is the source of truth. The homepage, pathway detail pages,
archive cards, and end-of-playbook "next" suggestions all read from here.

Color accent meaning (used in card styling):
  work-reset   = gold       (Manna-aligned)
  identity-walk = purple    (Mirror Series-aligned)
  ai-age       = teal       (tech/future)
  money        = green      (wealth)
  resilience   = copper     (Shield Series-aligned)
  inner-battle = crimson    (Lay It Down-aligned)
  family       = coral      (warmth)
  strategist   = steel blue (decision instruments)
"""

# ============================================================================
# PATHWAYS — primary front-door curriculum
# ============================================================================

PATHWAYS = [
    {
        "slug": "work-reset",
        "order": 1,
        "name": "The Work Reset",
        "tagline": "Make Monday Lighter",
        "audience": "If you got the job you wanted and dread Monday",
        "promise": "Make work feel given again, not demanded. The seven playbooks that walk you from heavy to held.",
        "accent": "gold",
        "estimated_minutes": 210,
        "playbook_sequence": [
            "given",
            "returning",
            "the-source",
            "the-fruit",
            "attend",
            "done-before-you-started",
            "the-spiders-loom",
        ],
        "scripture": '"Moreover it is required in stewards, that a man be found faithful." 1 Corinthians 4:2',
    },
    {
        "slug": "identity-walk",
        "order": 2,
        "name": "The Identity Walk",
        "tagline": "Stop Performing, Start Being",
        "audience": "If you have performed so long you forgot there was someone underneath",
        "promise": "Set down the borrowed shell. Find the self that was always there. Six playbooks from recognition to return.",
        "accent": "purple",
        "estimated_minutes": 180,
        "playbook_sequence": [
            "the-hermit-crabs-shell",
            "the-scorpions-molt",
            "the-vampire-squids-light",
            "the-narrator",
            "the-body-lie",
            "the-source",
        ],
        "scripture": '"For we are his workmanship, created in Christ Jesus unto good works." Ephesians 2:10',
    },
    {
        "slug": "ai-age",
        "order": 3,
        "name": "The AI Age",
        "tagline": "Operate The Future, Don't Fear It",
        "audience": "If you are equal parts curious about AI and afraid of it",
        "promise": "Stop fearing the machines. Start operating them. Eight playbooks on the actual economy and mechanics arriving now.",
        "accent": "teal",
        "estimated_minutes": 270,
        "playbook_sequence": [
            "the-lifted-ceiling",
            "the-new-earning",
            "conductors-playbook",
            "the-mockingbirds-song",
            "the-cuttlefishs-canvas",
            "the-centipedes-march",
            "the-ravens-trial",
            "the-lyrebirds-echo",
        ],
        "scripture": '"And God said, Let us make man in our image, after our likeness: and let them have dominion." Genesis 1:26',
    },
    {
        "slug": "money-architecture",
        "order": 4,
        "name": "The Money Architecture",
        "tagline": "Build Wealth That Compounds",
        "audience": "If money is something that happens to you instead of through you",
        "promise": "From macroeconomics to portfolio sizing. Seven playbooks on the architecture of money in the era you actually live in.",
        "accent": "green",
        "estimated_minutes": 210,
        "playbook_sequence": [
            "the-squirrel-economy",
            "the-cost-ledger",
            "the-lifted-ceiling",
            "the-new-earning",
            "the-octopus-protocol",
            "the-bonsai-method",
            "the-fibonacci-trim",
        ],
        "scripture": '"The blessing of the Lord, it maketh rich, and he addeth no sorrow with it." Proverbs 10:22',
    },
    {
        "slug": "resilience-stack",
        "order": 5,
        "name": "The Resilience Stack",
        "tagline": "Harder To Break, Slower To Burn",
        "audience": "If you are facing something hard right now and need real tools",
        "promise": "Become harder to break without becoming brittle. Seven playbooks on structural protection and antifragile growth.",
        "accent": "copper",
        "estimated_minutes": 210,
        "playbook_sequence": [
            "the-mantis-shrimps-eye",
            "the-porcupines-quills",
            "the-tardigrade-protocol",
            "the-coyotes-laugh",
            "the-pangolins-armor",
            "the-geckos-grip",
            "the-bears-winter",
        ],
        "scripture": '"We are troubled on every side, yet not distressed; we are perplexed, but not in despair." 2 Corinthians 4:8',
    },
    {
        "slug": "inner-battle",
        "order": 6,
        "name": "The Inner Battle",
        "tagline": "Lay Down The Seven Weights",
        "audience": "If you are doing real spiritual formation on the oldest patterns of the soul",
        "promise": "Name, expose, and counter the seven deadly patterns. Eight playbooks built on the desert tradition for modern life.",
        "accent": "crimson",
        "estimated_minutes": 300,
        "playbook_sequence": [
            "lay-it-down",
            "lay-it-down-pride",
            "lay-it-down-envy",
            "lay-it-down-wrath",
            "lay-it-down-sloth",
            "lay-it-down-greed",
            "lay-it-down-gluttony",
            "lay-it-down-lust",
        ],
        "scripture": '"Wherefore seeing we also are compassed about with so great a cloud of witnesses, let us lay aside every weight." Hebrews 12:1',
    },
    {
        "slug": "family-foundation",
        "order": 7,
        "name": "The Family Foundation",
        "tagline": "Hard Conversations, Soft Delivery",
        "audience": "If you have to talk to your kid about the hard things and do not want to lecture",
        "promise": "Dad Talks plus the relational architecture playbooks. Eight playbooks for the conversations that matter most.",
        "accent": "coral",
        "estimated_minutes": 240,
        "playbook_sequence": [
            "dad-talks-the-dopamine-drought",
            "dad-talks-the-mirror-test",
            "dad-talks-the-flinch",
            "dad-talks-the-invisible-contract",
            "dad-talks-the-scoreboard-lie",
            "dad-talks-the-first-punch",
            "the-three-tables",
            "the-roche-limit",
        ],
        "scripture": '"And, ye fathers, provoke not your children to wrath: but bring them up in the nurture and admonition of the Lord." Ephesians 6:4',
    },
    {
        "slug": "strategist-toolkit",
        "order": 8,
        "name": "The Strategist's Toolkit",
        "tagline": "Decide Better, Lead Cleaner",
        "audience": "If you make decisions for other people and want sharper instruments",
        "promise": "From two-fovea focus to pot odds to phase coupling. Seven playbooks on the mechanics of judgment.",
        "accent": "steel-blue",
        "estimated_minutes": 210,
        "playbook_sequence": [
            "the-eagles-lens",
            "the-crows-gambit",
            "the-fireflys-signal",
            "the-foxs-trail",
            "the-starlings-murmuration",
            "the-wolfs-table",
            "the-chameleons-code",
        ],
        "scripture": '"The simple believeth every word: but the prudent man looketh well to his going." Proverbs 14:15',
    },
]


# ============================================================================
# NEAREST_PATHWAY — for archive-only playbooks
# ============================================================================
# Maps every playbook (in pathway OR not) to its primary pathway tag.
# Used by archive grid cards to show a Pathway descriptor badge.
# If a playbook is in a pathway's sequence, that pathway is its primary tag.
# If not, the listed pathway is its nearest thematic home.

NEAREST_PATHWAY = {
    # === In pathway sequences (canonical primary tag) ===
    # Work Reset
    "given": "work-reset",
    "returning": "work-reset",
    "the-fruit": "work-reset",
    "attend": "work-reset",
    "done-before-you-started": "work-reset",
    "the-spiders-loom": "work-reset",
    # Identity Walk
    "the-hermit-crabs-shell": "identity-walk",
    "the-scorpions-molt": "identity-walk",
    "the-vampire-squids-light": "identity-walk",
    "the-narrator": "identity-walk",
    "the-body-lie": "identity-walk",
    "the-source": "identity-walk",  # appears in two pathways; nearest primary = identity-walk
    # AI Age
    "the-lifted-ceiling": "ai-age",
    "the-new-earning": "ai-age",
    "conductors-playbook": "ai-age",
    "the-mockingbirds-song": "ai-age",
    "the-cuttlefishs-canvas": "ai-age",
    "the-centipedes-march": "ai-age",
    "the-ravens-trial": "ai-age",
    "the-lyrebirds-echo": "ai-age",
    "love-the-practice": "ai-age",
    # Money Architecture
    "the-squirrel-economy": "money-architecture",
    "the-cost-ledger": "money-architecture",
    "the-octopus-protocol": "money-architecture",
    "the-bonsai-method": "money-architecture",
    "the-fibonacci-trim": "money-architecture",
    # Resilience Stack
    "the-mantis-shrimps-eye": "resilience-stack",
    "the-porcupines-quills": "resilience-stack",
    "the-tardigrade-protocol": "resilience-stack",
    "the-coyotes-laugh": "resilience-stack",
    "the-pangolins-armor": "resilience-stack",
    "the-geckos-grip": "resilience-stack",
    "the-bears-winter": "resilience-stack",
    # Inner Battle
    "lay-it-down": "inner-battle",
    "lay-it-down-pride": "inner-battle",
    "lay-it-down-envy": "inner-battle",
    "lay-it-down-wrath": "inner-battle",
    "lay-it-down-sloth": "inner-battle",
    "lay-it-down-greed": "inner-battle",
    "lay-it-down-gluttony": "inner-battle",
    "lay-it-down-lust": "inner-battle",
    # Family Foundation
    "dad-talks-the-dopamine-drought": "family-foundation",
    "dad-talks-the-mirror-test": "family-foundation",
    "dad-talks-the-flinch": "family-foundation",
    "dad-talks-the-invisible-contract": "family-foundation",
    "dad-talks-the-scoreboard-lie": "family-foundation",
    "dad-talks-the-first-punch": "family-foundation",
    "the-three-tables": "family-foundation",
    "the-roche-limit": "family-foundation",
    # Strategist's Toolkit
    "the-eagles-lens": "strategist-toolkit",
    "the-crows-gambit": "strategist-toolkit",
    "the-fireflys-signal": "strategist-toolkit",
    "the-foxs-trail": "strategist-toolkit",
    "the-starlings-murmuration": "strategist-toolkit",
    "the-wolfs-table": "strategist-toolkit",
    "the-chameleons-code": "strategist-toolkit",

    # === Archive-only (nearest pathway by theme) ===
    # Work Reset adjacent
    "before-the-garden-returns": "work-reset",  # Eden Pattern foundation
    "the-soil": "work-reset",                    # Eden Pattern stability
    "tending-the-garden": "work-reset",          # Eden Pattern orchestration
    "the-horses-gait": "work-reset",             # burnout / resonant frequency
    "the-gravity-well": "work-reset",            # attention as gravity
    "the-arrival": "work-reset",                 # insertion burn at goal-arrival
    "the-unfinished-song": "work-reset",         # productive tension for unfinished work

    # Identity Walk adjacent
    "the-moths-flame": "identity-walk",          # counterfeit north / signal corruption
    "the-kintsugi-bowl": "identity-walk",        # the Kintsugi Protocol / inner repair

    # AI Age adjacent
    "the-termite-cathedral": "ai-age",           # emergence / stigmergy

    # Money Architecture adjacent
    "the-mycelium-network": "money-architecture",  # cooperation game theory

    # Strategist's Toolkit adjacent
    "the-ghost-frame": "strategist-toolkit",     # predictive brain / mental models
    "the-ant-network": "strategist-toolkit",     # verification trust

    # Note: the-salmon-journey, the-compass-rose, the-lighthouse-keepers-log
    # are in seed_playbooks.py but have no asset file (planned/placeholder).
    # They will not appear in the archive grid until their assets are built.

    # A Process Model / Philosophy — these get the "philosophy" sub-label in archive
    # but their nearest active pathway is Identity Walk (Tide Pool, Otter) or Resilience (Whale, Elephant, Butterfly, Bee)
    "the-tide-pools-echo": "identity-walk",
    "the-otters-play": "identity-walk",
    "the-whales-breath": "resilience-stack",
    "the-elephants-ground": "resilience-stack",
    "the-butterflys-crossing": "resilience-stack",
    "the-bees-dance": "family-foundation",       # communication
}


# ============================================================================
# Helpers
# ============================================================================

def get_pathway(slug):
    """Return the pathway dict for a given slug, or None."""
    return next((p for p in PATHWAYS if p["slug"] == slug), None)


def get_pathway_for_playbook(playbook_slug):
    """Return the pathway slug a playbook belongs to (primary) or its nearest tag."""
    return NEAREST_PATHWAY.get(playbook_slug)


def get_playbook_position_in_pathway(playbook_slug, pathway_slug):
    """Return (current_step, total_steps) for a playbook within a pathway, or None."""
    p = get_pathway(pathway_slug)
    if not p:
        return None
    seq = p["playbook_sequence"]
    if playbook_slug not in seq:
        return None
    return (seq.index(playbook_slug) + 1, len(seq))


def get_next_playbook_in_pathway(playbook_slug, pathway_slug):
    """Return the next playbook slug in the pathway, or None if last."""
    pos = get_playbook_position_in_pathway(playbook_slug, pathway_slug)
    if not pos:
        return None
    current, total = pos
    if current >= total:
        return None
    p = get_pathway(pathway_slug)
    return p["playbook_sequence"][current]  # current is 1-indexed; this is next
