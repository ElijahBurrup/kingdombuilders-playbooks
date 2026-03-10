"""
Seed script — populates reading_paths and reading_path_steps.

Usage:
    python -m scripts.seed_paths

Curated multi-playbook journeys that cross categories, each connected by a theme.
Idempotent: safe to re-run (upserts by slug).
"""

import asyncio
import sys
from pathlib import Path

# Ensure project root is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select
from api.database import async_session
from api.models.playbook import Playbook
from api.models.discovery import ReadingPath, ReadingPathStep


# ---------------------------------------------------------------------------
# Path definitions: slug -> (title, description, theme_tag, emoji, color, steps)
# Each step: (playbook_slug, transition_text)
# transition_text is shown BEFORE reading that playbook (why you're reading it next)
# ---------------------------------------------------------------------------
PATHS = [
    {
        "slug": "the-trust-journey",
        "title": "The Trust Journey",
        "description": "Four playbooks across four categories, all connected by the invisible thread of trust. From digital networks to human ones, from negotiation tables to faith itself.",
        "theme_tag": "trust",
        "emoji": "\U0001F91D",
        "color": "#7B4FBF",
        "steps": [
            ("the-ant-network",
             None),  # First step has no transition
            ("the-starlings-murmuration",
             "The ants built trust through code. Now see what happens when trust moves through people instead of wires."),
            ("the-wolfs-table",
             "Trust can unite a flock. But what happens when trust sits across the table from self interest?"),
            ("lay-it-down",
             "You have seen trust in systems, in flocks, at the negotiation table. Now the hardest question: can you trust what you cannot see?"),
        ],
    },
    {
        "slug": "the-discipline-path",
        "title": "The Discipline Path",
        "description": "From saving to pruning to rhythm to endurance. Four lenses on the same muscle: the ability to choose what matters over what feels good.",
        "theme_tag": "discipline",
        "emoji": "\U0001F3AF",
        "color": "#228B22",
        "steps": [
            ("the-squirrel-economy",
             None),
            ("the-bonsai-method",
             "The squirrel stores everything it can. The bonsai master cuts away everything that does not serve the shape. Same discipline, opposite motion."),
            ("the-horses-gait",
             "You have learned to save and to prune. Now find the rhythm that makes discipline feel less like punishment and more like power."),
            ("the-bears-winter",
             "Rhythm sustains you through productive seasons. But what about the seasons where nothing grows? The bear knows."),
        ],
    },
    {
        "slug": "the-identity-quest",
        "title": "The Identity Quest",
        "description": "Who are you when nobody is watching? When the mirror lies? When your story changes? Four playbooks that strip identity down to its foundation.",
        "theme_tag": "identity",
        "emoji": "\U0001F3AD",
        "color": "#C71585",
        "steps": [
            ("the-narrator",
             None),
            ("the-ghost-frame",
             "You have rewritten your story. Now discover the invisible frame that shaped it before you could choose."),
            ("the-chameleons-code",
             "The narrator writes. The ghost frame reveals. Now: who are you when you keep adapting to every room you enter?"),
            ("the-arrival",
             "You have explored your narrative, your frames, your adaptations. Now the final question: what does it look like to actually arrive?"),
        ],
    },
    {
        "slug": "the-strategy-circuit",
        "title": "The Strategy Circuit",
        "description": "Game theory, deception, adaptation, and signals. Four approaches to the same problem: how do you win when others are playing too?",
        "theme_tag": "strategy",
        "emoji": "\U0001F9E0",
        "color": "#4B0082",
        "steps": [
            ("the-crows-gambit",
             None),
            ("the-foxs-trail",
             "The crow plays the board. The fox plays the terrain. Same strategic mind, different battlefield."),
            ("the-fireflys-signal",
             "Strategy is not just about what you do. It is about what you signal. The firefly knows that truth and deception both start with a flash."),
            ("the-eagles-lens",
             "You have studied the game, the terrain, and the signal. Now rise above all three and see the whole picture at once."),
        ],
    },
    {
        "slug": "the-systems-spiral",
        "title": "The Systems Spiral",
        "description": "From networks to webs to cathedrals to mycelium. Everything alive is a system. These four playbooks reveal the hidden architecture of the world.",
        "theme_tag": "systems",
        "emoji": "\U0001F578\uFE0F",
        "color": "#008080",
        "steps": [
            ("the-spiders-loom",
             None),
            ("the-mycelium-network",
             "The spider builds alone. The mycelium connects everything. What happens when the network is the organism?"),
            ("the-termite-cathedral",
             "Mycelium connects silently underground. Termites build cathedrals above it. Same principle: individual actions, collective architecture."),
            ("the-bees-dance",
             "The termites build. The bees communicate. Watch how a system coordinates when every member can speak."),
        ],
    },
    {
        "slug": "the-courage-crossing",
        "title": "The Courage Crossing",
        "description": "Fear, armor, fire, and transformation. Four playbooks that ask the same question different ways: what are you willing to walk through?",
        "theme_tag": "courage",
        "emoji": "\U0001F525",
        "color": "#DC143C",
        "steps": [
            ("the-pangolins-armor",
             None),
            ("the-moths-flame",
             "The pangolin protects itself. The moth flies toward what could destroy it. Both are responding to the same thing: fear."),
            ("the-geckos-grip",
             "You have seen armor and attraction. Now see what happens when you fall and have to grip something, anything, on the way down."),
            ("the-butterflys-crossing",
             "You have armored up, faced the flame, and learned to grip. Now the final crossing: the transformation that costs everything."),
        ],
    },
    {
        "slug": "the-shield-series",
        "title": "The Shield Series",
        "description": "Three playbooks that teach you to see narcissistic manipulation, build automatic defenses, and survive when the attack outlasts your energy. Detection. Defense. Endurance.",
        "theme_tag": "narcissism",
        "emoji": "\U0001f6e1\ufe0f",
        "color": "#8B0000",
        "steps": [
            ("the-mantis-shrimps-eye",
             None),
            ("the-porcupines-quills",
             "You learned to see the lie. Now build the system that punishes the lie automatically, without spending a single calorie of your own energy."),
            ("the-tardigrade-protocol",
             "Your quills are up and your boundaries are live. But what happens when the siege lasts longer than your resources? The tardigrade knows: you shut down everything except what keeps you alive."),
        ],
    },
]


async def seed_paths():
    async with async_session() as db:
        # Build slug -> playbook lookup
        result = await db.execute(select(Playbook))
        playbooks = {pb.slug: pb for pb in result.scalars()}
        print(f"Found {len(playbooks)} playbooks in DB")

        created = 0
        updated = 0

        for path_data in PATHS:
            # Check if path exists
            existing = await db.execute(
                select(ReadingPath).where(ReadingPath.slug == path_data["slug"])
            )
            path = existing.scalar_one_or_none()

            if path:
                path.title = path_data["title"]
                path.description = path_data["description"]
                path.theme_tag = path_data["theme_tag"]
                path.emoji = path_data["emoji"]
                path.color = path_data["color"]
                path.display_order = PATHS.index(path_data)
                # Delete existing steps to re-create
                await db.execute(
                    select(ReadingPathStep).where(ReadingPathStep.path_id == path.id)
                )
                for step in (await db.execute(
                    select(ReadingPathStep).where(ReadingPathStep.path_id == path.id)
                )).scalars():
                    await db.delete(step)
                updated += 1
            else:
                path = ReadingPath(
                    slug=path_data["slug"],
                    title=path_data["title"],
                    description=path_data["description"],
                    theme_tag=path_data["theme_tag"],
                    emoji=path_data["emoji"],
                    color=path_data["color"],
                    display_order=PATHS.index(path_data),
                )
                db.add(path)
                await db.flush()
                created += 1

            # Create steps
            for i, (pb_slug, transition) in enumerate(path_data["steps"]):
                if pb_slug not in playbooks:
                    print(f"  WARNING: Playbook '{pb_slug}' not in DB, skipping step")
                    continue
                step = ReadingPathStep(
                    path_id=path.id,
                    playbook_id=playbooks[pb_slug].id,
                    step_order=i,
                    transition_text=transition,
                )
                db.add(step)

            await db.flush()
            step_count = len([s for s in path_data["steps"] if s[0] in playbooks])
            print(f"  {'Updated' if path_data['slug'] in [p['slug'] for p in PATHS[:updated]] else 'Created'} path: {path_data['title']} ({step_count} steps)")

        await db.commit()
        print(f"\nDone! {created} created, {updated} updated.")


if __name__ == "__main__":
    asyncio.run(seed_paths())
