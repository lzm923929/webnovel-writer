<!-- 入口：通用（极薄壳 v1.1。Cursor / Windsurf / Claude Code / Codex 均会读取）。权威指令源：README.md。 -->

# Webnovel Writer — 通用入口壳

> **单一权威指令源是 `README.md`**。本壳文件只保留入口声明、环境引导与铁律；
> 命令、子代理、审查标准（§8）、排错、目录结构等全部内容以 `README.md` 为准，本文件不重复维护。
> 开始任何任务前，先读本目录下的 `README.md`。

## 环境引导（每次开新会话先执行）

```bash
export WEBNOVEL_ROOT="$(pwd)"
export WEBNOVEL_WORKSPACE="$(pwd)"
export SCRIPTS_DIR="${WEBNOVEL_ROOT}/scripts"
```

- 斜杠命令不可用（非 Claude Code 环境）时：读取 `skills/<命令>/SKILL.md` 严格按步骤执行。
- 子代理调用：用平台的子任务工具，或读取 `agents/<代理>.md` 后"扮演"该角色；
  **不得由主流程口头替代子代理的真实输出**，也不得伪造审查 JSON。
- 命令清单与子代理清单：见 `README.md` §4 / §5。

## 铁律（必须守住，与 README.md §6 一致）

1. 所有 Story System 写入（合同 / 提交 / 投影）**只能通过** `python "${SCRIPTS_DIR}/webnovel.py"` 的
   `story-system` / `chapter-commit` / `write-gate` / `projections` 子命令完成。
2. **禁止**直接用 Write/Edit/Bash 改写 `.story-system/`（合同与提交）以及 `.webnovel/index.db`、
   `vectors.db`、`memory_scratchpad.json`、`projection_log.jsonl` 等只读视图——运行护栏 hook 会拦截。
3. 写章流程严格按 `skills/webnovel-write/SKILL.md` 的 Step 1→6，不跳步、不并步、不伪造审查。
4. 作者友好：最终回复用固定三段式（总状态 / 产生的文件与完成情况 / 下一步建议），不直接甩原始 JSON、traceback 或长命令日志。
5. **审查不可静默**：reviewer 跳过 / 失败 / 输出不完整 / 正文为空 / 维度跳过 / 耗时异常，必须在最终报告显式汇报，不得隐瞒。
