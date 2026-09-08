#!/usr/bin/env python3
from pathlib import Path
import argparse, datetime, re, shutil, sys

try:
    import tomllib as _toml
except ModuleNotFoundError:  # Python < 3.11
    try:
        import tomli as _toml
    except ModuleNotFoundError:
        _toml = None

HERE = Path(__file__).resolve().parent
BUNDLE = HERE.parent
SRC_GLOBAL = BUNDLE / "global"

MANAGED_START = "# --- Smart Router managed block ---"
MANAGED_END = "# --- End Smart Router managed block ---"
MANAGED_AGENTS = {
    "enabled": True,
    "max_concurrent_threads_per_session": 4,
    "default_subagent_model": "gpt-5.6-luna",
    "default_subagent_reasoning_effort": "medium",
}
MANAGED_AGENT_ROLE_CONFIGS = {
    "explorer": "agents/explorer.toml",
    "researcher": "agents/researcher.toml",
    "tester": "agents/tester.toml",
    "fast_worker": "agents/fast_worker.toml",
    "worker": "agents/worker.toml",
    "expert": "agents/expert.toml",
    "reviewer": "agents/reviewer.toml",
    "deep_reviewer": "agents/deep_reviewer.toml",
}

SECTION_RE = re.compile(r"^\s*\[\[?([^\]]+)\]\]?\s*(?:#.*)?$")
ROOT_KEY_RE = re.compile(r"^\s*(model|model_reasoning_effort)\s*=")
MODEL_RE = re.compile(r"^[A-Za-z0-9._:-]+$")


def unique_backup_path(path: Path, suffix: str = "bak") -> Path:
    """Return a non-existing, timestamped sibling backup path.

    Seconds alone are not unique: an installer can back up several files or be
    run twice in the same second.  Keep the timestamp readable and add an
    incrementing suffix only when necessary.
    """
    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    candidate = path.with_name(path.name + f".{suffix}-{stamp}")
    number = 1
    while candidate.exists():
        candidate = path.with_name(path.name + f".{suffix}-{stamp}-{number}")
        number += 1
    return candidate


def backup(path: Path):
    if not path.exists():
        return None
    dst = unique_backup_path(path)
    shutil.copy2(path, dst)
    return dst


def parse_toml(text: str):
    """Return the parsed TOML document, or raise if no parser is available."""
    if _toml is None:
        raise RuntimeError("No TOML parser available (need Python >= 3.11 or the 'tomli' package)")
    return _toml.loads(text)


def managed_block() -> str:
    lines = [
        MANAGED_START,
        "[agents]",
    ]
    for k, v in MANAGED_AGENTS.items():
        if isinstance(v, bool):
            lines.append(f"{k} = {'true' if v else 'false'}")
        elif isinstance(v, int):
            lines.append(f"{k} = {v}")
        else:
            lines.append(f'{k} = "{v}"')
    for role, config_file in MANAGED_AGENT_ROLE_CONFIGS.items():
        lines.extend(["", f"[agents.{role}]", f'config_file = "{config_file}"'])
    lines.append(MANAGED_END)
    return "\n".join(lines)


def _strip_blank_edges(lines):
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()
    return lines


def merge_config(existing: str, default_model: str | None = None,
                 default_reasoning_effort: str | None = None) -> str:
    """Merge the Smart Router settings into an existing Codex config.toml.

    Layout of the result:
      1. the user's original top-level keys (everything before the first table),
         including their selected/default root model settings unless an explicit
         `default_model` override was requested
      2. the Smart Router managed block (`[agents]` table only)
      3. every other table from the original file, in original order

    The bare `[agents]` table and the eight Smart Router role-registration
    subtables are replaced. Other user-defined `[agents.*]` subtables and all
    unrelated tables are preserved verbatim.
    """
    top = []
    rest = []
    section = None
    skip_agents_body = False

    for line in existing.splitlines():
        if line.strip() in (MANAGED_START, MANAGED_END):
            continue
        m = SECTION_RE.match(line)
        if m:
            section = m.group(1).strip()
            skip_agents_body = section == "agents" or section in {
                f"agents.{role}" for role in MANAGED_AGENT_ROLE_CONFIGS
            }
            if not skip_agents_body:
                rest.append(line)
            continue
        if section is None:
            if default_model is not None and ROOT_KEY_RE.match(line):
                continue
            top.append(line)
            continue
        if skip_agents_body:
            continue
        rest.append(line)

    top = _strip_blank_edges(top)
    rest = _strip_blank_edges(rest)

    parts = []
    if default_model is not None:
        parts.append("\n".join([
            f'model = "{default_model}"',
            f'model_reasoning_effort = "{default_reasoning_effort}"',
        ]))
    if top:
        parts.append("\n".join(top))
    parts.append(managed_block())
    if rest:
        parts.append("\n".join(rest))
    return "\n\n".join(parts) + "\n"


# Backwards-compatible alias for the old function name.
replace_top_level_and_agents = merge_config


def validate_merged(existing: str, merged: str, default_model: str | None = None,
                    default_reasoning_effort: str | None = None) -> dict:
    """Parse the merged config and check that nothing the user had was lost."""
    doc = parse_toml(merged)

    agents = doc.get("agents")
    if not isinstance(agents, dict):
        raise ValueError("merged config has no [agents] table")
    for k, v in MANAGED_AGENTS.items():
        if agents.get(k) != v:
            raise ValueError(f"merged config: agents.{k} = {agents.get(k)!r}, expected {v!r}")
    if default_model is not None:
        if doc.get("model") != default_model:
            raise ValueError(f"merged config: model = {doc.get('model')!r}, expected {default_model!r}")
        if doc.get("model_reasoning_effort") != default_reasoning_effort:
            raise ValueError("merged config did not set the requested default reasoning effort")
    try:
        original = parse_toml(existing) if existing.strip() else {}
    except Exception:
        # The original was not valid TOML (e.g. a previously broken install);
        # we can only validate the output itself in that case.
        return doc

    for key, value in original.items():
        if default_model is not None and key in {"model", "model_reasoning_effort"}:
            continue
        if key == "agents":
            # user sub-tables under agents must survive, scalar keys are managed
            for sub_k, sub_v in value.items() if isinstance(value, dict) else []:
                if sub_k in MANAGED_AGENT_ROLE_CONFIGS:
                    expected = {"config_file": MANAGED_AGENT_ROLE_CONFIGS[sub_k]}
                    if agents.get(sub_k) != expected:
                        raise ValueError(f"merged config: agents.{sub_k} registration is invalid")
                    continue
                if isinstance(sub_v, dict) and agents.get(sub_k) != sub_v:
                    raise ValueError(f"merged config lost agents.{sub_k}")
            continue
        if key not in doc:
            raise ValueError(f"merged config lost top-level key {key!r}")
        if doc[key] != value:
            raise ValueError(f"merged config changed key {key!r}")
        if key in agents:
            raise ValueError(f"top-level key {key!r} leaked into [agents]")
    return doc


def merge_and_validate(existing: str, default_model: str | None = None,
                       default_reasoning_effort: str | None = None) -> str:
    merged = merge_config(existing, default_model, default_reasoning_effort)
    validate_merged(existing, merged, default_model, default_reasoning_effort)
    return merged


def merge_agents_md(existing: str, block: str) -> str:
    start = "<!-- SMART-ROUTER:START -->"
    end = "<!-- SMART-ROUTER:END -->"
    managed = f"{start}\n{block.strip()}\n{end}"
    pattern = re.compile(re.escape(start) + r".*?" + re.escape(end), re.S)
    if pattern.search(existing):
        return pattern.sub(managed, existing)
    if existing.strip():
        return existing.rstrip() + "\n\n" + managed + "\n"
    return managed + "\n"


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--default-model", help="optional global default model; the conversation model picker still wins")
    p.add_argument("--default-reasoning-effort", choices=["low", "medium", "high", "xhigh", "max", "ultra"],
                   help="optional default reasoning effort; defaults to medium when --default-model is set")
    p.add_argument("--home", default=str(Path.home()))
    p.add_argument("--codex-dir", help="override the Codex directory; enables safe project-scoped installation")
    p.add_argument("--skills-dir", help="override the skills directory; defaults to <home>/.agents/skills")
    p.add_argument("--agents-md", help="override the AGENTS.md path; defaults to <codex-dir>/AGENTS.md")
    args = p.parse_args()
    if args.default_reasoning_effort and not args.default_model:
        p.error("--default-reasoning-effort requires --default-model")
    if args.default_model and not MODEL_RE.fullmatch(args.default_model):
        p.error("--default-model must contain only letters, numbers, dots, underscores, colons, or hyphens")
    default_effort = "medium" if args.default_model and not args.default_reasoning_effort else args.default_reasoning_effort

    home = Path(args.home).expanduser().resolve()
    codex = Path(args.codex_dir).expanduser().resolve() if args.codex_dir else home / ".codex"
    agents_dir = codex / "agents"
    skills_dir = (Path(args.skills_dir).expanduser().resolve()
                  if args.skills_dir else home / ".agents" / "skills")
    # Validate the config merge before creating target directories or changing files.
    cfg = codex / "config.toml"
    existing = cfg.read_text(encoding="utf-8") if cfg.exists() else ""
    try:
        merged = merge_and_validate(existing, args.default_model, default_effort)
    except Exception as e:
        print(f"ERROR: refusing to write {cfg}: {e}", file=sys.stderr)
        sys.exit(1)

    agents_dir.mkdir(parents=True, exist_ok=True)
    skills_dir.mkdir(parents=True, exist_ok=True)

    for src in (SRC_GLOBAL / ".codex" / "agents").glob("*.toml"):
        dst = agents_dir / src.name
        if dst.exists(): backup(dst)
        shutil.copy2(src, dst)

    src_skill = SRC_GLOBAL / ".agents" / "skills" / "smart-router"
    dst_skill = skills_dir / "smart-router"
    if dst_skill.exists():
        backups_dir = skills_dir.parent / "skills-backups"
        backups_dir.mkdir(parents=True, exist_ok=True)
        skill_backup = unique_backup_path(backups_dir / "smart-router")
        shutil.move(str(dst_skill), str(skill_backup))
    shutil.copytree(src_skill, dst_skill)

    settings = codex / "smart-router.toml"
    if not settings.exists():
        shutil.copy2(SRC_GLOBAL / ".codex" / "smart-router.toml", settings)

    if cfg.exists(): backup(cfg)
    cfg.write_text(merged, encoding="utf-8")

    global_agents = (Path(args.agents_md).expanduser().resolve()
                     if args.agents_md else codex / "AGENTS.md")
    existing_agents = global_agents.read_text(encoding="utf-8") if global_agents.exists() else ""
    if global_agents.exists(): backup(global_agents)
    block = (SRC_GLOBAL / ".codex" / "AGENTS.md").read_text(encoding="utf-8")
    global_agents.write_text(merge_agents_md(existing_agents, block), encoding="utf-8")

    print("Installed Codex Smart Router")
    if args.default_model:
        print(f"Default model: {args.default_model} / {default_effort} (conversation model picker has priority)")
    else:
        print("Root model: inherited from the Codex conversation model picker")
    print(f"Config: {cfg}")
    print(f"Agents: {agents_dir}")
    print(f"Skill: {dst_skill}")
    print(f"Global instructions: {global_agents}")
    print(f"Token report setting: {settings}")
    print("Restart Codex after installation.")

if __name__ == "__main__":
    main()
