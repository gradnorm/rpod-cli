from rpod.pod import pod_label


def test_pod_label_uses_name_and_id():
    assert pod_label({"name": "train", "id": "abc123"}) == "train (abc123)"


def test_pod_label_handles_missing_values():
    assert pod_label({}) == "unnamed (unknown-id)"
