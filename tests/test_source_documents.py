"""NiFi 전달 레코드의 오류 위치를 명확히 알려주는 변환 로직 테스트입니다."""

import pytest

from app.ingestion.client import SourceTextClient


def test_empty_record_identifies_records_index() -> None:
    with pytest.raises(ValueError, match=r"records\[1\] is an empty object"):
        SourceTextClient.to_documents([{"kor_co_nm": "정상"}, {}])


def test_blank_record_identifies_records_index() -> None:
    with pytest.raises(ValueError, match=r"records\[0\] contains only null or blank values"):
        SourceTextClient.to_documents([{"kor_co_nm": "", "cal_tel": None}])
