import json
import shutil

from generate_sample_dicom import build_phi_nested_private, build_pseudonymized_mr

from app.cli.dicom_scan import main
from tests.conftest import SAMPLES


def test_scan_folder_prints_summary_and_jsonl(tmp_path, capsys) -> None:
    folder = tmp_path / "study"
    (folder / "sub").mkdir(parents=True)
    build_pseudonymized_mr().save_as(folder / "a.dcm", enforce_file_format=True)
    build_phi_nested_private().save_as(folder / "sub" / "IM0001", enforce_file_format=True)
    (folder / "notes.txt").write_text("not dicom")
    out = tmp_path / "scan.jsonl"

    assert main([str(folder), "--json", str(out)]) == 0
    text = capsys.readouterr().out
    assert "DICOM files: 2  skipped (not DICOM): 1" in text
    assert "DEID-PRIVATE-PRESENT private attributes" in text
    assert "FAKE^PRIVATE^NAME" not in text
    records = [json.loads(line) for line in out.read_text().splitlines()]
    assert len(records) == 2 and {"layer1", "layer2", "counts"} <= set(records[0])
    assert "FAKE^PRIVATE^NAME" not in out.read_text()


def test_fail_on_error_and_redacted_paths(tmp_path, capsys) -> None:
    shutil.copy(SAMPLES / "dicom" / "sample-ct-anonymized.dcm", tmp_path / "secret-name.dcm")
    assert main([str(tmp_path), "--fail-on", "error", "--redact-paths"]) == 1
    text = capsys.readouterr().out
    assert "secret-name" not in text and "#1" in text
