"""
Usage tracking and enforcement service for cost control.

Tracks document uploads, storage, AI queries, and embeddings to enforce
plan-based limits and prevent cost overruns.
"""

from datetime import date
from typing import Dict, Optional
from uuid import UUID

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession


class UsageTracker:
    """Track and enforce usage limits per company plan tier."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def check_document_limit(self, company_id: UUID) -> bool:
        """
        Check if company can upload more documents.

        Returns:
            True if upload is allowed, False if limit reached
        """
        query = text("""
            SELECT
                c.usage_documents_count,
                pl.max_documents
            FROM bc_legal_ds.companies c
            JOIN bc_legal_ds.plan_limits pl ON pl.plan_tier = c.plan_tier
            WHERE c.id = :company_id
        """)

        result = await self.db.execute(query, {"company_id": str(company_id)})
        row = result.first()

        if not row:
            return False

        current, max_allowed = row

        # -1 means unlimited
        if max_allowed == -1:
            return True

        return current < max_allowed

    async def check_storage_limit(self, company_id: UUID, file_size_bytes: int) -> bool:
        """
        Check if company has storage space for new file.

        Args:
            company_id: Company UUID
            file_size_bytes: Size of file to upload in bytes

        Returns:
            True if upload is allowed, False if limit reached
        """
        query = text("""
            SELECT
                c.usage_storage_bytes,
                pl.max_storage_gb
            FROM bc_legal_ds.companies c
            JOIN bc_legal_ds.plan_limits pl ON pl.plan_tier = c.plan_tier
            WHERE c.id = :company_id
        """)

        result = await self.db.execute(query, {"company_id": str(company_id)})
        row = result.first()

        if not row:
            return False

        current_bytes, max_gb = row

        # -1 means unlimited
        if max_gb == -1:
            return True

        max_bytes = max_gb * 1024 * 1024 * 1024
        return (current_bytes + file_size_bytes) <= max_bytes

    async def check_ai_query_limit(self, company_id: UUID) -> bool:
        """
        Check if company can make more AI queries this month.
        Auto-resets counter on new month.

        Returns:
            True if query is allowed, False if limit reached
        """
        query = text("""
            SELECT
                c.usage_ai_queries_count,
                c.usage_reset_date
            FROM bc_legal_ds.companies c
            WHERE c.id = :company_id
        """)

        result = await self.db.execute(query, {"company_id": str(company_id)})
        row = result.first()

        if not row:
            return False

        current_queries, reset_date = row

        # Check if we need to reset monthly counter
        first_of_month = date.today().replace(day=1)
        if reset_date is None or reset_date < first_of_month:
            await self.reset_monthly_usage(company_id)

        # For now, AI queries are unlimited
        return True

    async def check_document_size_limit(self, company_id: UUID, file_size_bytes: int) -> bool:
        """
        Check if document size is within plan limits.

        Args:
            company_id: Company UUID
            file_size_bytes: Size of document in bytes

        Returns:
            True if size is allowed, False if too large
        """
        query = text("""
            SELECT pl.max_document_size_mb
            FROM bc_legal_ds.companies c
            JOIN bc_legal_ds.plan_limits pl ON pl.plan_tier = c.plan_tier
            WHERE c.id = :company_id
        """)

        result = await self.db.execute(query, {"company_id": str(company_id)})
        row = result.first()

        if not row:
            return False

        max_mb = row[0]
        max_bytes = max_mb * 1024 * 1024

        return file_size_bytes <= max_bytes

    async def increment_document_count(self, company_id: UUID, file_size_bytes: int) -> None:
        """
        Increment document count and storage usage.

        Args:
            company_id: Company UUID
            file_size_bytes: Size of uploaded document in bytes
        """
        query = text("""
            UPDATE bc_legal_ds.companies
            SET
                usage_documents_count = usage_documents_count + 1,
                usage_storage_bytes = usage_storage_bytes + :file_size
            WHERE id = :company_id
        """)

        await self.db.execute(
            query,
            {"company_id": str(company_id), "file_size": file_size_bytes}
        )
        await self.db.commit()

    async def increment_ai_query_count(self, company_id: UUID) -> None:
        """
        Increment AI query count for the current month.

        Args:
            company_id: Company UUID
        """
        query = text("""
            UPDATE bc_legal_ds.companies
            SET usage_ai_queries_count = usage_ai_queries_count + 1
            WHERE id = :company_id
        """)

        await self.db.execute(query, {"company_id": str(company_id)})
        await self.db.commit()

    async def increment_embeddings_count(self, company_id: UUID, chunk_count: int) -> None:
        """
        Increment embeddings count (for cost tracking).

        Args:
            company_id: Company UUID
            chunk_count: Number of chunks/embeddings generated
        """
        query = text("""
            UPDATE bc_legal_ds.companies
            SET usage_embeddings_count = usage_embeddings_count + :chunk_count
            WHERE id = :company_id
        """)

        await self.db.execute(
            query,
            {"company_id": str(company_id), "chunk_count": chunk_count}
        )
        await self.db.commit()

    async def reset_monthly_usage(self, company_id: UUID) -> None:
        """
        Reset monthly usage counters (AI queries).
        Called automatically when usage_reset_date is in the past.

        Args:
            company_id: Company UUID
        """
        first_of_month = date.today().replace(day=1)

        query = text("""
            UPDATE bc_legal_ds.companies
            SET
                usage_ai_queries_count = 0,
                usage_reset_date = :reset_date
            WHERE id = :company_id
        """)

        await self.db.execute(
            query,
            {"company_id": str(company_id), "reset_date": first_of_month}
        )
        await self.db.commit()

    async def get_usage_stats(self, company_id: UUID) -> Dict:
        """
        Get current usage statistics with limits and percentages.

        Returns:
            Dictionary with usage details for documents, storage, and AI queries
        """
        query = text("""
            SELECT
                c.usage_documents_count,
                c.usage_storage_bytes,
                c.usage_ai_queries_count,
                c.usage_embeddings_count,
                c.plan_tier,
                pl.max_documents,
                pl.max_storage_gb,
                pl.max_document_size_mb,
                pl.max_users
            FROM bc_legal_ds.companies c
            JOIN bc_legal_ds.plan_limits pl ON pl.plan_tier = c.plan_tier
            WHERE c.id = :company_id
        """)

        result = await self.db.execute(query, {"company_id": str(company_id)})
        row = result.first()

        if not row:
            return {}

        (
            doc_count, storage_bytes, ai_queries, embeddings_count,
            plan_tier, max_docs, max_storage_gb,
            max_doc_size_mb, max_users
        ) = row

        def calc_percentage(current: int, maximum: int) -> float:
            """Calculate percentage, handling unlimited (-1) plans."""
            if maximum == -1:
                return 0.0
            if maximum == 0:
                return 100.0 if current > 0 else 0.0
            return (current / maximum) * 100

        storage_gb = storage_bytes / (1024 ** 3)
        storage_mb = storage_bytes / (1024 ** 2)

        return {
            "plan_tier": plan_tier,
            "documents": {
                "current": doc_count,
                "limit": max_docs if max_docs != -1 else "unlimited",
                "percentage": calc_percentage(doc_count, max_docs)
            },
            "storage": {
                "current_bytes": storage_bytes,
                "current_mb": round(storage_mb, 1),
                "limit_mb": max_storage_gb * 1024 if max_storage_gb != -1 else "unlimited",
                "percentage": (storage_gb / max_storage_gb) * 100 if max_storage_gb > 0 else 0.0
            },
            "ai_queries": {
                "current": ai_queries,
                "limit": "unlimited",
                "percentage": 0.0
            },
            "embeddings": {
                "total_generated": embeddings_count
            },
            "limits": {
                "max_document_size_mb": max_doc_size_mb,
                "max_users": max_users if max_users != -1 else "unlimited"
            }
        }

    async def get_plan_limits(self, company_id: UUID) -> Optional[Dict]:
        """
        Get the plan limits for a company.

        Returns:
            Dictionary with all plan limit details
        """
        query = text("""
            SELECT
                pl.plan_tier,
                pl.max_documents,
                pl.max_storage_gb,
                pl.max_document_size_mb,
                pl.max_users
            FROM bc_legal_ds.companies c
            JOIN bc_legal_ds.plan_limits pl ON pl.plan_tier = c.plan_tier
            WHERE c.id = :company_id
        """)

        result = await self.db.execute(query, {"company_id": str(company_id)})
        row = result.first()

        if not row:
            return None

        return {
            "plan_tier": row[0],
            "max_documents": row[1],
            "max_storage_gb": row[2],
            "max_document_size_mb": row[3],
            "max_users": row[4]
        }
