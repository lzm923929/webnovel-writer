<!-- 入口：通用（Cursor / Windsurf / Claude Code / Codex 均会读取）。 -->

# Webnovel Writer（跨平台版 · Claude Code / ChatGPT Codex / Codex 通用）

长篇网文创作系统：从初始化设定、规划卷纲，到写章、审查、沉淀记忆、查询状态，再到只读可视化面板，
整条创作流程已串好。本目录是一份**与 AI 工具无关**的便携包，原本只面向 Claude Code 插件，
现已改写为同时可在 **Claude Code、ChatGPT Codex、Codex** 三种环境中使用。

> 核心理念：让 AI 写到几百章，依然记得住设定、接得住伏笔、守得住大纲。
> 这是一套面向长篇连载的一致性系统，不是写完就忘的一次性生成器。

---

## 0. 环境准备（每次开新会话先执行）

原 Claude Code 插件依赖 `${CLAUDE_PLUGIN_ROOT}` 和 `${CLAUDE_PROJECT_DIR}` 这两个只有
Claude Code 插件机制才会注入的环境变量；本跨平台版统一替换为：

- `${WEBNOVEL_ROOT}`：本工具目录（含 `scripts/`、`skills/`、`agents/`、`references/`）的绝对路径。
  未设置时**自动回退到当前目录 `$PWD`**，因此三种 AI 工具通用。
- `${WEBNOVEL_WORKSPACE}`：书项目工作区（新书将被创建为它的子目录）。未设置时回退到 `$PWD`。

开会话时先设置（把本目录作为项目打开时，`pwd` 就是工具目录）：

```bash
export WEBNOVEL_ROOT="$(pwd)"
export WEBNOVEL_WORKSPACE="$(pwd)"
export SCRIPTS_DIR="${WEBNOVEL_ROOT}/scripts"
```

> Claude Code 用户：本项目已内置 `.claude/`（agents / commands / settings），可直接用
> 斜杠命令与 `Agent` 工具；无需额外配置，开箱即用。
> ChatGPT Codex / Codex 用户：直接用 `codex.md`（本项目根）作为指令入口；需要时读取
> `skills/<命令>/SKILL.md` 与 `agents/<代理>.md` 按步骤执行即可。

## 1. Python 依赖

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

## 2. 命令（8 个）

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
- **ChatGPT Codex / Codex**：读取对应的 `skills/<命令>/SKILL.md`，严格按其中的 Bash / Read / Write
  步骤执行（必要时用平台的问题工具向用户确认）。

## 3. 子代理（4 个）

| 代理 | 职责 | 被谁调用 |
|------|------|---------|
| `context-agent` | 写前 research，输出五段写作任务书 | `webnovel-write` Step 1 |
| `reviewer` | 逐维度事实审查 | `webnovel-write` Step 3、`webnovel-review` |
| `data-agent` | 从正文提取事实，生成 commit artifacts | `webnovel-write` Step 5 |
| `deconstruction-agent` | 参考书拆解，提炼可迁移写法 | `webnovel-init` Step 1.5 |

- **Claude Code**：用 `Agent` 工具调用 `context-agent` / `reviewer` / `data-agent` / `deconstruction-agent`
  （已注册到 `.claude/agents/`）。
- **ChatGPT Codex / Codex**：用平台的子任务（task）工具，或直接读取 `agents/<代理>.md` 后“扮演”该角色
  （把该文件内容作为本轮子任务的 prompt）。**不得由主流程口头替代子代理的真实输出**，也不得伪造审查 JSON。

## 4. 铁律（必须守住）

1. 所有 Story System 写入（合同 / 提交 / 投影）**只能通过** `python "${SCRIPTS_DIR}/webnovel.py"` 的
   `story-system` / `chapter-commit` / `write-gate` / `projections` 子命令完成。
2. **禁止**直接用 Write/Edit/Bash 改写 `.story-system/`（合同与提交）以及 `.webnovel/index.db`、
   `vectors.db`、`memory_scratchpad.json`、`projection_log.jsonl` 等只读视图——运行护栏 hook 会拦截。
3. 写章流程严格按 `skills/webnovel-write/SKILL.md` 的 Step 1→6，不跳步、不并步、不伪造审查。
4. 作者友好：最终回复用固定三段式（总状态 / 产生的文件与完成情况 / 下一步建议），不直接甩原始 JSON、traceback 或长命令日志。

## 5. 快速开始

```bash
# 1) 初始化一本书（会创建 <WEBNOVEL_WORKSPACE>/<书名安全化>/ 子目录）
#    按 skills/webnovel-init/SKILL.md 的分阶段问答收集信息
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

## 6. 平台差异速查

| 能力 | Claude Code | ChatGPT Codex / Codex |
|------|-------------|------------------------|
| 指令入口 | `CLAUDE.md` + `AGENTS.md` | `codex.md` + `AGENTS.md` |
| 斜杠命令 | 内置 `/webnovel-*`（`.claude/commands/`） | 读取 `skills/<命令>/SKILL.md` 执行 |
| 子代理 | `Agent` 工具（`context-agent` 等） | 子任务工具，或读取 `agents/*.md` 扮演 |
| 运行护栏 | `.claude/settings.json` hooks（自动） | 手动执行 `preflight` / `doctor` 等效校验 |
| 环境变量 | 设 `WEBNOVEL_ROOT`（或默认 pwd） | 同左 |

> 三套入口文件（`CLAUDE.md` / `AGENTS.md` / `codex.md`）内容一致，确保任一工具打开本目录都能获得完整指令。

## 7. 排错

```bash
python -X utf8 "${SCRIPTS_DIR}/webnovel.py" --project-root "<BOOK_ROOT>" preflight
python -X utf8 "${SCRIPTS_DIR}/webnovel.py" --project-root "<BOOK_ROOT>" doctor --format text
```

重点查看：`story_runtime.mainline_ready` 是否为 true；`projection_status` 是否全部 done/skipped；
`.story-system/commits/chapter_XXX.commit.json` 是否存在且 accepted。

## 8. 目录结构

```text
webnovel-writer/
├── CLAUDE.md / AGENTS.md / codex.md   # 三工具通用指令入口
├── .claude/                           # Claude Code 原生：agents / commands / settings(hooks)
├── .codex/                            # OpenAI Codex 配置
├── agents/                            # 4 个子代理定义（跨平台可读）
├── skills/                            # 8 个命令（SKILL.md，路径已归一化）
├── scripts/                           # Python CLI（webnovel.py 统一入口）
├── references/                        # 题材/写法 CSV 与共享参考
├── hooks/                             # 运行护栏（Claude Code 用；Codex 等效手动）
├── dashboard/                         # 只读可视化面板（Python + 预打包前端）
└── README.md                          # 本文档
```

协议：GPL-3.0（与原项目一致）。原项目：https://github.com/lingfengQAQ/webnovel-writer
