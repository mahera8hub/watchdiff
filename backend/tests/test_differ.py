from differ import hash_response, semantic_diff, classify_severity

def test_identical_objects_same_hash():
    a = {"b": 2, "a": 1}
    b = {"a": 1, "b": 2}  # different key order
    assert hash_response(a) == hash_response(b)

def test_changed_value_detected():
    diff = semantic_diff({"price": 100}, {"price": 200})
    assert diff.get("values_changed")

def test_removed_key_is_critical():
    diff = semantic_diff({"a": 1, "b": 2}, {"a": 1})
    assert classify_severity(diff) == "CRITICAL"

def test_added_key_is_warning():
    diff = semantic_diff({"a": 1}, {"a": 1, "b": 2})
    assert classify_severity(diff) == "WARNING"

def test_type_change_is_critical():
    diff = semantic_diff({"id": 1}, {"id": "1"})
    assert classify_severity(diff) == "CRITICAL"

def test_no_change_returns_no_change():
    diff = semantic_diff({"a": 1}, {"a": 1})
    assert classify_severity(diff) == "NO_CHANGE"

def test_array_order_ignored_when_configured():
    diff = semantic_diff(["a","b"], ["b","a"], ignore_order=True)
    assert classify_severity(diff) == "NO_CHANGE"

def test_array_order_matters_by_default():
    diff = semantic_diff(["a","b"], ["b","a"], ignore_order=False)
    assert classify_severity(diff) != "NO_CHANGE"
