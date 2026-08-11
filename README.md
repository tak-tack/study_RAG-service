# Study RAG Service

로컬 우선 RAG 수집 서비스를 위한 Python 프로젝트입니다. 목표 처리 흐름은 다음과 같습니다.

`외부 REST API → 텍스트 정제 → 청크 분할 → Ollama 임베딩 → PostgreSQL + pgvector`

금융감독원 회사 정보 수집 배치가 구현되어 있습니다. 배치는 금융감독원 API의 페이지를 순회하고, 텍스트를 정규화해 LangChain 청크를 생성한 뒤 로컬 Ollama 임베딩을 만들고 pgvector에 저장합니다. 의미 검색, 프롬프트 구성, 채팅/RAG API는 의도적으로 아직 구현하지 않았습니다.

## 실행 준비

1. `.env.example`을 `.env`로 복사하고 필요하면 값을 변경합니다.
2. pgvector가 포함된 PostgreSQL을 실행합니다: `docker compose up -d postgres`.
3. Python 3.11+ 가상 환경을 만들고 프로젝트를 설치합니다: `pip install -e '.[dev]'`.
4. 데이터베이스 마이그레이션을 실행합니다: `alembic upgrade head`.
5. Ollama가 실행 중인지 확인하고 설정한 모델을 내려받습니다. 예: `ollama pull bge-m3`.
6. API를 실행합니다: `uvicorn app.main:app --reload`.

`GET /health`는 웹 프로세스가 실행 중인지 확인합니다. 데이터베이스나 Ollama 연결 상태는 검사하지 않습니다.

## 금융감독원 수집 배치

`.env`에 아래 값을 설정합니다. 인증 키는 Git에 커밋하지 마세요.

```env
FINLIFE_API_KEY=발급받은_인증키
FINLIFE_TOP_FIN_GRP_NOS=020000,030200,030300,050000,060000
FINLIFE_PAGE_NOS=1,2,3,4
```

`FINLIFE_TOP_FIN_GRP_NOS`와 `FINLIFE_PAGE_NOS`에는 각각 수집할 `topFinGrpNo`, `pageNo` 값을 쉼표로 구분해 지정합니다. 배치는 각 그룹의 최대 페이지를 확인하고 유효한 페이지만 순서대로 수집합니다.

Windows PowerShell에서 수동 실행 테스트를 하려면 다음 명령을 사용합니다.

```powershell
python -m app.jobs.finlife_company_sync --trigger manual
```

매일 오전 3시에 Windows 작업 스케줄러로 실행하려면 다음 명령을 사용합니다. `-StartAt` 값은 원하는 시간으로 바꿀 수 있습니다.

```powershell
.\scripts\register-finlife-sync-task.ps1 -StartAt "03:00"
```

작업 실행 이력은 `takhyeong_saving_log` 테이블에서 확인할 수 있습니다. `execution_type`은
`manual` 또는 `scheduled`이며, `api_name`에는 호출한 금융감독원 API 이름(현재 `companySearch`)이 저장됩니다.

수집 시 호출한 `topFinGrpNo`는 `takhyeong_saving_company.top_fin_grp_no`와
`takhyeong_saving_company_chunk.top_fin_grp_no`에 함께 저장됩니다. 동일 회사 번호라도
권역 코드가 다르면 별도 회사 레코드로 관리합니다.

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
- `app/ingestion` — 금융감독원 API 클라이언트, 텍스트 정제, LangChain 청킹, Ollama 임베딩, 저장 처리
- `app/jobs` — Windows 작업 스케줄러가 실행하는 수집 배치
- `app/retrieval` — 향후 의미 검색 기능을 위한 영역
- `app/rag` — 향후 컨텍스트 구성과 생성 처리를 위한 영역
- `alembic` — PostgreSQL/pgvector 스키마 마이그레이션
