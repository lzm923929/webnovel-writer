# Webnovel Writer v1.1 优化变更清单

> 本文档逐项记录本次优化（依据 `webnovel-writer1.md` 评审意见）对项目文件的修改。
> 原项目 `../webnovel-writer` 保持原状，未做任何改动；所有修改仅作用于本目录。
> 优化范围：**仅文档与审查标准表述**，未改动任何 Python 脚本逻辑，运行时行为不变。

---

## 变更总览

| # | 级别 | 问题 | 修改文件 | 状态 |
|---|------|------|----------|------|
| 1 | 🟡 | severity 四级无判定阈值与示例 | `references/review-schema.md` | ✅ 已修复 |
| 2 | 🟡 | category 枚举不一致 / anti_ai 归属模糊 | `references/review-schema.md`、`agents/reviewer.md` | ✅ 已修复 |
| 3 | 🔴 | blocking 定点修复后无复检，存在修复盲区 | `skills/webnovel-write/SKILL.md`、`agents/reviewer.md` | ✅ 已修复 |
| 4 | 🟡 | 有指标无放行阈值与趋势解读 | `references/review-schema.md` | ✅ 已修复 |
| 5 | 🟡 | --fast / --minimal 无适用约束 | `skills/webnovel-write/SKILL.md` | ✅ 已修复 |
| 6 | 🟡 | blocking 裁决仅二元、无 SLA | `skills/webnovel-review/SKILL.md` | ✅ 已修复 |
| 7 | 💭 | 三入口文件重复易漂移 | `README.md`、`CLAUDE.md`、`AGENTS.md`、`codex.md` | ✅ 已收敛 |
| 8 | 💭 | reviewer 输出示例不贴合 5 维 | `agents/reviewer.md` | ✅ 已修复 |
| 9 | 🔧 附带 | `.claude/commands/webnovel-init.md` 漂移（错误信息残留 `CLAUDE_PLUGIN_ROOT`） | `.claude/commands/webnovel-init.md` | ✅ 已修复 |
| 10 | 🔧 附带 | `blocking-override-guidelines.md` 步骤引用过时（Step 6 → Step 8） | `references/review/blocking-override-guidelines.md` | ✅ 已修复 |

---

## 逐项明细

### 1. severity 判定阈值（🟡）

**文件**：`references/review-schema.md`（v6 → v7）
**改动**：新增 §3「severity 判定阈值（四级，带示例）」，固化每级含义、判定阈值、示例与默认阻断行为。
**效果**：跨会话 severity 分级不再靠主观感觉；`critical` 限定为"确定性事实矛盾"，禁止因文笔/主观原因升级。

### 2. category 枚举一致性（🟡）

**文件**：`references/review-schema.md` §2.1、`agents/reviewer.md` §5/§7
**改动**：
- schema 新增 §2.1「category 枚举归属」表：reviewer 唯一主动产出范围为 5 维；`pacing`/`other` 仅为后端兼容枚举；`ai_flavor` 明确归 `webnovel-write` Step 4 polish Anti-AI 终检。
- reviewer.md §5 边界新增"不查 AI 味""不主动产出 pacing/other"两条禁区。
**效果**：枚举产出方唯一化，终检归属不再模糊。

### 3. blocking 定点修复复检（🔴 风险级）

**文件**：`skills/webnovel-write/SKILL.md` Step 3 + 充分性闸门第 3 条、`agents/reviewer.md` 新增 §10
**改动**：
- reviewer.md §10「定点修复后的 targeted 复检」：修复后必须对修改段落做 targeted 复检（只查修改段及直接上下文），或显式标注"已定点修复，修改段未经复检"；复检输出沿用同一 schema，`issues` 可为空但受影响维度必须给结论。
- SKILL.md Step 3 增加 🔴 复检段落；充分性闸门第 3 条同步纳入复检条件。
**效果**：堵住"修复引入新问题无人发现"的盲区，同时不破坏"审查只跑一轮"的性能约束。

### 4. 放行阈值与 KPI（🟡）

**文件**：`references/review-schema.md` 新增 §4「阻断与放行闸门」与 §5.1「KPI 与趋势解读」
**改动**：
- §4 固化 accept（`blocking_count==0` 且 `missed_nodes` 空且 `pending` 空）/ reject 条件。
- §5.1 给出四条 KPI：放行门槛（硬性）、一次性通过率（≥90% 目标 / <70% 复盘）、10 章滑动趋势预警、维度热力聚合。
**效果**："多少算好"有了可度量口径，趋势回归可预警。

### 5. 分层模式适用约束（🟡）

**文件**：`skills/webnovel-write/SKILL.md` 模式表
**改动**：模式表新增"审查范围"与"适用章节类型（约束）"两列；明确 `--minimal` 仅限草稿章/非正史番外/用户明确选择，滥用视为违反铁律第 3 条。
**效果**：分层模式不再被滥用跳过审查。

### 6. 裁决协议 SLA（🟡）

**文件**：`skills/webnovel-review/SKILL.md` Step 8
**改动**：二元裁决（立即修/存报告）升级为四路分级路由表：blocking → 立即升级三选项；reviewer 异常 → `needs_user_action` 三选项；非阻断建议 → 不阻断；无阻断 → 直接放行。并链接 `blocking-override-guidelines.md` 的禁止 override 场景。
**效果**：每种异常都有明确路由与 SLA，不再一刀切。

### 7. 三入口收敛（💭）

**文件**：`README.md`（升级为 v1.1 单一权威源）、`CLAUDE.md` / `AGENTS.md` / `codex.md`（改为极薄壳）
**改动**：
- README.md 现为唯一权威指令源（含完整 §8 审查标准）。
- 三个入口文件各约 30 行：入口注释 + 环境引导 + 铁律 + 指向 README.md 的引导，不再重复全文。
**效果**：指令内容变更只改 README.md 一处，从机制上杜绝三份副本漂移。
**兼容性说明**：壳文件保留了环境变量设置与铁律，即使平台只读入口文件也能安全启动。

### 8. reviewer 输出示例统一（💭）

**文件**：`agents/reviewer.md` §7
**改动**：示例从"枚举占位 + category=continuity 但 dimension_results 报 timeline"的矛盾示例，改为完整贴合 5 维的具体实例（continuity / high / 非阻断 / 五维结论齐全），与 `review-schema.md` §6、README.md §8.11 三处完全一致。

### 9. webnovel-init 漂移修复（🔧 附带）

**文件**：`.claude/commands/webnovel-init.md` 第 54 行
**改动**：错误信息 `未设置 CLAUDE_PLUGIN_ROOT` → `未设置 WEBNOVEL_ROOT`（检查条件本就是 WEBNOVEL_ROOT，原信息误导排错）。

### 10. override 指南步骤引用（🔧 附带）

**文件**：`references/review/blocking-override-guidelines.md` frontmatter 与引用行
**改动**：`webnovel-review Step 6` → `Step 8`（与实际 skill 步骤编号一致）。

---

## 副本同步校验

`.claude/` 下的 agents / commands 副本已与主文件逐一 diff 校验，全部一致：

- `agents/reviewer.md` ⇔ `.claude/agents/reviewer.md` ✅
- `skills/webnovel-write/SKILL.md` ⇔ `.claude/commands/webnovel-write.md` ✅
- `skills/webnovel-review/SKILL.md` ⇔ `.claude/commands/webnovel-review.md` ✅
- 其余 4 agents / 8 commands 保持与原项目一致 ✅

> 维护规约（见 README.md §10）：今后修改 `agents/*.md` 或 `skills/*/SKILL.md` 后，必须同步 `.claude/` 对应副本。

## 未改动项（明确保留）

- 所有 Python 脚本（`scripts/`、`dashboard/`、`hooks/`）：零改动，运行时行为不变。
- 审查 5 维度、blocking 闸门、防伪造护栏、指标落库等原机制亮点：全部保留。
- `.git` 历史：完整保留在本目录中。
