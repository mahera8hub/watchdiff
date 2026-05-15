import hashlib, json
from deepdiff import DeepDiff

def hash_response(body: dict) -> str:
    """SHA-256 of canonically serialized JSON."""
    canonical = json.dumps(body, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(canonical.encode()).hexdigest()

def semantic_diff(old: dict, new: dict, ignore_order: bool = False) -> dict:
    """Return deepdiff result as plain dict."""
    diff = DeepDiff(
        old, new,
        ignore_order=ignore_order,
        verbose_level=2,
        ignore_numeric_type_changes=False,
    )
    return diff.to_dict()

def classify_severity(diff: dict) -> str:
    """Classify how serious a change is."""
    if not diff:
        return "NO_CHANGE"
    if diff.get("type_changes") or diff.get("dictionary_item_removed"):
        return "CRITICAL"   # breaking: type mismatch or key gone
    if diff.get("dictionary_item_added"):
        return "WARNING"    # additive: new key appeared
    return "INFO"           # value changed but structure intact
