"""Not needed. Case queries live in `app/api/v1/cases.py` and `app/triage/service.py`.

Only `genetic.py` became a repository, because loading a result means decrypting several rows with
their own associated data, and that logic shouldn't sit in a route. A plain SQLAlchemy select
doesn't need a wrapper to hide it.
"""
