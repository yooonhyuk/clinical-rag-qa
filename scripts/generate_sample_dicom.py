"""Generate synthetic DICOM files with fake values (no real patient data, blank pixels).

Usage: uv run --project backend python scripts/generate_sample_dicom.py

Files:
- sample-ct-anonymized.dcm      CT, all required/recommended tags, residual PHI-like FAKE values
                                (PatientName "TEST^PATIENT" etc.) so privacy warnings show up.
- sample-mr-anonymized.dcm      MR, properly de-identified, all tags present.
- sample-mr-missing-tags.dcm    MR, missing SliceThickness, ImageOrientationPatient, SOPInstanceUID
"""

from pathlib import Path
from typing import Any

from pydicom.dataset import FileDataset, FileMetaDataset
from pydicom.uid import ExplicitVRLittleEndian, generate_uid

OUT = Path(__file__).resolve().parents[1] / "samples" / "dicom"
_SOP_CLASS = {"CT": "1.2.840.10008.5.1.4.1.1.2", "MR": "1.2.840.10008.5.1.4.1.1.4"}


def build_dataset(
    modality: str, tags: dict[str, Any], *, omit: tuple[str, ...] = ()
) -> FileDataset:
    meta = FileMetaDataset()
    meta.MediaStorageSOPClassUID = _SOP_CLASS[modality]
    meta.MediaStorageSOPInstanceUID = generate_uid()
    meta.TransferSyntaxUID = ExplicitVRLittleEndian

    ds = FileDataset("synthetic", {}, file_meta=meta, preamble=b"\0" * 128)
    ds.SOPClassUID = meta.MediaStorageSOPClassUID
    ds.SOPInstanceUID = meta.MediaStorageSOPInstanceUID
    ds.StudyInstanceUID = generate_uid()
    ds.SeriesInstanceUID = generate_uid()
    ds.Modality = modality
    ds.Manufacturer = "DEMO_VENDOR"
    ds.SeriesNumber = 1
    ds.Rows = 64
    ds.Columns = 64
    ds.PixelSpacing = [0.7, 0.7]
    ds.SliceThickness = "1.0"
    ds.ImagePositionPatient = [0.0, 0.0, 0.0]
    ds.ImageOrientationPatient = [1.0, 0.0, 0.0, 0.0, 1.0, 0.0]
    ds.SamplesPerPixel = 1
    ds.PhotometricInterpretation = "MONOCHROME2"
    ds.BitsAllocated = 16
    ds.BitsStored = 12
    ds.HighBit = 11
    ds.PixelRepresentation = 0
    for key, value in tags.items():
        setattr(ds, key, value)
    for key in omit:
        if key in ds:
            delattr(ds, key)
    ds.PixelData = b"\0\0" * (64 * 64)  # blank image: nothing to "read"
    return ds


SAMPLES: dict[str, tuple[str, dict[str, Any], tuple[str, ...]]] = {
    "sample-ct-anonymized.dcm": (
        "CT",
        {
            "PatientName": "TEST^PATIENT",
            "PatientID": "FAKE-0001",
            "AccessionNumber": "FAKEACC0001",
            "StudyDate": "20260101",
            "StudyDescription": "DEMO CT CHEST",
            "SeriesDescription": "AXIAL 1.0",
            "BodyPartExamined": "CHEST",
        },
        (),
    ),
    "sample-mr-anonymized.dcm": (
        "MR",
        {
            "PatientID": "DEMO-001-0001",
            "StudyDescription": "DEMO MR BRAIN",
            "SeriesDescription": "T1 POST",
            "BodyPartExamined": "BRAIN",
        },
        (),
    ),
    "sample-mr-missing-tags.dcm": (
        "MR",
        {"PatientID": "DEMO-001-0002", "StudyDescription": "DEMO MR (BROKEN EXPORT)"},
        ("SliceThickness", "ImageOrientationPatient", "SOPInstanceUID"),
    ),
}


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for name, (modality, tags, omit) in SAMPLES.items():
        path = OUT / name
        build_dataset(modality, tags, omit=omit).save_as(path, enforce_file_format=True)
        print(f"wrote {path}")


if __name__ == "__main__":
    main()
