# Insight Query Agent

一个可持续对话的语义数据分析助手：将自然语言问题转换为只读 SQL，并在连续追问中保留指标、时间、维度和过滤条件。

本项目基于 [AI Agents From Zero](https://didilili.github.io/ai-agents-from-zero) 的工程思路改造与扩展，现以独立的 Insight Query Agent 维护。

## 核心能力

- **连续问数**：短期 Memory 和 `StructuredQueryState` 保存会话中的指标、时间、维度、筛选、排序与 Top-N。
- **状态可视化**：前端侧栏实时展示本轮分析状态，明确 AI 会继承的上下文。
- **Dense + Sparse Hybrid Retrieval**：Qdrant 语义候选结合词项重排，并根据问题复杂度动态调整 Top-K。
- **Elasticsearch Value Retrieval**：检索真实字段取值，降低筛选条件的值域幻觉。
- **Schema Dependency Expansion**：补齐指标依赖字段、时间字段和主外键 Join Key，再进入 SQL 生成闭环。
- **可观察执行**：FastAPI SSE 流式返回检索、生成、校验和执行进度。

## 架构

```text
React Console ── session_id ──> FastAPI / SSE
                                  │
                    Memory + StructuredQueryState
                                  │
Query expansion ─> Qdrant dense + sparse rerank ─┐
ES value retrieval ───────────────────────────────┼─> schema expansion ─> SQL loop
                                                   ┘
```

## 本地启动

需要 Python 3.14+、[uv](https://docs.astral.sh/uv/)、Node 22+、pnpm 10+ 和 Docker。

```bash
copy .env.example .env
docker compose -f docker/docker-compose.yaml up -d
uv sync
uv run python app/scripts/build_meta_knowledge.py
uv run fastapi dev main.py
```

在另一个终端启动前端：

```bash
pnpm --dir frontend install
pnpm --dir frontend dev
```

在 `.env` 配置 `LLM_API_KEY` 后访问 `http://localhost:5173`。公开部署前请用密钥管理服务替代本地数据库密码，并确保数仓账户只读。

## GitHub 质量门禁

```bash
uv run ruff check .
pnpm --dir frontend build
```

仓库包含 GitHub Actions 工作流，推送与 Pull Request 都会执行以上检查；`.env`、日志、虚拟环境和本地 embedding 模型均不会被提交。

## 扩展建议

本地的 `ConversationStateStore` 适用于单实例开发。生产多副本部署时，将其替换为带 TTL 的 Redis，同时保持 `session_id` API 契约即可。

## License

MIT，详见 [LICENSE](LICENSE)。
