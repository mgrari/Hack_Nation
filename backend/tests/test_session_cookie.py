def test_db_tables_created(client):
    from db import Base

    table_names = set(Base.metadata.tables.keys())
    assert {"sessions", "consent_records", "documents", "fields", "audit_log"} <= table_names
