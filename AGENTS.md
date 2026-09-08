# Repository Rules

## Documentation contract

Any change to user-visible behavior, installation commands, CLI or PowerShell parameters, configuration defaults, model-routing policy, compatibility requirements, or recovery workflow must update `README.md` in the same change.

Before committing, verify that README examples match the implemented commands and options. Do not defer README updates to a later change.

## Validation

For installer changes, run:

```bash
python3 -m unittest discover -v tests
bash -n scripts/*.sh
python3 -m py_compile scripts/install_global.py scripts/repair_config.py
git diff --check
```
