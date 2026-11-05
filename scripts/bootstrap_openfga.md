# Bootstrap OpenFGA

The stack does this for you. The `openfga-bootstrap` service in `infra/docker-compose.yml` runs before the API starts, and it can run on every start.

**What it does:** `python -m app.ops.bootstrap_openfga` creates the store named by `OPENFGA_STORE_NAME` if it's missing, and loads `backend/app/privacy/authz_model.json` if the newest stored model differs. The API finds the store and newest model by name, so no IDs need copying into `.env`.

**Access:** OpenFGA requires the preshared key `OPENFGA_PRESHARED_KEY`. If you created `infra/.env` before this setting existed, run `python scripts/generate_env.py` again. It fills in missing settings and never changes existing ones.

**Changing the model:** edit both `infra/openfga/model.fga` (for reading) and `authz_model.json` (what gets loaded). A test compares their relations. To compare them fully:

```bash
docker run --rm -v "$PWD/infra/openfga:/m:ro" openfga/cli model transform --file /m/model.fga --output-format json
```

**Background jobs:** beat runs `samvid.apply_authz_outbox` every 30 s and `samvid.reconcile_authz` every 15 minutes.
