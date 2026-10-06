from tune_gate import replay, split


def _row(qid: str, qtype: str, answerable: bool, refused: bool, score: float | None) -> dict:
    return {
        "id": qid,
        "type": qtype,
        "answerable": answerable,
        "refused": refused,
        "gate": {"topRerank": score},
    }


def test_split_alternates_within_each_type_and_keeps_toy_in_dev() -> None:
    rows = [_row(i, t, True, False, 0.5) for i, t in [("p03", "a"), ("p01", "a"), ("p02", "b")]]
    assert split("public", rows) == {"p01": "dev", "p03": "test", "p02": "dev"}
    assert set(split("toy", rows).values()) == {"dev"}


def test_replay_refuses_below_threshold_including_zero_scores() -> None:
    rows = [
        _row("a", "f", True, False, 0.9),
        _row("b", "f", True, False, 0.0),
        _row("c", "n", False, False, 0.05),
        _row("d", "n", False, True, None),
    ]
    m = replay(rows, 0.1)
    assert m["false_refusals"] == 1 and m["refused_correctly"] == 2
    assert m["gate_refused_ids"] == ["b", "c"]
    assert replay(rows, 0.0)["refused_correctly"] == 1
