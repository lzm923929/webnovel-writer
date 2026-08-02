# 审查输出 Schema（v7）

> **主服务 skill**: `webnovel-write` Step 3、`webnovel-review` Step 4
> **内容层级**: 流程闸门 / schema 定义
> **关键原则**: reviewer 输出 JSON 是审查唯一事实源；`review-pipeline` 负责 report + metrics 落库；主 skill 不应伪造 `overall_score`。
> **v7 变更**: 新增 severity 判定阈值与示例（§3）、category 枚举归属澄清（§2.1）、阻断与放行闸门（§4）、指标 KPI 与趋势解读（§5.1）。

统一审查 Agent 输出格式。替代原 checker-output-schema.md 的评分制。

## 1. 核心变化

- **无总分**：不再输出 overall_score，改为结构化问题清单
- **blocking 语义**：替代原 timeline_gate，severity=critical 默认阻断
- **单 agent**：不再区分 6 个 checker，统一由 reviewer agent 输出

## 2. Issue Schema

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| severity | critical/high/medium/low | ✅ | 严重度（判定标准见 §3） |
| category | continuity/setting/character/timeline/logic（reviewer 五维）+ ai_flavor/pacing/other（兼容枚举，见 §2.1） | ✅ | 问题分类 |
| location | string | ✅ | 位置（如"第3段"） |
| description | string | ✅ | 问题描述 |
| evidence | string | ❌ | 原文引用或记忆对比（reviewer 自检清单要求**必须提供**，见 `agents/reviewer.md` §6） |
| fix_hint | string | ❌ | 修复建议 |
| blocking | bool | ❌ | 是否阻断（critical 默认 true） |

### 2.1 category 枚举归属（v7 澄清）

| 枚举值 | 产出方 | 说明 |
|--------|--------|------|
| `setting` / `timeline` / `continuity` / `character` / `logic` | **reviewer 唯一主动产出范围** | 固定 5 维，逐维必查并输出 `dimension_results` |
| `ai_flavor` | **不归 reviewer 负责** | AI 味 / Anti-AI 检测由 `webnovel-write` Step 4 polish Anti-AI 终检单独把关（`anti_ai_force_check=fail` 时阻断进 Step 5） |
| `pacing` / `other` | 后端兼容枚举 | reviewer 不主动产出；`low` 级可选节奏提示可归 `pacing`，仅参考、不计入 5 维阻塞 |

## 3. severity 判定阈值（四级，带示例）

跨会话一致性靠固化阈值，不靠主观感觉：

| 级别 | 含义 | 判定阈值 | 示例 | 默认阻断 |
|------|------|----------|------|----------|
| **critical** | 确定性事实矛盾，影响后续不可忽略 | 与已确立事实/设定/时间线/角色**确定性冲突** | 已死角色出场；境界倒退；时间倒流无交代；货币规则被破；角色用了不可能知道的信息 | ✅ `blocking=true` |
| **high** | 有矛盾但有解释空间，或读者明显出戏 | 与设定/角色/时间线冲突，存在可圆回来的余地 | 角色语气明显 OOC；上章钩子无回应；地点无过渡跳变；倒计时未推进 | 由 reviewer 按上下文判定 |
| **medium** | 读者可能注意到的细节瑕疵 | 不一致但**不阻断**剧情连续性 | 武器/外貌前后小出入；时间精度不一致；称呼前后不统一 | 否 |
| **low** | 非事实性可选改进 | 仅限可验证的小问题或命名/设定细节建议 | 某设定名可更统一；可选节奏提示（属 `pacing` 仅参考，不计入 5 维阻塞） | 否 |

> 规则：`severity=critical` 自动 `blocking=true`；其余级别由 reviewer 依据上下文与"是否阻断后续"判定。
> `critical` 仅用于**确定的事实矛盾**，不得因文笔/主观原因升级为 critical。

## 4. 阻断与放行闸门（Gate）

### 4.1 阻断规则

- 存在任何 `blocking=true` 的 issue → Step 4 不得开始
- `severity=critical` 自动 `blocking=true`
- 其余 severity 由审查 agent 根据上下文判断

### 4.2 章节放行（accept）条件（全部满足）

- `blocking_count == 0`
- `missed_nodes` 为空（必须覆盖的剧情节点无遗漏）
- `pending` 为空（无待消歧事实）

### 4.3 章节拒绝（reject）条件（任一满足）

- `blocking_count > 0`，或
- `missed_nodes` 非空，或
- `pending` 非空

等价于 `chapter-commit` 自动判定为 `rejected`，`chapter_status` 不进入 `committed`。
放行后仍需 `write-gate` 的 `prewrite` / `precommit` / `postcommit` 三阶段全部通过。

## 5. 指标沉淀

统一审查 agent 的原始输出保存为 `review_results.json`，保留完整 `issues` 列表。

随后由 `review-pipeline` 生成 `review_metrics.json`，用于写入 `index.db.review_metrics`。
该文件同时包含两类信息：

- **落库兼容字段**：
  - `start_chapter`
  - `end_chapter`
  - `overall_score`（由问题严重度推导的兼容分）
  - `dimension_scores`
  - `severity_counts`
  - `critical_issues`
  - `report_file`
  - `notes`
- **观测字段**：
  - `chapter`
  - `issues_count`
  - `blocking_count`
  - `categories`
  - `timestamp`

说明：
- `review_metrics` 表仍沿用现有 dashboard / trend / context 消费的兼容 schema。
- `overall_score` 仅用于趋势观测与排序，不替代原始 issue 清单。
- gate 决策仍以 `blocking=true` 和 issue 明细为准。

### 5.1 KPI 与趋势解读（v7 新增，可按团队调整，非硬约束）

- **放行门槛**：`blocking_count == 0` 方可 ship（硬性）。
- **一次性通过率**：目标 ≥ 90% 章节首审即 `blocking_count == 0`；低于 70% 触发复盘。
- **趋势预警**：每 10 章滑动统计 `issues_count` 均值，若连续上升 → 提示设定/写作流程回归，运行 `/webnovel-doctor`。
- **维度热力**：`severity_counts` 按维度聚合，若某维度（如 `character` OOC）长期偏高 → 针对性补强设定约束。

> `overall_score` 仅用于趋势观测与排序，gate 决策**始终以 `blocking=true` 与 issue 明细为准**。

## 6. reviewer 输出契约（贴合 5 维的示例）

reviewer 仅返回以下 JSON，无其他文本；`issues_count` / `blocking_count` / `has_blocking` 必须与 `issues` 一致；
`dimension_results` 必须且只能覆盖 5 维（无问题也输出 `pass`）：

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
