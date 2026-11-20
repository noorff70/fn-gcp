# ACE practice – resource ledger

Rule: **write the row (including the delete command) *before* you run the create command.**
Tick "Deleted" only after the delete command succeeded. At the end of every session every row
must be ticked and `bash scripts/ace-leftovers.sh fn-fruits` must print `CLEAN`.

**This file is public (pushed to GitHub).** Never write a password, key, token or signed URL here.
Write `***` or point to the file instead, e.g. `--password="$(cat private/fruit-db-pass.txt)"`.

Kept on purpose until the exam: the project itself, the budget, the `billing_export` dataset.

| Date | Week | Resource (type / name / region) | Created with | Delete with | Deleted |
|---|---|---|---|---|---|
| 2026-11-16 | 1 | Budget `ace-study`, ID `f9c8671c-2547-4aa1-8cd8-d23c86bcb2fa` (15 CAD, alerts at 50%/100%, whole billing account). **Kept until the exam** | `gcloud billing budgets create --billing-account=$BILLING --display-name="ace-study" --budget-amount=15CAD --threshold-rule=percent=0.5 --threshold-rule=percent=1.0 --billing-project=fn-fruits` | `gcloud billing budgets delete f9c8671c-2547-4aa1-8cd8-d23c86bcb2fa --billing-account=$BILLING --billing-project=fn-fruits` | kept |
| 2026-11-16 | 1 | Project `fn-scratch-8998` (practice, labels `course=ace`, `week=1`) | `gcloud projects create fn-scratch-8998 --name="ACE scratch" "--labels=course=ace,week=1"` | `gcloud projects delete fn-scratch-8998 --quiet` | [x] 2026-11-16 (DELETE_REQUESTED, purged after ~30 days) |
| 2026-11-__ | 1 | IAM binding: second account → `roles/viewer` on `fn-fruits` (member in `private/second-member.txt`) | `gcloud projects add-iam-policy-binding fn-fruits --member=$MEMBER --role=roles/viewer --condition=None` | `gcloud projects remove-iam-policy-binding fn-fruits --member=$MEMBER --role=roles/viewer --condition=None` | [ ] |
| 2026-11-__ | 1 | IAM binding: second account → `roles/run.invoker` on `fn-fruits` | `gcloud projects add-iam-policy-binding fn-fruits --member=$MEMBER --role=roles/run.invoker --condition=None` | `gcloud projects remove-iam-policy-binding fn-fruits --member=$MEMBER --role=roles/run.invoker --condition=None` | [ ] |
| 2026-11-__ | 1 | Local Docker image `fruit:day2` (PC only, no GCP cost) | `docker build -t fruit:day2 .` | `docker rmi fruit:day2` | [ ] |
| 2026-11-__ | 1 | Local Docker containers `fruit-day2`, `fruit-day2-port` (PC only) | `docker run -d --name fruit-day2 ...` / `--name fruit-day2-port ...` | `docker rm -f fruit-day2 fruit-day2-port` | [ ] |
| 2026-11-__ | 1 | Cloud Shell clone `~/fn-gcp` (free) | `git clone https://github.com/noorff70/fn-gcp.git` | `rm -rf ~/fn-gcp` | [ ] |
|  |  |  |  |  | [ ] |

## Session log

| Date | Teardown run | ace-leftovers.sh result |
|---|---|---|
| 2026-11-16 (Day 1) | Yes – scratch project deleted; budget kept on purpose | Not run in Cloud Shell. Manual check of `fn-fruits`: no VMs, disks, IPs, buckets or forwarding rules → clean |
