"""Generate one image with the BFL FLUX 3 API and save it with its provenance.

Usage (from isaac-obstacle-course/):
  uv run --no-project python tools/flux_generate.py OUT.png "prompt" [--aspect 16:9] [--ref IMAGE ...]

Reads BFL_API_KEY from the workspace .env (../.env). Writes OUT.png and OUT.json
(prompt, model, aspect ratio, reference images, request id, date, cost if reported).
"""

import argparse
import base64
import json
import os
import sys
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ENDPOINT = "https://api.bfl.ai/v1/flux-3-image"
ENV = Path(__file__).resolve().parents[2] / ".env"
FAILED = {"Error", "Failed", "Content Moderated", "Request Moderated", "Task not found"}


def api_key() -> str:
    if os.environ.get("BFL_API_KEY"):
        return os.environ["BFL_API_KEY"]
    for line in ENV.read_text().splitlines():
        if line.startswith("BFL_API_KEY="):
            return line.split("=", 1)[1].strip()
    sys.exit(f"BFL_API_KEY not found in environment or {ENV}")


def request(url: str, key: str, body: dict | None = None) -> dict:
    req = urllib.request.Request(
        url,
        data=json.dumps(body).encode() if body is not None else None,
        headers={"x-key": key, "Content-Type": "application/json", "accept": "application/json"},
        method="POST" if body is not None else "GET",
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        sys.exit(f"HTTP {e.code} from {url}: {e.read().decode()[:500]}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("out", type=Path)
    ap.add_argument("prompt")
    ap.add_argument("--aspect", default="16:9")
    ap.add_argument("--ref", type=Path, action="append", default=[], help="reference image, >= 256x256 (repeatable)")
    ap.add_argument("--resume", metavar="POLLING_URL", help="collect an already-submitted job (its polling_url) instead of submitting again")
    args = ap.parse_args()

    key = api_key()
    if args.resume:
        job = {"id": args.resume.rsplit("id=", 1)[-1], "polling_url": args.resume}
    else:
        body = {"prompt": args.prompt, "aspect_ratio": args.aspect}
        if args.ref:
            body["images"] = [base64.b64encode(p.read_bytes()).decode() for p in args.ref]
        job = request(ENDPOINT, key, body)
        # Results live on a regional host; keep this URL to resume with --resume if polling is interrupted.
        print("polling_url:", job.get("polling_url"), flush=True)
    poll = job["polling_url"]
    for _ in range(300):
        time.sleep(2)
        res = request(poll, key)
        status = res.get("status")
        if status == "Ready":
            break
        # In-progress states include Pending, Queued, Processing and Reasoning (FLUX 3).
        if status in FAILED:
            sys.exit(f"Generation failed: {json.dumps(res)[:500]}")
    else:
        sys.exit("Timed out waiting for the image")

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(res["result"]["sample"], timeout=120) as r:
        args.out.write_bytes(r.read())

    meta = {
        "model": "flux-3-image",
        "endpoint": ENDPOINT,
        "date": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "request_id": job.get("id"),
        "aspect_ratio": args.aspect,
        "prompt": args.prompt,
        "reference_images": [str(p) for p in args.ref],
        "cost": job.get("cost"),
    }
    args.out.with_suffix(".json").write_text(json.dumps(meta, indent=2) + "\n")
    print(args.out, "| cost:", job.get("cost"))


if __name__ == "__main__":
    main()
