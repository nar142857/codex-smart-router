# Codex Smart Router v3 — user-selected Root

一套可直接复制/安装到 Codex 的多 Agent 路由配置，目标是：**尽量保持复杂任务质量，同时减少高价模型的无效 token 消耗。**

## 角色映射

```text
Current conversation model -> Root (engineering decisions and non-UI work)

Engineering roles are optional; UI execution must be delegated:
Luna  -> explorer / researcher / tester / fast_worker
Terra -> worker
gpt-6.1-terra -> browser_operator (all computer/browser UI execution required)
Sol   -> expert / reviewer
Astra -> deep_reviewer (exceptional high-risk review only)
```

这张图是委派发生时的角色映射，不是固定拓扑或执行流水线。电脑和浏览器 UI 操作必须委派；其它研发工作由 Root 判断是否存在独立、边界清楚且值得委派的子任务，没有则直接完成。

## 路由原则

- Root：用户在 Codex 对话框模型选择器中选什么模型，该对话就用什么模型做 Root；包括 Astra 在内的 Root 都可以直接完成分析、实现、测试、Review 和整合。
- 对于非 UI 研发工作，只委派边界清楚、可独立交付且工作量足以覆盖上下文传递、协调和整合成本的子任务。非 UI 小任务、顺序依赖强或紧密耦合的工作由 Root 完成。
- 不要求固定代理数量，也不要求 explorer → worker → tester → reviewer 的角色流水线。运行时并发上限只是容量限制，不是启动目标。
- 委派发生时，优先用 Luna 做聚焦搜索、研究、验证和明确的小改动；Terra 做常规实现；Sol 做困难实现或有必要的独立 Review。
- 所有需要操作电脑或浏览器 UI 的任务，都必须委派给 `browser_operator`（`gpt-6.1-terra`）子代理执行，包括原生应用、截图、点击、输入、滚动、页面导航、表单和 UI 验证。简单、顺序依赖强或紧密耦合的 UI 步骤也不例外；Root 即使用相同模型，也不能直接执行 UI 操作。
- 混合任务由 Root 保留研发判断，将全部 UI 执行交给 Terra 子代理；复杂研发分析、实现和 Review 保留原路由，`worker` 等现有角色模型不变。无需操作 UI 的 Shell 命令、代码编辑、API 和连接器调用仍按原路由处理，适用时优先使用专用工具。
- 若该角色、模型、UI 工具或并发名额不可用，报告阻塞并等待或请用户决定；Root 不接管 UI，也不擅自替换模型。UI 强制委派优先于一般的委派成本判断。
- 额外的 Astra subagent 只用于失败代价很高的独立深度复核；这项限制不影响 Astra 作为 Root 正常工作。

## 版本要求

建议使用最新 Codex App / Codex CLI。

- GPT-5.6 在 Codex 至少需要较新的 0.144.x 以上版本。
- 额外的 GPT-6 Astra subagent 仅在实际需要高风险深度复核时才会被调用；用户选择 Astra 作为 Root 时不受此限制。

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
- 新增 `~/.codex/smart-router.toml`，默认在任务结束时显示 root 与各 subagent 的 token 用量快照
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

## 任务结束时的 Token 用量报告

安装后默认开启，但不会为普通单 Agent 任务额外输出。只有本轮实际使用 `$smart-router` 进行路由，或产生过有用量记录的 subagent 时，Root 才会在最终回复中附加本次 root turn 的快照，分别列出 root 和每个实际运行过的 subagent 的输入、缓存输入、缓存命中率、输出及总 token。子代理名称取自会话元数据中的实际角色（例如 `explorer`、`tester`），不会因为 `turn_context.task_path` 缺失而错误显示为 `root`。

报告还会显示两类估算：`估算 Credits` 是按模型 token 费率换算的 Codex credit 参考值，`任务占比` 是该 agent 占本任务估算 credits 的比例。`预算占比` 需要你显式设置一个预算分母才会显示；它不是账户剩余额度，因为本地会话日志不含套餐上限或实时余额。`估算 API 费用` 是按 OpenAI 公开 API 单价计算的美元等价值，仅用于比较，不是订阅或 Codex 的账单。费率在包内固定为 2026-09-08 的参考值，未知模型显示 `N/A`。由于快照生成在最终回复之前，最终回复本身消耗的 token 不包含在该表中；缓存输入已包含在输入 token 内。

如果希望用你的内部额度预算查看“预算占比”，在全局 `~/.codex/smart-router.toml` 或项目 `.codex/smart-router.toml` 中增加正数（项目级优先）：

```toml
quota_budget_credits = 1000
```

全局关闭：编辑 `~/.codex/smart-router.toml`。关闭后，即使使用 Smart Router 或 subagent 也不输出报告：

```toml
token_usage_report = false
```

项目级关闭：在项目根目录创建或编辑 `.codex/smart-router.toml`，写入相同设置。项目设置优先于全局设置。重新设为 `true` 或删除该行即可恢复；没有配置文件时默认开启。

需要手动查看当前任务快照时，运行已安装 Smart Router skill 中的 `scripts/token_report.py`。项目级安装时该文件位于 `.agents/skills/smart-router/scripts/token_report.py`。

## 1. 普通使用：让 Codex 自动判断

直接正常下任务即可：

```text
实现完整的用户登录和会话管理，并补齐测试。
```

全局规则会要求 Codex：

```text
当前对话选中模型 -> Root / 规划 / 决策 / 整合
Root 可以直接完成非 UI 工作
电脑和浏览器 UI 操作一律委派给 GPT-6.1 Terra 子代理
其它研发工作仅当子任务独立、边界清楚且工作量足够时委派
委派的聚焦搜索/验证 -> Luna
必须委派的电脑和浏览器 UI 执行 -> browser_operator / gpt-6.1-terra
委派的常规实现 -> Terra
委派的困难实现或重要 Review -> Sol
额外的极高风险深度复核 -> Astra
```

## 2. 显式调用路由 Skill

复杂任务建议直接写：

```text
$smart-router

实现完整的支付退款功能。
由 Root 先确认边界并推进；电脑和浏览器 UI 操作一律交给 GPT-6.1 Terra 子代理执行。
其它研发工作只有存在可独立交付、工作量足够的子任务时才委派。
不要固定代理数量，也不要套用角色流水线。
需要委派时，根据实际难度选择 Luna、Terra 或 Sol；仅在失败代价很高且独立复核有明显价值时使用额外的 Astra deep reviewer。
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

检查当前仓库中三个互不依赖的模块，分别返回入口、关键依赖和现有测试；不要修改文件。
这三个只读结果可以并行获取，Root 最后合并结论。
```

这个示例专门验证独立任务的并行能力，不代表日常任务需要启动三个 subagent。

---

# Agent 列表

| Agent | 模型 | 权限 | 用途 |
|---|---|---|---|
| `explorer` | Luna | read-only | 搜索代码、调用链、依赖、测试 |
| `researcher` | Luna | read-only | API / 框架 / 文档研究 |
| `tester` | Luna | workspace-write | 测试、lint、typecheck、build |
| `fast_worker` | Luna | workspace-write | 非常明确的低风险小改动 |
| `worker` | Terra | workspace-write | 委派的常规实现 |
| `browser_operator` | `gpt-6.1-terra` | workspace-write | 所有电脑和浏览器 UI 操作（强制委派） |
| `expert` | Sol | workspace-write | 困难实现、Debug、算法/并发/性能 |
| `reviewer` | Sol | read-only | 独立代码 Review |
| `deep_reviewer` | Astra | read-only | 仅失败代价很高的独立复核 |

---

# Root 模型选择

在 Codex 对话框的模型选择器中选择模型，即可决定该对话的 Root。Root 可以直接完成非 UI 工作，电脑和浏览器 UI 操作必须交给 GPT-6.1 Terra 子代理执行；Smart Router 不会因为 Root 是 Astra 就把日常工作机械地委派出去。只有委派本身值得时，才按 Luna、Terra、Sol 和 Astra 的角色映射选择 subagent。

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
│   │       ├── browser_operator.toml
│   │       ├── expert.toml
│   │       ├── reviewer.toml
│   │       └── deep_reviewer.toml
│   └── .agents/
│       └── skills/
│           └── smart-router/
│               ├── SKILL.md
│               └── scripts/token_report.py
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
    ├── install-project.ps1
    ├── repair-global.sh
    └── repair_config.py
```

每次 push 和 pull request 都会在 GitHub Actions 中执行单元测试、Shell 语法、Python 编译和 diff 格式检查。
