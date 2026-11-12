# Scripts

| File | What it's for |
|---|---|
| `check_clone.py` | Checks this copy is complete, and that no .gitignore rule hides a source file. Runs first in CI |
| `generate_env.py` | Creates `infra/.env` with random secrets, and fills in settings added later |
| `smoke_stack.py` | Checks the running stack end to end, including a real OpenFGA outage |
| `bootstrap_openfga.md` | How the OpenFGA store and model get set up |

The other `.md` files here are stubs for later phases.
