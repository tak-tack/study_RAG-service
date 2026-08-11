import argparse
from datetime import UTC, datetime

from app.core.config import settings
from app.db.models.saving_log import SavingLog
from app.db.session import SessionLocal
from app.ingestion.finlife import FinlifeCompanyClient
from app.ingestion.service import IngestionService

JOB_NAME = "finlife_company_sync"


def main() -> None:
    parser = argparse.ArgumentParser(description="Synchronize Finlife company data and embeddings.")
    parser.add_argument("--trigger", choices=("manual", "scheduled"), default="manual")
    parser.add_argument("--api-name", default="companySearch")
    arguments = parser.parse_args()

    session = SessionLocal()
    run = SavingLog(
        job_name=JOB_NAME,
        execution_type=arguments.trigger,
        api_name=arguments.api_name,
        status="running",
    )
    session.add(run)
    session.commit()

    try:
        client = FinlifeCompanyClient()
        total_companies = 0
        total_chunks = 0
        requested_page_numbers = settings.finlife_page_numbers()
        completed_groups: list[str] = []
        for group_number in settings.finlife_group_numbers():
            first_page = client.fetch_page(group_number, 1)
            page_numbers = [page for page in requested_page_numbers if page <= first_page.max_page_number]
            skipped_pages = [page for page in requested_page_numbers if page > first_page.max_page_number]
            if not page_numbers:
                raise ValueError(
                    f"No configured page is available for group {group_number}; "
                    f"Finlife API reports max_page_no={first_page.max_page_number}"
                )
            for page_number in page_numbers:
                page = first_page if page_number == 1 else client.fetch_page(group_number, page_number)
                result = IngestionService(session).sync_companies(page.documents, group_number)
                total_companies += result.companies_stored
                total_chunks += result.chunks_stored
            completed_groups.append(group_number)
            if skipped_pages:
                print(
                    f"Skipped unavailable pages for group {group_number}: "
                    f"{','.join(map(str, skipped_pages))}; max_page_no={first_page.max_page_number}"
                )

        run.status = "success"
        run.companies_stored = total_companies
        run.chunks_stored = total_chunks
        run.finished_at = datetime.now(UTC)
        session.commit()
        print(
            f"{JOB_NAME} completed: companies={total_companies}, chunks={total_chunks}, "
            f"groups={','.join(completed_groups)}, pages={','.join(map(str, requested_page_numbers))}"
        )
    except Exception as error:
        session.rollback()
        run.status = "failed"
        run.error_message = str(error)
        run.finished_at = datetime.now(UTC)
        session.add(run)
        session.commit()
        raise
    finally:
        session.close()


if __name__ == "__main__":
    main()
