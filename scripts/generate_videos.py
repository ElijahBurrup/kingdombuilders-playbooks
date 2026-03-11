"""
Playbook Video Generator — Runway Gen-4 API
Generates installation videos for KingdomBuilders AI playbooks.

Usage:
  pip install runwayml requests
  export RUNWAYML_API_SECRET=your_key_here
  python scripts/generate_videos.py [--playbook starlings] [--dry-run]

Videos are saved to assets/videos/ locally and uploaded to Cloudflare R2 for production serving.
R2 bucket: kb-playbook-videos
Public URL: https://pub-3be2b691e42247078311064d9672c978.r2.dev/
"""

import os
import sys
import json
import time
import argparse
import subprocess
import requests
from pathlib import Path
from datetime import datetime

try:
    from runwayml import RunwayML
except ImportError:
    print("Install the Runway SDK: pip install runwayml")
    sys.exit(1)

# ── Project paths ──────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent.parent
ASSETS_DIR = PROJECT_ROOT / "assets"
VIDEO_DIR = ASSETS_DIR / "videos"

# ── Cloudflare R2 ─────────────────────────────────────────────
R2_ACCOUNT_ID = "81f3bf31ee69fe657517c485ad8f62b3"
R2_BUCKET = "kb-playbook-videos"
R2_PUBLIC_URL = "https://pub-3be2b691e42247078311064d9672c978.r2.dev"

# ── Video specifications ───────────────────────────────────────
# Each entry: playbook key, video ID, prompt, placement description
# Only videos that INSTALL a mental model. No decoration.

VIDEO_SPECS = {
    "starlings": {
        "playbook": "The_Starlings_Murmuration.html",
        "videos": [
            {
                "id": "starlings-murmuration-flow",
                "prompt": (
                    "A massive flock of thousands of starlings performing a murmuration "
                    "at golden hour sunset, the birds flowing as one continuous liquid shape "
                    "against a warm orange and purple sky, constantly shifting form from a "
                    "sphere to a ribbon to a wave, no single bird leading, cinematic drone "
                    "shot, slow motion, photorealistic, 4K"
                ),
                "duration": 8,
                "placement": "Chapter on emergent coordination. The murmuration itself IS the concept. 5 seconds of this installs decentralized leadership better than 500 words.",
                "mental_model": "Emergent coordination without a leader",
            },
        ],
    },
    "ravens": {
        "playbook": "The_Ravens_Trial.html",
        "videos": [
            {
                "id": "raven-string-pull",
                "prompt": (
                    "Close-up of a large black raven perched on a wooden branch, "
                    "methodically pulling a string upward with its beak, stepping on the "
                    "loop with its foot to pin it, releasing its beak, reaching down to "
                    "pull another length, repeating the sequence with precise deliberate "
                    "movements, a small piece of food visible dangling at the bottom of "
                    "the string getting closer with each pull, soft laboratory lighting, "
                    "cinematic, shallow depth of field, 4K"
                ),
                "duration": 8,
                "placement": "Chapter 3: The String. The pull-pin-pull-pin rhythm IS sequential chain-of-thought reasoning made physical.",
                "mental_model": "Sequential reasoning (chain of thought)",
            },
            {
                "id": "raven-stone-drop",
                "prompt": (
                    "A glossy black raven standing beside a clear glass tube filled with "
                    "water, carefully picking up a small grey stone in its beak, leaning "
                    "over the tube opening, and dropping the stone precisely into the water, "
                    "the water level visibly rising as the stone sinks, the raven watching "
                    "the water level intently before reaching for the next stone, "
                    "scientific laboratory setting, soft even lighting, cinematic, 4K"
                ),
                "duration": 6,
                "placement": "Chapter 2: The Stone. Tool selection made visible. She evaluates, selects, and commits.",
                "mental_model": "Tool selection and evaluation",
            },
        ],
    },
    "centipede": {
        "playbook": "The_Centipedes_March.html",
        "videos": [
            {
                "id": "centipede-wave-motion",
                "prompt": (
                    "Extreme close-up of a large golden centipede walking across dark "
                    "earth, camera angle from the side showing all legs in profile, the "
                    "legs moving in a perfect rippling wave pattern from back to front, "
                    "each pair of legs slightly out of phase with the next creating a "
                    "mesmerizing wave propagation, slow motion, macro photography, warm "
                    "amber lighting, shallow depth of field, cinematic, 4K"
                ),
                "duration": 6,
                "placement": "Chapter 1: The Leg/The Wave. Temporal coherence made physical. Each leg is a frame, the wave is temporal attention keeping them in sequence.",
                "mental_model": "Temporal coherence in video generation",
            },
            {
                "id": "diffusion-noise-to-image",
                "prompt": (
                    "Abstract visualization of an image emerging from static noise, "
                    "starting as pure colorful grain and gradually resolving into a clear "
                    "sharp photograph of a mountain landscape, the noise dissolving in "
                    "waves from center outward, each frame slightly more defined than the "
                    "last, the process visible and beautiful, dark background, cinematic "
                    "motion graphics style, 4K"
                ),
                "duration": 6,
                "placement": "Chapter on diffusion/denoising. The reader watches the exact process they are learning about. Meta-installation: the concept teaches itself.",
                "mental_model": "Diffusion denoising process",
            },
        ],
    },
    "mockingbird": {
        "playbook": "The_Mockingbirds_Song.html",
        "videos": [
            {
                "id": "token-prediction-flow",
                "prompt": (
                    "Abstract visualization of glowing words appearing one at a time on a "
                    "dark background, each word materializing from a cloud of faintly "
                    "visible alternative words that fade away as the chosen word solidifies "
                    "and glows bright amber, the sentence building left to right word by "
                    "word, probability clouds narrowing with each selection, elegant "
                    "typography, dark navy background, motion graphics, cinematic, 4K"
                ),
                "duration": 8,
                "placement": "Chapter on token prediction. The reader SEES next-token prediction happening. Each word collapses from many possibilities into one.",
                "mental_model": "Next-token prediction / probability collapse",
            },
        ],
    },
    "bees": {
        "playbook": "The_Bees_Dance.html",
        "videos": [
            {
                "id": "waggle-dance-communication",
                "prompt": (
                    "Close-up of a honeybee performing the waggle dance on a honeycomb "
                    "surface inside a hive, the bee running in a figure-eight pattern with "
                    "a distinctive waggling vibration during the straight run portion, "
                    "other bees gathered close around watching the dancer intently, warm "
                    "golden honey-colored lighting from within the hive, macro photography, "
                    "slow motion, cinematic, 4K"
                ),
                "duration": 6,
                "placement": "Chapter on the waggle dance as communication protocol. Angle encodes direction, duration encodes distance. 5 seconds of seeing it installs 'information encoded in movement' permanently.",
                "mental_model": "Information encoding in physical movement",
            },
        ],
    },
    "horses": {
        "playbook": "The_Horses_Gait.html",
        "videos": [
            {
                "id": "four-gaits-transition",
                "prompt": (
                    "Side profile of a beautiful dark horse in an open field transitioning "
                    "smoothly through all four gaits in sequence, starting with a calm walk "
                    "then accelerating into a trot then into a rocking canter then finally "
                    "into a full gallop, the camera tracking alongside at the same speed, "
                    "golden hour lighting, green meadow, slow motion showing the distinct "
                    "leg patterns of each gait, cinematic, 4K"
                ),
                "duration": 8,
                "placement": "Chapter on pacing modes. The four gaits are four speeds of work. Seeing the transitions shows that speed is not one thing. It is discrete modes with transition costs.",
                "mental_model": "Discrete pacing modes with transition costs",
            },
        ],
    },
}


def ensure_video_dir():
    """Create the videos directory if it doesn't exist."""
    VIDEO_DIR.mkdir(parents=True, exist_ok=True)
    # Add .gitkeep
    gitkeep = VIDEO_DIR / ".gitkeep"
    if not gitkeep.exists():
        gitkeep.touch()


def generate_video(client, spec, dry_run=False):
    """Generate a single video from a spec dict."""
    video_id = spec["id"]
    output_path = VIDEO_DIR / f"{video_id}.mp4"

    if output_path.exists():
        print(f"  SKIP {video_id} (already exists)")
        return str(output_path)

    print(f"  GENERATING {video_id}...")
    print(f"    Prompt: {spec['prompt'][:100]}...")
    print(f"    Duration: {spec['duration']}s")
    print(f"    Mental model: {spec['mental_model']}")

    if dry_run:
        print(f"    DRY RUN: Would generate {video_id}.mp4")
        return None

    # Generate via Runway SDK
    task = client.text_to_video.create(
        model="gen4.5",
        prompt_text=spec["prompt"],
        ratio="1280:720",
        duration=spec["duration"],
    )

    print(f"    Task ID: {task.id}")
    print(f"    Waiting for completion (this takes 2-4 minutes)...")
    sys.stdout.flush()

    # Use SDK's built-in polling (handles THROTTLED, RUNNING, etc.)
    start_time = time.time()
    try:
        result = task.wait_for_task_output()
    except Exception as e:
        print(f"    FAILED: {e}")
        return None

    elapsed = int(time.time() - start_time)
    print(f"    Completed in {elapsed}s")

    # Get video URL from result
    video_url = None
    if hasattr(result, 'output') and result.output:
        video_url = result.output[0]
    elif isinstance(result, list) and len(result) > 0:
        video_url = result[0]
    else:
        # Try retrieving the task directly
        task_detail = client.tasks.retrieve(task.id)
        if hasattr(task_detail, 'output') and task_detail.output:
            video_url = task_detail.output[0]

    if not video_url:
        print(f"    FAILED: No output URL found. Result: {result}")
        return None

    print(f"    Downloading from: {str(video_url)[:80]}...")

    # Download the video
    response = requests.get(str(video_url), stream=True)
    response.raise_for_status()
    with open(output_path, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)

    size_mb = output_path.stat().st_size / (1024 * 1024)
    print(f"    Saved: {output_path} ({size_mb:.1f} MB)")

    # Upload to Cloudflare R2
    upload_to_r2(output_path, spec["id"])

    return str(output_path)


def upload_to_r2(file_path, video_id):
    """Upload a video file to Cloudflare R2 bucket."""
    r2_token = os.environ.get("CLOUDFLARE_R2_TOKEN")
    if not r2_token:
        print(f"    SKIP R2 upload: Set CLOUDFLARE_R2_TOKEN to enable")
        return False

    filename = f"{video_id}.mp4"
    url = f"https://api.cloudflare.com/client/v4/accounts/{R2_ACCOUNT_ID}/r2/buckets/{R2_BUCKET}/objects/{filename}"

    print(f"    Uploading to R2: {R2_PUBLIC_URL}/{filename}")
    with open(file_path, "rb") as f:
        resp = requests.put(url, headers={
            "Authorization": f"Bearer {r2_token}",
            "Content-Type": "video/mp4",
        }, data=f)

    if resp.status_code == 200:
        print(f"    R2 upload OK: {R2_PUBLIC_URL}/{filename}")
        return True
    else:
        print(f"    R2 upload FAILED ({resp.status_code}): {resp.text[:200]}")
        return False


def generate_playbook_videos(client, playbook_key, dry_run=False):
    """Generate all videos for a specific playbook."""
    if playbook_key not in VIDEO_SPECS:
        print(f"Unknown playbook: {playbook_key}")
        print(f"Available: {', '.join(VIDEO_SPECS.keys())}")
        return []

    spec = VIDEO_SPECS[playbook_key]
    print(f"\n{'='*60}")
    print(f"Playbook: {spec['playbook']}")
    print(f"Videos to generate: {len(spec['videos'])}")
    print(f"{'='*60}")

    results = []
    for i, video_spec in enumerate(spec["videos"]):
        result = generate_video(client, video_spec, dry_run)
        results.append({"id": video_spec["id"], "path": result, "spec": video_spec})
        # Delay between videos to avoid rate limiting
        if i < len(spec["videos"]) - 1 and not dry_run:
            print(f"  Waiting 10s before next video...")
            time.sleep(10)

    return results


def generate_all(client, dry_run=False):
    """Generate videos for all playbooks."""
    all_results = {}
    for key in VIDEO_SPECS:
        results = generate_playbook_videos(client, key, dry_run)
        all_results[key] = results
    return all_results


def print_summary():
    """Print a summary of all video specs without generating."""
    total_videos = 0
    total_seconds = 0
    total_cost_est = 0

    print("\n" + "=" * 70)
    print("PLAYBOOK VIDEO INSTALLATION PLAN")
    print("=" * 70)

    for key, spec in VIDEO_SPECS.items():
        print(f"\n  {spec['playbook']}")
        for v in spec["videos"]:
            total_videos += 1
            total_seconds += v["duration"]
            # Gen-4 Turbo: 5 credits/sec, $0.01/credit
            cost = v["duration"] * 5 * 0.01
            total_cost_est += cost
            exists = (VIDEO_DIR / f"{v['id']}.mp4").exists()
            status = "EXISTS" if exists else "PENDING"
            print(f"    [{status}] {v['id']} ({v['duration']}s, ~${cost:.2f})")
            print(f"           Model: {v['mental_model']}")
            print(f"           Where: {v['placement'][:80]}...")

    print(f"\n{'='*70}")
    print(f"  Total: {total_videos} videos, {total_seconds}s of content")
    print(f"  Estimated cost: ${total_cost_est:.2f} (Gen-4 Turbo)")
    print(f"  Videos directory: {VIDEO_DIR}")
    print(f"{'='*70}\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate playbook installation videos")
    parser.add_argument("--playbook", "-p", help="Generate for specific playbook (e.g., starlings, ravens)")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be generated without calling API")
    parser.add_argument("--summary", action="store_true", help="Print video plan summary")
    args = parser.parse_args()

    ensure_video_dir()

    if args.summary:
        print_summary()
        sys.exit(0)

    # Check for API key
    api_key = os.environ.get("RUNWAYML_API_SECRET")
    if not api_key and not args.dry_run:
        print("ERROR: Set RUNWAYML_API_SECRET environment variable")
        print("  Get your key at: https://dev.runwayml.com/")
        print("  Then: export RUNWAYML_API_SECRET=your_key_here")
        print("\n  Or use --dry-run to preview without generating")
        sys.exit(1)

    if args.dry_run:
        client = None
    else:
        client = RunwayML()

    if args.playbook:
        generate_playbook_videos(client, args.playbook, args.dry_run)
    else:
        generate_all(client, args.dry_run)
