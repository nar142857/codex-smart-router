# Codex Smart Router — Astra / Sol / Terra / Luna

一套可直接复制/安装到 Codex 的多 Agent 路由配置，目标是：**尽量保持复杂任务质量，同时减少高价模型的无效 token 消耗。**

## 默认拓扑

```text
                 GPT-6 Astra root
             plan / decide / integrate
                      |
        +-------------+-------------+
        |             |             |
      Luna          Terra           Sol
  cheap tasks      normal work    hard work
        |             |             |
 explorer          worker         expert
 researcher                       reviewer
 tester
 fast_worker
                      |
             Astra deep_reviewer
              only high-risk
```

## 路由原则

- 小任务：root 直接做，不机械启动 subagents。
- Luna：搜索、读代码、研究、测试、非常明确的低风险小改动。
- Terra：默认实现模型，承担常规 feature / refactor / bugfix。
- Sol：困难 Bug、算法、并发、性能、复杂集成、独立 Review。
- Astra：主要作为根 Agent 做理解、拆解、架构判断、最终整合；只有非常高风险任务才再启用 Astra `deep_reviewer`。
- 默认最多 4 个 subagent 并发。

## 版本要求

建议使用最新 Codex App / Codex CLI。

- GPT-5.6 在 Codex 至少需要较新的 0.144.x 以上版本。
- GPT-6 Astra 需要 Codex CLI 0.153.0 或更新版本，并且 Astra 仍可能处于账户逐步开放阶段。

如果 Astra 在你的 Codex 账户暂不可用，使用 `sol` 根模型即可，其他路由逻辑不变。

---

# 方案 A：全局安装（推荐）

一次安装后，所有 Codex 项目都可以使用。

## macOS / Linux

解压后进入目录：

```bash
cd codex-smart-router
chmod +x scripts/install-global.sh
./scripts/install-global.sh astra
```

如果 Astra 暂不可用：

```bash
./scripts/install-global.sh sol
```

安装器会：

- 安装角色到 `~/.codex/agents/`
- 安装 Skill 到 `~/.agents/skills/smart-router/`
- 合并路由规则到 `~/.codex/AGENTS.md`
- 合并 `~/.codex/config.toml` 中的 root model 和 `[agents]` 设置
- 保留你其他 config section，例如 MCP server / provider / permissions
- 修改已有文件前自动生成 `.bak-时间戳` 备份

## Windows PowerShell

```powershell
cd codex-smart-router
powershell -ExecutionPolicy Bypass -File .\scripts\install-global.ps1 -Root astra
```

Astra 暂不可用：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\install-global.ps1 -Root sol
```

安装完成后**完全退出并重启 Codex App / CLI**。

> 如果安装后 Codex 报 `expected struct AgentRoleToml in \`agents\``，请运行 `./scripts/repair-global.sh`，详见 [HOTFIX.md](HOTFIX.md)。

---

# 方案 B：项目级安装

适合只想让某一个 repo 使用这套架构。

## macOS / Linux

```bash
./scripts/install-project.sh /path/to/your/repo astra
```

Astra 暂不可用：

```bash
./scripts/install-project.sh /path/to/your/repo sol
```

## Windows PowerShell

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\install-project.ps1 -Target "D:\Projects\MyApp" -Root astra
```

项目最终会包含：

```text
repo/
├── .codex/
│   ├── config.toml
│   └── agents/
├── .agents/
│   └── skills/
│       └── smart-router/
│           └── SKILL.md
└── AGENTS.md
```

---

# 怎么使用

## 1. 普通使用：让 Codex 自动判断

直接正常下任务即可：

```text
实现完整的用户登录和会话管理，并补齐测试。
```

全局规则会要求 Codex：

```text
简单任务 -> 不分流
常规实现 -> Terra
搜索/测试 -> Luna
难点 -> Sol
高风险判断/最终整合 -> Astra
```

## 2. 显式调用路由 Skill

复杂任务建议直接写：

```text
$smart-router

实现完整的支付退款功能。
先分析现有支付调用链，再制定实现边界。
常规实现用 Terra，测试用 Luna；
只有困难或高风险部分才升级 Sol/Astra。
```

## 3. Smoke Test

安装后先运行这个只读任务：

```text
$smart-router

只分析，不修改代码。
并行找出：
1. 应用入口
2. 数据访问层
3. 测试入口

最后只返回关键文件、调用关系和风险。
```

然后再测试实现：

```text
$smart-router

实现一个中等复杂度功能。
先探索现有路径；常规实现使用 Terra；
验证使用 Luna；只有遇到真正难点才升级 Sol。
```

---

# Agent 列表

| Agent | 模型 | 权限 | 用途 |
|---|---|---|---|
| `explorer` | Luna | read-only | 搜索代码、调用链、依赖、测试 |
| `researcher` | Luna | read-only | API / 框架 / 文档研究 |
| `tester` | Luna | workspace-write | 测试、lint、typecheck、build |
| `fast_worker` | Luna | workspace-write | 非常明确的低风险小改动 |
| `worker` | Terra | workspace-write | 默认常规实现 |
| `expert` | Sol | workspace-write | 困难实现、Debug、算法/并发/性能 |
| `reviewer` | Sol | read-only | 独立代码 Review |
| `deep_reviewer` | Astra | read-only | 仅极高风险最终复核 |

---

# Astra 暂不可用

使用：

```text
fallbacks/config-root-sol.toml
```

或者重新运行：

```bash
./scripts/install-global.sh sol
```

这会变成：

```text
Sol root
  -> Luna search/test
  -> Terra normal implementation
  -> Sol hard work/review
```

依然可以正常工作，只是没有 Astra 总控。

---

# Luna subagent 启动失败

如果出现类似：

```text
Unknown model gpt-5.6-luna for spawn_agent
```

或 subagent Luna 返回 404：

1. 先更新 Codex App / CLI 到最新版并重启。
2. 如果 Luna 主线程可用但 subagent 仍不可用，阅读：

```text
fallbacks/luna-to-terra.md
```

临时把 Luna 角色替换成 Terra。

---

# 注意：Codex App Custom Instructions

Codex 的全局 instructions 会使用 `~/.codex/AGENTS.md`。
某些 Codex App 版本中，在 Settings → Personalization 保存 Custom Instructions 可能重写这个文件。
本安装器会在修改前自动备份，但安装后仍建议确认 `~/.codex/AGENTS.md` 中的 `SMART-ROUTER` 区块没有被覆盖。

---

# 包内文件

```text
codex-smart-router/
├── README.md
├── global/
│   ├── .codex/
│   │   ├── config.toml
│   │   ├── AGENTS.md
│   │   └── agents/
│   │       ├── explorer.toml
│   │       ├── researcher.toml
│   │       ├── tester.toml
│   │       ├── fast_worker.toml
│   │       ├── worker.toml
│   │       ├── expert.toml
│   │       ├── reviewer.toml
│   │       └── deep_reviewer.toml
│   └── .agents/
│       └── skills/
│           └── smart-router/
│               └── SKILL.md
├── project-template/
│   └── AGENTS.md
├── fallbacks/
│   ├── config-root-sol.toml
│   └── luna-to-terra.md
└── scripts/
    ├── install_global.py
    ├── install-global.sh
    ├── install-global.ps1
    ├── install-project.sh
    └── install-project.ps1
```
