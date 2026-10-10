"""eval/tune_cosine_gate.py replays a gate-off run; the tie rule and the split are fixed."""

from tune_cosine_gate import objective, replay


def _row(qid: str, answerable: bool, cosine: float, refused: bool = False) -> dict:
    return {"id": qid, "answerable": answerable, "maxCosine": cosine, "refused": refused}


ROWS = [
    _row("a1", True, 0.80),
    _row("a2", True, 0.62),
    _row("a3", True, 0.50),
    _row("m1", False, 0.55),
    _row("m2", False, 0.40),
    _row("m3", False, 0.30, refused=True),  # refused by the generator / scope, whatever the gate
]


def test_replay_without_gate_counts_only_real_refusals() -> None:
    m = replay(ROWS, -1.0)
    assert (m["false_refusals"], m["refused_correctly"]) == (0, 1)


def test_replay_applies_the_cosine_threshold_to_every_question() -> None:
    m = replay(ROWS, 0.45)
    assert (m["false_refusals"], m["answerable"]) == (0, 3)
    assert (m["refused_correctly"], m["must_refuse"]) == (2, 3)  # m2 (0.40) and m3
    m = replay(ROWS, 0.60)
    assert m["false_refusals"] == 1  # a3 (0.50) is lost
    assert m["refused_correctly"] == 3


def test_objective_is_refusal_accuracy_minus_false_refusal_rate() -> None:
    # 0.45: 2/3 - 0/3 ; 0.60: 3/3 - 1/3 ; 0.0: 1/3 - 0
    assert round(objective(replay(ROWS, 0.45)), 4) == round(2 / 3, 4)
    assert round(objective(replay(ROWS, 0.60)), 4) == round(2 / 3, 4)
    assert objective(replay(ROWS, 0.0)) < objective(replay(ROWS, 0.45))
