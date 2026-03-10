"""
Seed script — populates playbook_tags and playbook_connections for the
Thread System discovery engine.

Usage:
    python -m scripts.seed_discovery
"""

import asyncio
from pathlib import Path

from sqlalchemy import select

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from api.database import async_session
from api.models.playbook import Playbook
from api.models.discovery import PlaybookTag, PlaybookConnection


# ---------------------------------------------------------------------------
# Tag definitions: slug -> [(tag, weight), ...]
# Weight 1.0 = core theme, 0.7 = strong secondary, 0.4 = subtle thread
# ---------------------------------------------------------------------------
TAGS = {
    "conductors-playbook": [
        ("mastery", 1.0), ("ai", 1.0), ("creativity", 0.9), ("productivity", 0.8),
        ("taste", 0.8), ("convergence", 0.7), ("leadership", 0.5), ("discipline", 0.5),
    ],
    "the-ant-network": [
        ("trust", 1.0), ("decentralization", 1.0), ("systems", 0.9), ("technology", 0.8),
        ("money", 0.6), ("community", 0.5), ("faith", 0.3),
    ],
    "the-squirrel-economy": [
        ("money", 1.0), ("economics", 1.0), ("saving", 0.9), ("risk", 0.8),
        ("systems", 0.7), ("discipline", 0.6), ("patience", 0.5),
    ],
    "the-salmon-journey": [
        ("money", 1.0), ("finance", 1.0), ("growth", 0.9), ("patience", 0.8),
        ("discipline", 0.7), ("sacrifice", 0.5), ("faith", 0.4),
    ],
    "the-wolfs-table": [
        ("negotiation", 1.0), ("relationships", 1.0), ("trust", 0.9), ("strategy", 0.8),
        ("power", 0.7), ("community", 0.6), ("deception", 0.5),
    ],
    "the-crows-gambit": [
        ("strategy", 1.0), ("game_theory", 1.0), ("deception", 0.8), ("trust", 0.7),
        ("risk", 0.7), ("negotiation", 0.6), ("systems", 0.4),
    ],
    "the-narrator": [
        ("identity", 1.0), ("self_awareness", 1.0), ("narrative", 0.9), ("courage", 0.7),
        ("vulnerability", 0.7), ("faith", 0.4), ("fear", 0.5),
    ],
    "the-eagles-lens": [
        ("leadership", 1.0), ("decision_making", 1.0), ("clarity", 0.9), ("perception", 0.8),
        ("discipline", 0.7), ("courage", 0.5), ("strategy", 0.5),
    ],
    "the-lighthouse-keepers-log": [
        ("resilience", 1.0), ("endurance", 0.9), ("faith", 0.8), ("discipline", 0.7),
        ("fear", 0.6), ("identity", 0.5), ("patience", 0.5),
    ],
    "the-octopus-protocol": [
        ("money", 1.0), ("systems", 1.0), ("diversification", 0.9), ("strategy", 0.8),
        ("risk", 0.7), ("growth", 0.6), ("discipline", 0.5),
    ],
    "the-starlings-murmuration": [
        ("leadership", 1.0), ("community", 1.0), ("influence", 0.9), ("trust", 0.8),
        ("systems", 0.7), ("relationships", 0.6), ("self_awareness", 0.4),
    ],
    "the-chameleons-code": [
        ("communication", 1.0), ("adaptation", 1.0), ("perception", 0.8), ("relationships", 0.7),
        ("identity", 0.6), ("trust", 0.5), ("self_awareness", 0.5),
    ],
    "the-spiders-loom": [
        ("systems", 1.0), ("networks", 1.0), ("productivity", 0.8), ("patience", 0.7),
        ("strategy", 0.6), ("creativity", 0.5), ("discipline", 0.5),
    ],
    "the-geckos-grip": [
        ("resilience", 1.0), ("recovery", 1.0), ("adaptation", 0.8), ("courage", 0.7),
        ("endurance", 0.7), ("fear", 0.5), ("growth", 0.5),
    ],
    "the-fireflys-signal": [
        ("authenticity", 1.0), ("strategy", 0.9), ("trust", 0.8), ("deception", 0.7),
        ("communication", 0.6), ("vulnerability", 0.5), ("identity", 0.5),
    ],
    "the-foxs-trail": [
        ("strategy", 1.0), ("adaptation", 0.9), ("perception", 0.8), ("deception", 0.7),
        ("systems", 0.6), ("risk", 0.5), ("creativity", 0.4),
    ],
    "the-moths-flame": [
        ("desire", 1.0), ("self_awareness", 0.9), ("fear", 0.8), ("discipline", 0.7),
        ("sacrifice", 0.6), ("identity", 0.5), ("faith", 0.4),
    ],
    "the-bears-winter": [
        ("patience", 1.0), ("endurance", 1.0), ("rest", 0.9), ("discipline", 0.7),
        ("fear", 0.6), ("growth", 0.5), ("faith", 0.4),
    ],
    "the-coyotes-laugh": [
        ("resilience", 1.0), ("adaptation", 0.9), ("courage", 0.8), ("creativity", 0.7),
        ("identity", 0.6), ("fear", 0.5), ("growth", 0.4),
    ],
    "the-pangolins-armor": [
        ("boundaries", 1.0), ("self_awareness", 0.9), ("vulnerability", 0.8),
        ("fear", 0.7), ("identity", 0.6), ("courage", 0.5), ("faith", 0.4),
    ],
    "the-horses-gait": [
        ("productivity", 1.0), ("rhythm", 1.0), ("discipline", 0.8), ("endurance", 0.7),
        ("patience", 0.6), ("mastery", 0.5), ("growth", 0.5),
    ],
    "the-compass-rose": [
        ("navigation", 1.0), ("history", 1.0), ("decision_making", 0.8), ("courage", 0.7),
        ("faith", 0.6), ("identity", 0.5), ("leadership", 0.4),
    ],
    "the-cost-ledger": [
        ("money", 1.0), ("sacrifice", 1.0), ("self_awareness", 0.8), ("identity", 0.7),
        ("discipline", 0.6), ("fear", 0.5), ("courage", 0.4),
    ],
    "the-ghost-frame": [
        ("perception", 1.0), ("self_awareness", 1.0), ("narrative", 0.9), ("identity", 0.8),
        ("vulnerability", 0.6), ("courage", 0.5), ("fear", 0.5),
    ],
    "the-gravity-well": [
        ("focus", 1.0), ("productivity", 1.0), ("discipline", 0.9), ("identity", 0.7),
        ("sacrifice", 0.6), ("courage", 0.5), ("systems", 0.4),
    ],
    "the-mockingbirds-song": [
        ("ai", 1.0), ("technology", 1.0), ("communication", 0.8), ("creativity", 0.7),
        ("systems", 0.7), ("perception", 0.5), ("mastery", 0.4),
    ],
    # --- Lay It Down series (faith) ---
    "lay-it-down": [
        ("faith", 1.0), ("surrender", 1.0), ("identity", 0.8), ("courage", 0.7),
        ("vulnerability", 0.7), ("sacrifice", 0.6), ("fear", 0.5),
    ],
    "lay-it-down-pride": [
        ("faith", 1.0), ("surrender", 1.0), ("identity", 0.9), ("leadership", 0.7),
        ("self_awareness", 0.7), ("vulnerability", 0.6), ("courage", 0.5),
    ],
    "lay-it-down-envy": [
        ("faith", 1.0), ("surrender", 1.0), ("identity", 0.9), ("self_awareness", 0.8),
        ("relationships", 0.6), ("fear", 0.5), ("courage", 0.5),
    ],
    "lay-it-down-wrath": [
        ("faith", 1.0), ("surrender", 1.0), ("relationships", 0.9), ("fear", 0.8),
        ("courage", 0.7), ("vulnerability", 0.6), ("self_awareness", 0.5),
    ],
    "lay-it-down-sloth": [
        ("faith", 1.0), ("surrender", 1.0), ("discipline", 0.9), ("productivity", 0.7),
        ("patience", 0.6), ("identity", 0.5), ("courage", 0.5),
    ],
    "lay-it-down-greed": [
        ("faith", 1.0), ("surrender", 1.0), ("money", 0.9), ("sacrifice", 0.8),
        ("discipline", 0.6), ("identity", 0.5), ("self_awareness", 0.5),
    ],
    "lay-it-down-gluttony": [
        ("faith", 1.0), ("surrender", 1.0), ("discipline", 0.9), ("desire", 0.8),
        ("self_awareness", 0.7), ("boundaries", 0.6), ("identity", 0.5),
    ],
    "lay-it-down-lust": [
        ("faith", 1.0), ("surrender", 1.0), ("desire", 0.9), ("identity", 0.8),
        ("vulnerability", 0.7), ("boundaries", 0.6), ("self_awareness", 0.5),
    ],
    # --- A Process Model series (philosophy) ---
    "the-tide-pools-echo": [
        ("philosophy", 1.0), ("systems", 0.9), ("perception", 0.8), ("patience", 0.7),
        ("growth", 0.6), ("self_awareness", 0.5), ("adaptation", 0.4),
    ],
    "the-whales-breath": [
        ("philosophy", 1.0), ("rest", 0.9), ("endurance", 0.8), ("patience", 0.7),
        ("self_awareness", 0.6), ("rhythm", 0.5), ("growth", 0.4),
    ],
    "the-butterflys-crossing": [
        ("philosophy", 1.0), ("transformation", 1.0), ("courage", 0.8), ("identity", 0.7),
        ("growth", 0.7), ("sacrifice", 0.5), ("faith", 0.4),
    ],
    "the-elephants-ground": [
        ("philosophy", 1.0), ("endurance", 0.9), ("community", 0.8), ("trust", 0.7),
        ("leadership", 0.6), ("patience", 0.5), ("identity", 0.4),
    ],
    "the-bees-dance": [
        ("philosophy", 1.0), ("communication", 0.9), ("community", 0.8), ("systems", 0.7),
        ("trust", 0.6), ("leadership", 0.5), ("creativity", 0.4),
    ],
    "the-otters-play": [
        ("philosophy", 1.0), ("creativity", 0.9), ("rest", 0.8), ("growth", 0.7),
        ("relationships", 0.6), ("community", 0.5), ("identity", 0.4),
    ],
    # --- Newer playbooks ---
    "dad-talks-the-dopamine-drought": [
        ("discipline", 1.0), ("self_awareness", 0.9), ("technology", 0.8),
        ("identity", 0.7), ("relationships", 0.6), ("fear", 0.5), ("growth", 0.4),
    ],
    "dad-talks-the-mirror-test": [
        ("identity", 1.0), ("self_awareness", 1.0), ("courage", 0.8),
        ("relationships", 0.7), ("vulnerability", 0.6), ("growth", 0.5), ("faith", 0.4),
    ],
    "the-arrival": [
        ("identity", 1.0), ("courage", 0.9), ("growth", 0.8),
        ("faith", 0.7), ("fear", 0.6), ("sacrifice", 0.5), ("vulnerability", 0.4),
    ],
    "the-body-lie": [
        ("perception", 1.0), ("self_awareness", 1.0), ("identity", 0.8),
        ("fear", 0.7), ("vulnerability", 0.6), ("courage", 0.5), ("discipline", 0.4),
    ],
    "the-mycelium-network": [
        ("systems", 1.0), ("community", 1.0), ("trust", 0.8), ("networks", 0.8),
        ("growth", 0.6), ("relationships", 0.5), ("leadership", 0.4),
    ],
    "the-termite-cathedral": [
        ("systems", 1.0), ("community", 1.0), ("patience", 0.8), ("leadership", 0.7),
        ("discipline", 0.6), ("trust", 0.5), ("growth", 0.5),
    ],
    "the-bonsai-method": [
        ("money", 1.0), ("discipline", 1.0), ("patience", 0.8), ("growth", 0.7),
        ("sacrifice", 0.6), ("systems", 0.5), ("self_awareness", 0.4),
    ],
    "the-fibonacci-trim": [
        ("money", 1.0), ("systems", 0.9), ("discipline", 0.8), ("growth", 0.7),
        ("patience", 0.6), ("strategy", 0.5), ("self_awareness", 0.4),
    ],
    "the-mantis-shrimps-eye": [
        ("narcissism", 1.0), ("perception", 1.0), ("manipulation", 0.9), ("self_awareness", 0.8),
        ("fear", 0.7), ("identity", 0.6), ("courage", 0.5), ("discipline", 0.4),
    ],
    "the-porcupines-quills": [
        ("narcissism", 1.0), ("boundaries", 1.0), ("systems", 0.8), ("discipline", 0.7),
        ("self_awareness", 0.7), ("fear", 0.6), ("identity", 0.5), ("courage", 0.4),
    ],
    "the-tardigrade-protocol": [
        ("narcissism", 1.0), ("resilience", 1.0), ("survival", 0.9), ("courage", 0.8),
        ("fear", 0.7), ("self_awareness", 0.6), ("identity", 0.5), ("growth", 0.4),
    ],
    "the-hermit-crabs-shell": [
        ("narcissism", 1.0), ("identity", 1.0), ("self_awareness", 0.9), ("vulnerability", 0.8),
        ("fear", 0.7), ("perception", 0.6), ("courage", 0.5), ("growth", 0.4),
    ],
    "the-scorpions-molt": [
        ("narcissism", 1.0), ("vulnerability", 1.0), ("courage", 0.9), ("discipline", 0.8),
        ("self_awareness", 0.7), ("fear", 0.7), ("growth", 0.6), ("identity", 0.5),
    ],
    "the-vampire-squids-light": [
        ("narcissism", 1.0), ("self_awareness", 1.0), ("growth", 0.9), ("identity", 0.8),
        ("courage", 0.7), ("vulnerability", 0.7), ("resilience", 0.6), ("faith", 0.4),
    ],
}


# ---------------------------------------------------------------------------
# Connection definitions: source_slug -> [(type, target_slug, teaser, reason)]
# Types: deeper, bridge, surprise
# ---------------------------------------------------------------------------
CONNECTIONS = {
    # --- Conductor's Playbook ---
    "conductors-playbook": [
        ("deeper", "the-mockingbirds-song",
         "The AI system behind the creativity",
         "Both explore how AI and human creativity interact"),
        ("bridge", "the-eagles-lens",
         "From creating to deciding. The lens sharpens what the conductor composes.",
         "Creativity without clear decision making wastes potential"),
        ("surprise", "lay-it-down-pride",
         "What happens when mastery becomes your identity",
         "The conductor masters the craft; pride explores when mastery owns you instead"),
    ],
    # --- The Ant Network ---
    "the-ant-network": [
        ("deeper", "the-spiders-loom",
         "From decentralized trust to the architecture of networks",
         "Both explore how systems build strength without central control"),
        ("bridge", "the-starlings-murmuration",
         "From digital networks to human ones. Same principle, different species.",
         "Decentralized coordination appears in nature and technology alike"),
        ("surprise", "lay-it-down",
         "Both are about trusting a system bigger than yourself",
         "The ant trusts the colony; faith asks you to trust something larger too"),
    ],
    # --- The Squirrel Economy ---
    "the-squirrel-economy": [
        ("deeper", "the-octopus-protocol",
         "From understanding money to building multiple income streams",
         "Once you understand economics, diversification is the next move"),
        ("bridge", "the-bears-winter",
         "Saving and waiting. The squirrel stores; the bear endures the wait.",
         "Both explore the discipline of preparation and patience"),
        ("surprise", "lay-it-down-greed",
         "What if saving becomes hoarding? When enough is never enough.",
         "The squirrel saves wisely; greed asks when saving becomes a trap"),
    ],
    # --- The Salmon Journey ---
    "the-salmon-journey": [
        ("deeper", "the-bonsai-method",
         "From growing money to pruning it. Intentional finance.",
         "Both teach financial discipline through natural metaphors"),
        ("bridge", "the-horses-gait",
         "The salmon swims upstream; the horse finds its rhythm. Both move with purpose.",
         "Financial growth and productive rhythm share the same discipline"),
        ("surprise", "the-butterflys-crossing",
         "The salmon and the butterfly both make one great journey. Neither comes back the same.",
         "Transformation through a journey that costs everything"),
    ],
    # --- The Wolf's Table ---
    "the-wolfs-table": [
        ("deeper", "the-crows-gambit",
         "From the table to the board. Negotiation meets game theory.",
         "Both explore strategic interaction between competing parties"),
        ("bridge", "the-chameleons-code",
         "The wolf reads the room. The chameleon adapts to it.",
         "Social strategy through different lenses: power vs. adaptation"),
        ("surprise", "lay-it-down-wrath",
         "What happens when the negotiation breaks down and anger takes the table",
         "The wolf negotiates with control; wrath is what happens without it"),
    ],
    # --- The Crow's Gambit ---
    "the-crows-gambit": [
        ("deeper", "the-foxs-trail",
         "From game theory to strategic adaptation in the wild",
         "Both explore deception, strategy, and reading opponents"),
        ("bridge", "the-fireflys-signal",
         "The crow bluffs. The firefly signals truth. What happens when signals lie?",
         "Strategy through deception vs. strategy through authenticity"),
        ("surprise", "the-lighthouse-keepers-log",
         "What if the smartest strategy is simply to endure?",
         "The crow outthinks its problems; the lighthouse keeper outlasts them"),
    ],
    # --- The Narrator ---
    "the-narrator": [
        ("deeper", "the-ghost-frame",
         "From rewriting your story to seeing the frames that shaped it",
         "The narrator writes the story; the ghost frame reveals the invisible lens"),
        ("bridge", "the-chameleons-code",
         "Both ask: who are you when nobody is watching?",
         "Identity through narrative vs. identity through adaptation"),
        ("surprise", "the-tide-pools-echo",
         "Your identity is not fixed. It echoes and shifts like a tide pool.",
         "The narrator rewrites the story; the tide pool shows nothing is permanent"),
    ],
    # --- The Eagle's Lens ---
    "the-eagles-lens": [
        ("deeper", "the-compass-rose",
         "From sharp decisions to navigating the unknown",
         "Both teach decision making but at different altitudes"),
        ("bridge", "the-gravity-well",
         "The eagle sees everything. The gravity well asks: what are you pulled toward?",
         "Clarity of vision meets the invisible forces that shape your choices"),
        ("surprise", "lay-it-down-pride",
         "The eagle sees from above. But what if that vantage point becomes superiority?",
         "Leadership clarity can become pride when the high view makes you feel higher"),
    ],
    # --- The Lighthouse Keeper's Log ---
    "the-lighthouse-keepers-log": [
        ("deeper", "the-geckos-grip",
         "From enduring the storm to recovering after it",
         "Both explore resilience but at different phases: during vs. after"),
        ("bridge", "the-bears-winter",
         "The lighthouse stands through the storm. The bear sleeps through the winter. Both survive by staying.",
         "Two kinds of endurance: vigilance vs. rest"),
        ("surprise", "the-bees-dance",
         "The keeper works alone. The hive works together. Which kind of strength do you need?",
         "Solitary endurance meets collective communication"),
    ],
    # --- The Octopus Protocol ---
    "the-octopus-protocol": [
        ("deeper", "the-fibonacci-trim",
         "From building income arms to trimming what does not work",
         "Both are advanced finance: building streams then optimizing them"),
        ("bridge", "the-spiders-loom",
         "Eight arms, eight connections. Both build systems with multiple touch points.",
         "Diversification in finance mirrors network architecture"),
        ("surprise", "lay-it-down-sloth",
         "What if building all those arms becomes an excuse to avoid the real work?",
         "Busy diversification can mask the sloth of avoiding your true calling"),
    ],
    # --- The Starling's Murmuration ---
    "the-starlings-murmuration": [
        ("deeper", "the-elephants-ground",
         "From flying together to standing together. Two forms of collective strength.",
         "Both explore how groups create something greater than individuals"),
        ("bridge", "the-mycelium-network",
         "The starlings move as one above ground. The mycelium connects below.",
         "Visible collective intelligence meets invisible networks"),
        ("surprise", "lay-it-down-envy",
         "You are shaped by your seven closest. What happens when comparison replaces connection?",
         "Murmuration is about healthy influence; envy is its shadow"),
    ],
    # --- The Chameleon's Code ---
    "the-chameleons-code": [
        ("deeper", "the-fireflys-signal",
         "From adapting your signal to choosing when to shine it",
         "Both explore communication authenticity vs. strategic signaling"),
        ("bridge", "the-narrator",
         "The chameleon changes color. The narrator changes story. Both ask who you really are.",
         "Adaptation and identity through different metaphors"),
        ("surprise", "the-whales-breath",
         "What if the best communication is silence?",
         "The chameleon adapts constantly; the whale teaches the power of pausing"),
    ],
    # --- The Spider's Loom ---
    "the-spiders-loom": [
        ("deeper", "the-termite-cathedral",
         "From individual networks to collective architecture",
         "Both explore building something larger than yourself, thread by thread"),
        ("bridge", "the-ant-network",
         "The spider weaves alone. The ant builds with millions. Different scales, same principle.",
         "Network architecture at individual vs. collective scales"),
        ("surprise", "the-otters-play",
         "The spider weaves with precision. What if the web also needs play?",
         "Disciplined creation benefits from the looseness of play"),
    ],
    # --- The Gecko's Grip ---
    "the-geckos-grip": [
        ("deeper", "the-coyotes-laugh",
         "From recovery to finding joy in the comeback",
         "Both explore resilience: the gecko grips; the coyote laughs"),
        ("bridge", "the-pangolins-armor",
         "The gecko grips the wall. The pangolin rolls into armor. Two ways to survive.",
         "Active resilience vs. protective withdrawal"),
        ("surprise", "lay-it-down-wrath",
         "Sometimes what you are gripping is anger, not the wall",
         "Recovery means knowing what to hold and what to release"),
    ],
    # --- The Firefly's Signal ---
    "the-fireflys-signal": [
        ("deeper", "the-foxs-trail",
         "From authentic signals to strategic deception. When should you hide your light?",
         "Both explore when to reveal and when to conceal"),
        ("bridge", "the-narrator",
         "The firefly signals who it is. The narrator writes who it wants to be.",
         "Authenticity through display vs. through narrative"),
        ("surprise", "the-elephants-ground",
         "The firefly shines alone. But some lights only make sense in a herd.",
         "Individual authenticity meets collective identity"),
    ],
    # --- The Fox's Trail ---
    "the-foxs-trail": [
        ("deeper", "the-crows-gambit",
         "From the trail to the chessboard. Strategy at a higher altitude.",
         "Both explore strategic thinking, deception, and adaptation"),
        ("bridge", "the-chameleons-code",
         "The fox adapts its path. The chameleon adapts its color. Same survival, different surface.",
         "Strategic adaptation through movement vs. through appearance"),
        ("surprise", "the-compass-rose",
         "The fox knows every trail. But does it know where it is going?",
         "Tactical brilliance needs directional wisdom"),
    ],
    # --- The Moth's Flame ---
    "the-moths-flame": [
        ("deeper", "the-cost-ledger",
         "The moth pays the price. The ledger shows you the bill.",
         "Both explore the hidden cost of desire and poor choices"),
        ("bridge", "lay-it-down-lust",
         "The moth is drawn to the flame. Faith asks you to walk away from it.",
         "Desire explored through nature and through spirit"),
        ("surprise", "the-geckos-grip",
         "After the flame burns you, how do you grip the wall again?",
         "The moth falls; the gecko recovers. Desire meets resilience"),
    ],
    # --- The Bear's Winter ---
    "the-bears-winter": [
        ("deeper", "the-horses-gait",
         "From waiting to moving. Rest precedes rhythm.",
         "Both explore productive timing: when to stop and when to go"),
        ("bridge", "the-tide-pools-echo",
         "The bear rests. The tide recedes. Both trust the cycle will return.",
         "Patience in nature: dormancy and tidal rhythm"),
        ("surprise", "lay-it-down-sloth",
         "When does healthy rest become avoidance? The bear knows. Do you?",
         "Strategic rest vs. spiritual paralysis"),
    ],
    # --- The Coyote's Laugh ---
    "the-coyotes-laugh": [
        ("deeper", "the-geckos-grip",
         "From laughing through it to gripping through it. Two resilience postures.",
         "Both explore bouncing back but with humor vs. tenacity"),
        ("bridge", "the-otters-play",
         "The coyote laughs. The otter plays. Both survive by refusing to be heavy.",
         "Lightness as a survival strategy in different contexts"),
        ("surprise", "the-narrator",
         "The coyote rewrites the punchline. The narrator rewrites the story.",
         "Resilience through humor and resilience through identity reframing"),
    ],
    # --- The Pangolin's Armor ---
    "the-pangolins-armor": [
        ("deeper", "the-lighthouse-keepers-log",
         "From personal boundaries to enduring through the storm",
         "Both explore self-protection: armor vs. persistence"),
        ("bridge", "lay-it-down",
         "The pangolin curls up. Faith asks you to uncurl. Both require courage.",
         "Boundaries and surrender are opposite postures that both protect"),
        ("surprise", "the-chameleons-code",
         "The pangolin hides. The chameleon reveals differently. Which do you need?",
         "Protection through withdrawal vs. protection through adaptation"),
    ],
    # --- The Horse's Gait ---
    "the-horses-gait": [
        ("deeper", "the-gravity-well",
         "From finding your rhythm to understanding what pulls you off it",
         "Both explore productive consistency and the forces that disrupt it"),
        ("bridge", "the-whales-breath",
         "The horse runs. The whale breathes. Both find power in rhythm.",
         "Rhythmic productivity meets rhythmic existence"),
        ("surprise", "lay-it-down-sloth",
         "The horse moves with purpose. Sloth is when the horse refuses to run.",
         "Productive rhythm vs. spiritual inertia"),
    ],
    # --- The Compass Rose ---
    "the-compass-rose": [
        ("deeper", "the-eagles-lens",
         "From navigation to high-altitude decision making",
         "Both explore finding direction: one through history, one through clarity"),
        ("bridge", "the-arrival",
         "The compass points the way. But what happens when you finally arrive?",
         "Navigation and destination: the journey and its end"),
        ("surprise", "lay-it-down-pride",
         "The compass always knows north. What if you confuse your direction with being right?",
         "Certainty of direction can become the pride of always knowing"),
    ],
    # --- The Cost Ledger ---
    "the-cost-ledger": [
        ("deeper", "the-bonsai-method",
         "From counting the cost to pruning the excess. Financial clarity in action.",
         "Both explore financial self-awareness and intentional spending"),
        ("bridge", "the-ghost-frame",
         "The ledger shows what you spent. The ghost frame shows why you did not see it.",
         "Financial awareness meets perceptual blind spots"),
        ("surprise", "lay-it-down-greed",
         "The ledger reveals the truth about your money. Faith reveals the truth about your heart.",
         "Financial self-awareness meets spiritual self-awareness"),
    ],
    # --- The Ghost Frame ---
    "the-ghost-frame": [
        ("deeper", "the-body-lie",
         "From invisible mental frames to the lies your body tells you",
         "Both explore hidden forces shaping perception"),
        ("bridge", "the-narrator",
         "The ghost frame shapes your story without your permission. The narrator takes it back.",
         "Unconscious narrative vs. conscious rewriting"),
        ("surprise", "the-butterflys-crossing",
         "What if the frame you are trapped in is actually a chrysalis?",
         "The frame that limits you might be the structure transforming you"),
    ],
    # --- The Gravity Well ---
    "the-gravity-well": [
        ("deeper", "the-horses-gait",
         "From understanding gravitational pull to finding your stride",
         "Both explore focus and the forces that keep or pull you from your path"),
        ("bridge", "the-cost-ledger",
         "The gravity well pulls you. The ledger shows you what that pull costs.",
         "Invisible forces meet visible consequences"),
        ("surprise", "the-tide-pools-echo",
         "Gravity pulls everything down. But the tide rises anyway.",
         "The physics of focus meets the philosophy of natural cycles"),
    ],
    # --- The Mockingbird's Song ---
    "the-mockingbirds-song": [
        ("deeper", "conductors-playbook",
         "From understanding AI to mastering it. The mockingbird mimics; the conductor creates.",
         "Both explore the relationship between human creativity and AI"),
        ("bridge", "the-bees-dance",
         "The mockingbird processes language. The bee communicates through movement. Both encode meaning.",
         "AI communication meets natural communication systems"),
        ("surprise", "the-narrator",
         "The mockingbird learns every song. But whose voice is it really singing?",
         "AI identity mirrors the human question: who is the real narrator?"),
    ],
    # --- Lay It Down series ---
    "lay-it-down": [
        ("deeper", "lay-it-down-pride",
         "Ready to go deeper? Pride is where the real fight begins.",
         "The introduction leads to the first and most fundamental sin"),
        ("bridge", "the-pangolins-armor",
         "Surrender asks you to open up. But what if you need armor first?",
         "Faith through vulnerability meets protection through boundaries"),
        ("surprise", "the-gravity-well",
         "Surrender is not falling. It is choosing what pulls you.",
         "Spiritual surrender and gravitational focus share the same physics"),
    ],
    "lay-it-down-pride": [
        ("deeper", "lay-it-down-envy",
         "Pride says you are above everyone. Envy says everyone is above you. Same wound.",
         "Sequential series progression through the seven deadly sins"),
        ("bridge", "the-eagles-lens",
         "The eagle sees from above without superiority. Leadership without pride.",
         "Faith asks you to lead without letting the height corrupt you"),
        ("surprise", "conductors-playbook",
         "The conductor masters everything. When does mastery become pride?",
         "Excellence and pride share a razor thin boundary"),
    ],
    "lay-it-down-envy": [
        ("deeper", "lay-it-down-wrath",
         "Envy compares. Wrath explodes. The fire was already burning.",
         "Sequential series progression"),
        ("bridge", "the-starlings-murmuration",
         "You are shaped by your seven closest. Envy poisons that shaping.",
         "Healthy influence vs. toxic comparison"),
        ("surprise", "the-squirrel-economy",
         "The squirrel stores what it needs. Envy wants what everyone else stored.",
         "Financial wisdom vs. the comparison trap"),
    ],
    "lay-it-down-wrath": [
        ("deeper", "lay-it-down-sloth",
         "After the anger burns out, what is left? Sometimes nothing. That is sloth.",
         "Sequential series progression"),
        ("bridge", "the-wolfs-table",
         "The wolf negotiates with control. Wrath is what happens without it.",
         "Controlled conflict vs. uncontrolled anger"),
        ("surprise", "the-geckos-grip",
         "Anger makes you lose your grip. The gecko teaches you how to hold on again.",
         "The aftermath of rage meets the skill of recovery"),
    ],
    "lay-it-down-sloth": [
        ("deeper", "lay-it-down-greed",
         "Sloth avoids action. Greed takes too much of it. Both miss the mark.",
         "Sequential series progression"),
        ("bridge", "the-bears-winter",
         "The bear rests with purpose. Sloth rests without it. Know the difference.",
         "Holy rest vs. spiritual paralysis"),
        ("surprise", "the-horses-gait",
         "The horse finds its rhythm. Sloth is the refusal to even start moving.",
         "Productive rhythm as the antidote to inertia"),
    ],
    "lay-it-down-greed": [
        ("deeper", "lay-it-down-gluttony",
         "Greed wants more money. Gluttony wants more of everything.",
         "Sequential series progression"),
        ("bridge", "the-salmon-journey",
         "The salmon builds wealth with patience. Greed skips the patience part.",
         "Patient finance vs. the urgency of wanting"),
        ("surprise", "the-cost-ledger",
         "Greed never counts the cost. The ledger does.",
         "Spiritual blindness meets financial clarity"),
    ],
    "lay-it-down-gluttony": [
        ("deeper", "lay-it-down-lust",
         "Gluttony consumes without thinking. Lust desires without boundaries. The finale.",
         "Sequential series progression to the series finale"),
        ("bridge", "the-bonsai-method",
         "The bonsai teaches you to trim. Gluttony refuses to stop growing.",
         "Intentional limitation vs. uncontrolled consumption"),
        ("surprise", "dad-talks-the-dopamine-drought",
         "Gluttony chases the next hit. Dopamine is the chemical behind the chase.",
         "Spiritual excess meets neurological craving"),
    ],
    "lay-it-down-lust": [
        ("deeper", "lay-it-down",
         "You finished the series. Go back to the beginning and read it differently.",
         "Series finale loops back to the introduction with new eyes"),
        ("bridge", "the-moths-flame",
         "The moth is drawn to the flame. Lust is drawn to destruction dressed as beauty.",
         "Desire explored through nature and through spirit"),
        ("surprise", "the-fireflys-signal",
         "Lust confuses the signal. The firefly teaches you to read it clearly.",
         "Distorted desire vs. authentic signaling"),
    ],
    # --- A Process Model series ---
    "the-tide-pools-echo": [
        ("deeper", "the-whales-breath",
         "From tidal rhythms to the rhythm of breath. Part two of the journey.",
         "Sequential series progression"),
        ("bridge", "the-bears-winter",
         "The tide pool waits. The bear waits. Both trust the cycle.",
         "Philosophical patience meets natural endurance"),
        ("surprise", "the-narrator",
         "The tide pool reflects whatever looks into it. So does your story.",
         "Natural reflection meets narrative identity"),
    ],
    "the-whales-breath": [
        ("deeper", "the-butterflys-crossing",
         "From rhythm to transformation. The whale breathes; the butterfly becomes.",
         "Sequential series progression"),
        ("bridge", "the-horses-gait",
         "The whale breathes. The horse runs. Both are about rhythm as survival.",
         "Philosophical rhythm meets productive rhythm"),
        ("surprise", "lay-it-down-sloth",
         "The whale surfaces slowly. Is that wisdom or avoidance? Know the difference.",
         "Philosophical rest meets the temptation of inaction"),
    ],
    "the-butterflys-crossing": [
        ("deeper", "the-elephants-ground",
         "From transformation to finding solid ground after the change.",
         "Sequential series progression"),
        ("bridge", "the-ghost-frame",
         "The butterfly breaks the chrysalis. The ghost frame is a chrysalis you do not know you are in.",
         "Conscious transformation meets invisible limitation"),
        ("surprise", "the-salmon-journey",
         "Both make one great journey that changes everything. Neither comes back the same.",
         "Transformation through a journey that costs everything"),
    ],
    "the-elephants-ground": [
        ("deeper", "the-bees-dance",
         "From standing firm to communicating what you stand for.",
         "Sequential series progression"),
        ("bridge", "the-starlings-murmuration",
         "The elephant holds ground through weight. The starling holds together through movement.",
         "Two collective strategies: rootedness vs. fluidity"),
        ("surprise", "lay-it-down-pride",
         "The elephant is grounded. Pride thinks it IS the ground.",
         "Philosophical groundedness vs. spiritual inflation"),
    ],
    "the-bees-dance": [
        ("deeper", "the-otters-play",
         "From communicating purpose to finding joy in the process. The finale approaches.",
         "Sequential series progression"),
        ("bridge", "the-chameleons-code",
         "The bee dances to communicate. The chameleon changes to communicate. Both encode meaning differently.",
         "Communication through movement vs. through adaptation"),
        ("surprise", "the-ant-network",
         "The bee dances. The ant marches. Both build something no individual could.",
         "Philosophical communication meets technological coordination"),
    ],
    "the-otters-play": [
        ("deeper", "the-tide-pools-echo",
         "You finished the series. Go back to where it started. The echo is different now.",
         "Series finale loops back to the beginning"),
        ("bridge", "the-coyotes-laugh",
         "The otter plays. The coyote laughs. Both survive by refusing to be heavy.",
         "Philosophical play meets resilient humor"),
        ("surprise", "conductors-playbook",
         "The otter plays its way to mastery. The conductor drills its way there. Which path is yours?",
         "Play and discipline as two roads to the same destination"),
    ],
    # --- Newer playbooks ---
    "dad-talks-the-dopamine-drought": [
        ("deeper", "dad-talks-the-mirror-test",
         "From what pulls your attention to what looks back at you.",
         "Dad Talks series: from distraction to reflection"),
        ("bridge", "the-moths-flame",
         "Dopamine is the flame. You are the moth. Now you know.",
         "Neurological craving meets natural metaphor"),
        ("surprise", "the-bears-winter",
         "The drought ends when you learn to sit still. The bear already knows.",
         "Digital distraction meets the discipline of rest"),
    ],
    "dad-talks-the-mirror-test": [
        ("deeper", "the-narrator",
         "The mirror shows you. The narrator lets you rewrite what you see.",
         "Self-awareness through reflection meets identity through story"),
        ("bridge", "the-ghost-frame",
         "The mirror shows the surface. The ghost frame shows what shaped it.",
         "Visible identity meets invisible conditioning"),
        ("surprise", "lay-it-down-envy",
         "The mirror test asks: do you like what you see? Envy says: not compared to them.",
         "Self-awareness corrupted by comparison"),
    ],
    "the-arrival": [
        ("deeper", "the-compass-rose",
         "You arrived. But where are you? The compass helps you find out.",
         "Destination and navigation: after arriving, reorienting"),
        ("bridge", "the-butterflys-crossing",
         "The butterfly crosses to become. The arrival is what happens after becoming.",
         "Transformation and its aftermath"),
        ("surprise", "lay-it-down",
         "What if arriving means letting go of the journey that got you here?",
         "Arrival as surrender"),
    ],
    "the-body-lie": [
        ("deeper", "the-ghost-frame",
         "The body lies to you. The ghost frame explains why you believe it.",
         "Physical deception meets perceptual blind spots"),
        ("bridge", "the-pangolins-armor",
         "The body lies about danger. The pangolin's armor responds to it. Both ask: is the threat real?",
         "False signals and protective responses"),
        ("surprise", "the-whales-breath",
         "Your body says panic. The whale says breathe. Who do you listen to?",
         "Bodily deception meets rhythmic wisdom"),
    ],
    "the-mycelium-network": [
        ("deeper", "the-termite-cathedral",
         "From invisible networks to visible structures built by millions",
         "Both explore collective intelligence building something larger"),
        ("bridge", "the-starlings-murmuration",
         "Underground networks meet aerial coordination. Same intelligence, different medium.",
         "Invisible community meets visible community"),
        ("surprise", "lay-it-down",
         "The mycelium connects everything beneath the surface. Faith connects everything above it.",
         "Natural interconnection meets spiritual interconnection"),
    ],
    "the-termite-cathedral": [
        ("deeper", "the-mycelium-network",
         "From visible architecture to the invisible network that feeds it",
         "Collective building above and below ground"),
        ("bridge", "the-spiders-loom",
         "The termite builds with millions. The spider builds alone. Both create architecture.",
         "Collective construction vs. individual weaving"),
        ("surprise", "the-elephants-ground",
         "The termite builds without blueprints. The elephant stands without question. Both just know.",
         "Instinctive collective wisdom"),
    ],
    "the-bonsai-method": [
        ("deeper", "the-fibonacci-trim",
         "From pruning your budget to trimming with mathematical precision",
         "Both explore intentional financial reduction"),
        ("bridge", "the-gravity-well",
         "The bonsai trims what does not serve growth. The gravity well reveals what pulls you off course.",
         "Intentional cutting meets invisible forces"),
        ("surprise", "lay-it-down-gluttony",
         "The bonsai says less. Gluttony says more. The fight is in every dollar.",
         "Financial discipline meets spiritual excess"),
    ],
    "the-fibonacci-trim": [
        ("deeper", "the-squirrel-economy",
         "From trimming to the full economic system. See the bigger picture.",
         "Targeted finance meets systemic economics"),
        ("bridge", "the-spiders-loom",
         "Fibonacci is nature's pattern. The spider weaves it. Math meets architecture.",
         "Mathematical patterns in finance and nature"),
        ("surprise", "the-tide-pools-echo",
         "Fibonacci spirals in sea shells. The trim follows the same curve as the tide pool.",
         "Financial patterns echo natural ones"),
    ],
    "the-mantis-shrimps-eye": [
        ("deeper", "the-porcupines-quills",
         "You learned to see the manipulation. Now build the automatic defense system that does not require your energy.",
         "Detection leads to automated boundaries"),
        ("bridge", "the-narrator",
         "The narcissist rewrites your story. The Narrator teaches you to take it back.",
         "Seeing manipulation clearly meets reclaiming your narrative"),
        ("surprise", "the-chameleons-code",
         "The narcissist is the ultimate chameleon. See how adaptation works when it is honest instead of predatory.",
         "Deceptive adaptation vs authentic adaptation"),
    ],
    "the-porcupines-quills": [
        ("deeper", "the-tardigrade-protocol",
         "You built the automatic defense. Now learn to survive when the attack outlasts your quills.",
         "Boundary systems meet survival architecture"),
        ("bridge", "the-pangolins-armor",
         "The porcupine strikes back automatically. The pangolin rolls into a ball. Two animals, two defenses, one question: how do you protect what matters?",
         "Automatic consequence vs passive armor"),
        ("surprise", "the-elephants-ground",
         "After building walls, you need to find ground. The elephant never forgets where it stands.",
         "Defense architecture meets grounded identity"),
    ],
    "the-tardigrade-protocol": [
        ("deeper", "the-mantis-shrimps-eye",
         "You survived. Now go back and sharpen your detection. See the lies before the damage starts.",
         "Survival loops back to perception"),
        ("bridge", "the-bears-winter",
         "The tardigrade shuts down to survive. The bear sleeps to endure. Both teach the same lesson: sometimes the strongest move is stillness.",
         "Shutdown survival meets seasonal endurance"),
        ("surprise", "lay-it-down",
         "You learned to survive narcissistic abuse. Now the hardest question: can you lay down the identity it gave you?",
         "Survival meets spiritual surrender"),
    ],
    "the-hermit-crabs-shell": [
        ("deeper", "the-scorpions-molt",
         "You have seen the shells. Now learn to take them off. Layer by layer. Skin by skin.",
         "Recognition leads to deconstruction"),
        ("bridge", "the-narrator",
         "The hermit crab wears borrowed shells. The Narrator wears borrowed stories. Both need to find what is underneath.",
         "False identity through objects meets false identity through narrative"),
        ("surprise", "the-mantis-shrimps-eye",
         "You built the shells to protect yourself from something. The Mantis Shrimp teaches the person on the other side to see through them.",
         "The narcissist's mirror meets the survivor's lens"),
    ],
    "the-scorpions-molt": [
        ("deeper", "the-vampire-squids-light",
         "You shed the armor. Now build something in its place. Not another shell. A light source.",
         "Deconstruction leads to rebuilding"),
        ("bridge", "the-pangolins-armor",
         "The scorpion sheds armor to grow. The pangolin rolls into armor to survive. Two strategies. Same question: what is the armor for?",
         "Shedding defense meets embracing defense"),
        ("surprise", "the-body-lie",
         "The scorpion's molt happens in the body. The Body Lie asks what your body has been telling you that your mind refused to hear.",
         "Physical shedding meets somatic truth"),
    ],
    "the-vampire-squids-light": [
        ("deeper", "the-hermit-crabs-shell",
         "The light reveals what the shells were hiding. Go back to the beginning and see the catalog with new eyes.",
         "Rebuilding illuminates the original architecture"),
        ("bridge", "the-moths-flame",
         "The vampire squid generates its own light. The moth chases someone else's. One is the cure. The other is the disease.",
         "Internal light vs external attraction"),
        ("surprise", "lay-it-down",
         "You generated your own light. Now the final question: can you lay down the version of yourself that needed the dark?",
         "Self-generated light meets spiritual surrender"),
    ],
}


async def seed():
    print("Seeding discovery data (tags + connections)...")

    async with async_session() as db:
        # Build slug -> playbook map
        result = await db.execute(select(Playbook))
        playbooks = {pb.slug: pb for pb in result.scalars().all()}
        print(f"  Found {len(playbooks)} playbooks in database")

        # --- Tags ---
        tag_count = 0
        for slug, tag_list in TAGS.items():
            pb = playbooks.get(slug)
            if not pb:
                print(f"  WARNING: playbook '{slug}' not found, skipping tags")
                continue

            for tag, weight in tag_list:
                existing = (await db.execute(
                    select(PlaybookTag)
                    .where(PlaybookTag.playbook_id == pb.id)
                    .where(PlaybookTag.tag == tag)
                )).scalar_one_or_none()

                if existing:
                    existing.weight = weight
                else:
                    db.add(PlaybookTag(
                        playbook_id=pb.id,
                        tag=tag,
                        weight=weight,
                    ))
                    tag_count += 1

        await db.flush()
        print(f"  Created {tag_count} new tags")

        # --- Connections ---
        conn_count = 0
        for source_slug, conn_list in CONNECTIONS.items():
            source = playbooks.get(source_slug)
            if not source:
                print(f"  WARNING: source playbook '{source_slug}' not found, skipping connections")
                continue

            for ctype, target_slug, teaser, reason in conn_list:
                target = playbooks.get(target_slug)
                if not target:
                    print(f"  WARNING: target playbook '{target_slug}' not found, skipping")
                    continue

                existing = (await db.execute(
                    select(PlaybookConnection)
                    .where(PlaybookConnection.source_id == source.id)
                    .where(PlaybookConnection.target_id == target.id)
                    .where(PlaybookConnection.connection_type == ctype)
                )).scalar_one_or_none()

                if existing:
                    existing.teaser = teaser
                    existing.reason = reason
                else:
                    order = {"deeper": 0, "bridge": 1, "surprise": 2}.get(ctype, 0)
                    db.add(PlaybookConnection(
                        source_id=source.id,
                        target_id=target.id,
                        connection_type=ctype,
                        teaser=teaser,
                        reason=reason,
                        display_order=order,
                    ))
                    conn_count += 1

        await db.commit()
        print(f"  Created {conn_count} new connections")

    print("Discovery seeding complete!")


if __name__ == "__main__":
    asyncio.run(seed())
