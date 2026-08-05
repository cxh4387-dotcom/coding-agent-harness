# AGENT_LOG.md

> 按时间顺序记录关键节点

---

## 2026-08-05 brainstorming 阶段

- **技能**: brainstorming
- **关键 prompt**: "严格按照要求完成任务，你需要一步一步详细完成"
- **关键节点**:
  - Q1: 选择 Python 作为技术栈
  - Q2: 选择治理/护栏作为重点维度
  - Q3: 选择 OpenAI 兼容 API
  - Q4: 选择 Docker 分发
  - Q5: 选择方案 A (FastAPI+WebSocket+原生JS)
- **产出**: SPEC.md (commit 663be2e)
- **人工干预**: 要求"校对文档要求"后发现 10 个问题并修复 (commit b5a97e5)

## 2026-08-05 writing-plans 阶段

- **技能**: writing-plans
- **产出**: PLAN.md (commit 831709e5)，22 个 task，TDD 步骤
- **自审**: SPEC 覆盖完整、无占位符、类型一致

## 2026-08-05 冷启动验证 (§4.5)

- **技能**: task (general subagent, 全新 session)
- **指定 task**: Task 2 (数据模型) + Task 8 (危险检测器)
- **subagent 产出**: 19 测试通过，commits 40c4f11..789f15e
- **暴露的缺陷**:
  1. Task 1 前置依赖未标注 → 修复 (commit c93641a)
  2. pip_install_global 规则 bug → 修复 (commit c93641a)
  3. Makefile pytest 命令 → 修复 (commit c93641a)
- **教训**: PLAN 的代码精确度足够让陌生 agent 无需猜测实现，但执行顺序和前置依赖需要更明确

## 2026-08-05 实现阶段 (§4.6)

- **技能**: using-git-worktrees + subagent-driven-development
- **worktree**: `.worktrees/feature-core` (branch `feature/core-foundation`)

### Task 1: 脚手架
- **subagent**: general
- **commit**: 5697ae2
- **产出**: requirements.txt, Makefile, .gitlab-ci.yml, config/default.yaml, 5 个 __init__.py
- **测试**: 21 passed

### Task 3: LLM 抽象层
- **subagent**: general
- **commit**: 4fbc6dc
- **产出**: interface.py, mock.py, openai_compat.py + 3 测试文件
- **测试**: 30 passed (+9)
- **人工修改**: subagent 修复了 mock_llm 测试的 async 兼容性 (commit fc1ce95)

### Tasks 4-7: 工具模块
- **subagent**: general
- **commits**: 86a877d..115d635
- **产出**: dispatcher.py, file_ops.py, shell.py, test_runner.py + 4 测试文件
- **测试**: 44 passed (+14)
- **subagent 改进**: shell.py 添加 proc.kill() 清理超时进程 (Windows 兼容)

### Tasks 9-11: 治理模块
- **subagent**: general
- **commits**: 41c7b36..d71b24c
- **产出**: hitl_state_machine.py, sandbox.py, scope_fence.py + 3 测试文件
- **测试**: 65 passed (+21)

### Tasks 12-15: 反馈/记忆/配置/凭据
- **subagent**: general
- **commits**: 76b8997..8d43466
- **产出**: feedback.py, memory.py, config.py, credentials.py + 4 测试文件
- **测试**: 80 passed (+15)
- **subagent 修改**: 在 models.py 添加 Memory dataclass

### Task 16: Agent 主循环
- **subagent**: general
- **commit**: 7efd589
- **产出**: agent_loop.py + test_agent_loop.py
- **测试**: 83 passed (+3)

### Tasks 17-19: WebUI
- **subagent**: general
- **commits**: d6b9767..f39056b
- **产出**: app.py, api.py, ws.py, index.html, app.js, style.css + 2 测试文件
- **测试**: 90 passed (+7)

### Tasks 20-22: 演示/Docker/集成测试
- **subagent**: general
- **commits**: 68abc4b..7890c44
- **产出**: 3 demo 脚本, Dockerfile, README.md, 2 集成测试
- **测试**: 93 passed (90 unit + 3 integration)
- **subagent 改进**: agent_loop.py 集成 Sandbox 路径校验
- **人工修改**: demo 脚本 Unicode 字符 → ASCII (Windows 兼容, commit c544c75)

## 教训总结

1. **PLAN 精确度是关键**: 逐字精确代码让 subagent 无需猜测，但前置依赖需要显式标注
2. **Windows 兼容性**: Unicode 字符、进程清理、PATH 问题需要持续关注
3. **TDD 有效**: 先写测试确保了每个模块的接口正确性
4. **subagent 改进有价值**: shell.py 的进程清理、agent_loop.py 的 sandbox 集成都是合理的改进
5. **冷启动验证有价值**: 发现了 pip_install_global bug 和前置依赖问题
