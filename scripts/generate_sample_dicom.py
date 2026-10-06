"""Generate synthetic DICOM files with fake values (no real patient data, blank pixels).

Usage: uv run --project backend python scripts/generate_sample_dicom.py   (= make samples)

The builders are also imported by the tests (pytest pythonpath includes scripts/).

Files (samples/dicom/):
- sample-ct-anonymized.dcm        classic CT, residual PHI-like FAKE values (TEST^PATIENT,
                                  descriptions, accession number) -> Layer 2 findings
- sample-mr-anonymized.dcm        classic MR, pseudonymised (subject ID) and declared
                                  de-identified (PatientIdentityRemoved=YES, CID 7050 code)
- sample-mr-missing-tags.dcm      MR missing SliceThickness, ImageOrientationPatient, SOPInstanceUID
- sample-enhanced-mr.dcm          Enhanced MR (2 frames), spatial info only in functional groups
- sample-pet-suv-ready.dcm        PET with all SUV-related attributes
- sample-pet-no-suv.dcm           PET without PatientWeight / radiopharmaceutical information
- sample-us-burned-in.dcm         US with Burned In Annotation = YES
- sample-phi-nested-private.dcm   CT with PHI-like values in nested sequences and private tags
- sample-malformed-values.dcm     CT with malformed UI / DA / TM / Modality values
"""

from collections.abc import Callable
from pathlib import Path
from typing import Any

from pydicom.dataset import Dataset, FileDataset, FileMetaDataset
from pydicom.sequence import Sequence
from pydicom.uid import ExplicitVRLittleEndian, generate_uid

OUT = Path(__file__).resolve().parents[1] / "samples" / "dicom"
SOP_CLASS = {
    "CT": "1.2.840.10008.5.1.4.1.1.2",
    "MR": "1.2.840.10008.5.1.4.1.1.4",
    "PT": "1.2.840.10008.5.1.4.1.1.128",
    "US": "1.2.840.10008.5.1.4.1.1.6.1",
    "ENHANCED_MR": "1.2.840.10008.5.1.4.1.1.4.1",
}
SUBJECT_ID = "DEMO-001-0001"


def _code(value: str, scheme: str, meaning: str) -> Dataset:
    item = Dataset()
    item.CodeValue = value
    item.CodingSchemeDesignator = scheme
    item.CodeMeaning = meaning
    return item


def _new(sop_class: str, modality: str) -> FileDataset:
    meta = FileMetaDataset()
    meta.MediaStorageSOPClassUID = sop_class
    meta.MediaStorageSOPInstanceUID = generate_uid()
    meta.TransferSyntaxUID = ExplicitVRLittleEndian
    ds = FileDataset("synthetic", {}, file_meta=meta, preamble=b"\0" * 128)
    ds.SOPClassUID = sop_class
    ds.SOPInstanceUID = meta.MediaStorageSOPInstanceUID
    # Patient / General Study: Type 2 attributes present but empty (Basic Profile "Z").
    ds.PatientName = ""
    ds.PatientID = ""
    ds.PatientBirthDate = ""
    ds.PatientSex = ""
    ds.StudyInstanceUID = generate_uid()
    ds.StudyDate = ""
    ds.StudyTime = ""
    ds.ReferringPhysicianName = ""
    ds.StudyID = ""
    ds.AccessionNumber = ""
    ds.SeriesInstanceUID = generate_uid()
    ds.Modality = modality
    ds.SeriesNumber = 1
    ds.Manufacturer = "DEMO_VENDOR"
    ds.InstanceNumber = 1
    ds.SamplesPerPixel = 1
    ds.PhotometricInterpretation = "MONOCHROME2"
    ds.Rows = 64
    ds.Columns = 64
    ds.BitsAllocated = 16
    ds.BitsStored = 12
    ds.HighBit = 11
    ds.PixelRepresentation = 0
    return ds


def _image_plane(ds: Dataset) -> None:
    ds.FrameOfReferenceUID = generate_uid()
    ds.PositionReferenceIndicator = ""
    ds.PixelSpacing = [0.7, 0.7]
    ds.SliceThickness = "1.0"
    ds.ImagePositionPatient = [0.0, 0.0, 0.0]
    ds.ImageOrientationPatient = [1.0, 0.0, 0.0, 0.0, 1.0, 0.0]


def _apply(ds: Dataset, tags: dict[str, Any], omit: tuple[str, ...]) -> None:
    for key, value in tags.items():
        setattr(ds, key, value)
    for key in omit:
        if key in ds:
            delattr(ds, key)


def _pixels(ds: Dataset, frames: int = 1) -> None:
    """Blank image: there is nothing to "read"."""
    bytes_per_sample = 1 if ds.get("BitsAllocated") == 8 else 2
    rows, columns = ds.get("Rows") or 64, ds.get("Columns") or 64
    ds.PixelData = b"\0" * (rows * columns * frames * bytes_per_sample)


def _pet(ds: Dataset) -> None:
    ds.SeriesDate = "20260101"
    ds.SeriesTime = "090000"
    ds.Units = "BQML"
    ds.CountsSource = "EMISSION"
    ds.SeriesType = ["STATIC", "IMAGE"]
    ds.NumberOfSlices = 1
    ds.CorrectedImage = ["ATTN", "DECY"]
    ds.DecayCorrection = "START"
    ds.CollimatorType = "NONE"
    ds.RescaleIntercept = "0"
    ds.RescaleSlope = "1"
    ds.FrameReferenceTime = "0"
    ds.ImageIndex = 1
    ds.AcquisitionDate = "20260101"
    ds.AcquisitionTime = "090000"
    ds.ActualFrameDuration = 300000
    ds.PatientWeight = "70"
    ds.PatientGantryRelationshipCodeSequence = Sequence([_code("F-10470", "SRT", "headfirst")])
    ds.PatientOrientationCodeSequence = Sequence([_code("F-10450", "SRT", "recumbent")])
    dose = Dataset()
    dose.RadiopharmaceuticalStartTime = "083000"
    dose.RadionuclideTotalDose = "370000000"
    dose.RadionuclideHalfLife = "6586.2"
    dose.RadionuclideCodeSequence = Sequence([_code("C-111A1", "SRT", "^18^Fluorine")])
    ds.RadiopharmaceuticalInformationSequence = Sequence([dose])


def build_dataset(
    modality: str, tags: dict[str, Any] | None = None, *, omit: tuple[str, ...] = ()
) -> FileDataset:
    """Classic single-frame CT / MR / PT / US image with the mandatory Type 1/2 attributes."""
    ds = _new(SOP_CLASS[modality], modality)
    if modality in ("CT", "MR", "PT"):
        _image_plane(ds)
    ds.ImageType = ["ORIGINAL", "PRIMARY", "AXIAL"]
    if modality == "CT":
        ds.RescaleIntercept = "-1024"
        ds.RescaleSlope = "1"
        ds.KVP = "120"
        ds.AcquisitionNumber = 1
    elif modality == "MR":
        ds.ScanningSequence = "SE"
        ds.SequenceVariant = "NONE"
        ds.ScanOptions = ""
        ds.MRAcquisitionType = "2D"
        ds.EchoTime = "10"
        ds.EchoTrainLength = 1
    elif modality == "PT":
        _pet(ds)
    elif modality == "US":
        ds.BitsAllocated = 8
        ds.BitsStored = 8
        ds.HighBit = 7
        ds.ImageType = ["ORIGINAL", "PRIMARY"]
    _apply(ds, tags or {}, omit)
    _pixels(ds)
    return ds


def build_enhanced_mr(frames: int = 2, *, shared_spatial: bool = True) -> FileDataset:
    """Enhanced MR: Pixel Measures / Plane Orientation shared, Plane Position per frame.

    With shared_spatial=False the shared macros are left out (to test L1-FG-MISSING).
    """
    ds = _new(SOP_CLASS["ENHANCED_MR"], "MR")
    ds.FrameOfReferenceUID = generate_uid()
    ds.PositionReferenceIndicator = ""
    ds.ImageType = ["ORIGINAL", "PRIMARY", "M", "NONE"]
    ds.NumberOfFrames = frames
    ds.ContentDate = ""
    ds.ContentTime = ""
    shared = Dataset()
    if shared_spatial:
        pixel = Dataset()
        pixel.PixelSpacing = [0.5, 0.5]
        pixel.SliceThickness = "2.0"
        orientation = Dataset()
        orientation.ImageOrientationPatient = [1.0, 0.0, 0.0, 0.0, 1.0, 0.0]
        shared.PixelMeasuresSequence = Sequence([pixel])
        shared.PlaneOrientationSequence = Sequence([orientation])
    per_frame = []
    for i in range(frames):
        item = Dataset()
        position = Dataset()
        position.ImagePositionPatient = [0.0, 0.0, float(i * 2)]
        item.PlanePositionSequence = Sequence([position])
        content = Dataset()
        content.FrameAcquisitionNumber = i + 1
        item.FrameContentSequence = Sequence([content])
        per_frame.append(item)
    ds.SharedFunctionalGroupsSequence = Sequence([shared])
    ds.PerFrameFunctionalGroupsSequence = Sequence(per_frame)
    _pixels(ds, frames)
    return ds


def declare_deidentified(ds: Dataset, *codes: tuple[str, str]) -> Dataset:
    """PatientIdentityRemoved=YES + De-identification Method Code Sequence (CID 7050)."""
    ds.PatientIdentityRemoved = "YES"
    ds.DeidentificationMethodCodeSequence = Sequence(
        [_code(value, "DCM", meaning) for value, meaning in codes]
        or [_code("113100", "DCM", "Basic Application Confidentiality Profile")]
    )
    return ds


def build_pseudonymized_mr() -> FileDataset:
    ds = build_dataset("MR", {"PatientID": SUBJECT_ID, "PatientName": SUBJECT_ID})
    return declare_deidentified(ds)


def build_phi_nested_private() -> FileDataset:
    """PHI-like values hidden in nested sequences and private tags (all FAKE)."""
    ds = build_dataset("CT", {"PatientID": SUBJECT_ID})
    block = ds.private_block(0x0011, "DEMO PRIVATE CREATOR", create=True)
    block.add_new(0x01, "LO", "FAKE^PRIVATE^NAME")
    block.add_new(0x02, "LO", "FAKE-MRN-0099")
    request = Dataset()
    request.RequestedProcedureDescription = "FAKE NESTED DESCRIPTION"
    request.RequestingPhysician = "FAKE^DOCTOR"
    ds.RequestAttributesSequence = Sequence([request])
    other = Dataset()
    other.PatientID = "FAKE-OTHER-ID-77"
    ds.OtherPatientIDsSequence = Sequence([other])
    return ds


def build_malformed() -> FileDataset:
    return build_dataset(
        "CT",
        {
            "StudyInstanceUID": "1.2.840.01.5",  # leading zero in a component
            "SeriesInstanceUID": "1.2.abc.4",  # non-numeric
            "StudyDate": "2026-01-01",  # not YYYYMMDD
            "StudyTime": "25:61",  # not HHMMSS
            "Modality": "CTX",  # not a Defined Term
        },
    )


SAMPLES: dict[str, Callable[[], FileDataset]] = {
    "sample-ct-anonymized.dcm": lambda: build_dataset(
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
    ),
    "sample-mr-anonymized.dcm": build_pseudonymized_mr,
    "sample-mr-missing-tags.dcm": lambda: build_dataset(
        "MR",
        {"PatientID": "DEMO-001-0002"},
        omit=("SliceThickness", "ImageOrientationPatient", "SOPInstanceUID"),
    ),
    "sample-enhanced-mr.dcm": build_enhanced_mr,
    "sample-pet-suv-ready.dcm": lambda: build_dataset("PT", {"PatientID": SUBJECT_ID}),
    "sample-pet-no-suv.dcm": lambda: build_dataset(
        "PT",
        {"PatientID": SUBJECT_ID},
        omit=("PatientWeight", "RadiopharmaceuticalInformationSequence"),
    ),
    "sample-us-burned-in.dcm": lambda: build_dataset(
        "US", {"PatientID": SUBJECT_ID, "BurnedInAnnotation": "YES"}
    ),
    "sample-phi-nested-private.dcm": build_phi_nested_private,
    "sample-malformed-values.dcm": build_malformed,
}


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for name, builder in SAMPLES.items():
        path = OUT / name
        builder().save_as(path, enforce_file_format=True)
        print(f"wrote {path}")


if __name__ == "__main__":
    main()
