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

## 기술 선정 이유
1. Postgre + pgvector 
- 기존 관계형 데이터와 벡터 데이터를 하나의 PostgreSQL 환경에서 함께 관리할 수 있고,별도의 VectorDB를 구축하지 않아도
pgvector 확장을 통해 벡터 유사도 검색을 구현할 수 있다.
- 금융회사 코드, 상품 유형 등 정형 데이터 조건과 벡터 유사도 검색을 결합한 검색이 가능하고, 기존 PostgreSQL 의 트랜잭션, 백업, 권한 관리, 인덱싱 등
운영 기능을 그대로 활용할 수 있다는 장점이 있다.
- 구축이 간단함 : 별도의 Vector DB 서버를 추가하지 않고 PostgreSQL 에 `pgvector` extension 만 추가
- 정형 + 백터 데이터 통합 : 회사코드, 상품구분 같은 일반 컬럼과 embedding 을 같은 DB에서 관리
- 필터+벡터검색 가능 : `where 금융권역='은행` 같은 조건 + 유사도 검색 조합 가능
- SQL 사용 가능 : 기존 PostgreSQL/SQL 경험을 그대로 활용
- 운영 부담 감소 : DB를 PostgreSQL+별도 Vector DB 두 개로 운영할 필요가 없음
- 트랜잭션 지원 : PostgreSQL 의 ACID 특성을 그대로 활용
- 인덱스 지원 : pgvector의 HNSW, IVFFlat 등을 이용해 벡터 검색 성능 개선 가능
- RAG 규모에 적합 : 수십만 ~ 수백만 정도의 일반적인 사내 RAG라면 충분히 현실적인 선택

2. Python 3.11+
- AI/RAG 관련 라이브러리와 프레임워크 지원이 가장 활발하고, 외부 API 연동과 데이터 가공, 임베딩 처리,
Vector DB 연계까지 하나의 언어로 빠르게 구현 가능
- Java는 대규모 엔터프라이즈 서비스나 복잡한 비즈니스 로직 처리에 강점이 있지만, 해당 프로젝트는 AI 모델 연동,
임베딩, 벡터 검색, 데이터 전처리가 핵심이기 때문에 과련 생태계가 더 풍부한 Python 이 적합하고 FastAPI 를 활용하면
별도의 무거운 WAS 구성 없이 REST API 를 빠르게 구현할 수 있다.
-> 요약 : AI/RAG 생태계가 Python 중심이고, 데이터 가공. 임베딩.Vector DB 연동.API 개발을 하나의 언어로 빠르게 구현할 수 있어서 Python 3.11+ 를 선정
- AI/RAG 생태계가 가장 큼 : OpenAI SDK, LangChain, LlamaIndex, sentence-transformers 등 대부분 Python 지원이 가장 빠름
- 데이터 처리 편함 : JSON, CSV, 텍스트 가공이 쉬움
- API 개발이 빠름 : FastAPI 같은 경량 프레임워크로 REST API 구현이 간단
- Vector DB 연동 편함 : pgvector, Qdrant, Milvus 등 관련 라이브러리 지원이 좋음
- 임베딩 처리에 유리 : Hugging Face, Pytorch, transformers 등 AI 라이브러리 대부분 Python 중심
- 개발 속도 빠름 : Java 보다 코드량이 적고 프로토타이핑이 빠름
- 3.11+ 성능 향상 : CPython 자체 실행 성능이 이전 보다 개선됨
- 최신 라이브러리 호환성 : 최신 AI 패키지들이 Python 3.10 ~ 3.12 정도를 주력 지원하는 경우가 많음

3. Ollama : AI 모델을 로컬에서 실행하고 관리해주는 도구
- #### 외부 모델 API로 원문 데이터를 보내지 않는 아키텍처를 구성할 수 있다.
- 로컬 환경에서 AI 모델을 간편하게 실행하고 REST API 형태로 사용
- 로컬 실행 : 외부 AI API 를 호출하지 않고 내부 서버에서 모델 실행 가능
- 구축이 간단 : 복잡한 모델 실행환경을 직접 구성할 필요가 적음
- REST API 제공 : Python 에서 HTTP 요청으로 쉽게 호출 가능
- 모델 관리 편리 : 모델 다운로드/실행/교체가 간단
- 비용 절감 : 외부 임베딩 API의 호출량 기반 비용을 줄일 수 있음
- 데이터 보안 : 금융 데이터를 외부 AI 서비스로 전송하지 않는 구조 구성 가능
- 모델 교체 용이 : 다른 임베딩/LLM 모델을 비교적 쉽게 테스트 가능

4. BGE-M3 : 문장을 숫자(Vector)로 바꿔주는 Embedding 모델
- 다국어 지원 : 한국어를 포함한 다양한 언어 지원
- 검색 특화 : 일반 텍스트 생성이 아니라 정보 검색/Retrieval 용도로 활용하기 좋음
- 오픈소스 모델 : 자체 환경에서 모델 운영 가능
- Dense Retrieval 지원 : 의미 기반 Vector 검색에 활용 가능
- 긴 텍스트 처리 : 비교적 긴 문서도 처리할 수 있어 문서 검색에 유리
- RAG 적합성 : 문서와 질문 간 의미적 유사도를 찾는 Retrieval 단계에 활용하기 좋음

5. Ollama + BGE-M3
- Ollama는 외부 AI API에 의존하지 않고 내부 환경에서 임베딩 모델을 간편하게 실행·관리하고 
REST API로 연동하기 위해 선정. 
- BGE-M3는 한국어를 포함한 다국어 지원과 검색에 적합한 임베딩 성능을 제공하는 
오픈소스 모델이기 때문에 선정. 
이를 통해 금융 데이터를 내부 환경에서 임베딩하고 pgvector에 저장하여 의미 기반 검색이 가능한 
RAG 구조를 구성

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
