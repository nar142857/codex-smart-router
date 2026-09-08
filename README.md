# Codex Smart Router v3 — user-selected Root

一套可直接复制/安装到 Codex 的多 Agent 路由配置，目标是：**尽量保持复杂任务质量，同时减少高价模型的无效 token 消耗。**

## 默认拓扑

```text
       Current Codex conversation model root
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
      exceptional high-risk only
```

## 路由原则

- 小任务：root 直接做，不机械启动 subagents。
- Luna：搜索、读代码、研究、测试、非常明确的低风险小改动。
- Root：用户在 Codex 对话框模型选择器中选什么模型，该对话就用什么模型做 Root / Orchestrator；Smart Router 不会覆盖它。
- Terra：承担常规 feature / refactor / bugfix；若用户在对话框选择 Terra，它同时就是该对话的 Root。
- Sol：困难 Bug、算法、并发、性能、复杂集成、独立 Review。
- Astra：只用于认证授权、安全边界、支付、破坏性迁移或极复杂架构等高风险场景的 `deep_reviewer`；不得用于日常搜索、实现、测试、总结或普通 Review。
- 默认最多 4 个 subagent 并发。

## 版本要求

建议使用最新 Codex App / Codex CLI。

- GPT-5.6 在 Codex 至少需要较新的 0.144.x 以上版本。
- GPT-6 Astra 仅在实际需要深度复核时才会被调用，且可能仍处于账户逐步开放阶段。

默认情况下，安装器不会设置或替换 `model`、`model_reasoning_effort`。请直接在 Codex 对话框选择 Root 模型；新对话和当前对话都可独立选择。

如果希望给“未在对话框显式选择模型”的新对话设置默认值，可在安装时传入 `--default-model`。这是默认值，不会覆盖用户在对话框中的选择；对话框选择始终优先。

---

# 方案 A：全局安装（推荐）

一次安装后，所有 Codex 项目都可以使用。

## 一条命令安装（无需 clone 或保留项目目录）

安装器会将 GitHub 归档下载到临时目录，执行全局安装后自动删除临时文件。

### macOS / Linux

```bash
curl -fsSL https://raw.githubusercontent.com/nar142857/codex-smart-router/main/scripts/install-remote.sh | bash
```

### Windows PowerShell

```powershell
irm https://raw.githubusercontent.com/nar142857/codex-smart-router/main/scripts/install-remote.ps1 | iex
```

如需固定某个已审阅的 tag、分支或 commit，可先下载引导脚本后传入 `--ref`（macOS / Linux），或保存脚本后使用 `-Ref`（PowerShell）。默认使用 `main` 的最新版本。

## 可选：设置默认 Root 模型

以下命令只设置 Codex 的默认模型。用户在对话框模型选择器中选择的模型始终优先，并成为当前对话的 Root。

```bash
curl -fsSL https://raw.githubusercontent.com/nar142857/codex-smart-router/main/scripts/install-remote.sh | bash -s -- --default-model gpt-5.6-terra
```

默认推理强度为 `medium`；需要时可明确指定：

```bash
curl -fsSL https://raw.githubusercontent.com/nar142857/codex-smart-router/main/scripts/install-remote.sh | bash -s -- --default-model gpt-5.6-sol --default-reasoning-effort high
```

PowerShell（先保存引导脚本再传入参数）：

```powershell
irm https://raw.githubusercontent.com/nar142857/codex-smart-router/main/scripts/install-remote.ps1 -OutFile install-remote.ps1
.\install-remote.ps1 -DefaultModel gpt-5.6-terra
```

## macOS / Linux

解压后进入目录：

```bash
cd codex-smart-router
chmod +x scripts/install-global.sh
./scripts/install-global.sh
```

可选默认模型：`./scripts/install-global.sh --default-model gpt-5.6-terra`。

安装器会：

- 安装角色到 `~/.codex/agents/`
- 安装 Skill 到 `~/.agents/skills/smart-router/`
- 合并路由规则到 `~/.codex/AGENTS.md`
- 合并 `~/.codex/config.toml` 中的 `[agents]` 设置及 8 个角色注册；不写入 Root 模型
- 保留你其他 config section，例如 MCP server / provider / permissions
- 项目级安装同样采用备份、合并和 TOML 校验，不覆盖项目已有的顶层配置或 AGENTS 规则
- 修改已有文件前自动生成 `.bak-时间戳` 备份

## Windows PowerShell

```powershell
cd codex-smart-router
powershell -ExecutionPolicy Bypass -File .\scripts\install-global.ps1
```

可选默认模型：`powershell -ExecutionPolicy Bypass -File .\scripts\install-global.ps1 -DefaultModel gpt-5.6-terra`。

安装完成后**完全退出并重启 Codex App / CLI**。

> 如果安装后 Codex 报 `expected struct AgentRoleToml in \`agents\``，请运行 `./scripts/repair-global.sh`，详见 [HOTFIX.md](HOTFIX.md)。

---

# 方案 B：项目级安装

适合只想让某一个 repo 使用这套架构。

## macOS / Linux

```bash
./scripts/install-project.sh /path/to/your/repo
```

## Windows PowerShell

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\install-project.ps1 -Target "D:\Projects\MyApp"
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

远程引导安装只支持全局安装；项目级安装仍需传入目标项目路径。

---

# 怎么使用

## 1. 普通使用：让 Codex 自动判断

直接正常下任务即可：

```text
实现完整的用户登录和会话管理，并补齐测试。
```

全局规则会要求 Codex：

```text
当前对话选中模型 -> Root / 规划 / 决策 / 整合
简单任务 -> 不分流
常规实现 -> Terra
搜索/测试 -> Luna
难点 -> Sol
极高风险深度复核 -> Astra
```

## 2. 显式调用路由 Skill

复杂任务建议直接写：

```text
$smart-router

实现完整的支付退款功能。
先分析现有支付调用链，再制定实现边界。
常规实现用 Terra，测试用 Luna；
只有真正困难的实现才升级 Sol；极高风险时才启用 Astra deep review。
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

# Root 模型选择

在 Codex 对话框的模型选择器中选择模型，即可决定该对话的 Root。模型选择只影响 Root；Smart Router 的子代理映射保持不变：Luna 用于探索/研究/测试，Terra 用于常规实现，Sol 用于困难任务和重要 Review，Astra 仅用于极高风险 deep review。

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
    ├── install-remote.sh
    ├── install-remote.ps1
    ├── install-project.sh
    └── install-project.ps1
```
