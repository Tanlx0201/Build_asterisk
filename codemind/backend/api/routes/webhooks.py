from __future__ import annotations

import hashlib
import hmac
import json
from dataclasses import dataclass


@dataclass(slots=True)
class PullRequestEvent:
    repo_id: str
    pr_number: int
    head_sha: str
    base_sha: str


def validate_signature(secret: str, payload: bytes, signature_header: str) -> bool:
    expected = "sha256=" + hmac.new(secret.encode("utf-8"), payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature_header)


def parse_pull_request_event(event_type: str, payload: bytes) -> PullRequestEvent | None:
    if event_type != "pull_request":
        return None

    body = json.loads(payload.decode("utf-8"))
    if body.get("action") not in {"opened", "synchronize"}:
        return None

    pr = body["pull_request"]
    return PullRequestEvent(
        repo_id=str(body["repository"]["id"]),
        pr_number=int(pr["number"]),
        head_sha=pr["head"]["sha"],
        base_sha=pr["base"]["sha"],
    )
