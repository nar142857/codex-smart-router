#!/usr/bin/env python3
from pathlib import Path
import argparse, datetime, re, shutil

HERE = Path(__file__).resolve().parent
BUNDLE = HERE.parent
SRC_GLOBAL = BUNDLE / "global"

def backup(path: Path):
    if not path.exists():
        return None
    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    dst = path.with_name(path.name + f".bak-{stamp}")
    shutil.copy2(path, dst)
    return dst

def replace_top_level_and_agents(existing: str, root_model: str) -> str:
    lines = existing.splitlines()
    out = []
    section = None
    skip_agents_body = False
    section_re = re.compile(r"^\s*\[([^\]]+)\]\s*(?:#.*)?$")
    top_key_re = re.compile(r"^\s*(model|model_reasoning_effort)\s*=")

    for line in lines:
        m = section_re.match(line)
        if m:
            sec = m.group(1).strip()
            if sec == "agents":
                section = sec
                skip_agents_body = True
                continue
            section = sec
            skip_agents_body = False
            out.append(line)
            continue
        if skip_agents_body:
            continue
        if section is None and top_key_re.match(line):
            continue
        out.append(line)

    effort = "low" if root_model == "gpt-6-astra" else "medium"
    header = (
        "# --- Smart Router managed block ---\n"
        f'model = "{root_model}"\n'
        f'model_reasoning_effort = "{effort}"\n\n'
        "[agents]\n"
        "enabled = true\n"
        "max_concurrent_threads_per_session = 4\n"
        'default_subagent_model = "gpt-5.6-luna"\n'
        'default_subagent_reasoning_effort = "medium"\n'
        "# --- End Smart Router managed block ---\n"
    )
    tail = "\n".join(out).strip()
    return header + ("\n\n" + tail + "\n" if tail else "\n")

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
    p.add_argument("--root", choices=["astra", "sol"], default="astra")
    p.add_argument("--home", default=str(Path.home()))
    args = p.parse_args()

    home = Path(args.home).expanduser().resolve()
    codex = home / ".codex"
    agents_dir = codex / "agents"
    skills_dir = home / ".agents" / "skills"
    agents_dir.mkdir(parents=True, exist_ok=True)
    skills_dir.mkdir(parents=True, exist_ok=True)

    for src in (SRC_GLOBAL / ".codex" / "agents").glob("*.toml"):
        dst = agents_dir / src.name
        if dst.exists(): backup(dst)
        shutil.copy2(src, dst)

    src_skill = SRC_GLOBAL / ".agents" / "skills" / "smart-router"
    dst_skill = skills_dir / "smart-router"
    if dst_skill.exists():
        stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
        shutil.move(str(dst_skill), str(dst_skill.with_name(dst_skill.name + f".bak-{stamp}")))
    shutil.copytree(src_skill, dst_skill)

    cfg = codex / "config.toml"
    existing = cfg.read_text(encoding="utf-8") if cfg.exists() else ""
    if cfg.exists(): backup(cfg)
    root_model = "gpt-6-astra" if args.root == "astra" else "gpt-5.6-sol"
    cfg.write_text(replace_top_level_and_agents(existing, root_model), encoding="utf-8")

    global_agents = codex / "AGENTS.md"
    existing_agents = global_agents.read_text(encoding="utf-8") if global_agents.exists() else ""
    if global_agents.exists(): backup(global_agents)
    block = (SRC_GLOBAL / ".codex" / "AGENTS.md").read_text(encoding="utf-8")
    global_agents.write_text(merge_agents_md(existing_agents, block), encoding="utf-8")

    print("Installed Codex Smart Router")
    print(f"Root model: {root_model}")
    print(f"Config: {cfg}")
    print(f"Agents: {agents_dir}")
    print(f"Skill: {dst_skill}")
    print(f"Global instructions: {global_agents}")
    print("Restart Codex after installation.")

if __name__ == "__main__":
    main()
