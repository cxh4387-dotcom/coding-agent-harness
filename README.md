# Coding Agent Harness

A self-coded Coding Agent Harness with governance guardrails as the focus dimension.

## 项目简介

Agent = LLM + Harness. 本项目实现 harness 内核：主循环、工具分发、治理护栏（重点）、反馈闭环、记忆、配置、凭据管理。所有机制为确定性代码，可用 MockLLM 单测。

## 安装

```bash
docker pull ghcr.io/<user>/coding-agent-harness:latest
# 或
git clone <repo-url>
pip install -r requirements.txt
```

## 运行

```bash
docker run -p 8000:8000 -v $(pwd)/workspace:/app/workspace coding-agent-harness
# 或
uvicorn web.app:app --host 0.0.0.0 --port 8000
```

## 分发命令

```bash
docker build -t coding-agent-harness .
docker push ghcr.io/<user>/coding-agent-harness:latest
```

## 目录结构

```
coding-agent-harness/
├── harness/          # Harness 内核（纯 Python）
│   ├── models.py     # 数据模型
│   ├── agent_loop.py # 主循环
│   ├── llm/          # LLM 抽象层
│   ├── tools/        # 工具
│   ├── guardrail/    # 治理（重点维度）
│   ├── feedback.py   # 反馈校验
│   ├── memory.py     # 记忆
│   ├── config.py     # 配置
│   └── credentials.py # 凭据
├── web/              # WebUI
├── tests/            # 测试
├── Dockerfile
├── requirements.txt
└── Makefile
```

## 安全边界说明

- API Key: 加密存储 (Fernet)，不硬编码、不提交 git、不写日志
- Sandbox: agent 文件操作限制在 workdir 内
- Guardrails: rm -rf → block, git push --force → HITL, etc.
- Scope Fence: 工具白名单 + 迭代上限 + 禁止模式

## key 在目标机的安全配置

1. WebUI 首次运行引导录入（加密存储）
2. 环境变量 HARNESS_API_KEY（明文风险）
3. 挂载 vault 文件

## 已知限制

- 平台: Linux x86_64 (Docker)
- 依赖: Docker 20+, Python 3.12+
- LLM: 需要 OpenAI 兼容 API
- 测试框架: 仅支持 pytest

## 部署架构与 CI/CD

### 部署架构

- 平台: Render (免费 Web Service 额度)
- 方式: Render 从 Git 仓库拉取，用 Dockerfile 构建，暴露 8000 端口
- 公网地址: `https://coding-agent-harness.onrender.com`（示例）
- 环境变量: 在 Render Dashboard 设置 `HARNESS_API_KEY`

### CI/CD

- CI 配置: `.gitlab-ci.yml`（NJU Git / GitLab）
- CI 流程:
  1. `unit-test` job: Python 3.12-slim 镜像，运行 `pytest tests/unit/`，产出 JUnit XML 报告
  2. `build-docker` job: Docker 镜像构建（仅 main 分支触发）
- 每次 push 自动运行测试，确保代码质量

### 第三方依赖

- [FastAPI](https://fastapi.tiangolo.com/) (MIT) — Web 框架
- [uvicorn](https://www.uvicorn.org/) (BSD-3-Clause) — ASGI 服务器
- [httpx](https://www.python-httpx.org/) (BSD-3-Clause) — HTTP 客户端
- [cryptography](https://cryptography.io/) (Apache-2.0/BSD-3-Clause) — 加密库
- [PyYAML](https://pyyaml.org/) (MIT) — YAML 解析
- [pytest](https://pytest.org/) (MIT) — 测试框架
