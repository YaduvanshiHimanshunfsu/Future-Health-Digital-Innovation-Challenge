# Core

Config, authentication, middleware, logging, errors, rate limits, i18n.

**Rules:** Secure by default. No PHI in logs or errors.

**Status:** built and tested.

## Files

| File | Purpose | Phase | Issues |
|---|---|---|---|
| `config.py` | Typed settings. | 1.4 | M12 |
| `errors.py` | Error handling. | 1.4 |  |
| `i18n.py` | Localisation. | 1.4 |  |
| `logging.py` | PHI-safe logging. | 1.4 |  |
| `middleware.py` | HTTP hardening. | 1.4 | M12 |
| `rate_limit.py` | Abuse prevention. | 1.4 |  |
| `security.py` | Authentication. | 1.4 |  |
