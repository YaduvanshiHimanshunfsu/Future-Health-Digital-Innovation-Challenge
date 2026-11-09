"""The centre finder reads the active country pack's `services.yaml` directly, in
`app/api/v1/centres.py`: each entry carries its public source and the date it was checked.

The `centre` table (`app/models/centre.py`) is kept for a later import from a public directory,
when a pack's list is too large to keep in YAML. Until then nothing writes to it, and nothing here
invents an entry: an empty list is shown as empty.
"""
