from __future__ import annotations

from contextlib import contextmanager
from typing import Any

from neo4j import Driver, GraphDatabase
from neo4j.exceptions import Neo4jError, ServiceUnavailable

if __package__ in (None, ""):  # allow running as `python src/neo4j_client.py`
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src import config

_driver: Driver | None = None


def get_driver() -> Driver:
    global _driver
    if _driver is None:
        _driver = GraphDatabase.driver(
            config.NEO4J_URI,
            auth=(config.NEO4J_USER, config.NEO4J_PASSWORD),
        )
    return _driver


def ping() -> tuple[bool, str]:
    try:
        drv = get_driver()
        drv.verify_connectivity()
        with drv.session(database=config.NEO4J_DATABASE) as s:
            n = s.run("MATCH (n) RETURN count(n) AS n").single()["n"]
        return True, f"Neo4j conectado ({n} nós em '{config.NEO4J_DATABASE}')."
    except (ServiceUnavailable, Neo4jError, OSError, ValueError) as error:
        return False, f"Neo4j indisponível: {type(error).__name__}: {error}"


def run_query(cypher: str, **params: Any) -> list[dict]:
    """Execute a parameterized query and return the list of records (dicts)."""
    drv = get_driver()
    with drv.session(database=config.NEO4J_DATABASE) as s:
        return [r.data() for r in s.run(cypher, **params)]


def close() -> None:
    global _driver
    if _driver is not None:
        _driver.close()
        _driver = None


if __name__ == "__main__":
    ok, msg = ping()
    print(("OK  " if ok else "ERRO ") + msg)
