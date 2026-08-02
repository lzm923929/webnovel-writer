# Webnovel Writer（优化版 v1.1）— 系统化审查标准与流程

> 本版基于原 `webnovel-writer`（跨平台版 · Claude Code / ChatGPT Codex / Codex 通用）优化。
> 本次优化的核心目标：把分散在 `agents/reviewer.md`、`references/review-schema.md`、
> `skills/webnovel-review`、`skills/webnovel-write` 中的审查逻辑，**收敛为一份可执行、可审计、
> 可度量的审查标准与流程**，并修正原机制中的若干一致性缺口。
> **本文件（README.md）为单一权威指令源**；`CLAUDE.md` / `AGENTS.md` / `codex.md` 为各平台极薄壳文件，
> 仅含入口声明与引导，不再重复本文件内容（见 §10）。

---

## 0. 本次优化说明（Code Review Expert 评审意见）

### 0.1 原机制亮点（已保留，未改动逻辑）

- **维度化审查**：`reviewer` 固定 5 个事实维度（设定 / 时间线 / 连贯 / 角色 / 逻辑），避免主观散评。
- **无总分、只报问题**：以结构化 `issues` 清单替代 overall_score 评分制，聚焦可验证事实。
- **阻断闸门清晰**：`severity=critical` 自动 `blocking=true`；`blocking=true` 即 chapter-commit rejected。
- **防伪造护栏**：禁止主流程口头替代 subagent 输出，reviewer 只返回严格 JSON，`review-pipeline` 负责落库。
- **指标已落库**：`review_metrics` 表已记录 `issues_count` / `blocking_count` / `severity_counts` / `categories` 等。

### 0.2 发现的问题与本次修复（均已落地）

| 级别 | 问题 | 原位置 | 修复位置 |
|------|------|--------|----------|
| 🟡 建议 | `severity` 四级（critical/high/medium/low）无判定阈值与示例，跨会话一致性靠主观 | `references/review-schema.md` | 已固化到 `references/review-schema.md` §3（各级定义 + 示例），对应本文 §8.3 |
| 🟡 建议 | `category` 枚举不一致：`reviewer.md` 仅产出 5 维，schema 额外列 `ai_flavor`/`pacing`/`other`；`anti_ai` 终检归属模糊 | `reviewer.md` §7 / `review-schema.md` | 已在 `review-schema.md` §2.1 与 `agents/reviewer.md` §5/§7 明确：reviewer 只产 5 维，`ai_flavor` 归 polish Anti-AI 终检，对应本文 §8.2/§8.3 |
| 🔴 风险 | blocking 定点修复后"不重新调用 reviewer"，存在修复引入新问题的盲区 | `webnovel-write` Step 3 | 已在 `skills/webnovel-write/SKILL.md` Step 3 与 `agents/reviewer.md` §10 增加"定点修复后 targeted 复检或显式标注未复检"要求，对应本文 §8.5/§8.7 |
| 🟡 建议 | 有指标但无"多少算好"的放行阈值与趋势解读口径 | `review-schema.md` 指标沉淀 | 已在 `review-schema.md` §4/§5.1 固化放行标准 + KPI 与趋势预警，对应本文 §8.4/§8.10 |
| 🟡 建议 | `--fast` / `--minimal` 分层模式无适用约束，易被滥用跳过审查 | `webnovel-write` 模式表 | 已在 `skills/webnovel-write/SKILL.md` 模式表限定各模式适用章节类型，对应本文 §8.7 |
| 🟡 建议 | blocking 升级仅为二元裁决（立即修 / 存报告），无 SLA 与分级路由 | `webnovel-review` Step 8 | 已在 `skills/webnovel-review/SKILL.md` Step 8 固化为裁决协议 + 分级路由，对应本文 §8.8 |
| 💭 细节 | 三套入口文件（CLAUDE/AGENTS/codex）内容完全重复，维护易漂移 | 根目录三文件 | 已收敛：本文件为单一权威源，三入口改为极薄壳文件，见 §10 |
| 💭 细节 | `reviewer.md` 输出示例的 `category` 用 `continuity`，与 5 维示例略有出入 | `reviewer.md` §7 | 已统一示例贴合 5 维，见 `agents/reviewer.md` §7、`review-schema.md` §6、本文 §8.11 |

> 附带修复（副本同步漂移）：`.claude/commands/webnovel-init.md` 错误信息残留 `CLAUDE_PLUGIN_ROOT`（应为 `WEBNOVEL_ROOT`）；
> `references/review/blocking-override-guidelines.md` 的步骤引用过时（Step 6 → Step 8）。

---

## 1. 系统概览

长篇网文创作系统：从初始化设定、规划卷纲，到写章、审查、沉淀记忆、查询状态，再到只读可视化面板，
整条创作流程已串好。本目录是一份**与 AI 工具无关**的便携包，可在 **Claude Code、ChatGPT Codex、Codex**
三种环境中使用。

> 核心理念：让 AI 写到几百章，依然记得住设定、接得住伏笔、守得住大纲。
> 这是一套面向长篇连载的一致性系统，不是写完就忘的一次性生成器。

---

## 2. 环境准备（每次开新会话先执行）

原 Claude Code 插件依赖 `${CLAUDE_PLUGIN_ROOT}` 和 `${CLAUDE_PROJECT_DIR}`；本跨平台版统一替换为：

- `${WEBNOVEL_ROOT}`：本工具目录（含 `scripts/`、`skills/`、`agents/`、`references/`）的绝对路径。
  未设置时**自动回退到当前目录 `$PWD`**，三种 AI 工具通用。
- `${WEBNOVEL_WORKSPACE}`：书项目工作区（新书将被创建为它的子目录）。未设置时回退到 `$PWD`。

```bash
export WEBNOVEL_ROOT="$(pwd)"
export WEBNOVEL_WORKSPACE="$(pwd)"
export SCRIPTS_DIR="${WEBNOVEL_ROOT}/scripts"
```

> Claude Code 用户：已内置 `.claude/`（agents / commands / settings），开箱即用。
> ChatGPT Codex / Codex 用户：直接用 `codex.md` 作为指令入口，按需读取 `skills/<命令>/SKILL.md` 与
> `agents/<代理>.md` 按步骤执行。

---

## 3. Python 依赖

```bash
python -m pip install -r "${WEBNOVEL_ROOT}/scripts/requirements.txt"
```

（可选）RAG 语义检索：在**书项目根目录**放一个 `.env`（缺失时自动退回 BM25 关键词检索）：

```bash
EMBED_BASE_URL=https://api-inference.modelscope.cn/v1
EMBED_MODEL=Qwen/Qwen3-Embedding-8B
EMBED_API_KEY=your_embed_api_key
RERANK_BASE_URL=https://api.jina.ai/v1
RERANK_MODEL=jina-reranker-v3
RERANK_API_KEY=your_rerank_api_key
```

---

## 4. 命令（8 个）

| 命令 | 用途 | 文件 |
|------|------|------|
| `/webnovel-init` | 深度初始化项目骨架、设定集、总纲 | `skills/webnovel-init/SKILL.md` |
| `/webnovel-plan` | 拆卷纲、时间线、章纲，并写回新增设定 | `skills/webnovel-plan/SKILL.md` |
| `/webnovel-write` | 一条龙写章：上下文→起草→审查→润色→提交→备份 | `skills/webnovel-write/SKILL.md` |
| `/webnovel-review` | 多维度审查章节并把指标落库 | `skills/webnovel-review/SKILL.md` |
| `/webnovel-query` | 查询设定、角色、伏笔、运行时信息（只读） | `skills/webnovel-query/SKILL.md` |
| `/webnovel-learn` | 把有效写法沉淀进项目长期记忆 | `skills/webnovel-learn/SKILL.md` |
| `/webnovel-dashboard` | 启动只读可视化面板 | `skills/webnovel-dashboard/SKILL.md` |
| `/webnovel-doctor` | 阶段感知检查目录、文件、数据库、RAG、依赖 | `skills/webnovel-doctor/SKILL.md` |

- **Claude Code**：直接输入斜杠命令（已注册到 `.claude/commands/`）。
- **ChatGPT Codex / Codex**：读取对应的 `skills/<命令>/SKILL.md`，严格按其中的 Bash / Read / Write 步骤执行。

---

## 5. 子代理（4 个）

| 代理 | 职责 | 被谁调用 |
|------|------|---------|
| `context-agent` | 写前 research，输出五段写作任务书 | `webnovel-write` Step 1 |
| `reviewer` | 逐维度事实审查（见 §8 标准） | `webnovel-write` Step 3、`webnovel-review` |
| `data-agent` | 从正文提取事实，生成 commit artifacts | `webnovel-write` Step 5 |
| `deconstruction-agent` | 参考书拆解，提炼可迁移写法 | `webnovel-init` Step 1.5 |

- **Claude Code**：用 `Agent` 工具调用上述代理（已注册到 `.claude/agents/`）。
- **ChatGPT Codex / Codex**：用平台的子任务工具，或读取 `agents/<代理>.md` 后"扮演"该角色
  （把该文件内容作为本轮子任务的 prompt）。**不得由主流程口头替代子代理的真实输出**，也不得伪造审查 JSON。

---

## 6. 铁律（必须守住）

1. 所有 Story System 写入（合同 / 提交 / 投影）**只能通过** `python "${SCRIPTS_DIR}/webnovel.py"` 的
   `story-system` / `chapter-commit` / `write-gate` / `projections` 子命令完成。
2. **禁止**直接用 Write/Edit/Bash 改写 `.story-system/`（合同与提交）以及 `.webnovel/index.db`、
   `vectors.db`、`memory_scratchpad.json`、`projection_log.jsonl` 等只读视图——运行护栏 hook 会拦截。
3. 写章流程严格按 `skills/webnovel-write/SKILL.md` 的 Step 1→6，不跳步、不并步、不伪造审查。
4. 作者友好：最终回复用固定三段式（总状态 / 产生的文件与完成情况 / 下一步建议），不直接甩原始 JSON、traceback 或长命令日志。
5. **审查不可静默**：reviewer 跳过 / 失败 / 输出不完整 / 正文为空 / 维度跳过 / 耗时异常，必须在最终报告显式汇报，不得隐瞒。

---

## 7. 快速开始

```bash
# 1) 初始化一本书（会创建 <WEBNOVEL_WORKSPACE>/<书名安全化>/ 子目录）
python "${SCRIPTS_DIR}/webnovel.py" --project-root "${WEBNOVEL_WORKSPACE}" preflight

# 2) 规划第 1 卷、写第 1 章、审查、查询
#    Claude Code: /webnovel-plan 1   /webnovel-write 1   /webnovel-review 1-5   /webnovel-query 伏笔
#    Codex:       读取 skills/webnovel-plan/SKILL.md 等并按步骤执行

# 3) 打开可视化面板（只读）
#    Claude Code: /webnovel-dashboard
```

初始化完成后书项目目录：

```text
<书名>/
├── .story-system/        # 合同、章节提交和事件审计（唯一事实源头）
├── .webnovel/            # 状态、索引、摘要、备份和长期记忆
├── 正文/                 # 章节正文
├── 大纲/                 # 总纲、卷纲、时间线和章纲
├── 设定集/               # 世界观、角色、力量体系等设定
└── 审查报告/             # 章节审查报告
```

---

## 8. 审查标准与流程（系统化 · 核心）

> 本节约等于项目内的"Code Review 规范"。所有审查行为（无论由 `webnovel-write` Step 3 内联，
> 还是由 `webnovel-review` 独立触发）都必须遵守本节。本节的权威实现见
> `agents/reviewer.md` 与 `references/review-schema.md`，本节为其**人类可读的标准化摘要**。

### 8.1 审查定位与边界

审查只回答一个问题：**"这一章的事实/一致性是否站得住脚，能否安全并入正史？"**

| ✅ 审查范围（属于 issue） | ❌ 审查禁区（不属于 issue） |
|--------------------------|----------------------------|
| 设定矛盾（能力/地点/物品规则） | 文笔优劣、"写得好不好" |
| 时间线错乱、双地点 | 主观情节建议（"这里该加反转"） |
| 叙事不连贯、钩子无回应 | 暴露未发生剧情（剧透大纲） |
| 角色 OOC、知识越界 | 风格偏好（"可以更燃一点"） |
| 逻辑/因果/力量对比矛盾 | 评分、总体打分 |

- 每个 issue **必须有 evidence**（原文引用或数据对比），禁止"感觉不对"类主观评价。
- `ai_flavor`（AI 味 / Anti-AI 检测）**不归 reviewer 负责**，由 `webnovel-write` Step 4 的
  polish Anti-AI 终检单独把关（`anti_ai_force_check=fail` 时阻断进 Step 5）。

### 8.2 审查维度（固定 5 维）

| 维度 | category | 必查项 |
|------|----------|--------|
| 设定一致性 | `setting` | 角色能力 vs 当前境界；地点 vs 世界观；物品/货币 vs 已建立规则 |
| 时间线 | `timeline` | 本章时间 vs 上章衔接；倒计时/截止日期推进；同角色是否双地点 |
| 叙事连贯 | `continuity` | 上章钩子是否回应；场景转换是否有过渡；情绪弧是否连续 |
| 角色一致性 | `character` | 对话风格 vs 角色特征；行为 vs 性格/动机；知识边界（是否用了不该知道的信息） |
| 逻辑 | `logic` | 因果关系；决策动机；战斗/冲突结果 vs 力量对比 |

- `reviewer` **只产出上述 5 维**。`review-schema.md` 中的 `pacing` / `other` 仅为后端兼容枚举，
  本代理不主动产出；`ai_flavor` 由 polish 阶段处理（见 §8.1）。
- 完成 5 维检查后，**每个维度必须显式输出一行结论**（无问题也输出 `pass`）。

### 8.3 严重度分级标准（四级，带示例）

| 级别 | 含义 | 判定阈值 | 示例 | 默认阻断 |
|------|------|----------|------|----------|
| **critical** | 确定性事实矛盾，影响后续不可忽略 | 与已确立事实/设定/时间线/角色**确定性冲突** | 已死角色出场；境界倒退；时间倒流无交代；货币规则被破；角色用了不可能知道的信息 | ✅ `blocking=true` |
| **high** | 有矛盾但有解释空间，或读者明显出戏 | 与设定/角色/时间线冲突，存在可圆回来的余地 | 角色语气明显 OOC；上章钩子无回应；地点无过渡跳变；倒计时未推进 | 由 reviewer 按上下文判定 |
| **medium** | 读者可能注意到的细节瑕疵 | 不一致但**不阻断**剧情连续性 | 武器/外貌前后小出入；时间精度不一致；称呼前后不统一 | 否 |
| **low** | 非事实性可选改进 | 仅限可验证的小问题或命名/设定细节建议 | 某设定名可更统一；可选节奏提示（属 `pacing` 仅参考，不计入 5 维阻塞） | 否 |

> 规则：`severity=critical` 自动 `blocking=true`；其余级别由 reviewer 依据上下文与"是否阻断后续"判定。
> `critical` 仅用于**确定的事实矛盾**，不得因文笔/主观原因升级为 critical。

### 8.4 阻断与放行闸门（Gate）

**章节放行（accept）条件**（全部满足）：
- `blocking_count == 0`
- `missed_nodes` 为空（必须覆盖的剧情节点无遗漏）
- `pending` 为空（无待消歧事实）

**章节拒绝（reject）条件**（任一满足）：
- `blocking_count > 0`，或
- `missed_nodes` 非空，或
- `pending` 非空

等价于 `chapter-commit` 自动判定为 `rejected`，`chapter_status` 不进入 `committed`。
放行后仍需 `write-gate` 的 `prewrite` / `precommit` / `postcommit` 三阶段全部通过（见 §8.9）。

### 8.5 审查者（reviewer）职责与自检清单

**职责**：读正文 → 逐维查事实问题 → 输出严格 JSON（不评分、不总结、不写文件）。
**输出契约**：仅返回 reviewer schema JSON，无其他文本；`issues_count` / `blocking_count` / `has_blocking`
必须与 `issues` 一致；`dimension_results` 覆盖全部 5 维。

**自检清单（每项必须达标方可视为"审查完成"）**：
- [ ] 每个 issue 都有 `evidence`（原文引用或数据对比）
- [ ] 无"感觉"类主观评价
- [ ] `severity` 分级符合 §8.3 阈值（critical 仅用于确定事实矛盾）
- [ ] `category` 归 5 维之一，不主动产出 `pacing`/`other`/`ai_flavor`
- [ ] `blocking` 仅在 critical 或确认阻断时为 `true`
- [ ] `dimension_results` 覆盖全部 5 维（无问题也输出 `pass`）
- [ ] 正文为空 → 输出单条 critical issue："正文为空"
- [ ] 状态/上章摘要读取失败 → 跳过对应维度并在 `summary` 标注，不静默

**🔴 定点修复后的复检要求**：
原机制规定 blocking 定点修复后"不重新调用 reviewer"，存在修复引入新问题的盲区。现要求：
- 若 blocking 在本回被定点修复（不破设定/不破剧情），必须对**修改段落**做一次 targeted 复检，
  确认未引入新的 critical/high issue；或显式在报告标注"已定点修复，修改段未经复检"。
- 确实无法在本回闭环的 blocking → 交用户裁决（见 §8.8），不得默认放行。

### 8.6 作者（writer）职责与处理清单

审查结果回到作者侧后，作者按以下清单处理：

- [ ] **blocking（critical）**：必须定点修复或交用户裁决；修复只改事实不改表达、不破设定/剧情
- [ ] **high（非阻断）**：本回尽量回填；无法闭环则标注并交作者/用户确认
- [ ] **medium**：可批量后续处理，不阻断
- [ ] **low**：确认是否采纳（命名/设定细节建议），不强制
- [ ] 不得静默任何问题；所有 issue 的处理状态须进入最终报告

### 8.7 分层审查流程（full / --fast / --minimal）

| 模式 | 审查范围 | 适用章节类型（约束） | 产物要求 |
|------|----------|----------------------|----------|
| **默认 full** | 5 维全查 | 正文章、关键节点章、卷首/卷尾章 | 标准 `review_results.json` + 报告 + metrics |
| `--fast` | 仅 `setting`/`timeline`/`continuity` 3 维 | 过渡章、低风险日常章 | 同 full，但 `dimension_results` 仅 3 维达标 |
| `--minimal` | 跳过 reviewer | **仅限**草稿章、非正史番外、或用户明确选择 | 必须**覆盖写入**新 no-review artifact，禁止复用旧 artifact |

> 约束：`--minimal` 不得用于正史主线关键章；滥用跳过审查视为违反 §6 铁律第 3 条。
> 审查只跑一轮（reviewer 只调用一次）；blocking 定点修复后按 §8.5 复检，不整体重跑 reviewer。

### 8.8 升级与裁决协议（SLA）

| 情形 | 路由 | 用户裁决选项 |
|------|------|--------------|
| 存在 `blocking=true` | 立即升级（不可静默） | 立即修复 / 仅存报告稍后处理 / 放弃本次审查 |
| reviewer `failed` / `partial` / 正文空 / 维度跳过 / 耗时异常 | 标记 `needs_user_action=true` | 重跑审查 / 人工介入 / 放弃 |
| 非 blocking 高收益建议 | 列为"建议确认"，**不阻断** | （无需裁决，作者自行采纳） |
| 无阻断 | 不询问，直接放行并提示可继续写下一章 | — |

> 裁决影响须向用户说明（如"立即修复"会做最小修改，"仅存报告"保留记录结束流程）。
> 卡住时必须说明卡点、已完成内容与恢复建议（如"reviewer 结果已保存，metrics 落库失败；重跑 `/webnovel-review` 会从落库继续"）。

### 8.9 质量闸门（write-gate 三阶段）

| 阶段 | 命令 | 作用 |
|------|------|------|
| `prewrite` | `write-gate --stage prewrite` | 写前校验合同树、必备文件（`MASTER_SETTING.json` / `volume_*.json` / `chapter_*.review.json`） |
| `precommit` | `write-gate --stage precommit` | 提交前闸门：结合 review 结果判定 blocking / missed_nodes / pending |
| `postcommit` | `write-gate --stage postcommit` | 提交后校验 projection 五项（state/index/summary/memory/vector）done 或 skipped |

**章节 Definition of Done（充分性闸门）**：
1. 正文文件存在且非空
2. 审查已落库（--minimal 除外）
3. `blocking=true` 已在 Step 3 定点修复（修改段经 targeted 复检或显式标注未复检）或经用户裁决
4. `anti_ai_force_check=pass`（--minimal 除外）
5. accepted `CHAPTER_COMMIT`，projection 五项 done/skipped
6. `chapter_status=committed`
7. `write-gate` 的 prewrite / precommit / postcommit 均通过

### 8.10 指标与 KPI（度量审查健康度）

`review_metrics` 已落库字段（`references/review-schema.md` v7）：

- **观测字段**：`chapter`、`issues_count`、`blocking_count`、`categories`、`severity_counts`、`timestamp`
- **兼容字段**：`overall_score`（由严重度推导，仅用于趋势/排序，不替代 issue 明细）、`dimension_scores`、`report_file`

**建议 KPI 与趋势解读**（可按团队调整，非硬约束）：
- **放行门槛**：`blocking_count == 0` 方可 ship（硬性）。
- **一次性通过率**：目标 ≥ 90% 章节首审即 `blocking_count == 0`；低于 70% 触发复盘。
- **趋势预警**：每 10 章滑动统计 `issues_count` 均值，若连续上升 → 提示设定/写作流程回归，运行 `/webnovel-doctor`。
- **维度热力**：`severity_counts` 按维度聚合，若某维度（如 `character` OOC）长期偏高 → 针对性补强设定约束。

> `overall_score` 仅用于趋势观测与排序，gate 决策**始终以 `blocking=true` 与 issue 明细为准**。

### 8.11 审查报告格式与归档

报告由 `review-pipeline --save-metrics` 生成，落盘到 `审查报告/第{NNN}章审查报告.md`，
同时写入 `review_metrics.json` 与 `index.db.review_metrics`。

reviewer 输出 JSON 示例（贴合 5 维，无额外文本）：

```json
{
  "chapter": 100,
  "issues": [
    {
      "severity": "high",
      "category": "continuity",
      "location": "第3段",
      "description": "上章结尾的钩子（神秘信件）本章未做任何回应",
      "evidence": "上章末段：'信封上的火漆印让他心头一紧'；本章无后续",
      "fix_hint": "在开篇或转场中回应信件，或显式交代'暂未拆阅'",
      "blocking": false
    }
  ],
  "issues_count": 1,
  "blocking_count": 0,
  "has_blocking": false,
  "dimension_results": [
    {"dimension": "setting", "conclusion": "pass"},
    {"dimension": "timeline", "conclusion": "pass"},
    {"dimension": "continuity", "conclusion": "发现1个问题：上章钩子未回应"},
    {"dimension": "character", "conclusion": "pass"},
    {"dimension": "logic", "conclusion": "pass"}
  ],
  "summary": "1个问题：0个阻断，1个高优"
}
```

### 8.12 持续改进闭环

- **`/webnovel-learn`**：把本次有效写法/修复模式沉淀进项目长期记忆，避免同类 issue 反复出现。
- **`/webnovel-doctor`**：阶段感知检查目录/文件/数据库/RAG/依赖，结合 §8.10 趋势预警触发复盘。
- **定期复盘**：每卷结束后查看 `review_metrics` 趋势，更新设定约束与 `core-constraints.md`，
  把高频 issue 维度转化为 `webnovel-write` Step 1 任务书的硬性约束。

---

## 9. 排错

```bash
python -X utf8 "${SCRIPTS_DIR}/webnovel.py" --project-root "<BOOK_ROOT>" preflight
python -X utf8 "${SCRIPTS_DIR}/webnovel.py" --project-root "<BOOK_ROOT>" doctor --format text
```

重点查看：`story_runtime.mainline_ready` 是否为 true；`projection_status` 是否全部 done/skipped；
`.story-system/commits/chapter_XXX.commit.json` 是否存在且 accepted。

---

## 10. 目录结构

```text
webnovel-writer/
├── README.md                          # 单一权威指令源（本文件）
├── CLAUDE.md / AGENTS.md / codex.md   # 各平台极薄壳文件：仅入口声明 + 引导读本文件
├── .claude/                           # Claude Code 原生：agents / commands / settings(hooks)
├── .codex/                            # OpenAI Codex 配置
├── agents/                            # 4 个子代理定义（跨平台可读）
├── skills/                            # 8 个命令（SKILL.md，路径已归一化）
├── scripts/                           # Python CLI（webnovel.py 统一入口）
├── references/                        # 题材/写法 CSV 与共享参考（含 review-schema.md v7）
├── hooks/                             # 运行护栏（Claude Code 用；Codex 等效手动）
├── dashboard/                         # 只读可视化面板（Python + 预打包前端）
└── OPTIMIZATION.md                    # v1.1 优化变更清单（对照原版的逐项 diff 说明）
```

> 💭 维护规约（v1.1 起生效）：`CLAUDE.md` / `AGENTS.md` / `codex.md` 为极薄壳文件，
> 内容变更只改本文件（README.md），壳文件不承载指令细节，杜绝三份副本长期漂移。
> 注意：`.claude/agents/*.md` 与 `.claude/commands/*.md` 是 `agents/*.md` 与 `skills/*/SKILL.md`
> 的同步副本，修改任一 side 后必须同步另一侧（可用 diff 校验）。

---

## 11. 协议与出处

协议：GPL-3.0（与原项目一致）。
原项目：https://github.com/lingfengQAQ/webnovel-writer

> 本优化版（v1.1）仅重构文档结构与审查标准表述，未改动任何 Python 脚本逻辑。
