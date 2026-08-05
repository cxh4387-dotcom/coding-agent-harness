# SPEC.md — Coding Agent Harness

> AI4SE 期末项目 · A · Coding Agent Harness
> 技术栈：Python 3.12 + FastAPI + WebSocket | LLM：OpenAI 兼容 API | 分发：Docker

---

## 1. 问题陈述

### 要解决什么问题？

当 LLM 能完成大部分"思考"时，工程师的价值落在 harness 这层工程——治理、反馈、上下文、安全、分发。本项目构建一个 **Coding Agent Harness**：一个自己编码实现的 agent 内核，能读写代码、执行命令、运行测试，并在危险动作执行前拦截以等待人工审批。

核心等式：**Agent = LLM + Harness**。LLM 只负责"决定下一步做什么"；harness 负责组织上下文、调用 LLM、解析动作、分发执行、治理护栏、反馈回灌、停机判断。

### 目标用户是谁？

- **AI4SE 课程学生**：学习 agent harness 的工程结构，理解治理与反馈机制
- **开发者**：需要一个可控、可观测、安全的 coding agent，而非黑盒
- **研究者**：需要一个可注入 mock LLM 的实验平台，用于确定性测试 agent 行为

### 为什么值得做？

现有 coding agent（Cursor、Copilot CLI 等）的治理逻辑是黑盒。本项目将治理护栏、反馈闭环、HITL 状态机等机制落实为**可独立测试的代码**，而非提示词，使 agent 行为可预测、可审计。

---

## 2. 用户故事（INVEST）

### US-1：提交编码任务
**作为**开发者，**我想**通过 WebUI 提交一个编码任务（如"写一个冒泡排序并测试"），**以便**让 agent 自主完成编码和测试。
- Independent：不依赖其他故事
- Negotiable：任务格式可调整
- Valuable：核心功能入口
- Estimable：明确的前后端交互
- Small：一个 API + 一个前端组件
- Testable：提交后能看到任务状态变化

### US-2：实时观察 agent 动作
**作为**开发者，**我想**通过 WebSocket 实时看到 agent 的每一步动作（读文件、写文件、执行命令），**以便**了解 agent 的工作过程。
- Independent：依赖 US-1 的任务提交
- Negotiable：展示格式可调整
- Valuable：可观测性是 harness 的核心价值
- Estimable：WebSocket 推送 + 前端渲染
- Small：一个 WebSocket 连接 + 消息渲染
- Testable：能收到 action 类型的 WebSocket 消息

### US-3：审批危险动作（HITL）
**作为**开发者，**我想**当 agent 试图执行危险动作（如 `rm -rf`）时收到审批请求，并能批准或拒绝，**以便**保持对 agent 的控制。
- Independent：依赖 US-2 的动作流
- Negotiable：审批 UI 可调整
- Valuable：治理是本项目的重点维度
- Estimable：HITL 状态机 + 审批 API + 前端弹窗
- Small：一个状态机 + 两个 API 端点
- Testable：mock LLM 触发危险动作 → 收到 hitl_request → 批准/拒绝 → agent 继续/跳过

### US-4：安全配置 API Key
**作为**开发者，**我想**通过 WebUI 安全地录入、查看状态、更新和清除 API Key，**以便**不将 key 硬编码或提交到 git。
- Independent：不依赖其他故事
- Negotiable：存储方式可调整
- Valuable：凭据安全是硬性要求
- Estimable：加密存储 + CRUD API
- Small：一个 CredentialManager + 三个 API 端点
- Testable：录入后状态为"已设置"，清除后为"未设置"，查看时不回显明文

### US-5：查看测试反馈
**作为**开发者，**我想**看到 agent 运行测试的结果（通过/失败计数、失败详情），**以便**了解 agent 是否在自我修正。
- Independent：依赖 US-1 的任务提交
- Negotiable：展示格式可调整
- Valuable：反馈闭环是 harness 的核心机制
- Estimable：FeedbackValidator + WebSocket 推送
- Small：一个校验器 + 消息渲染
- Testable：mock LLM 写错误代码 → 测试失败 → 反馈回灌 → mock LLM 修正 → 测试通过

---

## 3. 功能规约

### 3.1 模块：Agent 主循环（`harness/agent_loop.py`）

| 项 | 描述 |
|---|---|
| 输入 | 任务字符串（用户指令） |
| 行为 | 组织上下文 → 调用 LLM → 解析动作 → 护栏检查 → 分发执行 → 反馈校验 → 回灌 → 停机判断 |
| 输出 | `AgentResult`（执行历史、最终状态、被拦截动作列表） |
| 边界 | 最大迭代次数由配置限制（默认 50） |
| 错误处理 | LLM 调用失败 → 重试 3 次后停止；工具执行失败 → 记录错误并回灌 |

### 3.2 模块：LLM 抽象层（`harness/llm/`）

| 项 | 描述 |
|---|---|
| 输入 | `ConversationContext`（系统提示 + 记忆 + 历史 + 任务） |
| 行为 | 调用 LLM 单次补全，返回结构化响应（文本 + tool_calls） |
| 输出 | `LLMResponse`（content, tool_calls, finish_reason） |
| 边界 | 超时 60s；token 上限由配置控制 |
| 错误处理 | 网络错误重试 3 次；API key 无效 → 立即停止 |
| Mock | `MockLLM` 按预设脚本返回响应，用于确定性单测 |

### 3.3 模块：工具分发器（`harness/tools/`）

| 工具 | 输入 | 行为 | 输出 | 边界 |
|---|---|---|---|---|
| `read_file` | path | 读取文件内容 | `ToolResult(content)` | 沙箱内路径 |
| `write_file` | path, content | 写入文件 | `ToolResult(success)` | 沙箱内路径，大小限制 |
| `run_shell` | command | 执行 shell 命令 | `ToolResult(stdout, stderr, exit_code)` | 命令围栏，超时 30s |
| `run_tests` | test_path | 运行 pytest | `ToolResult(stdout, exit_code, report)` | 沙箱内路径 |

### 3.4 模块：治理/护栏（`harness/guardrail/`）— 重点维度

#### 3.4.1 危险动作检测器（`danger_detector.py`）

| 项 | 描述 |
|---|---|
| 输入 | `Action`（tool, args, raw） |
| 行为 | 遍历规则列表，匹配则返回拦截决策 |
| 输出 | `GuardrailDecision`（action, rule, decision: allow/block/hitl/warn） |
| 规则 | `rm -rf`→block, `git push --force`→hitl, 写 .env→hitl, 路径逃逸→block 等 |
| 错误处理 | 未知工具 → warn |
| 可测试性 | `DangerDetector.check(Action("run_shell", {"cmd": "rm -rf /"}))` → block，无需 LLM |

#### 3.4.2 HITL 状态机（`hitl_state_machine.py`）

| 项 | 描述 |
|---|---|
| 输入 | 危险动作 + 审批请求 |
| 行为 | 状态转换：Running → AwaitingApproval → Approved/Denied → Running |
| 输出 | 状态变更通知（通过 WebSocket 推送） |
| 超时 | 默认 120s 无响应 → Stopped |
| 可测试性 | 状态转换可单测，无需 LLM |

#### 3.4.3 沙箱（`sandbox.py`）

| 项 | 描述 |
|---|---|
| 输入 | 文件路径 / shell 命令 |
| 行为 | 验证路径在 workdir 内；检测命令逃逸 |
| 输出 | `bool`（允许/拒绝） |
| 可测试性 | `Sandbox.validate_path(Path("/etc/passwd"))` → False，无需 LLM |

#### 3.4.4 范围围栏（`scope_fence.py`）

| 项 | 描述 |
|---|---|
| 输入 | Action + 当前迭代次数 |
| 行为 | 检查工具白名单、迭代上限、文件大小、禁止模式 |
| 输出 | `FenceResult`（allowed, reason） |
| 配置 | YAML 声明式规则 |
| 可测试性 | `ScopeFence.enforce(action, 51)` → 拒绝（超迭代上限），无需 LLM |

### 3.5 模块：反馈校验器（`harness/feedback.py`）

| 项 | 描述 |
|---|---|
| 输入 | Action + ToolResult |
| 行为 | 运行测试 → 解析结果 → 分类失败 → 生成反馈 |
| 输出 | `Feedback`（passed, failed, failures, signal: pass/fail） |
| 失败分类 | 断言失败 / 导入错误 / 超时 / 语法错误 |
| 可测试性 | 解析 pytest 输出 → 分类，无需 LLM |

### 3.6 模块：记忆存储（`harness/memory.py`）

| 项 | 描述 |
|---|---|
| 输入 | 任务字符串 |
| 行为 | 检索相关记忆 → 组装上下文 |
| 输出 | `ConversationContext` |
| 持久化 | JSON 文件存储 |
| 检索 | 关键词匹配（自实现，不用框架 memory） |
| 可测试性 | 写入记忆 → 检索 → 断言匹配，无需 LLM |

### 3.7 模块：配置存储（`harness/config.py`）

| 项 | 描述 |
|---|---|
| 输入 | YAML 配置文件路径 |
| 行为 | 加载声明式规则 |
| 输出 | `HarnessConfig` |
| 配置项 | LLM 配置、scope 规则、guardrail 规则、sandbox 路径、memory 路径 |

### 3.8 模块：凭据管理（`harness/credentials.py`）

| 项 | 描述 |
|---|---|
| 输入 | API Key（隐藏输入） |
| 行为 | 加密存储（Fernet 对称加密，主密码派生自机器特征） |
| 输出 | 存储状态（已设置/未设置），不回显明文 |
| 操作 | 录入 / 查看（状态）/ 更新 / 清除 |
| 可测试性 | 存储 → 读取 → 断言匹配，无需 LLM |

### 3.9 模块：WebUI（`web/`）

| 端点 | 方法 | 行为 |
|---|---|---|
| `/api/tasks` | POST | 提交任务 |
| `/api/tasks/{id}` | GET | 查询状态 |
| `/api/tasks/{id}/approve` | POST | HITL 批准 |
| `/api/tasks/{id}/deny` | POST | HITL 拒绝 |
| `/api/config` | GET/PUT | 读取/更新配置 |
| `/api/credentials` | POST/DELETE | 录入/清除 key |
| `/api/credentials/status` | GET | 查看 key 状态 |
| `/ws/tasks/{id}` | WS | 实时动作流 |

---

## 4. 非功能性需求

### 4.1 性能
- Agent 循环单次迭代延迟 < 5s（含 LLM 调用）
- WebSocket 消息推送延迟 < 100ms
- 工具执行超时：shell 30s，测试 120s

### 4.2 安全（含凭据威胁模型）

**威胁模型**：

| 威胁 | 对策 |
|---|---|
| API Key 硬编码到源码 | 代码中无明文 key，从加密 vault 读取 |
| API Key 提交到 git | `.gitignore` 排除 vault 文件和 .env |
| API Key 写入日志 | 日志脱敏：`sk-xxx` → `sk-***` |
| Agent 执行危险命令 | DangerDetector 代码拦截 + HITL 审批 |
| Agent 写入系统文件 | Sandbox 路径围栏 |
| Agent 无限循环 | ScopeFence 迭代上限 |
| .env 明文风险 | 标注风险，提供加密 vault 作为首选 |

### 4.3 可用性
- WebUI 响应式布局，支持窄屏
- 首次运行引导录入 API Key
- 配置错误时给出明确错误信息

### 4.4 可观测性
- WebSocket 实时推送 agent 每一步动作
- AGENT_LOG.md 记录关键节点
- 测试结果面板显示通过/失败计数

---

## 5. 系统架构

```
┌─────────────────────────────────────────────────────────┐
│                    Docker Container                      │
│  ┌───────────────────────────────────────────────────┐  │
│  │              WebUI (HTML/JS + FastAPI)             │  │
│  │   WebSocket ←→ Agent Runner    REST API (config)  │  │
│  └────────────────┬──────────────────────────────────┘  │
│                   │ (thin wrapper, no logic)             │
│  ┌────────────────▼──────────────────────────────────┐  │
│  │              Harness Core (pure Python)            │  │
│  │                                                     │  │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────────────┐ │  │
│  │  │AgentLoop │─→│  Tools   │  │ GuardrailEngine  │ │  │
│  │  │ (主循环)  │  │Dispatcher│  │  (重点维度⭐)     │ │  │
│  │  └────┬─────┘  └──────────┘  └──────────────────┘ │  │
│  │       │           ┌──────────┐  ┌──────────────────┐ │  │
│  │       └──────────→│Feedback  │  │  HITL StateMachine│ │  │
│  │                   │Validator │  │  (暂停/审批/恢复) │ │  │
│  │  ┌──────────┐     └──────────┘  └──────────────────┘ │  │
│  │  │   LLM    │     ┌──────────┐  ┌──────────────────┐ │  │
│  │  │Abstraction│   │  Memory  │  │   ConfigStore    │ │  │
│  │  │(mockable)│    │  Store   │  │  (rules+creds)   │ │  │
│  │  └──────────┘     └──────────┘  └──────────────────┘ │  │
│  └─────────────────────────────────────────────────────┘  │
│                                                           │
│  ┌─────────┐  ┌──────────┐  ┌────────────────────────┐  │
│  │ Sandbox │  │Test Runner│  │ CredentialManager      │  │
│  │(workdir)│  │(pytest)  │  │ (.env + encrypted vault)│  │
│  └─────────┘  └──────────┘  └────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

**数据流**：
1. 用户通过 WebUI 提交任务 → POST /api/tasks
2. AgentLoop 启动：MemoryStore.build_context(task) → LLM.complete(context)
3. 解析 LLM 响应中的 tool_calls → 生成 Action 列表
4. 每个 Action → GuardrailEngine.check(action)
   - block → 记录并跳过
   - hitl → HITLStateMachine.request_approval() → WebSocket 推送 → 等待用户
   - allow → 继续
5. ScopeFence.enforce(action, iteration) → 检查范围
6. Sandbox.validate_path/command → 检查边界
7. ToolDispatcher.dispatch(action) → 执行
8. FeedbackValidator.validate(action, result) → 校验
9. 结果回灌到 context → 循环或停机

**外部依赖**：
- LLM 供应商：OpenAI 兼容 API（NJUSE Hub: glm-5.2/deepseek/kimi 等）
- Python 包：fastapi, uvicorn, httpx, cryptography, pyyaml, pytest

---

## 6. 数据模型

### 6.1 核心实体

```python
@dataclass
class Action:
    tool: str           # "read_file" | "write_file" | "run_shell" | "run_tests"
    args: dict          # 工具参数
    raw: str             # 原始 LLM 输出（用于护栏分析）

@dataclass
class ToolResult:
    success: bool
    stdout: str = ""
    stderr: str = ""
    exit_code: int = 0
    content: str = ""   # 文件内容（read_file）

@dataclass
class GuardrailDecision:
    action: Action
    rule: DangerRule | None
    decision: str       # "allow" | "block" | "hitl" | "warn"

@dataclass
class Feedback:
    passed: int
    failed: int
    failures: list[FailureClass]
    signal: str         # "pass" | "fail"

@dataclass
class FailureClass:
    type: str           # "assertion" | "import" | "timeout" | "syntax"
    message: str
    location: str       # 文件:行号

@dataclass
class LLMResponse:
    content: str
    tool_calls: list[ToolCall]
    finish_reason: str  # "stop" | "tool_calls" | "length"

@dataclass
class ToolCall:
    name: str
    arguments: dict

@dataclass
class AgentResult:
    actions: list[Action]
    results: list[ToolResult]
    feedbacks: list[Feedback]
    blocked_actions: list[GuardrailDecision]
    iterations: int
    final_feedback: Feedback | None
```

### 6.2 记忆实体

```python
@dataclass
class Memory:
    id: str
    task: str
    decision: str
    rationale: str
    timestamp: str
    tags: list[str]
```

### 6.3 配置实体

```python
@dataclass
class HarnessConfig:
    llm: LLMConfig          # base_url, model, temperature, max_tokens
    scope: ScopeConfig      # allowed_tools, max_iterations, max_file_size, forbidden_patterns
    guardrail: GuardrailConfig  # custom_rules
    sandbox: SandboxConfig  # workdir, allowed_paths
    memory: MemoryConfig    # store_path
```

---

## 7. 凭据与分发设计

### 7.1 凭据存储方案

**首选：加密 vault**
- 使用 `cryptography.fernet.Fernet` 对称加密
- 主密码派生自机器特征（MAC 地址 + 用户名 → PBKDF2 → 256bit key）
- vault 文件存储在 `~/.harness/vault.enc`（容器内为 volume）
- key 不以明文存在于磁盘

**备选：环境变量**
- 通过 `.env` 文件加载（`python-dotenv`）
- 标注明文风险：`.env` 为明文、进程环境可见
- `.gitignore` 排除 `.env`

**录入/更新/清除流程**：
1. 首次运行 → WebUI 提示录入 → `getpass` 隐藏输入 → 加密存储
2. 更新 → POST /api/credentials → 旧 key 解密验证 → 新 key 加密存储
3. 清除 → DELETE /api/credentials → vault 文件删除
4. 查看状态 → GET /api/credentials/status → 返回 "已设置"/"未设置"（不回显明文）

### 7.2 分发设计

**形态**：Docker 镜像

**Dockerfile**：
```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "harness.web.app:app", "--host", "0.0.0.0", "--port", "8000"]
```

**获取与运行**：
```bash
docker build -t coding-agent-harness .
docker run -p 8000:8000 -v $(pwd)/workspace:/app/workspace coding-agent-harness
```

**key 在目标机的安全配置**：
- 方式 1：WebUI 首次运行引导录入（加密存储在容器 volume）
- 方式 2：环境变量 `HARNESS_API_KEY`（标注明文风险）
- 方式 3：挂载 vault 文件 `-v ./vault:/root/.harness/vault.enc`

**已知限制**：
- 平台：Linux x86_64（Docker 跨平台）
- 依赖：Docker 20+
- LLM：需要 OpenAI 兼容 API 的 base_url 和 key

---

## 8. 技术选型与理由

| 选型 | 理由 |
|---|---|
| **Python 3.12** | 生态丰富、测试框架成熟（pytest）、LLM SDK 齐全、适合快速实现 harness 内核 |
| **FastAPI** | 原生 async 适合 agent 长循环；自动 OpenAPI 文档；WebSocket 内置支持 |
| **WebSocket** | 双向通信，适合 HITL 审批（服务器推送请求，客户端推送批准/拒绝） |
| **原生 HTML/JS** | 无框架依赖，减少构建链复杂度；harness 核心命题不在前端 |
| **OpenAI 兼容 API** | 生态最广；NJUSE Hub 已提供 glm-5.2/deepseek/kimi 等模型 |
| **pytest** | 成熟的确定性测试框架；JUnit XML 供 CI 解析 |
| **cryptography (Fernet)** | 对称加密，标准库级别可靠性 |
| **Docker** | 单条命令构建运行；WebUI 部署最自然；CI 可自动构建 |
| **YAML 配置** | 声明式规则约束 agent 行为，人类可读 |

---

## 9. 领域与机制设计（§A.5 专项要求）

### 9.1 Coding 领域的反馈信号

| 信号 | 来源 | 客观性 | 回灌方式 |
|---|---|---|---|
| 测试通过/失败 | pytest 运行结果 | 完全客观（exit code + 断言） | 解析 JUnit XML → 分类失败 → 回灌 |
| 语法错误 | Python `compile()` / `py_compile` | 完全客观 | 错误信息回灌 |
| Lint 结果 | `ruff check` | 客观（规则可配置） | 违规列表回灌 |
| 类型检查 | `mypy` | 客观 | 类型错误列表回灌 |

**重点**：这些信号全部由代码机制产生，不依赖 LLM"自行检查"。

### 9.2 Coding 领域的危险动作

| 危险动作 | 严重性 | 拦截方式 |
|---|---|---|
| `rm -rf` / `del /s` | block | DangerDetector 规则匹配 |
| `git push --force` | hitl | DangerDetector 规则匹配 → HITL |
| 写入 `.env` / `*.key` / `*.pem` | hitl | DangerDetector 规则匹配 → HITL |
| 写入 sandbox 外路径 | block | Sandbox.validate_path |
| `curl` / `wget` 外发 | hitl | DangerDetector 规则匹配 → HITL |
| `npm publish` / `pip install` 全局 | hitl | DangerDetector 规则匹配 → HITL |
| 超过迭代上限 | block | ScopeFence.enforce |

### 9.3 所需工具

| 工具 | 用途 |
|---|---|
| `read_file` | 读取代码文件 |
| `write_file` | 写入/修改代码文件 |
| `run_shell` | 执行 shell 命令（构建、安装依赖等） |
| `run_tests` | 运行 pytest，获取测试反馈 |

### 9.4 记忆需求

| 记忆类型 | 内容 | 检索方式 |
|---|---|---|
| 项目约定 | 编码规范、测试命令、构建命令 | 关键词匹配 |
| 历史决策 | agent 之前的决策和结果 | 任务相关检索 |
| 代码库知识 | 文件结构、模块依赖 | 关键词匹配 |

### 9.5 重点维度：治理/护栏

**选择理由**：
1. 治理天然由代码构成——护栏是确定性函数，不依赖 LLM 智能
2. 最契合 §A.4 的"机制必须是代码"要求
3. HITL 状态机有清晰的状态转换，可单测性强
4. 治理是 agent 安全的核心——没有治理，agent 不可控

**深入实现的 4 个子机制**：
1. **DangerDetector**：规则引擎，每条规则是可独立测试的函数
2. **HITLStateMachine**：状态机，状态转换可单测
3. **Sandbox**：路径围栏 + 命令围栏，可单测
4. **ScopeFence**：工具白名单 + 迭代上限 + 禁止模式，可单测

**机制如何编码实现（呼应 §A.4）**：
- (A) 主循环自己实现，不寄生于框架 ✓
- (B) 护栏是 `guardrail(action)` 函数，不是提示词 ✓
- (C) 移除 LLM 后，`DangerDetector.check(Action("rm -rf /"))` 仍返回 block ✓

---

## 10. 验收标准

| 功能 | 完成的客观判定标准 |
|---|---|
| Agent 主循环 | mock LLM 驱动，能完成"写文件→测试→修正→通过"的完整循环 |
| LLM 抽象层 | MockLLM 和 OpenAICompatibleLLM 实现同一接口；mock 可驱动全部测试 |
| 工具分发 | 4 个工具（read/write/shell/tests）均可执行并返回 ToolResult |
| 危险动作检测 | `rm -rf /` → block；`git push --force` → hitl；安全命令 → allow |
| HITL 状态机 | 状态转换：Running→AwaitingApproval→Approved→Running 可单测 |
| 沙箱 | `/etc/passwd` → 拒绝；workdir 内 → 允许 |
| 范围围栏 | 超迭代上限 → 拒绝；禁止模式 → 拒绝 |
| 反馈校验 | pytest 输出解析正确；失败分类正确 |
| 记忆存储 | 写入 → 检索 → 匹配 |
| 凭据管理 | 录入 → 状态为"已设置"；清除 → "未设置"；查看不回显明文 |
| WebUI | 能提交任务、实时看到动作流、审批 HITL、查看测试反馈 |
| 机制演示① | mock LLM 触发 `rm -rf` → 被护栏拦截，确定性可复现 |
| 机制演示② | mock LLM 写错误代码 → 测试失败 → 反馈回灌 → 修正 → 通过 |
| 机制演示③ | mock LLM 写 sandbox 外路径 → 被围栏拦截 |
| Docker | `docker build` + `docker run` 可启动 WebUI |
| CI | `.gitlab-ci.yml` 含 `unit-test` job，push 后自动运行 |
| 测试 | `make test` 一键运行，全部通过 |

---

## 11. 风险与未决问题

| 风险 | 影响 | 缓解 |
|---|---|---|
| LLM 不遵循 tool_calls 格式 | 动作解析失败 | 解析容错 + 重试提示 |
| Agent 无限循环 | 资源耗尽 | ScopeFence 迭代上限（默认 50） |
| WebSocket 断连 | HITL 审批丢失 | 重连机制 + 状态恢复 |
| 加密 vault 主密码可被推导 | key 泄露 | 主密码派生自机器特征，需物理访问 |
| Docker 容器内路径权限 | 文件操作失败 | 容器以非 root 用户运行 |
| 测试解析不兼容非 pytest 框架 | 反馈信号缺失 | 首版只支持 pytest，标注限制 |
| HITL 超时无响应 | agent 卡死 | 默认 120s 超时 → Stopped |
| 真实 LLM 费用 | 测试成本 | 全部单测用 mock LLM，无网络 |
