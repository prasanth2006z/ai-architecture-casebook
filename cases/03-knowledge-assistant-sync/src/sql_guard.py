import sqlglot
from sqlglot import exp
from sqlglot.errors import SqlglotError
from sqlglot.optimizer import qualify

WRITES = (exp.Insert, exp.Update,
          exp.Delete, exp.Drop,
          exp.Create, exp.Alter,
          exp.Merge, exp.Command)


def check_sql(sql, catalog):
    """catalog: {table: {column: type}}
    built from the live schema."""
    try:
        stmts = sqlglot.parse(
            sql, read="postgres")
    except SqlglotError as e:
        return [f"does not parse: {e}"]
    if len(stmts) != 1:
        return ["one statement only"]
    tree = stmts[0]

    # 1. Read-only: no writes anywhere.
    if not isinstance(tree, exp.Query):
        return ["SELECT only"]
    if any(tree.find_all(*WRITES)):
        return ["SELECT only"]

    # 2. Every table must exist now.
    ctes = {c.alias for c
            in tree.find_all(exp.CTE)}
    for t in tree.find_all(exp.Table):
        if (t.name not in catalog
                and t.name not in ctes):
            return [f"no table {t.name}"]

    # 3. Every column must exist now.
    try:
        qualify.qualify(
            tree, schema=catalog,
            dialect="postgres",
            validate_qualify_columns=True)
    except SqlglotError as e:
        return [f"unknown column: {e}"]
    return []
