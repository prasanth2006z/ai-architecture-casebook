"""Run: pip install sqlglot pytest && pytest -q"""
from sql_guard import check_sql

CATALOG = {
    "claims": {"claim_id": "int", "status": "text",
               "created_at": "timestamp"},
    "claim_items": {"item_id": "int", "claim_id": "int",
                    "claimed_amount": "numeric",
                    "approved_amount": "numeric"},
}


def ok(sql):
    return check_sql(sql, CATALOG) == []


def test_valid_select():
    assert ok("SELECT c.claim_id FROM claims c "
              "WHERE c.status = 'UNDER_REVIEW'")


def test_valid_join():
    assert ok("SELECT c.claim_id, SUM(i.approved_amount) "
              "FROM claims c JOIN claim_items i "
              "ON i.claim_id = c.claim_id GROUP BY c.claim_id")


def test_valid_cte():
    assert ok("WITH s AS (SELECT claim_id FROM claims) "
              "SELECT claim_id FROM s")


def test_renamed_column_rejected():
    assert not ok("SELECT i.amount FROM claim_items i")


def test_unknown_table_rejected():
    assert not ok("SELECT * FROM claim_lines")


def test_write_rejected():
    assert not ok("UPDATE claims SET status = 'PAID'")


def test_multiple_statements_rejected():
    assert not ok("SELECT 1; DELETE FROM claims")


def test_write_inside_cte_rejected():
    assert not ok("WITH d AS (DELETE FROM claims RETURNING claim_id) "
                  "SELECT * FROM d")


def test_unparseable_rejected():
    assert not ok("SELEC claim_id FROM")
