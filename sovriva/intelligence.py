"""Original, deterministic intelligence algorithms used by SOVRIVA."""

from __future__ import annotations

import re
from collections import defaultdict
from typing import Any, Iterable


TAXONOMY: dict[str, tuple[str, ...]] = {
    "technology": ("tech", "software", "computer", "coding", "ai", "artificial intelligence", "gadget"),
    "travel": ("travel", "flight", "airline", "hotel", "tourism", "vacation", "trip"),
    "shopping": ("shopping", "retail", "ecommerce", "fashion", "clothing", "beauty", "luxury"),
    "wellness": ("health", "wellness", "fitness", "yoga", "nutrition", "medicine"),
    "finance": ("finance", "bank", "investment", "insurance", "credit", "fintech", "crypto"),
    "entertainment": ("music", "movie", "film", "gaming", "game", "streaming", "entertainment"),
    "food": ("food", "restaurant", "cooking", "recipe", "grocery", "coffee"),
    "sports": ("sport", "football", "cricket", "basketball", "tennis", "athlete", "running", "cycling", "hiking"),
    "education": ("education", "school", "university", "course", "learning", "book"),
    "automotive": ("car", "auto", "vehicle", "motorcycle", "automotive"),
    "home": ("home", "furniture", "garden", "interior", "real estate"),
}


def tokenize(value: str) -> list[str]:
    return [token for token in re.findall(r"[a-z0-9]+", value.casefold()) if len(token) > 1]


def normalize_interest(label: str) -> tuple[str, str, float, str]:
    """Return canonical label, category, confidence and human-readable rationale."""
    tokens = set(tokenize(label))
    lowered = label.casefold()
    scores: dict[str, int] = {}
    matches: dict[str, list[str]] = {}
    for category, keywords in TAXONOMY.items():
        category_matches = [
            keyword
            for keyword in keywords
            if (keyword in tokens if " " not in keyword else keyword in lowered)
            or (" " in keyword and re.search(rf"(?<![a-z0-9]){re.escape(keyword)}(?![a-z0-9])", lowered))
        ]
        if category_matches:
            scores[category] = sum(2 if " " in keyword else 1 for keyword in category_matches)
            matches[category] = category_matches
    if not scores:
        return label.strip(), "other", 0.35, "No taxonomy keyword matched; retained original label."
    category = max(scores, key=scores.get)
    best = scores[category]
    confidence = min(0.98, 0.55 + (best * 0.12))
    rationale = f"Matched {category} taxonomy terms: {', '.join(matches[category])}."
    return f"{category}:{re.sub(r'[^a-z0-9]+', '-', label.casefold()).strip('-')}", category, confidence, rationale


def label_similarity(left: str, right: str) -> float:
    left_tokens = set(tokenize(left))
    right_tokens = set(tokenize(right))
    if not left_tokens or not right_tokens:
        return 0.0
    if left.casefold().strip() == right.casefold().strip():
        return 1.0
    intersection = len(left_tokens & right_tokens)
    union = len(left_tokens | right_tokens)
    return intersection / union if union else 0.0


def compare_platforms(records: Iterable[dict[str, Any]]) -> dict[str, Any]:
    """Reconcile labels without forcing ambiguous matches."""
    by_label: dict[str, list[dict[str, Any]]] = defaultdict(list)
    items = list(records)
    for record in items:
        by_label[record["normalized_label"]].append(record)
    matches: list[dict[str, Any]] = []
    used_pairs: set[tuple[str, str]] = set()
    for index, left in enumerate(items):
        for right in items[index + 1 :]:
            if left["platform"] == right["platform"]:
                continue
            pair = (left["id"], right["id"])
            if pair in used_pairs:
                continue
            score = label_similarity(left["original_label"], right["original_label"])
            if left["normalized_label"] == right["normalized_label"]:
                match_type, certainty = "EXACT_CANONICAL", "high"
            elif score >= 0.6:
                match_type, certainty = "SIMILAR_LABEL", "medium"
            else:
                continue
            used_pairs.add(pair)
            matches.append(
                {
                    "left_id": left["id"],
                    "right_id": right["id"],
                    "left_label": left["original_label"],
                    "right_label": right["original_label"],
                    "similarity": round(score, 3),
                    "match_type": match_type,
                    "certainty": certainty,
                    "evidence_ids": [left["id"], right["id"]],
                }
            )
    platform_specific = [
        {"id": record["id"], "platform": record["platform"], "label": record["original_label"]}
        for record in items
        if not any(record["id"] in match["evidence_ids"] for match in matches)
    ]
    return {
        "matches": matches,
        "platform_specific": platform_specific,
        "compared_records": len(items),
        "algorithm_version": "cross-platform-reconciliation-0.1",
        "uncertainty_rule": "Labels below 0.6 Jaccard similarity remain unmatched.",
    }


def drift_compare(
    before: Iterable[dict[str, Any]],
    after: Iterable[dict[str, Any]],
    before_coverage: dict[str, Any],
    after_coverage: dict[str, Any],
) -> dict[str, Any]:
    """Compare snapshots while distinguishing absence from supported removal."""
    before_records = list(before)
    after_records = list(after)
    before_by_label = {record["normalized_label"]: record for record in before_records}
    after_by_label = {record["normalized_label"]: record for record in after_records}
    added = [after_by_label[key] for key in sorted(after_by_label.keys() - before_by_label.keys())]
    retained = [
        {"before": before_by_label[key], "after": after_by_label[key]}
        for key in sorted(before_by_label.keys() & after_by_label.keys())
    ]
    explicit_after = bool(after_coverage.get("explicit_interest_support"))
    removed = []
    uncertain_absence = []
    for key in sorted(before_by_label.keys() - after_by_label.keys()):
        item = before_by_label[key]
        if explicit_after:
            removed.append(item)
        else:
            uncertain_absence.append(item)
    return {
        "added": added,
        "removed": removed,
        "retained": retained,
        "uncertain_absence": uncertain_absence,
        "changed_classifications": [
            pair
            for pair in retained
            if pair["before"]["category"] != pair["after"]["category"]
        ],
        "before_coverage": before_coverage,
        "after_coverage": after_coverage,
        "algorithm_version": "profile-drift-0.1",
        "interpretation": (
            "Removed means the later export explicitly contained supported interest data. "
            "Uncertain absence means the later export did not provide enough coverage."
        ),
    }


def evidence_graph(
    interests: Iterable[dict[str, Any]], observations: Iterable[dict[str, Any]]
) -> dict[str, list[dict[str, Any]]]:
    nodes: list[dict[str, Any]] = []
    edges: list[dict[str, Any]] = []
    seen: set[str] = set()

    def add_node(node_id: str, node_type: str, label: str, detail: dict[str, Any] | None = None) -> None:
        if node_id not in seen:
            seen.add(node_id)
            nodes.append({"id": node_id, "type": node_type, "label": label, "detail": detail or {}})

    for interest in interests:
        source_id = f"source:{interest['import_id']}:{interest['source_file']}"
        interest_id = f"interest:{interest['id']}"
        add_node(source_id, "source", interest["source_file"], {"platform": interest["platform"]})
        add_node(interest_id, "interest", interest["original_label"], interest)
        edges.append({"source": source_id, "target": interest_id, "label": interest["evidence_type"]})
    for observation in observations:
        visit_id = f"visit:{observation['id']}"
        domain_id = f"domain:{observation['destination_domain']}"
        policy_id = f"policy:{observation['id']}"
        add_node(visit_id, "observed_request", observation.get("initiator_domain") or "website", observation)
        add_node(domain_id, "third_party", observation["destination_domain"], observation)
        add_node(policy_id, "policy_decision", observation["decision"], observation)
        edges.extend(
            [
                {"source": visit_id, "target": domain_id, "label": "OBSERVED_REQUEST"},
                {"source": domain_id, "target": policy_id, "label": observation["classification"]},
            ]
        )
    return {"nodes": nodes, "edges": edges}


def preference_outcome(preference: str, evidence_type: str) -> str:
    if preference == "UNREVIEWED":
        return "UNVERIFIED"
    if evidence_type not in {"PLATFORM_REPORTED", "BROWSER_OBSERVED", "SYSTEM_INFERRED"}:
        return "INSUFFICIENT_EVIDENCE"
    return "PREFERENCE_MATCH" if preference == "ACCURATE" else "PREFERENCE_DISCREPANCY"


def classify_domain(domain: str) -> str:
    normalized = domain.casefold().strip().strip(".")
    ad_domains = {
        "doubleclick.net",
        "googlesyndication.com",
        "adnxs.com",
        "adsrvr.org",
        "taboola.com",
        "outbrain.com",
    }
    analytics_domains = {"google-analytics.com", "analytics.google.com", "segment.io", "mixpanel.com"}
    social_domains = {"facebook.com", "connect.facebook.net", "tiktok.com", "linkedin.com"}
    if normalized in ad_domains or any(normalized.endswith(f".{root}") for root in ad_domains):
        return "ADVERTISING"
    if normalized in analytics_domains or any(normalized.endswith(f".{root}") for root in analytics_domains):
        return "ANALYTICS"
    if normalized in social_domains or any(normalized.endswith(f".{root}") for root in social_domains):
        return "SOCIAL"
    return "OTHER"
