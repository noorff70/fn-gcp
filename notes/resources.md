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
| 2026-11-16 | 1 | IAM binding: second account → `roles/viewer` on `fn-fruits` (member in `private/second-member.txt`) | `gcloud projects add-iam-policy-binding fn-fruits --member=$MEMBER --role=roles/viewer --condition=None` | `gcloud projects remove-iam-policy-binding fn-fruits --member=$MEMBER --role=roles/viewer --condition=None` | not created (Day 2 Step 6 skipped) |
| 2026-11-22 | 1 | IAM binding: second account → `roles/run.invoker` on `fn-fruits` | `gcloud projects add-iam-policy-binding fn-fruits --member=$MEMBER --role=roles/run.invoker --condition=None` | `gcloud projects remove-iam-policy-binding fn-fruits --member=$MEMBER --role=roles/run.invoker --condition=None` | not created (Day 2 Step 6 skipped) |
| 2026-11-22 | 1 | Local Docker image `fruit:day2` (PC only, no GCP cost) | `docker build -t fruit:day2 .` | `docker rmi fruit:day2` | [ x] |
| 2026-11-22 | 1 | Local Docker containers `fruit-day2`, `fruit-day2-port` (PC only) | `docker run -d --name fruit-day2 ...` / `--name fruit-day2-port ...` | `docker rm -f fruit-day2 fruit-day2-port` | [x ] |
| 2026-11-22 | 1 | Cloud Shell clone `~/fn-gcp` (free) | `git clone https://github.com/noorff70/fn-gcp.git` | `rm -rf ~/fn-gcp` | [x ] |
| 2026-11-20 | 2 | Firewall rule `allow-fruit-8080` (default VPC, tcp:8080 from my IP → tag `fruit-web`) | `gcloud compute firewall-rules create allow-fruit-8080 ...` | `gcloud compute firewall-rules delete allow-fruit-8080 --quiet` | [x ] |
| 2026-11-22 | 2 | VM `fruit-vm` (e2-micro, us-central1-a) + 10 GB pd-standard boot disk | `gcloud compute instances create fruit-vm ...` | `gcloud compute instances delete fruit-vm --zone=us-central1-a --quiet` (boot disk goes with it) | [x ] |
| 2026-11-22 | 2 | Snapshot `fruit-snap-day3` | `gcloud compute disks snapshot fruit-vm --zone=us-central1-a --snapshot-names=fruit-snap-day3` | `gcloud compute snapshots delete fruit-snap-day3 --quiet` | [x ] |
| 2026-11-22 | 2 | Image `fruit-img-day3` (family `fruit`) | `gcloud compute images create fruit-img-day3 --source-snapshot=fruit-snap-day3 --family=fruit` | `gcloud compute images delete fruit-img-day3 --quiet` | not created (`images delete` said "not found") |
| 2026-11-22 | 2 | OS Login SSH public key on my profile (added by first `gcloud compute ssh`) | `gcloud compute ssh fruit-vm ...` | `gcloud compute os-login ssh-keys remove --key-file="$HOME\.ssh\google_compute_engine.pub"` | [x ] |
| 2026-11-22 | 2 | Cloud Shell clone `~/fn-gcp` (free) | `git clone https://github.com/noorff70/fn-gcp.git ~/fn-gcp` | `rm -rf ~/fn-gcp` | [ ] |
| 2026-11-22 | 2 | Instance template `fruit-tpl` (global) | `gcloud compute instance-templates create fruit-tpl ...` | `gcloud compute instance-templates delete fruit-tpl --quiet` | [ x] |
| 2026-11-22 | 2 | Health check `fruit-hc` (HTTP :8080 /healthz) | `gcloud compute health-checks create http fruit-hc ...` | `gcloud compute health-checks delete fruit-hc --quiet` | [x ] |
| 2026-11-22 | 2 | Firewall rule `allow-fruit-hc` (tcp:8080 from 35.191.0.0/16 + 130.211.0.0/22 → tag `fruit-web`) | `gcloud compute firewall-rules create allow-fruit-hc ...` | `gcloud compute firewall-rules delete allow-fruit-hc --quiet` | [x ] |
| 2026-11-22 | 2 | Regional MIG `fruit-mig` (us-central1, 1–3 × e2-micro, autoscaler, autohealing) + its VMs/disks | `gcloud compute instance-groups managed create fruit-mig --region=us-central1 ...` | `gcloud compute instance-groups managed delete fruit-mig --region=us-central1 --quiet` | [x ] |
| 2026-11-22 | 2 | Backend service `fruit-be` (global, EXTERNAL_MANAGED) | `gcloud compute backend-services create fruit-be --global ...` | `gcloud compute backend-services delete fruit-be --global --quiet` | [x ] |
| 2026-11-22 | 2 | URL map `fruit-map` | `gcloud compute url-maps create fruit-map --default-service=fruit-be` | `gcloud compute url-maps delete fruit-map --quiet` | [ x] |
| 2026-11-22 | 2 | Target HTTP proxy `fruit-proxy` | `gcloud compute target-http-proxies create fruit-proxy --url-map=fruit-map` | `gcloud compute target-http-proxies delete fruit-proxy --quiet` | [x ] |
| 2026-11-22 | 2 | Forwarding rule `fruit-fr` (global, port 80, ephemeral IP) – **billed hourly** | `gcloud compute forwarding-rules create fruit-fr --global ...` | `gcloud compute forwarding-rules delete fruit-fr --global --quiet` | [x ] |
| 2026-11-22 | 2 | Instance template `fruit-tpl-v2` (rolling update) | `gcloud compute instance-templates create fruit-tpl-v2 ...` | `gcloud compute instance-templates delete fruit-tpl-v2 --quiet` | [x] |
| 2026-11-22 | 2 | Spot VM `fruit-spot` (e2-custom-2-4096, us-central1-a) | `gcloud compute instances create fruit-spot --provisioning-model=SPOT ...` | `gcloud compute instances delete fruit-spot --zone=us-central1-a --quiet` | [ x] |
| 2026-11-22 | 2 | OS Login SSH key (re-added by Step 8 `gcloud compute ssh`) | `gcloud compute ssh ...` | `gcloud compute os-login ssh-keys remove --key-file="$HOME\.ssh\google_compute_engine.pub"` | [x ] |
|  |  |  |  |  | [ ] |

## Session log

| Date | Teardown run | ace-leftovers.sh result |
|---|---|---|
| 2026-11-16 (Day 1) | Yes – scratch project deleted; budget kept on purpose | Not run in Cloud Shell. Manual check of `fn-fruits`: no VMs, disks, IPs, buckets or forwarding rules → clean |
