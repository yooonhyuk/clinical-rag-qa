from fastapi import APIRouter, HTTPException, status

from app.api.deps import ContainerDep, SessionDep, resolve_allowed_path
from app.models import DicomFile
from app.schemas.dicom import (
    DicomAnalyzeRequest,
    DicomAnalyzeResponse,
    DicomFileListResponse,
    QAResult,
)
from app.services.dicom_service import DISCLAIMER, DicomReadError

router = APIRouter(prefix="/api/dicom", tags=["dicom"])


@router.get("/files", response_model=DicomFileListResponse)
async def list_dicom_files(container: ContainerDep) -> DicomFileListResponse:
    """DICOM files available for analysis (DICOM_PATH and samples)."""
    settings = container.settings
    roots = [settings.dicom_path, settings.samples_path / "dicom"]
    files = sorted(str(p) for root in roots if root.is_dir() for p in root.rglob("*.dcm"))
    return DicomFileListResponse(files=files)


@router.post("/analyze", response_model=DicomAnalyzeResponse, response_model_by_alias=True)
async def analyze(
    body: DicomAnalyzeRequest, container: ContainerDep, session: SessionDep
) -> DicomAnalyzeResponse:
    settings = container.settings
    path = resolve_allowed_path(body.file_path, settings.allowed_roots, base=settings.dicom_path)
    try:
        analysis = await container.dicom.analyze(path, explain=body.explain)
    except DicomReadError as exc:
        session.add(
            DicomFile(
                file_name=path.name,
                file_path=str(path),
                checksum="0" * 64,
                status="FAILED",
                tags={"error": str(exc)},
                privacy_warnings=[],
                missing_required_tags=[],
            )
        )
        await session.commit()
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc)) from exc

    session.add(
        DicomFile(
            file_name=analysis.file_name,
            file_path=analysis.file_path,
            checksum=analysis.checksum,
            status="ANALYZED",
            tags=analysis.tag_summary,
            privacy_warnings=analysis.privacy_warnings,
            missing_required_tags=analysis.missing_required_tags,
        )
    )
    await session.commit()
    return DicomAnalyzeResponse(
        file_name=analysis.file_name,
        summary=analysis.summary,
        summary_source=analysis.summary_source,
        tag_summary=analysis.tag_summary,
        privacy_warnings=analysis.privacy_warnings,
        missing_required_tags=analysis.missing_required_tags,
        qa_result=QAResult(
            passed=analysis.passed,
            warnings=analysis.warnings,
            missing=analysis.missing_required_tags,
        ),
        rule_source=analysis.rule_source,
        disclaimer=DISCLAIMER,
    )
