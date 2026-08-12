# Study RAG Service

로컬 우선 RAG 수집 서비스를 위한 Python 프로젝트입니다. 목표 처리 흐름은 다음과 같습니다.

`외부 REST API → 텍스트 정제 → 청크 분할 → Ollama 임베딩 → PostgreSQL + pgvector`

NiFi가 금융감독원 API를 호출해 전달한 회사 정보를 텍스트 정규화, LangChain 청킹, 로컬 Ollama 임베딩을 거쳐 pgvector에 저장합니다. 의미 검색, 프롬프트 구성, 채팅/RAG API는 의도적으로 아직 구현하지 않았습니다.

## 실행 준비

1. `.env.example`을 `.env`로 복사하고 필요하면 값을 변경합니다.
2. pgvector가 포함된 PostgreSQL을 실행합니다: `docker compose up -d postgres`.
3. Python 3.11+ 가상 환경을 만들고 프로젝트를 설치합니다: `pip install -e '.[dev]'`.
4. 데이터베이스 마이그레이션을 실행합니다: `alembic upgrade head`.
5. Ollama가 실행 중인지 확인하고 설정한 모델을 내려받습니다. 예: `ollama pull bge-m3`.
6. API를 실행합니다: `uvicorn app.main:app --reload`.

`GET /health`는 웹 프로세스가 실행 중인지 확인합니다. 데이터베이스나 Ollama 연결 상태는 검사하지 않습니다.

## NiFi 수신 연동

NiFi가 Open API를 호출·정규화한 뒤 FastAPI로 전송하는 경우 아래 엔드포인트를 사용합니다.

```text
POST /api/nifi/finlife/companies
```

`.env`에 NiFi와 공유할 비밀 키를 설정합니다. 운영 환경에서는 빈 값으로 두지 마십시오.

```env
NIFI_INGEST_API_KEY=충분히_긴_임의의_비밀값
```

NiFi의 `InvokeHTTP` 프로세서는 `POST`와 `Content-Type: application/json`을 사용합니다.
아래 식별 정보는 JSON Body가 아니라 HTTP Header에 넣어야 합니다. `X-API-Key`는
`.env`에서 `NIFI_INGEST_API_KEY`를 설정한 경우에만 추가합니다.

```text
X-Top-Fin-Grp-No: 020000
X-Page-No: 1
X-Api-Name: companySearch
X-API-Key: <NIFI_INGEST_API_KEY 값, 설정한 경우에만>
```

요청 Body는 `records`만 포함합니다.

```json
{
  "records": [
    {
      "dcls_month": "202607",
      "fin_co_no": "0010001",
      "kor_co_nm": "우리은행",
      "dcls_chrg_man": "개인상품마케팅부, 1588-5000",
      "homp_url": "https://example.com",
      "cal_tel": "15885000"
    }
  ]
}
```

`records`는 Finlife API의 `result.baseList` 배열을 변환 없이 담을 수 있습니다. `X-Top-Fin-Grp-No`는
6자리 문자열, `X-Page-No`는 1 이상의 정수여야 합니다. FastAPI는 레코드의 필수 키
`dcls_month`, `fin_co_no`, `kor_co_nm`을 검증하고, 텍스트 정제 → 청킹 →
`bge-m3` 임베딩 → `takhyeong_saving_company` 및
`takhyeong_saving_company_chunk` 저장을 수행합니다. 성공·실패 이력은
`takhyeong_saving_log`에 `execution_type = nifi`와 함께 기록됩니다.

`records`가 빈 배열이면 FastAPI는 DB INSERT, 적재, 임베딩을 모두 수행하지 않고 HTTP
`201`과 `status: "no_data"`, `log_id: null`, 저장 건수 `0`을 반환합니다.

동일한 `top_fin_grp_no`와 `fin_co_no`의 원본 저장 필드가 이전 적재 내용과 같으면 FastAPI는
원본 갱신과 청크 삭제·임베딩 재생성을 생략합니다. 이때 로그와 응답의
`companies_stored`, `chunks_stored`는 모두 `0`입니다. 값이 새로 생성되거나 변경된
회사만 해당 건수에 포함됩니다.

## 공용 `chatbot` 스키마 사용 시 초기화

`chatbot` 스키마에 다른 시스템의 `document_chunks`가 이미 있을 수 있습니다. 이
프로젝트는 해당 테이블을 사용하거나 변경하지 않습니다. 외부 DB를 처음 연결할 때는
아래 명령을 **한 번만** 순서대로 실행합니다.

```powershell
python -m alembic stamp 0005_saving_log
python -m alembic upgrade head
```

첫 번째 명령은 과거 로컬 프로토타입 마이그레이션을 실행하지 않고, 이 프로젝트의
전용 이력 테이블 `takhyeong_saving_alembic_version`에 기준 버전만 기록합니다.
두 번째 명령은 현재 사용하는 다음 테이블만 생성합니다.

- `takhyeong_saving_company`
- `takhyeong_saving_company_chunk`
- `takhyeong_saving_log`

## 프로젝트 구조

- `app/core` — 애플리케이션 설정
- `app/db` — SQLAlchemy base, 세션 팩토리, pgvector 모델
- `app/api` — NiFi가 호출하는 FastAPI 웹훅
- `app/ingestion` — NiFi 전달 데이터의 텍스트 정제, LangChain 청킹, Ollama 임베딩, 저장 처리
- `app/retrieval` — 향후 의미 검색 기능을 위한 영역
- `app/rag` — 향후 컨텍스트 구성과 생성 처리를 위한 영역
- `alembic` — PostgreSQL/pgvector 스키마 마이그레이션
