# SPEC_PROCESS.md — 规约与计划过程文档

> AI4SE 期末项目 · Coding Agent Harness
> 记录与 Superpowers (brainstorming + writing-plans) 协作生成 SPEC.md 与 PLAN.md 的全过程

---

## 1. Brainstorming 关键节点

### 1.1 智能体追问的好问题

在 brainstorming 阶段，智能体依次追问了以下关键问题，每个问题都促使设计向前推进：

| 轮次 | 智能体追问 | 为何是"好问题" | 对设计的影响 |
|------|-----------|---------------|-------------|
| Q1 | "你想用什么编程语言？" | 迫定了技术栈基座，影响所有后续设计 | 选择 Python，因生态丰富、pytest 成熟、LLM SDK 齐全 |
| Q2 | "你想让哪个维度作为主要贡献？" | §A.4-D 要求选一个维度深入，这是项目的 main contribution | 选择治理/护栏，因最契合"机制必须是代码"要求 |
| Q3 | "你想接入哪个 LLM 供应商？" | 决定 LLM 抽象层的真实实现 | 选择 OpenAI 兼容 API，与 NJUSE Hub 一致 |
| Q4 | "你想用哪种分发形态？" | §3.2 必做项，且影响 WebUI 部署架构 | 选择 Docker，最契合 WebUI 线上部署需求 |
| Q5 | "你选择哪个架构方案？" | 在 3 个方案中做权衡，锁定异步模型和前端策略 | 选择方案 A (FastAPI+WebSocket+原生JS) |

### 1.2 哪些追问让我修正了原设想

- **原设想**：最初考虑用 React 做前端（方案 C），认为组件化更好。
- **修正**：智能体在方案对比中指出"前端工作量大幅增加，偏离 harness 核心命题"。我采纳了方案 A（原生 HTML/JS），因为项目的核心价值在 harness 内核工程，不在前端。
- **原设想**：最初考虑多供应商可切换（LLM 抽象层支持多种供应商）。
- **修正**：智能体追问后意识到"更灵活但工作量更大"，选择只做 OpenAI 兼容 API + Mock，YAGNI。

---

## 2. 至少 3 轮关键迭代

### 迭代 1：架构方案选择

**对话节选**：
> 智能体提出 3 个方案：
> - 方案 A: FastAPI + WebSocket + 原生JS（推荐）
> - 方案 B: Flask + SSE + 线程
> - 方案 C: FastAPI + React
>
> 推荐理由：harness 内核 100% 纯 Python 可单测，FastAPI async 天然适合 agent 循环

**我的处理决策**：选择方案 A。理由：
1. harness 内核与 web 完全解耦——满足 §A.4-C 的硬标准
2. async 天然适合 agent 长循环 + HITL 暂停/恢复
3. 原生前端足够展示 agent 动作流和审批界面，不偏离核心命题

### 迭代 2：治理维度深入设计

**对话节选**：
> 智能体将治理/护栏拆分为 4 个子机制：
> 1. DangerDetector — 规则引擎
> 2. HITLStateMachine — 状态机
> 3. Sandbox — 路径围栏 + 命令围栏
> 4. ScopeFence — 工具白名单 + 迭代上限 + 禁止模式
>
> 每个子机制都附了"无需 LLM 即可单测"的代码示例

**我的处理决策**：全部采纳。4 个子机制各有清晰边界，可独立单测，且覆盖了治理的不同层面（检测、审批、边界、范围）。这使治理维度足够"深入"。

### 迭代 3：SPEC 审查与修复

**对话节选**：
> 用户要求"校对文档要求"——逐条对照两份需求文档审查 SPEC.md
>
> 智能体发现 10 个问题：
> 1. 未提及 Open Design（§3.6 条件要求）
> 2. 数据模型缺关系和约束（§4.2.6）
> 3. 工具表缺错误处理列（§4.2.3）
> 4. 主循环停机条件不明确
> 5. 云部署目标缺失（§4.11）
> 6. Docker 未推送到 registry（§3.2）
> 7. README 必含章节不明确（§五.4）
> 8. CI 配置矛盾（§4.8 vs §五.6）
> 9. 技术选型缺前端（Open Design）
> 10. 机制演示③对齐不明确

**我的处理决策**：全部修复。其中：
- Open Design：评估后豁免使用（前端为薄包装，§3.6 "纯 CLI / 纯后端项目可豁免"同此理）
- CI 矛盾：澄清 NJU Git (GitLab) 为主仓库 + GitHub 镜像备份
- 其余 8 项：直接补充

---

## 3. AI 建议的采纳与推翻

### 采纳的 AI 建议

| 建议 | 来源 | 采纳理由 |
|------|------|---------|
| 选择 Python 而非 TypeScript | 智能体推荐 | 生态、pytest、LLM SDK 齐全 |
| 选择治理/护栏作为重点维度 | 智能体推荐 | 最契合"机制必须是代码"要求，可单测性最强 |
| 方案 A (FastAPI+WebSocket) | 智能体推荐 | async 适合 agent 循环，内核与 web 解耦 |
| 治理拆为 4 个子机制 | 智能体提出 | 边界清晰，可独立单测 |
| MockLLM 按脚本返回响应 | 智能体设计 | 确定性测试，无需真实 LLM |
| 原生 HTML/JS 而非 React | 智能体推荐 | 不偏离 harness 核心命题 |
| YAGNI：不做多供应商 | 智能体建议 | 减少不必要的工作量 |

### 推翻或修正的 AI 建议

| 建议 | 推翻理由 |
|------|---------|
| 无（本次 brainstorming 中未出现需要推翻的建议） | 智能体的建议均合理且与文档要求一致 |

**说明**：本次 brainstorming 过程中，智能体的建议均经过文档要求校验，未出现需要推翻的情况。唯一的人工修正是在 SPEC 审查阶段，用户要求"校对文档要求"后发现的 10 个问题——这些问题是智能体在初次编写 SPEC 时遗漏的，说明 brainstorming 产出的 SPEC 仍需人工对照文档逐条审查。

---

## 4. 对 brainstorming 技能的反思

### 做得好的地方

1. **分节呈现设计**：brainstorming 技能将设计拆为 8 节，每节确认后再继续，避免了"一次性输出大量内容导致用户无法有效审查"的问题。
2. **一次只问一个问题**：遵循了技能的"one question at a time"原则，每个问题都聚焦于一个关键决策，不混淆多个维度。
3. **方案对比**：在架构选择时提供了 3 个方案及权衡分析，帮助用户做出知情决策而非被动接受。
4. **HARD-GATE 机制**：技能强制要求"在用户批准设计前不得写任何代码"，有效防止了跳过设计直接编码的冲动。

### 让我不满的地方

1. **未主动对照文档要求**：brainstorming 技能在产出 SPEC 时未自动对照需求文档逐条检查，导致遗漏了 Open Design、数据模型关系、错误处理等 10 个问题。这些问题是在用户要求"校对文档要求"后才发现的。如果技能能在 SPEC 写完后自动执行一次"spec self-review against requirements"，会更有价值。
2. **visual companion 未触发**：技能提到"just-in-time visual companion"，但在整个 brainstorming 过程中未出现真正需要可视化的问题（架构图用 ASCII 代替了），因此未触发。这可能是合理的，但也可能意味着技能对"何时需要可视化"的判断过于保守。
3. **冷启动验证未内建**：brainstorming 技能的 checklist 不包含 §4.5 的冷启动验证步骤。这是项目要求的重要环节，但技能本身没有覆盖。需要人工补充。

---

## 5. 冷启动验证（§4.5）

### 5.1 验证方法

- **agent 类型**：general subagent（与主开发 agent 不同，全新 session，无对话历史）
- **提供材料**：仅 SPEC.md + PLAN.md，不补充任何口头解释
- **指定 task**：Task 2（数据模型）+ Task 8（危险检测器）
- **指令**："遇到不确定之处即暂停询问，而非凭猜测继续"

### 5.2 subagent 在哪里暂停并提问

subagent 报告了 4 个不确定点（均未暂停，但记录了疑问）：

1. **Task 1 未完成但 Task 2/8 依赖它**：subagent 发现项目目录只有文档，没有 `harness/__init__.py` 等包结构。它判断这是硬性前置条件而非设计决策，自行创建了最小脚手架。
   - **暴露的 spec 缺陷**：PLAN.md 未显式标注 Task 1 是所有其他 task 的硬性前置依赖。
   - **修订**：在 PLAN.md Task 1 标题下添加前置依赖说明。

2. **Python 3.12 不可用**：环境只有 Python 3.13/3.11/3.14(msys2)。subagent 选用 3.13。
   - **暴露的 spec 缺陷**：SPEC.md 和 PLAN.md 指定 Python 3.12+，但未说明环境兼容性。
   - **修订**：无需修订 SPEC（3.13 满足 3.12+ 要求），但 PLAN.md 的 Makefile 应使用 `python -m pytest` 而非 `pytest`（后者依赖 PATH）。

3. **pytest 未预装**：subagent 自行安装了 pytest。
   - **暴露的 spec 缺陷**：PLAN.md 的 Makefile 假设 pytest 已在 PATH 中。
   - **修订**：PLAN.md Makefile 模板中 `pytest` → `python -m pytest`。

4. **`pip_install_global` 规则与 SPEC 矛盾**：SPEC §9.2 说"pip install 全局 → hitl"，但 PLAN Task 8 的实现匹配 `pip\s+install.*--user`——`--user` 是用户级安装，与"全局"相反。
   - **暴露的 spec 缺陷**：PLAN.md 代码 bug——规则名 `pip_install_global` 与匹配模式语义不一致。
   - **修订**：修复匹配模式为 `pip install` 不含 `--user`（即匹配全局安装），并添加 2 个测试覆盖。

### 5.3 subagent 做出的与原意不一致的解读

**无不一致解读**。subagent 严格照搬 PLAN.md 提供的逐字精确代码，未做任何设计偏离。唯一观察到的是 `pip_install_global` 语义问题——subagent 正确识别了这是 bug 但选择"严格照搬 PLAN 而非自行修正"（符合"遇到不确定即暂停询问"的指令）。

### 5.4 产出与预期差距

- **预期**：subagent 实现 Task 2 和 Task 8，测试通过
- **实际**：subagent 实现了 Task 2（10 测试）和 Task 8（9 测试），全部通过，额外创建了最小脚手架
- **差距**：subagent 额外创建了脚手架（Task 1 的部分内容），因为 PLAN 未显式标注 Task 1 为前置依赖
- **总评**：PLAN.md 的代码精确度足够让陌生 agent 无需猜测即可实现，但执行顺序和前置依赖需要更明确

### 5.5 据此对 SPEC / PLAN 的修订

| 修订项 | 修订前 | 修订后 | Commit |
|--------|--------|--------|--------|
| Task 1 前置依赖 | 无说明 | 添加"Task 1 是所有其他 task 的硬性前置" | `c93641a` |
| Makefile pytest 命令 | `pytest tests/` | `python -m pytest tests/` | `c93641a` |
| pip_install_global 规则 | 匹配 `pip\s+install.*--user`（用户级，与 SPEC 矛盾） | 匹配 `pip install` 不含 `--user`（全局安装，与 SPEC 一致） | `c93641a` |
| pip_install_global 测试 | 无测试覆盖 | 添加 2 个测试（全局→hitl，--user→不拦截） | `c93641a` |

### 5.6 冷启动验证结论

冷启动验证暴露了 1 个代码 bug（`pip_install_global` 语义矛盾）和 2 个 PLAN 不完整点（前置依赖、Makefile 命令），均已修复。PLAN.md 的代码精确度得到验证——陌生 agent 能严格照搬实现，无需猜测。这证实了 writing-plans 技能的"逐字精确代码"策略有效。
