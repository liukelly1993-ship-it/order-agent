# 本地 Docker + ngrok 部署

## 当前结构

- 前端：GitHub Pages 发布 `frontend/`
- 公网 API：`https://uprising-ladybug-curly.ngrok-free.dev`
- 本地 API：Docker 容器 `order-agent-api`，仅绑定 `127.0.0.1:8080`
- 数据服务：复用宿主机 MySQL、PostgreSQL、Redis 和 Milvus

## 启动

确保宿主机四个数据服务已启动，然后执行：

```bash
docker compose up -d --build
ngrok http 8080
```

检查状态：

```bash
docker compose ps
curl http://127.0.0.1:8080/healthz
curl https://uprising-ladybug-curly.ngrok-free.dev/healthz
```

查看日志和内存：

```bash
docker compose logs -f order-agent-api
docker stats --no-stream order-agent-api
```

## 停止

前台运行 ngrok 时按 `Ctrl+C` 停止隧道。停止 API 容器：

```bash
docker compose stop order-agent-api
```

## GitHub Pages

`.github/workflows/pages.yml` 会在 `master` 分支的 `frontend/` 发生变化后发布页面。首次使用前，需要在仓库 `Settings → Pages` 中将 Source 设置为 `GitHub Actions`。代码 push 由仓库所有者执行。

## 注意事项

- 电脑、Docker、宿主数据库和 ngrok 必须保持运行，公网功能才可用。
- `.env` 不会打进镜像，也不能提交到 Git。
- Docker 中使用 CPU 加载 BGE；不要把 `EMBEDDING_DEVICE` 改为 `mps`。
- 只对外开放 FastAPI，不要为数据库端口创建 ngrok 隧道。
- 分享公网地址前，应轮换源码历史中出现过的高德 MCP Key，并迁移到环境变量。
