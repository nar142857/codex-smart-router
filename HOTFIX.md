# HOTFIX: 全局安装器把顶层配置移到了 `[agents]` 之后

## 现象

运行 `scripts/install-global.sh` / `install-global.ps1` 之后，Codex 启动报错：

```text
invalid configuration: invalid type: string "never",
expected struct AgentRoleToml in `agents`
```

## 原因

旧版 `scripts/install_global.py` 合并 `~/.codex/config.toml` 时，先写入 Smart Router
的管理块（`model` / `model_reasoning_effort` / `[agents]`），再把用户原有内容整段追加在后面。
用户原本位于 TOML 顶层的键，例如：

```toml
approval_policy = "never"
sandbox_mode = "danger-full-access"
```

就被排到了 `[agents]` 表之后，按 TOML 语义变成了 `agents.approval_policy`，
Codex 因此把 `"never"` 当成一个 agent role 去解析而失败。

## 修复内容

- `scripts/install_global.py`
  - 用户原有的顶层键始终保留在任何 TOML table 之前；
  - 只替换 `model`、`model_reasoning_effort` 和裸 `[agents]` 表的内容，
    `[agents]` 只写入 `enabled` / `max_concurrent_threads_per_session` /
    `default_subagent_model` / `default_subagent_reasoning_effort`；
  - `approval_policy`、`sandbox_mode`、provider、MCP servers、`projects` / `trust_level`、
    `[agents.*]` 子表以及其它非 Smart Router 配置全部原样保留；
  - 写文件之前用 TOML parser 解析生成结果并校验用户配置无丢失，校验失败则不写入。
- 新增 `scripts/repair_config.py` 与 `scripts/repair-global.sh`，用于修复已经损坏的配置。
- 新增 `tests/test_install_global.py` smoke test。

## 如何修复已损坏的配置

```bash
cd codex-smart-router
chmod +x scripts/repair-global.sh
./scripts/repair-global.sh          # 自动沿用当前 root model
./scripts/repair-global.sh terra    # 或显式指定 terra / sol
```

修复脚本会：

1. 把当前损坏的 config 备份为 `~/.codex/config.toml.broken-<时间戳>`；
2. 自动寻找安装前的干净备份 `~/.codex/config.toml.bak-<时间戳>`
   （合法 TOML 且未被 Smart Router 写过）；
3. 从该备份恢复用户原始配置；
4. 用修复后的合并逻辑重新写入 Smart Router 设置。

如果找不到干净备份，脚本会把误入 `[agents]` 的非 Smart Router 键提升回顶层，并给出警告。
也可以用 `--backup <path>` 手动指定备份，或用 `--dry-run` 先预览结果：

```bash
python3 scripts/repair_config.py --dry-run
python3 scripts/repair_config.py --backup ~/.codex/config.toml.bak-20260907-174228
```

修复后请完全退出并重启 Codex App / CLI。

## 测试

```bash
python3 -m unittest discover -v tests
```
