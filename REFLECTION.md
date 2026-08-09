# REFLECTION.md — 反思报告

> AI4SE 期末项目 · Coding Agent Harness
>
> 声明：本反思报告由学生本人撰写核心内容，使用 AI 辅助润色措辞。

---

## 1. Superpowers 技能评价

### 哪些技能发挥了最大作用？

writing-plans 是作用最大的技能。其逐字精确代码策略让冷启动验证中的陌生 subagent 无需猜测就把 Task 2 和 Task 8 实现到测试全过。它把质量把控从执行阶段前移到写 PLAN 阶段，后续 22 个 task 基本是抄写和缝合。

test-driven-development 在接口契约层面有效：MockLLM 让 93 个测试无网络运行，冷启动可复现。subagent-driven-development 完成 22 个 task 和 93 个测试，但偏离了每 task 一个新鲜 subagent 的要求，本项目采用了批量派发方式（见 AGENT_LOG 偏差 2）。

### 哪些技能形式大于实质？

using-git-worktrees：只开了一个 worktree（偏差 1）。22 个 task 严格线性依赖，多 worktree 隔离收益低于合并成本。

requesting-code-review 和 finishing-a-development-branch：偏差 3 承认只在末尾做了一次综合评审，没做每 task 两阶段评审，靠 PLAN 精确度兜底。brainstorming 的 visual companion 也未触发。

---

## 2. TDD 在 AI 协作下的作用

### TDD 强制是阻碍还是放大器？

是放大器，但有明确边界：它防住接口契约偏离，防不住集成行为缺失。

放大面：MockLLM 让全部单测无网络运行，冷启动可复现。没有 TDD，移除 LLM 后护栏仍是确定性函数这条 §A.4 硬标准无法客观判定。

阻碍和失效面：当 PLAN 已给逐字代码，先写测试退化为先抄测试，red 阶段明知会 ModuleNotFoundError，是形式化的。真正有价值的 red 只在 PLAN 自身有 bug 时出现（见第 5 节的 pip_install_global 案例）。最关键的失效案例：agent_loop.py 第 64-67 行的 HITL 分支，HITLStateMachine 单测 9 个全过（状态转换正确），但 AgentLoop.run 里 request_approval 后直接 continue，永不阻塞等待审批（详见第 4 节案例一）。同理，SPEC §3.1 停机条件③测试全过即停在 agent_loop.py 第 48-103 行没实现。单测全过，集成行为不对。TDD 在模块边界处是放大器，在模块协作处是盲区。

---

## 3. Subagent-driven 工作流

### 智能体能自主运行多久而不偏离主题？

本项目最长一组批量派发约 4 个 task（Tasks 4-7、17-19、20-22），单 session 内未偏离。subagent 做了两个改进：shell.py 第 23-31 行的 proc.kill 和 transport.close 清理超时进程（Windows 兼容），agent_loop.py 第 75-89 行集成 Sandbox 路径校验，均合理。未出现有害偏离，因 PLAN 给了逐字代码，subagent 自由度被压到最低。

### 什么样的 task 颗粒度最优？

单个独立模块最优（如 DangerDetector）。太细会重复加载上下文，太粗会丢失单 task commit 可追溯性。实际选模块级加同模式批量，同模式 task 共享 session 省启动开销，但每 task 仍独立 commit。

---

## 4. SPEC/PLAN 质量对实现的影响

### 规约不清导致 subagent 偏离的具体案例

案例一（最严重）：HITL 在 agent_loop 中不真正阻塞。SPEC §3.1 数据流第 4 步用 prose 写 hitl 到 request_approval 到 WebSocket 推送到等待用户，但 PLAN Task 16 的 loop 代码模板里 hitl 分支只写了 request_approval 加 continue，没有 await 等待机制。subagent 忠实照搬，于是 agent_loop.py 第 64-67 行出现请求审批后直接 continue、永不阻塞。这不是 subagent 偏离原意，而是忠实复制了一个不完整的 PLAN：prose 里的等待用户没落到可抄的代码。修正：集成层承认待补（test_guardrail_to_hitl 只测状态机，不测 loop 阻塞）。

案例二：停机条件③缺失。SPEC §3.1 停机条件③测试全过即停，PLAN Task 16 代码模板没写，agent_loop.py 也就没实现。

教训：PLAN 的逐字精确代码对模块内部极有效，对模块间协作流程（prose 描述的部分）失效：prose 里的等待用户没落到可抄的代码，subagent 不会自己补。质量上限等于 PLAN 代码精确度的下限。

---

## 5. Prompt/Context 策略

### 你最有效的 prompt/context 策略是什么？

策略一：冷启动验证指令遇到不确定即暂停询问而非凭猜测继续（SPEC_PROCESS §5.1）。这让 subagent 把 pip_install_global 语义矛盾识别为 bug 并上报，而非自行修正后悄悄过去。

策略二：PLAN 每个 task 给 Consumes/Produces 接口契约，让 subagent 知道依赖什么、产出什么，不用猜模块边界。两者合力的机理：逐字代码消除实现层空白，暂停而非猜测把剩余空白变成显式提问而非隐式编造。前者可人工修正，后者沉淀成缺陷。

---

## 6. 凭据与分发工程要求

### 这两条要求迫使你想清楚了哪些原本会忽略的问题？

凭据方面：key 不能硬编码催生 CredentialManager；不能进 git 导致 .gitignore 排除 vault 和 .env；不能进日志促使 SPEC §4.2 写脱敏规则 sk-xxx 变 sk-星号；主密码从哪来导致 credentials.py 第 16-19 行用 uuid.getnode 加 username 派生，但暴露了硬编码 salt b 后接 harness-salt-v1（credentials.py 第 25 行）的弱点：固定 salt 等于废了 PBKDF2 抗彩虹表能力的一半。get_key 吞所有异常返回 None（credentials.py 第 42 行），导致 vault 损坏和未设置不可区分。

分发方面：镜像里 key 怎么进导致三种方式各标明文风险；容器以非 root 运行涉及路径权限；CI 要构建镜像对应 .gitlab-ci.yml build-docker job；NJU Git 无 dind 导致 commit 4ee00d7 标记 allow build-docker failure，CI 退化为只跑 unit-test。两条要求把安全从口号变成代码点检查清单，逼出原本不会考虑的工程问题。

---

## 7. 如果重做你会改变什么？

1. 把 HITL 阻塞做成可 await 的：PLAN Task 16 给 asyncio.Event 代码模板，而非只 prose 描述等待用户。最该改的。
2. 停机条件③写进 loop 代码模板，而非只写在 SPEC。
3. credentials.py 的 salt 改成安装时随机生成并持久化，而非硬编码。
4. 真正按每 task 一个新鲜 subagent 加每 task 评审执行，而非批量派发加末尾总评。批量省了启动开销，却废了新鲜 context 发现问题的最大优势。冷启动之所以有效正因为 context 新鲜。

---

## 8. 对 Superpowers 方法论的批判

### 它假设了什么？这些假设在你的项目里成立吗？

假设一：spec 足够清晰就能自动执行。部分成立。模块内成立，模块间协作流程不成立（见第 4 节：prose 描述的等待用户没落到代码，HITL 阻塞机制缺失）。精确度有边界：代码精确处有效，prose 处失效。

假设二：TDD 能防止 AI 偏离。弱成立。防住接口契约偏离，没防住集成层行为缺失（见第 2 节：HITL 不阻塞、停机条件 3 缺失，单测全过但集成行为不对）。盲区在模块边界。

假设三：每 task 派新鲜 subagent 能发现问题。本项目没真正执行（批量派发，偏差 2），无法直接验证。但冷启动（真新鲜 context）确实发现了 pip_install_global bug，间接支持该假设。讽刺的是，这个最有效的假设在实现阶段被批量派发绕过了。同理，worktree 隔离对线性依赖的 22 task 价值低（偏差 1），人类会做每步评审是最脆弱的假设：偏差 3 承认没做，靠 PLAN 精确度兜底。

核心批判：Superpowers 把过程纪律当质量来源，但执行成本高，人和 agent 都会偷工（5 处偏差即证据）。真正起作用的只有逐字精确 PLAN：它把质量从过程转移到前置产物，让后续执行可低成本复制。方法论的最强假设其实是项目可并行、可隔离、有远程仓库。一旦变成线性依赖加本地单仓，大半技能就失去用武之地。

---

字数统计：约 2100 字
