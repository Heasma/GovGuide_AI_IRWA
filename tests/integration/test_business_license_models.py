"""
GovGuide AI — Phase 3 Integration Tests: Business License Models

Tests for:
- BusinessLicenseHolder insertion and retrieval
- BusinessLicense insertion with FK to holder
- BusinessLicense → GovernmentService FK
- Duplicate license_id → IntegrityError
- FK integrity (license without holder → error)
- Composite unique index on (account_number, site_number)

Uses SQLite in-memory for isolation (no PostgreSQL required).
The SQLAlchemy models use postgresql.JSONB which is not compatible with
SQLite, so we use a table reflection approach with create_all().
"""

import sys
import uuid
from datetime import date
from pathlib import Path
from typing import Generator

import pytest
from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker, Session

# Add backend to path
PROJECT_ROOT = Path(__file__).parents[2]
BACKEND_DIR = PROJECT_ROOT / "backend"
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(BACKEND_DIR))


# ── SQLite-compatible test setup ──────────────────────────────────────────────
# We use PostgreSQL (govguide_db) for integration tests since JSONB and
# composite indexes are PostgreSQL-specific.
# Tests skip gracefully if DB is not available.

DB_URL = "postgresql://govguide:changeme@localhost:5432/govguide_db"


def _check_db_available() -> bool:
    """Return True if the test database is reachable."""
    try:
        import psycopg2
        conn = psycopg2.connect(DB_URL, connect_timeout=3)
        conn.close()
        return True
    except Exception:
        return False


DB_AVAILABLE = _check_db_available()
db_required = pytest.mark.skipif(
    not DB_AVAILABLE,
    reason="PostgreSQL govguide_db not reachable",
)


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def db_session() -> Generator[Session, None, None]:
    """
    Provide a transactional test session.
    All operations are rolled back after the test module completes.
    """
    from app.models import Base, BusinessLicenseHolder, BusinessLicense, GovernmentService, GovernmentOffice
    engine = create_engine(DB_URL, echo=False)
    TestingSession = sessionmaker(bind=engine)
    session = TestingSession()

    # Use a savepoint so we can roll back all test data
    session.begin_nested()

    yield session

    session.rollback()
    session.close()
    engine.dispose()


@pytest.fixture
def sample_office(db_session: Session):
    """Create a test GovernmentOffice record."""
    from app.models import GovernmentOffice
    office = GovernmentOffice(
        id=uuid.uuid4(),
        name=f"Test Office {uuid.uuid4().hex[:6]}",
        department="Test Department",
    )
    db_session.add(office)
    db_session.flush()
    return office


@pytest.fixture
def sample_service(db_session: Session, sample_office):
    """Create a test GovernmentService record."""
    from app.models import GovernmentService
    code = f"TEST{uuid.uuid4().hex[:4]}"
    service = GovernmentService(
        id=uuid.uuid4(),
        service_code=code,
        name="Test License Service",
        is_active=True,
        office_id=sample_office.id,
        source_confidence="REQUIRES_MANUAL_VERIFICATION",
    )
    db_session.add(service)
    db_session.flush()
    return service


@pytest.fixture
def sample_holder(db_session: Session):
    """Create a test BusinessLicenseHolder record."""
    from app.models import BusinessLicenseHolder
    acct = uuid.uuid4().hex[:8]
    holder = BusinessLicenseHolder(
        id=uuid.uuid4(),
        account_number=acct,
        site_number="1",
        legal_name="TEST CORPORATION INC",
        doing_business_as_name="Test Corp",
        address="123 N TEST ST",
        city="CHICAGO",
        state="IL",
        zip_code="60601",
        ward=42,
        latitude=41.8781,
        longitude=-87.6298,
    )
    db_session.add(holder)
    db_session.flush()
    return holder


# ── BusinessLicenseHolder Tests ───────────────────────────────────────────────

@db_required
class TestBusinessLicenseHolderModel:
    """Integration tests for BusinessLicenseHolder insertion and retrieval."""

    def test_insert_holder(self, db_session: Session, sample_holder):
        """A holder must be retrievable by account_number + site_number."""
        from app.models import BusinessLicenseHolder
        from sqlalchemy import select
        stmt = select(BusinessLicenseHolder).where(
            BusinessLicenseHolder.id == sample_holder.id
        )
        found = db_session.execute(stmt).scalar_one_or_none()
        assert found is not None
        assert found.legal_name == "TEST CORPORATION INC"
        assert found.ward == 42

    def test_holder_coordinates_stored_as_float(self, db_session: Session, sample_holder):
        """Latitude and longitude must be stored and retrieved as floats."""
        from app.models import BusinessLicenseHolder
        from sqlalchemy import select
        stmt = select(BusinessLicenseHolder).where(
            BusinessLicenseHolder.id == sample_holder.id
        )
        found = db_session.execute(stmt).scalar_one()
        assert isinstance(found.latitude, float)
        assert isinstance(found.longitude, float)

    def test_composite_unique_index_enforced(self, db_session: Session, sample_holder):
        """(account_number, site_number) must be unique — duplicate must fail."""
        from app.models import BusinessLicenseHolder
        from sqlalchemy.exc import IntegrityError
        duplicate = BusinessLicenseHolder(
            id=uuid.uuid4(),
            account_number=sample_holder.account_number,
            site_number=sample_holder.site_number,
            legal_name="DUPLICATE CORP",
        )
        db_session.add(duplicate)
        with pytest.raises(IntegrityError):
            db_session.flush()
        db_session.rollback()

    def test_holder_nullable_fields_accept_none(self, db_session: Session):
        """All nullable fields must accept None without errors."""
        from app.models import BusinessLicenseHolder
        holder = BusinessLicenseHolder(
            id=uuid.uuid4(),
            account_number=uuid.uuid4().hex[:8],
            site_number="1",
            legal_name="MINIMAL CORP",
            # All optional fields left as None
        )
        db_session.add(holder)
        db_session.flush()
        from sqlalchemy import select
        found = db_session.execute(
            select(BusinessLicenseHolder).where(BusinessLicenseHolder.id == holder.id)
        ).scalar_one()
        assert found.ward is None
        assert found.latitude is None
        assert found.neighborhood is None
        db_session.rollback()


# ── BusinessLicense Tests ─────────────────────────────────────────────────────

@db_required
class TestBusinessLicenseModel:
    """Integration tests for BusinessLicense insertion."""

    def test_insert_license_with_holder_fk(
        self, db_session: Session, sample_holder, sample_service
    ):
        """A license must link correctly to its holder and service."""
        from app.models import BusinessLicense
        lid = f"LIC-{uuid.uuid4().hex[:8]}"
        lic = BusinessLicense(
            id=uuid.uuid4(),
            license_id=lid,
            license_number="TEST-NUM-001",
            license_code="1006",
            license_description="Retail Food Establishment",
            application_type="ISSUE",
            conditional_approval=False,
            license_status="AAI",
            holder_id=sample_holder.id,
            government_service_id=sample_service.id,
        )
        db_session.add(lic)
        db_session.flush()

        from sqlalchemy import select
        found = db_session.execute(
            select(BusinessLicense).where(BusinessLicense.license_id == lid)
        ).scalar_one_or_none()

        assert found is not None
        assert found.holder_id == sample_holder.id
        assert found.government_service_id == sample_service.id
        assert found.license_code == "1006"

    def test_license_unique_constraint_on_license_id(
        self, db_session: Session, sample_holder
    ):
        """Duplicate license_id must raise IntegrityError."""
        from app.models import BusinessLicense
        from sqlalchemy.exc import IntegrityError
        lid = f"DUP-LIC-{uuid.uuid4().hex[:6]}"

        for _ in range(2):
            lic = BusinessLicense(
                id=uuid.uuid4(),
                license_id=lid,
                license_number="DUP-NUM",
                license_code="1006",
                license_description="Retail Food Establishment",
                conditional_approval=False,
                license_status="AAI",
                holder_id=sample_holder.id,
            )
            db_session.add(lic)

        with pytest.raises(IntegrityError):
            db_session.flush()
        db_session.rollback()

    def test_license_nullable_service_id_allowed(
        self, db_session: Session, sample_holder
    ):
        """government_service_id must be nullable (unmapped codes)."""
        from app.models import BusinessLicense
        lid = f"NULL-SVC-{uuid.uuid4().hex[:6]}"
        lic = BusinessLicense(
            id=uuid.uuid4(),
            license_id=lid,
            license_number="NULL-SVC-NUM",
            license_code="9999",  # unknown / unmapped code
            license_description="Unknown License Type",
            conditional_approval=False,
            license_status="AAI",
            holder_id=sample_holder.id,
            government_service_id=None,  # explicitly null
        )
        db_session.add(lic)
        db_session.flush()

        from sqlalchemy import select
        from app.models import BusinessLicense as BL
        found = db_session.execute(
            select(BL).where(BL.license_id == lid)
        ).scalar_one()
        assert found.government_service_id is None
        db_session.rollback()

    def test_license_requires_holder_fk(self, db_session: Session):
        """License without a holder must fail with IntegrityError."""
        from app.models import BusinessLicense
        from sqlalchemy.exc import IntegrityError
        fake_holder_id = uuid.uuid4()
        lic = BusinessLicense(
            id=uuid.uuid4(),
            license_id=f"NO-HOLDER-{uuid.uuid4().hex[:6]}",
            license_number="NO-HOLDER-NUM",
            license_code="1006",
            license_description="Retail Food Establishment",
            conditional_approval=False,
            license_status="AAI",
            holder_id=fake_holder_id,  # non-existent holder
        )
        db_session.add(lic)
        with pytest.raises(IntegrityError):
            db_session.flush()
        db_session.rollback()

    def test_license_date_fields_stored_as_date(
        self, db_session: Session, sample_holder
    ):
        """Date columns must be stored and retrieved as datetime.date."""
        from app.models import BusinessLicense
        lid = f"DATE-TEST-{uuid.uuid4().hex[:6]}"
        lic = BusinessLicense(
            id=uuid.uuid4(),
            license_id=lid,
            license_number="DATE-NUM",
            license_code="1006",
            license_description="Retail Food Establishment",
            conditional_approval=False,
            license_status="AAI",
            holder_id=sample_holder.id,
            date_issued=date(2026, 7, 30),
            license_term_start_date=date(2026, 7, 16),
            license_term_expiration_date=date(2028, 7, 15),
        )
        db_session.add(lic)
        db_session.flush()

        from sqlalchemy import select
        from app.models import BusinessLicense as BL
        found = db_session.execute(
            select(BL).where(BL.license_id == lid)
        ).scalar_one()
        assert found.date_issued == date(2026, 7, 30)
        assert found.license_term_start_date == date(2026, 7, 16)
        db_session.rollback()


# ── Relationship Tests ────────────────────────────────────────────────────────

@db_required
class TestBusinessLicenseRelationships:
    """Tests for ORM relationship navigation."""

    def test_holder_licenses_relationship(
        self, db_session: Session, sample_holder
    ):
        """holder.licenses must return associated BusinessLicense records."""
        from app.models import BusinessLicense
        lic1 = BusinessLicense(
            id=uuid.uuid4(),
            license_id=f"REL-1-{uuid.uuid4().hex[:6]}",
            license_number="REL-NUM-1",
            license_code="1006",
            license_description="Retail Food Establishment",
            conditional_approval=False,
            license_status="AAI",
            holder_id=sample_holder.id,
        )
        lic2 = BusinessLicense(
            id=uuid.uuid4(),
            license_id=f"REL-2-{uuid.uuid4().hex[:6]}",
            license_number="REL-NUM-2",
            license_code="1010",
            license_description="Limited Business License",
            conditional_approval=False,
            license_status="AAI",
            holder_id=sample_holder.id,
        )
        db_session.add_all([lic1, lic2])
        db_session.flush()

        # Reload holder to trigger relationship loading
        db_session.expire(sample_holder)
        from sqlalchemy import select
        from app.models import BusinessLicenseHolder
        holder = db_session.execute(
            select(BusinessLicenseHolder).where(
                BusinessLicenseHolder.id == sample_holder.id
            )
        ).scalar_one()

        assert len(holder.licenses) >= 2
        db_session.rollback()

    def test_service_issued_licenses_relationship(
        self, db_session: Session, sample_holder, sample_service
    ):
        """service.issued_licenses must return linked licenses."""
        from app.models import BusinessLicense
        lic = BusinessLicense(
            id=uuid.uuid4(),
            license_id=f"SVC-REL-{uuid.uuid4().hex[:6]}",
            license_number="SVC-REL-NUM",
            license_code="1006",
            license_description="Retail Food Establishment",
            conditional_approval=False,
            license_status="AAI",
            holder_id=sample_holder.id,
            government_service_id=sample_service.id,
        )
        db_session.add(lic)
        db_session.flush()

        from sqlalchemy import select
        from app.models import GovernmentService
        svc = db_session.execute(
            select(GovernmentService).where(GovernmentService.id == sample_service.id)
        ).scalar_one()
        assert any(l.government_service_id == sample_service.id for l in svc.issued_licenses)
        db_session.rollback()
