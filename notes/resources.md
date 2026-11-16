# ACE practice – resource ledger

Rule: **write the row (including the delete command) *before* you run the create command.**
Tick "Deleted" only after the delete command succeeded. At the end of every session every row
must be ticked and `bash scripts/ace-leftovers.sh ace-fruit-XXXX` must print `CLEAN`.

**This file is public (pushed to GitHub).** Never write a password, key, token or signed URL here.
Write `***` or point to the file instead, e.g. `--password="$(cat private/fruit-db-pass.txt)"`.

Kept on purpose until the exam: the project itself, the budget, the `billing_export` dataset.

| Date | Week | Resource (type / name / region) | Created with | Delete with | Deleted |
|---|---|---|---|---|---|
| 2026-11-__ | 2 | VM `fruit-vm` (us-central1-a) | `gcloud compute instances create fruit-vm ...` | `gcloud compute instances delete fruit-vm --zone=us-central1-a -q` | [ ] |
|  |  |  |  |  | [ ] |

## Session log

| Date | Teardown run | ace-leftovers.sh result |
|---|---|---|
|  |  |  |
