"""Build PlaybookFullReview.html + PlaybookSuggestions.html on S: drive."""
import json
import os
import html as H
from pathlib import Path

with open('playbook_audit.json', encoding='utf-8') as f:
    audit = json.load(f)

# Per-playbook ratings + notes + suggestions.
# Categories scored 1-10:
#   content  = idea originality + does this delivery beat existing material?
#   style    = writing style fits content
#   visuals  = custom visuals / interactive / non-written communication
#   memory   = memorability of the core sentence
#   apply    = practical applicability (can the reader do something tomorrow?)
#   reread   = will the reader come back to this?
RATINGS = {}

def R(slug, content, style, visuals, memory, apply_, reread, note, sugg):
    RATINGS[slug] = dict(content=content, style=style, visuals=visuals,
                         memory=memory, apply=apply_, reread=reread,
                         note=note, sugg=sugg)

# === Manna series ===
R("given", 9, 9, 7, 10, 8, 9,
    "Demand is decayed reception is a genuinely new sentence in the world. Recently rewritten in hybrid literary voice (meditation/psalm/pensee). Mid visual count but the visuals it has are load-bearing (decay-timeline, gap-viz, conversion-viz, trajectory, hands-viz).",
    ["The Ch 5 resentment trajectory is currently text-heavy past the traj-stages bar. Add a small SVG showing the 5 stages with iconic figures for each.",
     "The cover-tagline could be tightened by ~20 percent. Currently 3 sentences; second sentence carries weight, third is a setup that the playbook itself delivers.",
     "Consider an audio version. The hybrid literary voice (psalm parallelism + pensee) rewards being heard aloud and would dramatically expand reach."])

R("returning", 8, 9, 6, 9, 9, 8,
    "Seven well-chosen micro-breakthroughs. Strongest practical-application playbook in the library. Visual count lower than peers because it was just built and visuals were not yet deepened.",
    ["Each chapter currently shares generic scene markers. Each domain (work, body, marriage, time, beauty, children, place) needs its own dedicated SVG.",
     "MAJOR: Add a walk-through tracker interactive element so reader can mark which of the 7 doors they have actually walked through.",
     "The domain-grid pregame visual is a placeholder. Each tile should be a tiny domain-specific icon, not just text.",
     "The mm-viz (Meet vs Manage) and invert-viz are strong but only one chapter each gets a custom viz. Build similar custom viz for Marriage, Time, Beauty."])

# === Eden Pattern ===
R("before-the-garden-returns", 9, 8, 7, 8, 9, 9,
    "Identity/Stability/Execution for AI super abundance is an original synthesis. Strong diagnostic hook that opens the whole series.",
    ["MAJOR: Build a small interactive diagnostic widget. Three questions, scores your weakest pillar. Would push apply to 10.",
     "The trinity-in-motion visual is functional but not iconic. Needs to be the kind of image readers screenshot and share."])

R("the-source", 8, 8, 7, 8, 7, 8,
    "Identity received not constructed. Clean articulation of well-trodden territory with a fresh framing for the AI age.",
    ["Add a what-remains-when-X-is-removed visual that walks through career, title, body, applause being stripped away, showing what is left.",
     "The closer should tie back to Before The Garden Returns more explicitly to thread the series."])

R("the-soil", 8, 8, 7, 7, 8, 8,
    "Stability through pruning. The most counter-intuitive of the three pillars and well-handled.",
    ["A pruning vs preservation before/after visual would crystalize the central move.",
     "Add a longer scene showing what stability-without-pruning looks like (the hardpan soul) so the reader feels the difference."])

R("the-fruit", 8, 8, 6, 8, 8, 8,
    "Discretion not necessity. Five forms of human-only fruit is a fresh taxonomy. Visual count notably lower than Soil and Source.",
    ["Each of the five fruit forms deserves its own SVG. Currently text-heavy at the exact place visuals would carry the most weight.",
     "Add a pressure-vs-discretion before/after viz showing what fruit grows from which posture."])

R("tending-the-garden", 8, 8, 6, 8, 9, 9,
    "Orchestration is the most useful playbook of the Eden series for actual living. The six interactions between pillars is the original contribution.",
    ["MAJOR: Build a Tuesday-walkthrough interactive scene with the six interactions visualized. This playbook earns its top tier with that addition.",
     "The series-completion visual should be more celebratory. Currently functional, should be a moment of arrival."])

# === The Attending ===
R("attend", 8, 8, 6, 8, 10, 8,
    "Ancient discipline (acedia, the noonday demon) made tactical. Highest practical-application score in this group alongside Returning.",
    ["MAJOR: A timer/cell visualization or interactive practice mode would push this to overall 9+.",
     "The eight substitutes are embedded in prose. They deserve their own visual cards arranged as the diagnostic they are."])

R("done-before-you-started", 8, 8, 6, 8, 8, 8,
    "Identity inversion as the deeper foundation under perseverance. Sharper than most identity-work writing.",
    ["Add a becoming-vs-already before/after visual that anchors the inversion.",
     "The closer needs a stronger handoff. Currently ends as a Part 2; could explicitly point to Given and Source for what comes after."])

# === AI explainer series (animal metaphors) ===
R("the-mockingbirds-song", 9, 8, 8, 9, 8, 9,
    "LLMs through mockingbird mimicry. Possibly the single most accessible explanation of LLMs in the world. Free entry playbook by design.",
    ["MAJOR: Build an animated SVG of the absorption-then-recombination loop. Tiny animation would push this to 10.",
     "Add a where-it-breaks chapter for the technical reader, currently underserves the engineer audience."])

R("the-cuttlefishs-canvas", 9, 8, 8, 9, 7, 8,
    "Image generation as cuttlefish camouflage. 'She never memorized the reef. She memorized the rules of what makes a reef look like a reef.' is genuinely a new sentence in the world for explaining diffusion models.",
    ["Surface the bundled latent-space-walk video more prominently.",
     "An interactive noise-to-image slider would be exceptional. The model is already trained; this is a UI addition.",
     "The closing insight above should be elevated to the cover or near-cover position."])

R("the-centipedes-march", 7, 8, 6, 8, 7, 7,
    "Video generation through centipede stepping. Clean teaching. The 'Every leg knows what the leg beside it just did. That is enough.' line is sharp.",
    ["CRITICAL: Chapter titles 'The Flash', 'The Blind Artist', 'The Current' are duplicated from The Cuttlefish's Canvas. Rename them to centipede-specific concepts (e.g., 'The Sequence', 'The Sightless Walker', 'The Wave').",
     "MAJOR: Visual density is lower than peers in the AI series. Add a frame-by-frame timeline visual.",
     "Add a side-by-side photo-stack-vs-film visualization."])

R("the-ravens-trial", 8, 8, 7, 9, 7, 8,
    "AI agents through the raven who watches and solves. Eight-step opening hook is the strongest of the AI series.",
    ["The eight steps deserve a numbered SVG sequence. Currently described in prose; readers will not remember them.",
     "Add a where-this-analogy-breaks chapter for the technical reader."])

R("the-lyrebirds-echo", 8, 8, 6, 8, 6, 7,
    "AI music through lyrebird absorption. 'She did not compose the song. She cleared away everything that was not the song.' is the sharpest closing line in the entire AI series. Underbuilt despite the strong content.",
    ["MAJOR: Expand to 6 chapters to match the depth of Mockingbird and Cuttlefish.",
     "The closing line above is gold — promote it to the cover tagline.",
     "Add more SVGs of the listen-then-recombine cycle.",
     "Apply chapter is weakest; add a practical music-AI-tools recommendation section."])

# === The flagship visual playbooks ===
R("the-squirrel-economy", 8, 9, 10, 9, 8, 9,
    "Macroeconomics through squirrel parable. Highest visual density in the library (179 visual elements, 133 SVGs). The reference standard for what visual-first playbooks look like.",
    ["This is the gold standard. Use as the reference for what every playbook should aspire to in visual density.",
     "Add an interactive run-the-boom-bust widget. The data and visuals are already there; needs a small JS layer."])

R("the-wolfs-table", 9, 8, 9, 9, 8, 9,
    "David Mech correcting his own alpha-wolf research is a genuinely fresh fact most readers do not know. 95 SVGs, dense visual storytelling.",
    ["Add a before-and-after-the-correction visualization showing dominance vs care frames side by side.",
     "Could be expanded with a workplace application chapter (the alpha frame is rampant in corporate culture)."])

R("the-conductors-playbook", 9, 8, 8, 9, 9, 9,
    "Stop generating, start conducting. The founding metaphor of the library. Free entry playbook. Strong visual density.",
    ["Add a before-and-after visual of the conductor vs generator postures.",
     "Add a resonance-conditions-checklist as the installation prompt."])

# === AI Economy series ===
R("the-lifted-ceiling", 9, 9, 7, 10, 9, 9,
    "600 years of evidence that technology lifts ceilings not destroys floors. 'The Ledger has been open for six centuries. The right column has never lost.' is one of the strongest sentences in the library. The Scribe's Lament 1455 opening scene is exceptional storytelling.",
    ["MAJOR: A 600-year interactive timeline (printing press, loom, engine, spreadsheet, internet, AI) is the visual this playbook needs to be at 10.",
     "Add a where-AI-is-different counterfactual chapter for the skeptic. The argument is durable only if it can absorb its own strongest objection.",
     "The Scribe's Lament scene should be expanded — it is the strongest narrative hook in the AI Economy series."])

R("the-new-earning", 8, 8, 7, 8, 10, 9,
    "16 income categories + thermodynamics test. Highest practical applicability in the library along with Attend.",
    ["The 16 categories deserve individual visual cards. Currently presented as a list where visual cards would dramatically improve memorability.",
     "The thermodynamics test deserves its own diagnostic viz that readers can actually run on their work."])

# === Process Model / Philosophy series ===
R("the-tide-pools-echo", 8, 8, 7, 7, 6, 7,
    "Process philosophy through tide pool ecology. You ARE the interaction, not a thing in the world. Strongest opening of the series.",
    ["Apply scores are weakest in this series. Add a how-to-think-process-wise-about-your-week practice.",
     "The interactions visual could be more dynamic; currently static where animation would land."])

R("the-whales-breath", 8, 8, 7, 8, 7, 8,
    "Pre-adjustment to future environments. Mammalian dive reflex as cognition metaphor. Fresh.",
    ["Add a visualization of the body's actual pre-adjustment cascade (heart rate, blood flow, etc).",
     "Add a chapter on cultivating pre-adjustment in daily life. The frame is strong; practical bridge is weakest."])

R("the-butterflys-crossing", 8, 8, 8, 8, 7, 7,
    "A Process Model Part 3 of 6. Deep re-read: grand quote 'You will not become a better caterpillar. You will carry forward into something that changes what \"you\" means.' is sharper than the typical metamorphosis treatment. 109 custom CSS classes (significant audit miss). 9806 words. Real rating ~7.8 not 7.2.",
    ["AUDIT MISS: 109 custom CSS classes — one of the most heavily-styled in the library.",
     "The 'changes what you means' frame escapes the generic transformation territory. Promote this distinction.",
     "Add the imaginal-cells biology visualization — that is the actual mechanism most metamorphosis books skip.",
     "Trim slightly: 9806 words could become 8500 with no loss. The middle chapters drag."])

R("the-elephants-ground", 8, 8, 8, 8, 7, 8,
    "A Process Model Part 4 of 6. Deep re-read: grand quote 'I don't know. I feel. And what I feel holds more than knowing. The ground speaks to those who press their feet into it. Your situation speaks to those who press their attention into it.' is genuinely original — applies elephant infrasound sensitivity to attention-based knowing. 116 custom CSS classes (the most heavily-styled playbook in the library). Real rating ~7.9 not 7.2.",
    ["AUDIT MISS: 116 custom CSS classes — the heaviest visual styling in the entire library.",
     "The 'feel holds more than knowing' frame applied to executive attention is fresh. Promote it.",
     "Length: 10243 words can be trimmed to ~8500. The middle chapters could tighten.",
     "Add an infrasound visualization showing the frequency band elephants hear that humans cannot. Apply the same principle to the executive who can only sense after going still."])

R("the-bees-dance", 8, 8, 8, 8, 7, 7,
    "A Process Model Part 5 of 6. Deep re-read: 'Symbolization is not labeling. It is lossy compression. And the algorithm matters.' is genuinely original applied to communication. 'The dead dance is technically accurate. Every variable is correct. But the bees do not fly. Generation loss has eaten the signal.' is the sharpest line in the entire Process Model series. 87 custom CSS classes (significant audit miss). Real rating ~7.8 not 6.8.",
    ["AUDIT MISS: 87 custom CSS classes — heavily styled. Was rated low because of class-name mismatch.",
     "The 'dead dance / generation loss' frame is the breakthrough — promote it to cover-quality treatment.",
     "An interactive waggle-dance demo (angle = direction, duration = distance, vigor = quality) would push this to the top of the Process Model series.",
     "Cross-link to The Mockingbird's Song (both are about compression and re-generation)."])

R("the-otters-play", 8, 8, 7, 8, 7, 7,
    "A Process Model Part 6 of 6 (the series finale). Deep re-read: applies chaos theory and strange attractors to play and creative life. Real grand quote: 'None of this was here an hour ago. I made it by sliding. And it is making the next slide. Forty-seven passes, and no two were the same. But look at the shape.' 74 custom CSS classes. Real rating ~7.6 not 6.8.",
    ["The strange-attractor frame applied to play is genuinely original — promote it from inside the playbook to cover positioning.",
     "Add an interactive 'play attractor mapping' diagnostic showing how repeated free play creates emergent shape.",
     "As series finale of Process Model, ensure it explicitly threads back through the prior 5 (Tide Pool / Whale / Butterfly / Elephant / Bee). The series-closing callback is the strongest move available here."])

# === Animal financial / strategy ===
R("the-octopus-protocol", 8, 8, 8, 8, 9, 8,
    "Income streams through octopus (one brain, eight independent arms). Strong practical application.",
    ["MAJOR: A map-your-eight-arms interactive worksheet would push apply to 10.",
     "The independent-but-coordinated visual could be animated."])

R("the-bonsai-method", 8, 8, 7, 8, 8, 8,
    "Strategic pruning as the path to value. Counter-intuitive financial frame.",
    ["Add a before/after the cut financial visualization showing portfolio outcomes.",
     "Show specific pruning decisions for actual real-world portfolios (the playbook stays abstract)."])

R("the-fibonacci-trim", 8, 8, 8, 8, 8, 7,
    "Deep re-read: 'Fibonacci appears in sunflowers and galaxies not because nature loves math, but because it is the most efficient packing algorithm in the universe.' is genuinely original applied to finance/life. Chapters (Spiral's Secret / First Ratio / Golden Acceleration / Compound Curve / Phyllotaxis Principle / Your Spiral) commit fully. 104 custom CSS classes (massive audit miss). 1 insight card. Real rating ~7.9 not 6.9.",
    ["AUDIT MISS: 104 custom CSS classes — heavily styled.",
     "The 'efficient packing algorithm' frame is the breakthrough — most finance writing treats compounding as exponential growth. This frames it as efficient packing. Promote it.",
     "Add the actual phyllotaxis ratio (137.5 degrees) visualization showing how Fibonacci packing in nature parallels efficient capital allocation.",
     "Could anchor a Finance sub-series with The Bonsai Method (pruning) and The Octopus Protocol (multi-arm)."])

# === Network / Emergence / AI ===
R("the-mycelium-network", 8, 7, 5, 8, 7, 7,
    "Deep re-read: 6 chapters (Defection Trap / Shadow of the Future / Memory Thread / Punishment Signal / Generous Strategy / Network You Build) — solid game theory architecture. 51 custom CSS classes (audit miss but still genuinely low for the depth). Confirmed undersized at 3034 words.",
    ["MAJOR: Expand from 3034 to ~5000 words. Each chapter is currently 400-500 words where 700-800 would land better.",
     "Add a network visualization with persistent memory threads (who gave, who took, how the network remembers).",
     "The 'Shadow of the Future' game theory concept (the prospect of future interactions changes current behavior) is the breakthrough — feature it prominently.",
     "Cross-link to The Wolf's Table (cooperation vs dominance), The Ant Network (trust/verification)."])

R("the-termite-cathedral", 8, 8, 7, 8, 8, 7,
    "REBUILT 2026-05-13. Expanded from 3458 to ~4863 words. Added stigmergy visualization SVG (3-stage emergence diagram). Added new chapter 'What the Colony Cannot Build' as counter-balance to the pro-emergence thesis (essential for credibility). Expanded Colony Protocol from 4 to 5 steps (added Maintain the Pheromone). Added cross-links to Mycelium Network, Starling's Murmuration, Ant Network as the natural emergence sub-series. Hyphens cleaned.",
    ["The 'What the Colony Cannot Build' chapter is the new credibility anchor. Watch reader response — if it lands, the playbook becomes the flagship for emergence content.",
     "Future addition: an interactive stigmergy simulator where the reader can adjust pheromone strength and watch emergence happen at different rates.",
     "Audio version of the 5-step Colony Protocol would land well as a checklist someone can listen to before starting a project."])

R("the-ant-network", 8, 7, 6, 8, 7, 7,
    "After actually reading: this is actually a TRIPLE synthesis — immune system + ant colony + human trust all running the same algorithm. Chapters (Verification Problem / Antigen Pattern / Memory Cell / Autoimmune Response / Tolerance Threshold / Colony Protocol / Deliberate Exposure) commit fully to the metaphor. 59 custom CSS classes (audit miss). More ambitious than initial rating credited.",
    ["MAJOR: Underbuilt at 3971 words for the ambition of the triple synthesis. Expand to ~5500.",
     "The 'autoimmune response' chapter is the most interesting — when trust verification goes wrong and attacks the self. Feature it more.",
     "Add a visualization showing the three systems (immune cell / ant scout / human trust) running the same algorithm in parallel.",
     "The 'deliberate exposure' closing concept is the practical anchor — make sure it has a concrete daily practice attached."])

R("the-spiders-loom", 8, 8, 7, 8, 9, 7,
    "REBUILT 2026-05-13. Expanded from 2857 to 4440 words. Added Pull Rate Diagnostic (three-state self-identification: brittle / formless / phase transition) as the central interactive section. Reframed Csikszentmihalyi as the observed phenomenon explained by deeper materials-science mechanism. Added chocolate tempering as second phase-transition example. Cross-linked to The Horse's Gait. Added composite-architecture examples (novel, startup, marriage). Closing reframe: 'Extraordinary work is not the product of intensity. It is the product of sustained tension over long distance.'",
    ["Add the central Pull Rate visualization SVG (currently text-driven). The three-state diagram (brittle/formless/transition) would be the cover-quality image.",
     "Consider adding a Final Test section to match library standard.",
     "The chocolate-tempering example could use a small inline visual showing the temperature curve."])

# === Decision / strategy animal ===
R("the-crows-gambit", 8, 8, 8, 9, 9, 8,
    "Pot odds and expected value through crow decision-making. Strong delivery of a math frame for non-math readers.",
    ["Add an interactive run-the-math-on-a-decision widget.",
     "Could be the flagship of a Decision-Making series."])

R("the-eagles-lens", 7, 8, 8, 8, 7, 7,
    "Two-fovea decisions. Fresh insight about telephoto plus stereoscopic simultaneous focus.",
    ["Add a visualization of what dual-focus looks like in actual decisions (split-screen showing what each fovea sees).",
     "Practical application is weakest; needs more do-this-Tuesday content."])

R("the-fireflys-signal", 7, 8, 8, 7, 7, 7,
    "Phase coupling and the information in silence. Sophisticated content.",
    ["The phase-coupling visualization deserves animation. Currently static where motion is the point.",
     "Apply gap: how does a reader use phase-coupling in actual work?"])

R("the-foxs-trail", 7, 8, 8, 7, 7, 7,
    "Strategy: never run the same path twice. Solid.",
    ["More concrete strategy applications (decisions, careers, products).",
     "The misdirection visual could be more vivid."])

# === Resilience series ===
R("the-coyotes-laugh", 8, 8, 7, 8, 8, 8,
    "Antifragility through wound-becoming-weapon. The bone heals thicker. Strong frame.",
    ["This frame overlaps with what a future Suffering series would be. Careful to differentiate or fold them together.",
     "Add specific examples of wound-to-weapon transformations from history."])

R("the-pangolins-armor", 8, 8, 7, 8, 8, 7,
    "Deep re-read: KILLER grand quote 'The strongest position in any conflict is the one that requires the least energy to maintain.' is genuinely original applied to boundaries. Chapters (The Ball / Scale Architecture / Energy Equation / Soft Belly / Night Walk / Pangolin's Choice) commit fully. 'The Energy Equation' chapter is the breakthrough mental model. Real rating ~7.6 not 7.2.",
    ["The grand quote should be cover-positioned. 'Least energy to maintain' is the central insight and most readers will not reach chapter 3 where it currently sits.",
     "Add an 'energy equation' diagnostic for current boundary disputes — which positions cost the most maintenance, which cost the least, which are sustainable.",
     "Cross-link to The Porcupine's Quills (structural silence) and The Tardigrade Protocol (compression) — three different defense postures."])

R("the-bears-winter", 7, 8, 7, 7, 7, 7,
    "Cyclical rest and dormancy. Conventional but well-handled.",
    ["Add a specific plan-your-winter practice.",
     "Differentiate from sabbatical / rest-culture books."])

R("the-tardigrade-protocol", 9, 8, 8, 9, 8, 8,
    "Shield Series Part 3. After actually reading: chapter arc (Organism That Broke Physics / Cryptobiosis / The Tun State / Anhydrobiosis / Rehydration Sequence) is a real four-mechanism resilience taxonomy. 'The tardigrade does not become a different creature during the Drought. It becomes a more essential version of the same one.' is genuinely original. 94 custom CSS classes (significant audit miss). Real rating ~8.4 not 6.7.",
    ["AUDIT MISS: 94 custom CSS classes — one of the most heavily-styled in the library. Was rated low because of class-name mismatch.",
     "The four mechanisms (cryptobiosis / tun / anhydrobiosis / rehydration) deserve a central four-quadrant diagnostic letting readers identify which they need today.",
     "The Tun State concept ('compressed essential form') is the playbook's deepest insight — promote it from chapter to central insight.",
     "Cross-link explicitly to The Mantis Shrimp's Eye and The Porcupine's Quills as the completed Shield Series trio."])

R("the-hermit-crabs-shell", 8, 8, 7, 8, 7, 7,
    "Mirror Series Part 1. After actually reading: 'A playbook for the person who has performed so long they forgot there was someone underneath.' is a strong open. 'The hermit crab has no memory of its own body. It only remembers the shells.' is the central frame. 77 custom CSS classes. Real rating ~7.5+ not 6.5.",
    ["CRITICAL: This is part of the unregistered Mirror Series (Part 1 of 3). Register the series in seed_playbooks.py.",
     "The 'no memory of its own body' line should be elevated to the cover insight, not buried in a grand quote.",
     "9207 words — could trim by ~15 percent.",
     "Add a 'shell inventory' diagnostic — name the shells you're currently borrowing.",
     "This is the free-entry to the Mirror Series; needs strongest cover game."])

R("the-scorpions-molt", 9, 8, 8, 9, 9, 8,
    "Mirror Series Part 2. After actually reading: the 7-skin narcissism taxonomy (Charm/Storytelling/Contempt/Projection/Splitting/Denial/Shame) is genuinely original. Interactive Layer Locator widget is sophisticated UX. Custom SVG cover art (scorpion mid-molt). My original 5.5 rating was wrong — audit missed custom CSS architecture. Real rating ~8.4.",
    ["CRITICAL: Register Mirror Series in seed_playbooks.py. Currently the cover says 'Mirror Series Part 2 of 3' but the series doesn't exist in the database, breaking the dots navigation.",
     "CRITICAL: My audit metric of 'visual elements' undercounted this playbook badly because it uses non-standard class names. Either migrate to standard library classes OR officially document Mirror Series as having its own visual aesthetic.",
     "The 7-skin model is the strongest content asset. Promote it more aggressively in the cover and marketing copy.",
     "The 'doors in the armor' closing frame is sharp — make sure the cover tagline signals it.",
     "Length (12,723 words) is justifiable given the depth but the dark-panel notes repeat; consolidate."])

R("the-vampire-squids-light", 8, 8, 7, 8, 7, 7,
    "Mirror Series Part 3. After actually reading: 'You were never from hell. You were built for the sun.' is a sharp closing frame for the narcissism recovery arc. 67 unique CSS classes — heavily styled, audit missed visuals. Real rating ~7.5+ not 6.0. Still longest playbook in library at 14,373 words.",
    ["CRITICAL: Register Mirror Series with proper part-numbering. Cover says Part 3 of 3 but series isn't in seed_playbooks.py.",
     "MAJOR: 14,373 words is genuinely too long. Specific trim: collapse the back-half repetition of the bioluminescence and counter-illumination concepts.",
     "The 'built for the sun' frame should be the cover insight — currently buried.",
     "Add a visual showing the journey from deep dark to surface light (the actual squid migration map).",
     "Audit miss: the cover, scenes, and dark-panels are visually rich but use non-standard class names."])

R("the-porcupines-quills", 8, 8, 8, 9, 8, 7,
    "Shield Series Part 2. After actually reading: 'The porcupine walks through the forest with 30,000 reasons not to be touched, and everything that bites a porcupine learns the lesson once.' is sharp. 'Structural silence' as the highest defense is genuinely fresh. 89 unique CSS classes — heavily styled. Audit dramatically undercounted.",
    ["CRITICAL: Register Shield Series. Part 2 of 3 without registered series breaks navigation.",
     "Audit miss: visual count was wrong. This playbook is well-styled with its own architecture.",
     "The 'structural silence' practice deserves an entire chapter, not embedded in another. It's the breakthrough.",
     "Add a 'quill inventory' diagnostic: which of your defensive postures are armored porcupine quills vs frantic flailing?",
     "Title for the third Shield Series playbook should be identified — what's Shield Part 3?"])

# === Identity / Body ===
R("the-narrator", 8, 8, 9, 8, 8, 8,
    "You are performing a character someone else wrote. Strong identity inversion. High visual density (93 elements).",
    ["The 'audience no longer in the room' visual could be made more haunting.",
     "Add a whose-script-are-you-running diagnostic."])

R("the-body-lie", 9, 9, 8, 9, 9, 8,
    "REBUILT 2026-05-13. Expanded from 7397 to ~8242 words. Added 'Find Your Offset' capstone diagnostic with 4 sections: Phantom Generator Profile (rate the 4 generators 1-4), Time of Day Map (your 3 vulnerable hours), Compass Stories (inherited beliefs), Correction Bearing (write your sentence + application). This was the missing personalized practical tool. Zero hyphens (already clean). The declination frame was already perfectly featured on the cover. Real rating now ~8.5 with the capstone diagnostic added.",
    ["The 4-section Find Your Offset worksheet is the new center of gravity. Most readers will spend more time here than anywhere else.",
     "Future addition: a printable PDF version of the worksheet for readers to fill in by hand and refer back to.",
     "Consider featuring this in the catalog as a flagship. The science depth and the practical worksheet together make it one of the strongest body-image playbooks anywhere."])

R("the-arrival", 8, 8, 7, 8, 8, 8,
    "Insertion burn metaphor for arriving at goals. Original frame.",
    ["Add a fuel-budget visualization specifically for life-arrivals (graduation, marriage, hitting income target).",
     "Could be paired with The Source for an Identity series."])

# === Faith / Christian content ===
R("the-three-tables", 7, 7, 7, 7, 7, 7,
    "After actually reading: 'The First Sin Was a Meal' opener is sharp. The Birthright Bowl / Temple Inspection / Bread of Life / Daily Altar chapter arc is a real cohesive structure around tables-as-spiritual-formation. 71 custom CSS classes. Better than initial rating. Christian content but with a fresh angle (the three specific tables identified).",
    ["The 'first sin was a meal' opener is the strongest hook — promote it to the cover tagline.",
     "Identify the three tables explicitly in the cover marketing — what ARE the three? Currently the reader has to dig.",
     "Add a 'which table are you eating at right now' diagnostic. The structure asks for it.",
     "Cross-link to Manna and Given (the reception architecture is closely related)."])

R("the-kintsugi-bowl", 9, 8, 9, 8, 8, 7,
    "AUDIT MISS: This playbook's actual cover title is 'The Kintsugi Protocol' (filename/slug is misleading). The central frame is genuinely original: 'A playbook that proves do everything unto the Lord is not a moral exhortation. It is an engineering problem. And engineering problems have solutions.' Chapter titles are an unusual cross-domain synthesis (Closed System, Frequency, Hairline Fractures, Immune System, Commander's Intent, Kairos Windows, Game Film, Poison That Heals). 106 custom CSS classes. Real rating ~8.4 not 6.3.",
    ["CRITICAL: Three-way naming inconsistency. Slug is 'the-kintsugi-bowl', filename is 'The_Kintsugi_Bowl_The_Wandering_Eye.html', cover title is 'The Kintsugi Protocol'. Pick one canonical name and update everywhere.",
     "The 'engineering problem not moral exhortation' frame is the breakthrough — promote it from inside the playbook to the catalog card and series positioning.",
     "Chapter naming inconsistency: 'Commander's Intent' (military) and 'Kairos Windows' (theology) and 'Game Film' (sports) and 'Poison That Heals' all live in same playbook. That eclecticism either needs framing (e.g., 'we are stealing tools from every domain') or some chapters should split into a different playbook.",
     "The 10,850-word length is justifiable given the depth.",
     "What's 'The Wandering Eye' refer to in the filename? Either it's a deprecated working title or it's a real concept not surfaced in the chapter list. Investigate."])

R("the-unfinished-song", 7, 8, 7, 8, 7, 7,
    "Tritone as productive tension. Fresh musical metaphor for unfinished work.",
    ["Add actual audio samples of tritones to make this multi-modal. Currently described where it could be heard.",
     "Practical apply: which specific unfinished work in your life is the tritone? Add this prompt explicitly."])

# === Movement / body / burnout ===
R("the-horses-gait", 8, 8, 4, 8, 8, 7,
    "Resonant frequency for burnout. Original physics tie. 'The horse does not fear the gallop. It fears the transition. And so do you.' is genuinely sharp. CRITICALLY UNDERVISUALIZED.",
    ["CRITICAL: This strong concept is letting the reader down with too little visual (20 elements across 4496 words).",
     "The gait-frequency visualization IS the entire teaching; should be an interactive frequency-slider.",
     "The 'transition is the fear' line deserves to be the cover insight.",
     "Add a 'map your four gaits' diagnostic — when does the reader walk, trot, canter, gallop in actual work?"])

R("the-roche-limit", 8, 8, 6, 8, 8, 7,
    "Deep re-read: cover sub 'Why closeness keeps destroying you. And how to become dense enough to survive it.' is genuinely sharp. Chapters (Shattering / Hijack / Immune Response / Oxygen / Density) are not orbital but a hybrid frame combining orbital mechanics with immune-system biology applied to closeness. 'Density' as the survival adaptation is fresh. 55 custom CSS classes (audit miss). Real rating ~7.5 not 6.8.",
    ["The 'density not distance' frame is the breakthrough — promote it. Most relationship advice says 'set boundaries' (distance). This playbook says 'increase your structural density.' That is genuinely different.",
     "Add a Roche-Limit visualization showing the tidal forces vs body density tradeoff.",
     "Audit miss: the chapter framework is hybrid (orbital + immune) which is conceptually more sophisticated than a pure orbital metaphor would be."])

R("the-mantis-shrimps-eye", 9, 8, 8, 9, 9, 8,
    "Shield Series Part 1. After actually reading: 'You see three colors. The mantis shrimp sees sixteen.' applied to narcissistic-manipulation detection is a genuinely original frame. 116 unique CSS classes — most visually-rich playbook in library by that measure. Audit dramatically undercounted. Real rating ~8.4 not 6.0.",
    ["CRITICAL: Register Shield Series in seed_playbooks.py. Currently part numbering is broken.",
     "CRITICAL: Audit miss — this is one of the most visually-styled playbooks in the library and was rated low because of class-name mismatch.",
     "The 16-color-receptor central frame is excellent. Add a permanent reference card readers can keep open while interacting with people.",
     "Apply chapter (Cavitation Strike) is the strongest closer in the Shield series — keep it.",
     "Consider this for the free-entry slot of the Shield series."])

R("the-chameleons-code", 8, 8, 6, 8, 7, 7,
    "After actually reading: 'You have been using your greatest gift as a wall. I am going to teach you to use it as a voice.' is genuinely sharp — reframes social adaptation from people-pleasing failure into communication mastery. Real rating ~7.4 not 6.4. 64 custom CSS classes.",
    ["The 'wall vs voice' line should be the cover tagline.",
     "Add a 'where is your code a wall' diagnostic — specific scenarios where adaptation is hiding vs communicating.",
     "The cell-level color-change visualization is the strongest asset; lean on it harder.",
     "Cross-link to The Mantis Shrimp's Eye and The Porcupine's Quills (the Shield series adjacent)."])

R("the-geckos-grip", 8, 8, 7, 8, 7, 7,
    "Van der Waals as perseverance. Original physics tie. Good visual count.",
    ["The molecular-grip visualization deserves animation. Currently static.",
     "Practical apply: where does van der Waals show up in human work? Make this explicit."])

R("the-cost-ledger", 7, 8, 9, 8, 8, 7,
    "Cost of standing still. Strong financial frame applied to life. 93 visual elements.",
    ["Add an interactive cost-calculator widget. The ledger metaphor begs for it.",
     "The ledger metaphor deserves a more vivid central visual; currently strong but not iconic."])

R("the-ghost-frame", 8, 7, 7, 7, 7, 7,
    "Brain shows predictions, not reality. Touches Bayesian brain theory.",
    ["The prediction-vs-reality visualization should be the cover image.",
     "Apply: how does a reader update a stuck prediction? The frame needs a practice."])

R("the-gravity-well", 9, 8, 8, 9, 9, 8,
    "Deep re-read: KILLER grand quote 'You do not need more willpower. You need more mass. Build something so dense inside yourself that the noise cannot compete.' Genuinely a new sentence in the willpower/attention discourse. Chapters (A Warning / The Invisible Force / Building the Well / Defending the Well / The Lens / The Daily Practice) build the frame rigorously. 83 custom CSS classes. Real rating ~8.5 not 6.9.",
    ["AUDIT MAJOR MISS: This is one of the strongest playbooks in the library and was rated near the bottom. The 'mass not willpower' frame is genuinely original.",
     "The grand quote should be the cover tagline. Currently buried in chapter 4.",
     "Add a 'mass inventory' diagnostic: list the dense structures in your inner life that the noise cannot compete with. The few you have, the more vulnerable you are.",
     "Cross-link to Lay It Down: Sloth (the Burning Yes), The Moth's Flame (counterfeit signals), Dad Talks: Dopamine Drought. These four playbooks form a natural Attention sub-series."])

R("the-starlings-murmuration", 8, 8, 8, 8, 7, 7,
    "Alignment / phase transitions. The single-bird-shifts-the-flock frame is strong.",
    ["The murmuration visualization deserves video or animation. Static does not do it justice.",
     "Apply: how does a person become the single shifting bird in their family or team?"])

# === Lay It Down series ===
R("lay-it-down", 7, 7, 8, 7, 8, 7,
    "Master playbook for the seven deadly sins series. Classical territory, well-delivered, strong visual density (64 elements).",
    ["Consider a series-overview visualization showing all seven sins as a constellation, with progression paths.",
     "Add a sin-diagnostic widget that points readers to the part of the series they should read first."])

R("lay-it-down-pride", 8, 8, 8, 8, 9, 7,
    "Deep re-read: 9-chapter arc (Throne / Curator / Image Fast / Last Word / Surrender Protocol / Root Beneath the Root / One-Man Army / Dependency Drill / Low Place) shows real architectural commitment. 100 custom CSS classes (massive audit miss). 3 insight cards. 'The Curator' (you curate the version of yourself others see) and 'Image Fast' (the practice of refusing to manage perception) are genuinely fresh concepts. Real rating ~7.9 not 6.7.",
    ["The Curator and Image Fast concepts are the breakthrough — promote them in the cover marketing.",
     "Add an Image Fast diagnostic: identify the 3 contexts where you most aggressively manage perception. Those are the fast targets.",
     "The Dependency Drill (chapter 8) is the strongest practical close — could be a standalone tool.",
     "Cross-link to Done Before You Started (the identity inversion that makes the Image Fast sustainable)."])

R("lay-it-down-envy", 9, 8, 7, 9, 7, 7,
    "After actually reading: 'Envy is not a feeling. It is a lens defect. It separates what should be seen as one image into colors that cannot recombine.' Genuinely original — OPTICS as metaphor for envy. Chapters (Aberration, Splitting Lens, Achromatic Correction) commit fully to the frame. Real rating ~7.9 not 6.2. 54 custom CSS classes.",
    ["CRITICAL: Underbuilt at 2808 words. Expand to ~5000 to match the strength of the metaphor.",
     "The optics frame deserves a central visual diagram of chromatic aberration with the labels of envy/perception.",
     "The 'colors that cannot recombine' line is the strongest in the entire Lay It Down series — promote it.",
     "Cover tagline should be the lens-defect line, not whatever generic envy framing it currently uses.",
     "This could be the breakthrough entry that elevates the whole series."])

R("lay-it-down-wrath", 8, 8, 7, 8, 8, 7,
    "After actually reading: 'The Fire You Mistook for Strength' opener is sharp. The 8-chapter arc (Fuse / Pause Protocol / Ledger / Release Drill / Wound Under the Fire / Judge's Bench / Justice Fast) shows real architectural commitment. 'The Wound Under the Fire' and 'The Justice Fast' are genuinely fresh chapter concepts. 98 custom CSS classes. Real rating ~7.6 not 6.3.",
    ["The 'Justice Fast' concept is the breakthrough — abstaining from rendering verdicts for a period. Feature it.",
     "The 'fire you mistook for strength' opener should be the cover tagline.",
     "Add a 'rage spiral' visualization showing the cascade from fuse to ledger to release.",
     "Cross-link to Returning's section on receiving the day, since wrath is closely tied to demand/entitlement."])

R("lay-it-down-sloth", 8, 8, 8, 8, 9, 8,
    "Deep re-read: 9-chapter arc (Sin That Feels Like Rest / Comfort Threshold / Resistance Protocol / Delay Architecture / First Domino / Numb Zone / Wake Up Drill / Burning Yes / Awake Life). 'Burning Yes' and 'Numb Zone' are genuinely fresh concepts. 97 custom CSS classes (significant audit miss). Real rating ~8.1 not 6.8.",
    ["AUDIT MISS: 97 custom CSS classes — heavily styled. Was rated low because of class-name mismatch.",
     "The 'Burning Yes' concept (saying yes to one thing that pulls you out of comfort) is the strongest practical hook in the entire Lay It Down series. Feature it more prominently.",
     "Could be the free-entry playbook for the series given the breakthrough framing.",
     "Add a 'where is your Numb Zone' diagnostic — specific scenarios where comfort-as-rest is actually comfort-as-anesthesia."])

R("lay-it-down-greed", 8, 8, 8, 8, 9, 7,
    "REBUILT 2026-05-13. Expanded from 3215 to ~4396 words. Added 'The Network You Cannot See' SVG visualization showing surface mushrooms (visible greed behaviors) and underground root mass (the actual cause). Added Enough Declaration templates for 4 domains (Income, Possessions, Status, Time) with concrete example numbers. Expanded Why Cutting Mushrooms Fails chapter with compensation pattern examples (the man who quits drinking gains 40 lbs, etc). Expanded Legacy Soil chapter with specific 'what grows back' examples (catch with son, piano lessons). Added cross-link to The Mycelium Network with the distinction between Armillaria (parasite) and mycorrhizae (symbiont).",
    ["The 4-domain Enough Declaration template is the new practical centerpiece — readers can use it directly.",
     "The mycelium visualization is load-bearing now. Consider an animation version where the rhizomorphs visibly probe outward from the root mass.",
     "Could anchor a Finance/Money sub-series alongside The Bonsai Method and The Fibonacci Trim."])

R("lay-it-down-gluttony", 8, 7, 7, 8, 8, 7,
    "After actually reading: 'The Sin That Calls Itself Self Care' is a sharp opener. The Numbing Menu / Fasting Muscle / Fullness Myth / Table Flip / Open Hand chapter arc is a real architectural commitment, not just generic gluttony talk. 98 custom CSS classes (audit miss). Real rating ~7.5.",
    ["The 'sin that calls itself self care' frame is the strongest content asset — promote it.",
     "The fasting-muscle concept needs a visual showing the muscle metaphor concretely.",
     "Cross-link to attention/dopamine literature (specifically The Cost Ledger and the Dad Talks dopamine entry).",
     "The 'Table Flip' chapter title is intriguing — make sure the cover signals what this is."])

R("lay-it-down-lust", 8, 8, 7, 8, 8, 7,
    "After actually reading: 'The Sin That Counterfeits Intimacy' is sharp. Counterfeit Menu / Vulnerability Protocol / Objectification Reflex / Gaze Reset / Intensity Trap / Depth Practice / Holy Gaze chapter arc is rigorous. 112 custom CSS classes (audit miss). Real rating ~7.5.",
    ["The 'counterfeits intimacy' frame is the strongest content asset.",
     "The Gaze Reset and Holy Gaze chapters are unusual for the genre — feature them more.",
     "Add a 'is this intimacy or intensity' diagnostic widget. The distinction is the core teaching.",
     "Cross-link to identity work (DBYS, The Source)."])

# === Dad Talks ===
R("dad-talks-the-dopamine-drought", 7, 8, 6, 8, 8, 7,
    "Deep re-read: 5 chapters (The Lever Rats / Dad's Confession / The Dopamine Hierarchy / The Experiment / Day 14: The Results). Free entry playbook. The Lever Rats opener (classic dopamine science experiment) is the strongest hook in the Dad Talks series. Day 14: The Results gives a satisfying narrative bookend. 59 custom CSS classes.",
    ["The Dopamine Hierarchy concept deserves a visual rendering — currently embedded in dialogue.",
     "Audio version (Dad reading aloud) would massively expand reach. The dialogue format begs for it.",
     "Add a 14-day experiment tracker as an installation tool.",
     "Cross-link to Lay It Down: Sloth (the Numb Zone) and The Moth's Flame (counterfeit signals) which all triangulate on the same modern attention problem."])

R("dad-talks-the-mirror-test", 8, 9, 6, 8, 8, 8,
    "REBUILT 2026-05-13. Expanded from 4657 to ~5533 words. Added 'The Three Signal Test' (Repair after rupture / Behavior when not seen / Honesty without retaliation) as the trust diagnostic that distinguishes 'they need patience' from 'they need distance.' This was the missing complement to the Three Mirror Questions. Expanded 'Three Weeks Later' bookend significantly: Caleb reports applying the three signals to a friend named Tyler who fails signal 3 (punishes honesty), plus the lunch with the kid whose parents are divorcing. The expansion makes the structural bookend land. Hyphens cleaned.",
    ["The Three Signal Test is the new diagnostic centerpiece. Could be extracted as a standalone tool for the catalog.",
     "Audio version with dialogue would land particularly well — the rebuild added more direct Dad/Caleb exchange.",
     "The Tyler scene in Three Weeks Later is the most concrete teaching moment — consider featuring it in cover marketing."])

R("dad-talks-the-flinch", 8, 8, 6, 8, 8, 7,
    "Deep re-read: 5 chapters (What the Flinch Actually Is / Dad's First Flinch / The Flinch Library / The Five Second Drill / The Next Morning). 'The Five Second Drill' is a real installable practice — name it more prominently. 'The Flinch Library' as a cataloging tool for one's own avoidances is fresh.",
    ["The Five Second Drill is the playbook's installable tool — give it dedicated treatment (a permanent diagnostic widget).",
     "Add a physiological diagram of the actual flinch reflex (amygdala, sympathetic activation, cortisol cascade).",
     "Audio version would land strongly given the dialogue format.",
     "The 'Flinch Library' concept (cataloging your habitual avoidances) deserves an interactive checklist."])

R("dad-talks-the-first-punch", 8, 8, 6, 7, 8, 7,
    "Deep re-read: chapters 'The Physics of a Fight' / 'The Real First Punch' / 'Peaceful vs. Passive' / 'What Real Strength Looks Like' — the Peaceful vs Passive distinction is genuinely fresh. 66 custom CSS classes (audit miss). Two-fights narrative is structurally strong.",
    ["The 'Peaceful vs Passive' distinction deserves its own visual two-column diagram. This is the breakthrough.",
     "Add a walk-away-vs-stand decision flowchart.",
     "Audio version (Dad reading aloud) would massively expand reach.",
     "The Physics of a Fight chapter could include physiology diagrams (cortisol, adrenaline, sympathetic activation)."])

R("dad-talks-the-scoreboard-lie", 8, 8, 4, 8, 8, 8,
    "11-assists-vs-30-points opener is the sharpest of the Dad Talks. The 'invisible work' frame is genuinely fresh.",
    ["Add a visual scorecard showing visible vs invisible contributions.",
     "Strongest content in series. Needs visual upgrade to match the content quality."])

R("dad-talks-the-invisible-contract", 8, 8, 6, 8, 9, 7,
    "Deep re-read: 6 chapters (Contract Nobody Signed / Dad's Confession / Boundary Conversation / Resentment Test / What Happens When You Set Boundaries / Difference Between a Burden and a Load). The 'Burden vs Load' Galatians 6 distinction is genuinely sharp. 58 custom CSS classes. Real rating ~7.6 not 6.8.",
    ["The 'Burden vs Load' distinction is the breakthrough — promote it from chapter 6 to cover insight.",
     "Add a literal contract visual that gets torn up — physical metaphor for what setting a boundary actually does.",
     "The 'Resentment Test' (if you resent doing it, the contract was invisible/unsigned) deserves to be a permanent diagnostic widget.",
     "Audio version with the Dad/teen dialogue would land particularly well for this topic."])

# === Other ===
R("the-moths-flame", 8, 8, 6, 8, 7, 7,
    "Deep re-read: chapters (Perfect Navigator / Porch Lamp / Signal Audit / Spiral / Dark Flight / The Moon Is Enough) commit fully to the metaphor. 'Your navigation system is not broken. Your signal environment is corrupted.' is genuinely original — applies moth biology to attention economy. 59 custom CSS classes (audit miss).",
    ["The grand-quote line should be elevated to the cover tagline. Currently buried.",
     "Add a Signal Audit interactive diagnostic — let readers identify their three loudest counterfeit norths.",
     "The chapter 'The Moon Is Enough' is the strongest practical close — could be expanded into the central installation prompt.",
     "Visualization opportunity: the moonlight-vs-porch-lamp signal diagram showing what corrupted navigation looks like at the photon level."])

R("the-compass-rose", 0, 0, 0, 0, 0, 0,
    "Was in seed but not in registry. Skipping.",
    [])

R("the-lighthouse-keepers-log", 0, 0, 0, 0, 0, 0,
    "Was in seed but not in registry. Skipping.",
    [])

R("the-salmon-journey", 0, 0, 0, 0, 0, 0,
    "Was in seed but not in registry. Skipping.",
    [])


def overall(r):
    if r['content'] == 0:
        return 0
    w = r['content']*2 + r['style']*1.5 + r['visuals']*1.5 + r['memory'] + r['apply'] + r['reread']
    return round(w / 8.0, 2)


def color_for(score):
    if score >= 9: return "#1f6e3d"
    if score >= 8: return "#3a8c5a"
    if score >= 7: return "#7da651"
    if score >= 6: return "#b8a23a"
    if score >= 5: return "#c47e2c"
    return "#a13c1a"


# Build rows
rows = []
audit_by_slug = {a['slug']: a for a in audit}
for slug, r in RATINGS.items():
    if r['content'] == 0:
        continue
    r['overall'] = overall(r)
    r['slug'] = slug
    a = audit_by_slug.get(slug, {})
    r['title'] = a.get('title', slug)
    r['words'] = a.get('words', 0)
    r['vis_count'] = a.get('visual_total', 0)
    rows.append(r)

rows.sort(key=lambda x: -x['overall'])
for i, r in enumerate(rows, 1):
    r['rank'] = i


def cell(score):
    return (f'<td style="background:{color_for(score)};color:white;'
            f'text-align:center;font-weight:600;padding:6px 8px">{score}</td>')


def hl(text):
    """Wrap CRITICAL and MAJOR keywords in styled spans."""
    text = H.escape(text)
    text = text.replace('CRITICAL', '<span class="critical">CRITICAL</span>')
    text = text.replace('MAJOR', '<span class="major">MAJOR</span>')
    return text


# === FullReview HTML ===
out_dir = Path("S:/My Drive/1. Projects/KingdomBuilders.AI")
out_dir.mkdir(parents=True, exist_ok=True)

top_items = "\n".join(
    f'<li><strong>#{r["rank"]} {H.escape(r["title"])}</strong> <span style="color:#E8C96A">[{r["overall"]}]</span> '
    f'{H.escape(r["note"][:160])}{"..." if len(r["note"])>160 else ""}</li>'
    for r in rows[:10]
)
bottom_items = "\n".join(
    f'<li><strong>#{r["rank"]} {H.escape(r["title"])}</strong> <span style="color:#E8C96A">[{r["overall"]}]</span> '
    f'{H.escape(r["note"][:160])}{"..." if len(r["note"])>160 else ""}</li>'
    for r in rows[-10:]
)

table_rows = "\n".join(
    f'<tr>'
    f'<td class="rank">{r["rank"]}</td>'
    f'<td class="title">{H.escape(r["title"])}</td>'
    f'{cell(r["content"])}{cell(r["style"])}{cell(r["visuals"])}'
    f'{cell(r["memory"])}{cell(r["apply"])}{cell(r["reread"])}'
    f'<td style="background:{color_for(int(r["overall"]))};color:white;'
    f'text-align:center;font-weight:800;font-size:1.05rem">{r["overall"]}</td>'
    f'<td style="text-align:center">{r["words"]}</td>'
    f'<td style="text-align:center">{r["vis_count"]}</td>'
    f'<td class="note">{H.escape(r["note"])}</td>'
    f'</tr>'
    for r in rows
)

review_html = f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>Playbook Full Review</title>
<style>
body {{ font-family: -apple-system, BlinkMacSystemFont, sans-serif; max-width: 1500px;
       margin: 0 auto; padding: 24px; color: #222; line-height: 1.5; background: #fafafa }}
h1 {{ font-size: 1.8rem; margin-bottom: 4px }}
.sub {{ color: #666; font-size: 0.9rem; margin-bottom: 24px }}
table {{ width:100%; border-collapse: collapse; font-size: 0.82rem; margin-top: 16px;
        background: white; box-shadow: 0 1px 4px rgba(0,0,0,0.08) }}
th {{ background: #1f2440; color: white; text-align: left; padding: 8px;
     position: sticky; top: 0; z-index: 10 }}
td {{ padding: 6px 8px; border-bottom: 1px solid #eee; vertical-align: top }}
td.note {{ font-size: 0.75rem; color: #555; max-width: 420px; line-height: 1.5 }}
tr:hover {{ background: #fcfcfc }}
.rank {{ font-weight: 700; font-size: 1.05rem; text-align: center; width: 40px;
         color: #1f2440 }}
.title {{ font-weight: 600; min-width: 200px; color: #1f2440 }}
.legend {{ background: white; padding: 16px; border-radius: 8px;
           margin: 20px 0; font-size: 0.85rem; box-shadow: 0 1px 4px rgba(0,0,0,0.08) }}
.legend h3 {{ margin-bottom: 8px; color: #1f2440 }}
.legend dl {{ display: grid; grid-template-columns: 110px 1fr; gap: 6px 16px }}
.legend dt {{ font-weight: 700; color: #1f2440 }}
.tier-summary {{ background: #1f2440; color: white; padding: 20px;
                 border-radius: 8px; margin: 24px 0 }}
.tier-summary h3 {{ color: #E8C96A; margin-bottom: 12px }}
.tier-summary ul {{ margin-left: 20px }}
.tier-summary li {{ margin-bottom: 6px; line-height: 1.5 }}
.tier-summary.bottom {{ background: #8a3a1a }}
</style></head>
<body>
<h1>Playbook Full Review</h1>
<div class="sub">Ruthless rating of {len(rows)} playbooks. Sortable. Color-coded by score (green=high, red=low).</div>

<div class="legend">
<h3>Rating Categories (1-10 each)</h3>
<dl>
<dt>CONTENT</dt><dd>Idea originality + does this delivery beat existing material? Is there a new sentence in the world here, or just restatement?</dd>
<dt>STYLE</dt><dd>Writing voice fit for the content. Does the prose serve the subject?</dd>
<dt>VISUALS</dt><dd>Custom visuals, interactive elements, non-written ways of communicating the idea.</dd>
<dt>MEMORY</dt><dd>Memorability of the core sentence. Would a reader recall the central insight a week later?</dd>
<dt>APPLY</dt><dd>Practical applicability. Can a reader do something concrete with this tomorrow?</dd>
<dt>REREAD</dt><dd>Re-read value. Is this one-and-done or a reference they return to?</dd>
<dt>OVERALL</dt><dd>Weighted composite. CONTENT counts 2x, STYLE and VISUALS count 1.5x each, others count 1x. Out of 10.</dd>
</dl>
</div>

<div class="tier-summary">
<h3>Top 10 — keep, expand, feature</h3>
<ul>
{top_items}
</ul>
</div>

<div class="tier-summary bottom">
<h3>Bottom 10 — significant rework needed</h3>
<ul>
{bottom_items}
</ul>
</div>

<table>
<thead><tr>
<th>Rank</th><th>Title</th>
<th>CONTENT</th><th>STYLE</th><th>VISUALS</th>
<th>MEMORY</th><th>APPLY</th><th>REREAD</th>
<th>OVERALL</th><th>Words</th><th>Vis#</th><th>Notes</th>
</tr></thead>
<tbody>
{table_rows}
</tbody>
</table>
</body></html>"""

(out_dir / "PlaybookFullReview.html").write_text(review_html, encoding='utf-8')
print(f"Wrote {out_dir / 'PlaybookFullReview.html'}")

# === Suggestions HTML ===
sugg_cards = ""
for r in rows:
    sugg_items = "\n".join(f"<li>{hl(s)}</li>" for s in r['sugg'])
    score_bg = color_for(int(r['overall']))
    sugg_cards += f"""<div class="card">
<div class="card-head">
<div><span class="card-title">{H.escape(r['title'])}</span>
<span class="card-rank">#{r['rank']} of {len(rows)}</span></div>
<div class="card-score" style="background:{score_bg}">Overall {r['overall']}</div>
</div>
<div class="card-note">{H.escape(r['note'])}</div>
<ul class="suggestions">
{sugg_items}
</ul>
</div>
"""

sugg_html = f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>Playbook Suggestions</title>
<style>
body {{ font-family: -apple-system, BlinkMacSystemFont, sans-serif; max-width: 1000px;
       margin: 0 auto; padding: 24px; color: #222; line-height: 1.6; background: #fafafa }}
h1 {{ font-size: 1.8rem; margin-bottom: 4px }}
.sub {{ color: #666; font-size: 0.9rem; margin-bottom: 24px }}
.card {{ border: 1px solid #ddd; border-radius: 8px; padding: 16px;
         margin: 12px 0; background: white; box-shadow: 0 1px 3px rgba(0,0,0,0.05) }}
.card-head {{ display: flex; justify-content: space-between;
              align-items: baseline; margin-bottom: 8px }}
.card-title {{ font-weight: 700; font-size: 1.05rem; color: #1f2440 }}
.card-rank {{ color: #999; font-size: 0.85rem; margin-left: 8px }}
.card-score {{ font-weight: 700; padding: 4px 10px; border-radius: 4px;
               color: white; font-size: 0.85rem }}
.card-note {{ color: #555; font-size: 0.88rem; font-style: italic;
              margin-bottom: 10px; padding: 8px 12px; background: #f8f8f8;
              border-left: 3px solid #ddd; line-height: 1.5 }}
ul.suggestions {{ margin-left: 20px; margin-top: 8px }}
ul.suggestions li {{ margin-bottom: 8px; font-size: 0.92rem; line-height: 1.55 }}
.critical {{ color: #a13c1a; font-weight: 700; letter-spacing: 0.5px }}
.major {{ color: #c47e2c; font-weight: 700; letter-spacing: 0.5px }}
.filter {{ background: #1f2440; color: white; padding: 14px 18px;
           border-radius: 8px; margin-bottom: 20px; font-size: 0.88rem;
           line-height: 1.6 }}
.filter strong {{ color: #E8C96A }}
</style></head>
<body>
<h1>Playbook Suggestions</h1>
<div class="sub">Per-playbook improvement notes. {len(rows)} playbooks. Ranked by overall score (best first).</div>

<div class="filter">
<strong>Filter guide:</strong> Look for <span class="critical">CRITICAL</span> tags (delivery gaps so large they undercut the content) and <span class="major">MAJOR</span> tags (significant gaps that should be addressed soon).
<br><br>
Most playbooks at the top of this list need light polish. Most playbooks at the bottom need significant rework or honest assessment of whether they earn their slot.
</div>

{sugg_cards}
</body></html>"""

(out_dir / "PlaybookSuggestions.html").write_text(sugg_html, encoding='utf-8')
print(f"Wrote {out_dir / 'PlaybookSuggestions.html'}")
print(f"\nTotal playbooks rated: {len(rows)}")
print("Score distribution:")
print(f"  9+:      {sum(1 for r in rows if r['overall']>=9)}")
print(f"  8-8.9:   {sum(1 for r in rows if 8<=r['overall']<9)}")
print(f"  7-7.9:   {sum(1 for r in rows if 7<=r['overall']<8)}")
print(f"  6-6.9:   {sum(1 for r in rows if 6<=r['overall']<7)}")
print(f"  Below 6: {sum(1 for r in rows if r['overall']<6)}")
