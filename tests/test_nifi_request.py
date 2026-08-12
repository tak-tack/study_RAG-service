"""NiFi 수신 요청 형식과 빈 레코드 처리 계약을 검증합니다."""

from app.api.nifi import FinlifeCompanyIngestionRequest, NiFiIngestionResponse


def test_empty_records_is_a_valid_no_data_request() -> None:
    request = FinlifeCompanyIngestionRequest.model_validate({"records": []})
    assert request.records == []


def test_no_data_response_does_not_require_log_id() -> None:
    response = NiFiIngestionResponse(
        log_id=None,
        status="no_data",
        company_ids=[],
        companies_stored=0,
        chunks_stored=0,
    )
    assert response.log_id is None
