"""
GovGuide AI — Knowledge Chunk Generator

Loads the 56 GovernmentService records from PostgreSQL (or passed in-memory)
and generates the full corpus of searchable ServiceChunk objects.

Rules:
- Uses the 56 GovernmentService records as canonical knowledge.
- Does NOT chunk the 53,091 operational BusinessLicense records.
- Does not require database schema modifications.
"""

import logging
from typing import Any, Dict, List, Optional
import psycopg2
import psycopg2.extras

from app.config import get_settings
from app.retrieval.document_builder import build_service_document, CanonicalDocument
from app.retrieval.chunker import chunk_document, ServiceChunk

logger = logging.getLogger(__name__)


def fetch_services_from_db(db_url: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Fetch all GovernmentService records with joined GovernmentOffice details
    from PostgreSQL using psycopg2.
    """
    if db_url is None:
        db_url = get_settings().DATABASE_SYNC_URL

    conn = psycopg2.connect(db_url)
    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        query = """
            SELECT 
                s.id::text as id,
                s.service_code,
                s.name,
                s.description,
                s.category,
                s.is_active,
                s.source_url,
                s.license_term_years,
                s.fee_amount,
                s.fee_description,
                s.application_portal_url,
                s.eligibility_summary,
                s.required_documents,
                s.application_steps,
                s.inspection_required,
                s.renewal_required,
                s.renewal_period,
                s.legal_reference,
                s.source_confidence,
                o.id::text as office_id,
                o.name as office_name,
                o.department as office_department,
                o.street_address as office_street_address,
                o.city as office_city,
                o.state as office_state,
                o.zip_code as office_zip_code,
                o.phone as office_phone,
                o.email as office_email,
                o.business_hours as office_business_hours,
                o.website_url as office_website_url
            FROM government_services s
            LEFT JOIN government_offices o ON s.office_id = o.id
            WHERE s.is_active = TRUE
            ORDER BY s.service_code ASC;
        """
        cur.execute(query)
        rows = cur.fetchall()
        logger.info("Fetched %d active government services from database.", len(rows))
        return [dict(r) for r in rows]
    finally:
        conn.close()


def generate_chunks_from_db(db_url: Optional[str] = None) -> List[ServiceChunk]:
    """
    Generates all ServiceChunk objects directly from the database.
    """
    service_dicts = fetch_services_from_db(db_url)
    all_chunks: List[ServiceChunk] = []

    for item in service_dicts:
        # Build nested office dict
        office_dict = {
            "id": item.get("office_id"),
            "name": item.get("office_name"),
            "department": item.get("office_department"),
            "street_address": item.get("office_street_address"),
            "city": item.get("office_city"),
            "state": item.get("office_state"),
            "zip_code": item.get("office_zip_code"),
            "phone": item.get("office_phone"),
            "email": item.get("office_email"),
            "business_hours": item.get("office_business_hours"),
            "website_url": item.get("office_website_url"),
        }

        doc = build_service_document(service=item, office=office_dict)
        chunks = chunk_document(doc)
        all_chunks.extend(chunks)

    logger.info("Generated %d semantic chunks across %d services.", len(all_chunks), len(service_dicts))
    return all_chunks


def generate_chunks_from_services(services: List[Any]) -> List[ServiceChunk]:
    """
    Generate chunks from a list of ORM GovernmentService objects.
    """
    all_chunks: List[ServiceChunk] = []
    for svc in services:
        doc = build_service_document(svc)
        chunks = chunk_document(doc)
        all_chunks.extend(chunks)
    return all_chunks
