"""Short-term conversation memory and structured analytics query state."""

from collections import deque
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from threading import RLock


@dataclass
class StructuredQueryState:
    """The reusable analytical intent for a single browser session."""

    metrics: list[str] = field(default_factory=list)
    time_range: str | None = None
    dimensions: list[str] = field(default_factory=list)
    filters: list[str] = field(default_factory=list)
    sort: str | None = None
    limit: int | None = None


@dataclass
class ConversationSnapshot:
    session_id: str
    turns: deque[str] = field(default_factory=lambda: deque(maxlen=6))
    query_state: StructuredQueryState = field(default_factory=StructuredQueryState)
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class ConversationStateStore:
    """Small in-process store; replace with Redis when deploying multiple replicas."""

    _metric_terms = ("GMV", "销售额", "成交额", "销量", "订单数", "客单价", "AOV")
    _dimension_terms = ("地区", "大区", "省份", "品类", "商品", "品牌", "会员等级", "客户")
    _filter_terms = ("华东", "华北", "华南", "华中", "北京", "上海", "黄金", "白银", "普通")

    def __init__(self) -> None:
        self._sessions: dict[str, ConversationSnapshot] = {}
        self._lock = RLock()

    def hydrate(self, session_id: str, query: str) -> dict:
        with self._lock:
            snapshot = self._sessions.setdefault(session_id, ConversationSnapshot(session_id))
            state = snapshot.query_state
            # An omitted concept in a follow-up inherits the previous analytical intent.
            self._merge_terms(state.metrics, query, self._metric_terms)
            self._merge_terms(state.dimensions, query, self._dimension_terms)
            self._merge_terms(state.filters, query, self._filter_terms)
            time_range = self._extract_time(query)
            if time_range:
                state.time_range = time_range
            if "前" in query and any(token in query for token in ("top", "TOP", "前")):
                digits = "".join(char for char in query if char.isdigit())
                state.limit = int(digits) if digits else state.limit
            if any(token in query for token in ("排序", "最高", "最低", "top", "TOP", "前")):
                state.sort = "descending"
            context = list(snapshot.turns)
            snapshot.turns.append(query)
            snapshot.updated_at = datetime.now(timezone.utc)
            return {"conversation_context": context, "structured_query": asdict(state)}

    def get(self, session_id: str) -> dict:
        with self._lock:
            snapshot = self._sessions.get(session_id)
            if not snapshot:
                return {"conversation_context": [], "structured_query": asdict(StructuredQueryState())}
            return {"conversation_context": list(snapshot.turns), "structured_query": asdict(snapshot.query_state)}

    @staticmethod
    def _merge_terms(target: list[str], query: str, candidates: tuple[str, ...]) -> None:
        for candidate in candidates:
            if candidate.lower() in query.lower() and candidate not in target:
                target.append(candidate)

    @staticmethod
    def _extract_time(query: str) -> str | None:
        markers = ("年", "月", "季度", "本月", "本季度", "今年", "去年", "最近")
        return query if any(marker in query for marker in markers) else None


conversation_state_store = ConversationStateStore()
