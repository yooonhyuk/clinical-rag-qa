from eval_metrics import EvalQuestion
from retrieval_diagnostics import diagnose, trial_of


def test_trial_of_uses_the_nct_prefix() -> None:
    assert trial_of("NCT04494425_SAP_003.pdf") == "NCT04494425"
    assert trial_of("protocol_NCT03761056.pdf") == "NCT03761056"
    assert trial_of("recist_1.1_eisenhauer_2009.pdf") == "recist_1.1_eisenhauer_2009.pdf"


def test_probe_counts_scope_refused_questions_and_other_trial_chunks() -> None:
    q = EvalQuestion.from_dict(
        {
            "id": "r1",
            "type": "imaging_schedule",
            "question": "MRI 주기?",
            "expected_sources": [{"file": "NCT00000001_Prot_000.pdf", "pages": [3]}],
        }
    )
    row = {
        "id": "r1",
        "answerable": True,
        "refused": True,
        "refusalReason": "OUT_OF_SCOPE",
        "probe": [
            {"file": "NCT00000001_SAP_001.pdf", "section": None, "page": 9},
            {"file": "NCT00000001_Prot_000.pdf", "section": None, "page": 3},
            {"file": "NCT00000002_Prot_000.pdf", "section": None, "page": 3},
            {"file": "NCT00000003_Prot_000.pdf", "section": None, "page": 1},
        ],
    }
    report = diagnose([row], {"r1": q})
    assert report["probe_file_hit_at_k"] == 1.0
    assert report["probe_section_hit_at_k"] == 1.0
    assert report["other_trial_chunk_share"] == 0.5  # the SAP of the same trial is not "other"
    assert report["answerable_refused_by_reason"] == {"OUT_OF_SCOPE": 1}
