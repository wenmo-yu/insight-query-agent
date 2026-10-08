"""Hybrid ranking helpers shared by metadata retrieval nodes."""

from collections.abc import Callable


def dynamic_top_k(query: str, minimum: int = 6, maximum: int = 20) -> int:
    """Broaden recall for multi-constraint questions while capping prompt noise."""

    constraints = sum(query.count(token) for token in ("按", "和", "、", "以及", "同比", "环比"))
    return min(maximum, minimum + constraints * 3 + len(query) // 24)


def hybrid_rank[T](query: str, items: list[T], text: Callable[[T], str], limit: int) -> list[T]:
    """Fuse dense candidates with a transparent lexical (sparse) overlap score."""

    terms = {term.lower() for term in query.split() if term} | {char for char in query.lower() if char.strip()}
    scored = []
    for position, item in enumerate(items):
        searchable = text(item).lower()
        sparse_score = sum(term in searchable for term in terms) / max(len(terms), 1)
        # Dense rank is retained as a small prior because Qdrant already ordered the list.
        score = sparse_score + 0.15 / (position + 1)
        scored.append((score, position, item))
    return [item for _, _, item in sorted(scored, key=lambda entry: (-entry[0], entry[1]))[:limit]]
