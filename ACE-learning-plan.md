# Google Cloud Associate Cloud Engineer (ACE) – Learning Plan

*Written 2026-11-16. The hands-on project is `D:\dev\gcp`, a FastAPI app called "fruit".*

- **Pace:** 2–3 hours a day, about 15–20 hours a week.
- **Length:** 6 study weeks plus 1 revision and exam week, about 100–120 hours in all.
- **Exam date:** not fixed yet. Book the exam when you reach the end of Week 5.
- **Default region:** `us-central1`, zone `us-central1-a`. This region is eligible for the free tier and is usually the cheapest.

---

## 0. What the `D:\dev\gcp` project is today

| Aspect | Current state |
|---|---|
| Language / framework | Python (3.14 locally) with **FastAPI** and **uvicorn**. Settings come from `pydantic-settings` (`.env.dev`). |
| Architecture | API → Service → Repository → SQLite. Uses a repository pattern with manual dependency injection (`Depends(get_service)`). |
| Endpoints | `GET /fruits`, `GET /fruits-with-types`, `GET /locations` |
| Data | SQLite file `data/inventory.db` with tables `fruit`, `fruit_type`, `location` and `fruit_type_location` (the last one has a price). |
| Tests | `pytest` tests using an in-memory SQLite database. One test file for repositories, one for services. |
| Build / run | Run locally only: `uvicorn fruit.main:app --reload`. There is no Dockerfile and no CI. |
| GCP-related files | **None.** There is no Dockerfile, Terraform, `cloudbuild.yaml`, `app.yaml` or Kubernetes manifest. |
| Git | A single commit on `master` ("FastAPI for a Fruit Project"). |

### Small fixes to make before deploying anywhere (you do these in Week 1)
1. `requirements.txt` is saved as **UTF-16**. Re-save it as UTF-8 so `pip install` works reliably inside Linux containers. In PowerShell:
   `Get-Content requirements.txt | Set-Content -Encoding utf8 requirements.txt`
   Check afterwards that the file has no BOM.
2. `__pycache__/` folders and `.env.dev` are committed to git. Add a `.gitignore` and run `git rm -r --cached` on them.
3. `fruit/api/location_api.py` hard-codes `"data/inventory.db"`. Make it use `settings.DATABASE_URL`, as `fruit_api.py` already does.
4. `fruit/repositories/db_context.py` imports `fruit.repositories.interfaces`, which doesn't exist. Nothing imports `db_context.py`, so either fix the import or delete the file.
5. Add a `GET /healthz` endpoint. Health checks on load balancers, MIGs, Cloud Run and GKE will use it.
6. Make the app listen on `$PORT`. Cloud Run sets `PORT=8080`.

### Target shape of the app for the course
The same container image gets deployed in several ways over the weeks:

```
            ┌── Compute Engine VM / MIG + HTTP LB   (Week 2)
image in ───┼── Cloud Run (+ Cloud SQL MySQL)         (Weeks 3–4)
Artifact    └── GKE Autopilot                         (Week 5)
Registry
```

SQLite is fine for a VM. On Cloud Run and GKE, though, the container filesystem doesn't persist and every instance gets its own copy. That limitation is the reason to move the data to **Cloud SQL for MySQL** in Week 4, the same database engine you just moved Study Aid to.

Suggested `Dockerfile` (write it yourself in Week 1):

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY fruit ./fruit
COPY data ./data
ENV DATABASE_URL=data/inventory.db
CMD exec uvicorn fruit.main:app --host 0.0.0.0 --port ${PORT:-8080}
```

(`SQLiteFruitRepository` passes `DATABASE_URL` directly to `sqlite3.connect`, so the value must be a **file path**, not a `sqlite:///` URL.)

---

## 1. Exam facts (checked 2026-11-16)

Sources: the [exam guide](https://cloud.google.com/learn/certification/guides/cloud-engineer) and the [certification page](https://cloud.google.com/learn/certification/cloud-engineer). The guide page **shows no version number or date**. This plan uses the five-section guide that was live on 2026-11-16. Some third-party blogs describe a four-section guide refreshed in mid-2026, so check the official page again before you book.

- 2 hours, 50–60 multiple-choice and multiple-select questions, **US$125**, valid for 3 years. No prerequisites. Google recommends 6+ months of hands-on experience.
- Delivered online-proctored or at a test centre.
- Languages: English, Japanese, Spanish, Portuguese.

| § | Section | Weight |
|---|---|---|
| 1 | Setting up a cloud solution environment | ~20% |
| 2 | Planning and configuring a cloud solution | ~17.5% |
| 3 | Deploying and implementing a cloud solution | ~25% |
| 4 | Ensuring successful operation of a cloud solution | ~20% |
| 5 | Configuring access and security | ~17.5% |

### Exam objectives → exercises on this project

| Objective | Exercise on the fruit project | Week |
|---|---|---|
| 1.1 Resource hierarchy, org policies, IAM roles, Cloud Identity, enabling APIs, quotas | Create the `ace-fruit-*` project and folders (if you have an org), enable APIs, grant roles to a second Gmail account, view quotas | 1 |
| 1.1 Operations suite setup | Create the Monitoring workspace/scope, install Ops Agent | 1, 6 |
| 1.2 Billing accounts, linking, budgets and alerts, billing export | Link the project, create a budget with 50/90/100% alerts, export billing to BigQuery | 1 |
| 2.1 Compute choice; Spot VMs and custom machine types | Write a decision note "VM vs MIG vs Cloud Run vs GKE vs Functions for fruit"; create a Spot VM with a custom machine type | 2 |
| 2.2 Storage choice (Cloud SQL / BigQuery / Firestore / Spanner / Bigtable; disk and storage classes) | Decision table for fruit data; bucket in each storage class; zonal vs regional PD | 3, 4 |
| 2.3 Load balancing, locations, Network Service Tiers | HTTP(S) LB in front of the MIG; Standard vs Premium tier IP | 2, 5 |
| 3.1 Compute Engine: disks, SSH keys, OS Login, MIG + template + autoscaling, VM Manager | Fruit API on a VM via a startup script; template → MIG → autoscaler; OS Login; VM Manager OS inventory | 2 |
| 3.2 GKE: kubectl, Autopilot / regional / private clusters, deploying an app | Autopilot cluster; deploy the fruit image with a Deployment and Service | 5 |
| 3.3 Cloud Run / Functions: deploy, event-driven apps (Pub/Sub, GCS, Eventarc) | Fruit API on Cloud Run; a function triggered by a GCS upload that loads `fruits.csv` | 3 |
| 3.4 Data products and loading data | Cloud SQL MySQL; load to BigQuery from GCS; Pub/Sub topic; Firestore (brief) | 4 |
| 3.5 VPC, subnets, firewall rules (tags, service accounts), peering / VPN | Custom-mode VPC `fruit-vpc`; firewall rules by tag and by service account; VPC peering between two VPCs | 5 |
| 3.6 IaC (Terraform, Config Connector, Helm, CFT) | Terraform for the VPC, Artifact Registry and Cloud Run; Helm chart for GKE (brief) | 5, 6 |
| 4.1 Manage GCE: SSH, inventory, snapshots, images | Snapshot schedule; custom image from the VM; `instances list` filters | 2 |
| 4.2 Manage GKE: inventory, Artifact Registry access, node pools, HPA/VPA | `kubectl get`, HPA on the fruit deployment; Standard zonal cluster with an extra node pool (brief) | 5 |
| 4.3 Manage Cloud Run: new revisions, traffic splits, scaling | v2 revision with `/healthz`; 90/10 split; min/max instances | 3 |
| 4.4 Manage storage and DBs: GCS security and lifecycle, queries, cost estimates, backup and restore, job status | Lifecycle rules, signed URLs; MySQL queries; on-demand backup and restore; BigQuery job history | 3, 4 |
| 4.5 Manage networking: add or expand subnets, static IPs, Cloud DNS, Cloud NAT | Expand the subnet range; reserve an IP; private DNS zone; Cloud NAT for a VM without a public IP | 5 |
| 4.6 Monitoring and logging (alerts, custom metrics, sinks, log buckets, Log Analytics, Ops Agent, Managed Prometheus, audit logs) | Alert on Cloud Run 5xx; log-based metric "fruit_not_found"; sink to BigQuery; Data Access audit logs | 6 |
| 5.1 IAM policies; basic, predefined and custom roles | Custom role `fruitReader`; read and edit the project policy | 1, 6 |
| 5.2 Service accounts: create, least privilege, attach, impersonate, short-lived credentials | `fruit-run-sa` for Cloud Run with only `cloudsql.client`; impersonation with `--impersonate-service-account`; `print-access-token` | 3, 4, 6 |

---

## 2. Cost safety (read this before Week 1)

### Golden rule: every resource you create is deleted in the same session

Nothing is left running between sessions, including free-tier items. Recreating things the next day is cheap, and it's good exam practice. Four habits make this reliable:

1. **Write the delete command first.** Before you run any `create`, `deploy`, `submit` or `apply`, add a line to [`notes/resources.md`](notes/resources.md) with the resource, the command that creates it, and **the exact command that deletes it**.
2. **Label everything.** Add `--labels=course=ace,week=N` wherever the command supports labels. This lets you find stray resources by label, and the billing export can group costs by label.
3. **Tear down at the end of every session.** Each week below ends with a **Teardown** block that lists the delete commands in the right order (dependent resources first). Run it, then tick off each row in `notes/resources.md`.
4. **Prove it's clean.** Run [`scripts/ace-leftovers.sh`](scripts/ace-leftovers.sh) in Cloud Shell (`bash scripts/ace-leftovers.sh ace-fruit-XXXX`). It lists everything still left in the project and exits with a non-zero status if anything billable remains. **Don't end a session until it prints `CLEAN`.**

Safety nets in case you miss something: the budget alert (item 3 below), the billing report, filtered by label, checked weekly, and deleting the whole project after the exam.

1. **Free trial and free tier.** New accounts usually get a **US$300 / 90-day** credit, and there is an "Always Free" tier. Check [cloud.google.com/free](https://cloud.google.com/free) for the current limits. Relevant Always Free items:
   - one `e2-micro` VM in us-central1, us-west1 or us-east1, with 30 GB standard PD
   - 5 GB of Standard storage in US regions
   - a monthly allowance of Cloud Run requests and CPU time
   - some Cloud Build minutes
   - a small Artifact Registry allowance
   - the BigQuery 1 TB/month query allowance
2. **Things that cost money even when idle.** Delete each one the same day you create it:
   - **Cloud SQL** has *no* free tier and charges per hour while running. Stop it (`--activation-policy=NEVER`) when you take a break. Storage is still billed while it's stopped.
   - **Load balancer forwarding rules**, unused **static external IPs**, **Cloud NAT** gateways and **Cloud VPN** tunnels.
   - **GKE.** Each billing account gets a cluster-management-fee credit covering one zonal or Autopilot cluster. Nodes (Standard) or pod resources (Autopilot) are billed on top. **Never leave a cluster running overnight.**
   - VMs outside the e2-micro free tier, and persistent disks or snapshots left behind after deleting a VM.
3. **Budget alert (Week 1, day 1).** A budget only *alerts*; it does not stop spending.
   ```bash
   gcloud billing accounts list
   gcloud billing budgets create --billing-account=BILLING_ID \
     --display-name="ace-study" --budget-amount=20USD \
     --threshold-rule=percent=0.5 --threshold-rule=percent=0.9 --threshold-rule=percent=1.0
   ```
4. **Daily clean-up check.** Run `bash scripts/ace-leftovers.sh ace-fruit-XXXX` before you stop for the day. It checks Compute Engine, load-balancer pieces, networking, GKE, Cloud SQL, Cloud Run, Functions, Artifact Registry, Cloud Storage, Pub/Sub, Secret Manager, BigQuery, Cloud DNS and Logging. Alert policies and uptime checks have no reliable GA list command, so check them in the console under **Monitoring → Alerting** and **Monitoring → Uptime checks**.
5. **Nuclear option.** Deleting the project shuts everything in it down. It stays recoverable for 30 days.
   ```bash
   gcloud projects delete ace-fruit-XXXX
   ```
   Use **one practice project** for the whole course and delete it after the exam.
6. **Where to run commands.** Cloud Shell (free, bash, `gcloud`, `kubectl`, `terraform` and `docker` preinstalled) is the easiest place. The `\` line continuations below are bash syntax. In local PowerShell, use a backtick `` ` `` instead, or put the command on one line. Use local Docker Desktop and the gcloud CLI only for building and testing the image.

---

## 3. Week-by-week plan

Each week: about 5 weekday sessions of 2 hours, plus one longer lab of 3–5 hours at the weekend.
Rhythm: **learn (docs or Skills Boost) → lab on fruit → clean up → write notes in `notes/weekN.md`**.

### Week 1 — Environment, billing, IAM basics, containerise the app (§1, §5.1)

**Topics**
- Resource hierarchy (org → folders → projects), org policies, the IAM model (principal, role, policy, inheritance)
- Basic vs predefined vs custom roles, Cloud Identity, APIs and quotas
- Billing accounts, budgets, billing export
- gcloud configurations

**Hands-on**
- Install the gcloud CLI on Windows and run `gcloud init`. Create the project `ace-fruit-<random>` and link billing.
- Create the budget (see §2). Enable billing export to a BigQuery dataset `billing_export`.
- Grant a second Google account `roles/viewer`, then `roles/run.invoker`. Watch the policy change.
- If you want to practise org policies and folders: a free Cloud Identity Free tenant on a domain you own gives you an org node. Otherwise learn these concepts from the docs.
- Make the project fixes in §0. Add the Dockerfile and `.dockerignore`, then run `docker build -t fruit . && docker run -p 8080:8080 fruit` locally and test `/fruits`.

**gcloud to practise**
```bash
gcloud config configurations create ace; gcloud config set project ace-fruit-XXXX
gcloud config set compute/region us-central1; gcloud config set compute/zone us-central1-a
gcloud projects create ace-fruit-XXXX; gcloud billing projects link ace-fruit-XXXX --billing-account=BILLING_ID
gcloud services enable compute.googleapis.com run.googleapis.com artifactregistry.googleapis.com cloudbuild.googleapis.com
gcloud services list --enabled
gcloud projects get-iam-policy ace-fruit-XXXX --format=json
gcloud projects add-iam-policy-binding ace-fruit-XXXX --member=user:friend@gmail.com --role=roles/viewer
gcloud iam roles list --filter="name:roles/run" ; gcloud iam roles describe roles/run.invoker
gcloud compute project-info describe --format="value(quotas)"   # quotas
```

**Cost:** about $0. Only APIs, IAM and the budget are involved.

**Teardown (end of the week).** The project, the budget and the `billing_export` dataset are meant to stay until the exam. Everything else goes:
```bash
gcloud projects remove-iam-policy-binding ace-fruit-XXXX --member=user:friend@gmail.com --role=roles/viewer
gcloud projects remove-iam-policy-binding ace-fruit-XXXX --member=user:friend@gmail.com --role=roles/run.invoker
docker rm -f $(docker ps -aq --filter ancestor=fruit) ; docker rmi fruit    # local only, no cost
bash scripts/ace-leftovers.sh ace-fruit-XXXX
```

**Checkpoint**
- Fruit runs in local Docker.
- The budget is visible in the console.
- You can explain the difference between `roles/owner`, `roles/editor` and a predefined role.
- 15 practice questions on §1.

### Week 2 — Compute Engine end to end (§2.1, §2.3, §3.1, §4.1)

**Topics**
- Machine families, custom machine types, Spot VMs, availability policy
- Persistent Disk types, SSH and OS Login, metadata and startup scripts
- Instance templates, MIGs, autoscaling, health checks, the HTTP(S) load balancer family
- Snapshots, snapshot schedules, images, VM Manager

**Hands-on**
1. Create an `e2-micro` VM (free tier) with a startup script that clones or copies the fruit app, installs it, and runs it on port 8080. Add the network tag `fruit-web` and a firewall rule for tcp:8080 limited to your IP.
2. Turn on OS Login and SSH in with `gcloud compute ssh`.
3. Snapshot the disk, create a snapshot schedule, then build an image from the VM.
4. Create an instance template from the image → regional MIG (min 1, max 3, CPU target 60%) → health check on `/healthz` → global external Application Load Balancer.
5. Load-test the MIG with `hey` or `ab` from Cloud Shell and watch it autoscale.
6. Create one Spot VM with a custom machine type (`--custom-cpu=1 --custom-memory=2GB`) and note how preemption behaves.

**gcloud to practise**
```bash
gcloud compute instances create fruit-vm --machine-type=e2-micro --image-family=debian-12 --image-project=debian-cloud \
  --tags=fruit-web --metadata-from-file=startup-script=startup.sh --metadata=enable-oslogin=TRUE
gcloud compute firewall-rules create allow-fruit-8080 --network=default --allow=tcp:8080 --target-tags=fruit-web --source-ranges=YOUR_IP/32
gcloud compute ssh fruit-vm ; gcloud compute instances list --filter="status=RUNNING" --format="table(name,zone,networkInterfaces[0].accessConfigs[0].natIP)"
gcloud compute disks snapshot fruit-vm --snapshot-names=fruit-snap-1
gcloud compute resource-policies create snapshot-schedule daily-fruit --daily-schedule --start-time=02:00 --max-retention-days=3
gcloud compute images create fruit-img --source-disk=fruit-vm --source-disk-zone=us-central1-a --force
gcloud compute instance-templates create fruit-tpl --machine-type=e2-small --image=fruit-img --tags=fruit-web
gcloud compute instance-groups managed create fruit-mig --template=fruit-tpl --size=1 --region=us-central1
gcloud compute instance-groups managed set-autoscaling fruit-mig --region=us-central1 --min-num-replicas=1 --max-num-replicas=3 --target-cpu-utilization=0.6
gcloud compute instances create fruit-spot --provisioning-model=SPOT --instance-termination-action=STOP --custom-cpu=1 --custom-memory=2GB
```

**Cost:** the e2-micro is free. MIG instances, the LB forwarding rule and snapshots are not. Build the MIG and LB and **delete them the same session**. When you build the LB, use the names below so the teardown commands match: `fruit-hc`, `fruit-be`, `fruit-map`, `fruit-proxy`, `fruit-fr`.

**Teardown (end of every session).** The order matters, because each resource is in use by the one listed before it:
```bash
gcloud compute forwarding-rules delete fruit-fr --global -q
gcloud compute target-http-proxies delete fruit-proxy -q
gcloud compute url-maps delete fruit-map -q
gcloud compute backend-services delete fruit-be --global -q
gcloud compute health-checks delete fruit-hc -q
gcloud compute instance-groups managed delete fruit-mig --region=us-central1 -q
gcloud compute instance-templates delete fruit-tpl -q
gcloud compute instances delete fruit-vm fruit-spot --zone=us-central1-a -q   # boot disks auto-delete by default
gcloud compute images delete fruit-img -q
gcloud compute snapshots delete fruit-snap-1 -q        # plus any made by the schedule: gcloud compute snapshots list
gcloud compute resource-policies delete daily-fruit --region=us-central1 -q
gcloud compute firewall-rules delete allow-fruit-8080 -q
gcloud compute disks list                              # must be empty
bash scripts/ace-leftovers.sh ace-fruit-XXXX
```

**Checkpoint**
- Screenshot of the LB IP serving `/fruits`, plus a written teardown checklist.
- Can you answer: when would you choose a regional MIG over a zonal one? An image over a snapshot?
- 20 questions on §3.1 and §4.1.

### Week 3 — Artifact Registry, Cloud Build, Cloud Run, Cloud Storage, event-driven functions (§2.1, §2.2, §3.3, §4.3, §4.4, §5.2)

**Topics**
- Artifact Registry and Cloud Build, Cloud Run (services vs jobs, revisions, concurrency, min/max instances, ingress, auth)
- Cloud Run functions and Eventarc
- Cloud Storage classes, lifecycle rules, uniform bucket-level access, signed URLs, object versioning
- Service account basics

**Hands-on**
1. Create the Artifact Registry repo `fruit-repo` (Docker) and build with `gcloud builds submit --tag ...`. Then write a `cloudbuild.yaml` that runs `pytest`, builds and pushes.
2. Create the service account `fruit-run-sa` with **no** roles, and deploy fruit to Cloud Run with `--service-account=fruit-run-sa`.
3. Add `/healthz` or a version field and deploy v2 with `--no-traffic --tag=v2`. Split traffic 90/10, then roll back.
4. Set `--min-instances=0 --max-instances=2 --concurrency=40`, and compare `--no-allow-unauthenticated` with public access.
5. Create the bucket `ace-fruit-XXXX-uploads` with uniform access, versioning, and a lifecycle rule (→ Nearline after 30 days, delete after 365). Generate a signed URL.
6. Write a Cloud Run function (Python) triggered by `google.cloud.storage.object.v1.finalized` that logs the rows of an uploaded `fruits.csv`. This is the Eventarc pattern.

**gcloud to practise**
```bash
gcloud artifacts repositories create fruit-repo --repository-format=docker --location=us-central1
gcloud builds submit --tag us-central1-docker.pkg.dev/ace-fruit-XXXX/fruit-repo/fruit:v1
gcloud iam service-accounts create fruit-run-sa --display-name="Fruit Cloud Run SA"
gcloud run deploy fruit --image=us-central1-docker.pkg.dev/ace-fruit-XXXX/fruit-repo/fruit:v1 --region=us-central1 \
  --service-account=fruit-run-sa@ace-fruit-XXXX.iam.gserviceaccount.com --allow-unauthenticated --max-instances=2
gcloud run deploy fruit --image=...:v2 --no-traffic --tag=v2
gcloud run services update-traffic fruit --to-revisions=LATEST=10 ; gcloud run services update-traffic fruit --to-latest
gcloud run revisions list --service=fruit
gcloud storage buckets create gs://ace-fruit-XXXX-uploads --location=us-central1 --uniform-bucket-level-access
gcloud storage buckets update gs://ace-fruit-XXXX-uploads --versioning --lifecycle-file=lifecycle.json
gcloud storage cp fruits.csv gs://ace-fruit-XXXX-uploads/ ; gcloud storage sign-url gs://.../fruits.csv --duration=10m --private-key-file=KEY.json
gcloud functions deploy fruit-loader --gen2 --runtime=python312 --region=us-central1 --trigger-bucket=ace-fruit-XXXX-uploads --entry-point=on_upload --source=./loader
```
(To sign the URL without a key file, add `--impersonate-service-account=...`. That is the best practice; avoid downloading SA keys.)

**Cost:** Cloud Run, Cloud Build, Artifact Registry and GCS should all stay inside the free allowances. Even so, delete everything (golden rule). Weeks 4–6 start by recreating the repo, image, service account and Cloud Run service with the Week 3 commands, which is good repetition.

**Teardown (end of every session):**
```bash
gcloud functions delete fruit-loader --gen2 --region=us-central1 -q   # also removes its Eventarc trigger
gcloud run services delete fruit --region=us-central1 -q
gcloud artifacts repositories delete fruit-repo --location=us-central1 -q
gcloud storage rm -r gs://ace-fruit-XXXX-uploads
gcloud storage buckets list --format="value(name)"     # also delete auto-created buckets: ace-fruit-XXXX_cloudbuild, gcf-v2-sources-*, gcf-v2-uploads-*
gcloud iam service-accounts delete fruit-run-sa@ace-fruit-XXXX.iam.gserviceaccount.com -q
bash scripts/ace-leftovers.sh ace-fruit-XXXX
```

**Checkpoint**
- A public Cloud Run URL serving fruit, and a working canary rollout.
- You can explain why SQLite on Cloud Run is a problem.
- 20 questions on §3.3 and §4.3.

### Week 4 — Data: Cloud SQL (MySQL), BigQuery, Pub/Sub, choosing a database (§2.2, §3.4, §4.4, §5.2)

**Topics**
- Cloud SQL (editions, HA, read replicas, backups and PITR, private vs public IP, Auth Proxy and connectors), Secret Manager
- BigQuery (datasets, loading, querying, jobs, cost estimation with `--dry_run`), Pub/Sub
- When to use Firestore, Spanner, Bigtable or AlloyDB: theory and decision tables

**Hands-on**
1. Create the smallest Cloud SQL **MySQL** instance, then database `inventory` and user `fruit`. Store the password in Secret Manager.
2. Port the schema and data: `sqlite3 data/inventory.db .dump` → adapt to MySQL → `gcloud sql import sql` from GCS.
3. Add a `MySQLFruitRepository` (PyMySQL plus the Cloud SQL Python Connector) behind the existing repository interface, chosen through `DATABASE_URL`. This reuses your Study Aid MySQL experience.
4. Redeploy Cloud Run with `--add-cloudsql-instances` and `--set-secrets`. Grant `fruit-run-sa` **only** `roles/cloudsql.client` and `roles/secretmanager.secretAccessor`.
5. Take an on-demand backup → delete a row → restore. Run the queries with `gcloud sql connect`.
6. Export `fruit_type_location` to CSV in GCS → load it into BigQuery → `SELECT location, AVG(price)`. Run it with `--dry_run` first.
7. Create a Pub/Sub topic `fruit-events` with a pull subscription. Publish and pull a message.

**gcloud to practise**
```bash
gcloud sql instances create fruit-sql --database-version=MYSQL_8_0 --edition=ENTERPRISE --tier=db-f1-micro --region=us-central1 --storage-size=10GB --no-backup
gcloud sql databases create inventory --instance=fruit-sql ; gcloud sql users create fruit --instance=fruit-sql --password=...
gcloud sql import sql fruit-sql gs://ace-fruit-XXXX-uploads/inventory.sql --database=inventory
gcloud sql backups create --instance=fruit-sql ; gcloud sql backups list --instance=fruit-sql
gcloud sql backups restore BACKUP_ID --restore-instance=fruit-sql
gcloud sql instances patch fruit-sql --activation-policy=NEVER    # stop when not in use
printf 'secret' | gcloud secrets create fruit-db-pass --data-file=-
gcloud run deploy fruit --image=... --add-cloudsql-instances=ace-fruit-XXXX:us-central1:fruit-sql --set-secrets=DB_PASS=fruit-db-pass:latest
bq mk fruit_ds ; bq load --source_format=CSV --autodetect fruit_ds.prices gs://.../prices.csv
bq query --use_legacy_sql=false --dry_run 'SELECT ...' ; bq ls -j
gcloud pubsub topics create fruit-events ; gcloud pubsub subscriptions create fruit-sub --topic=fruit-events
gcloud pubsub topics publish fruit-events --message='{"fruit":"Apple"}' ; gcloud pubsub subscriptions pull fruit-sub --auto-ack
```

**Cost:** Cloud SQL is the main cost of the course. Create it at the start of a session and **delete it at the end**; stopping it still leaves storage being billed. Keep `inventory.sql` in a local folder so you can re-import it next session. BigQuery usage this small stays inside the free tier.

**Teardown (end of every session):**
```bash
gcloud sql instances delete fruit-sql -q              # its backups are deleted with it
gcloud secrets delete fruit-db-pass -q
gcloud pubsub subscriptions delete fruit-sub -q ; gcloud pubsub topics delete fruit-events -q
bq rm -r -f -d ace-fruit-XXXX:fruit_ds
# plus the Week 3 teardown block (Cloud Run, Artifact Registry, buckets, service account)
bash scripts/ace-leftovers.sh ace-fruit-XXXX
```

**Checkpoint**
- Fruit on Cloud Run reading from Cloud SQL, with no password in code or env files.
- A one-page "which database?" table: Cloud SQL / AlloyDB / Spanner / Firestore / Bigtable / BigQuery.
- 20 questions on §2.2, §3.4 and §4.4.

### Week 5 — Networking, GKE and Terraform (§2.3, §3.2, §3.5, §3.6, §4.2, §4.5)

**Topics**
- Custom-mode VPCs, subnets and secondary ranges, firewall rules and policies (tags vs service accounts, priority, ingress and egress)
- Private Google Access, Cloud NAT, Cloud DNS, static IPs, Network Service Tiers
- VPC peering, Shared VPC, Cloud VPN (theory)
- GKE Autopilot vs Standard; regional, zonal and private clusters; node pools; HPA and VPA; Artifact Registry access
- Terraform basics and Helm

**Hands-on (networking)**
1. Create the VPC `fruit-vpc` (custom mode) and subnet `fruit-subnet` 10.10.0.0/24, then expand it to /23.
2. Add firewall rules: allow tcp:22 from IAP (35.235.240.0/20) by service account, and allow 8080 by tag.
3. Create a VM **without a public IP** → set up Cloud NAT so it can reach `apt` → connect with `gcloud compute ssh --tunnel-through-iap`.
4. Reserve a static internal and a static external IP, create a private Cloud DNS zone `fruit.internal`, and add an A record for the VM.
5. Create a second VPC and set up VPC peering. Test connectivity with the internal IP.

**Hands-on (GKE, finish within one session)**
6. Create an Autopilot cluster in `fruit-vpc`. Deploy fruit with a `Deployment` (image from Artifact Registry) and a `Service` of type LoadBalancer, then add an HPA.
7. Run `kubectl get nodes,pods,svc` and `kubectl describe`, scale up, and do a rolling update to v2.
8. (Optional, short) Create a Standard zonal cluster with 1 node, add or resize or delete a node pool, then **delete the cluster**.

**Hands-on (IaC)**
9. Write Terraform in `infra/` that creates the VPC, subnet, firewall, Artifact Registry repo and Cloud Run service. Run `terraform plan/apply/destroy`.

**gcloud and kubectl to practise**
```bash
gcloud compute networks create fruit-vpc --subnet-mode=custom
gcloud compute networks subnets create fruit-subnet --network=fruit-vpc --range=10.10.0.0/24 --region=us-central1 --enable-private-ip-google-access
gcloud compute networks subnets expand-ip-range fruit-subnet --region=us-central1 --prefix-length=23
gcloud compute firewall-rules create fruit-iap-ssh --network=fruit-vpc --allow=tcp:22 --source-ranges=35.235.240.0/20 --target-service-accounts=SA_EMAIL
gcloud compute routers create fruit-router --network=fruit-vpc --region=us-central1
gcloud compute routers nats create fruit-nat --router=fruit-router --region=us-central1 --auto-allocate-nat-external-ips --nat-all-subnet-ip-ranges
gcloud compute addresses create fruit-ip --region=us-central1 ; gcloud compute addresses create fruit-int --region=us-central1 --subnet=fruit-subnet
gcloud dns managed-zones create fruit-internal --dns-name=fruit.internal. --visibility=private --networks=fruit-vpc --description="lab"
gcloud compute networks peerings create a-to-b --network=fruit-vpc --peer-network=other-vpc
gcloud container clusters create-auto fruit-gke --region=us-central1 --network=fruit-vpc --subnetwork=fruit-subnet
gcloud container clusters get-credentials fruit-gke --region=us-central1
kubectl create deployment fruit --image=us-central1-docker.pkg.dev/ace-fruit-XXXX/fruit-repo/fruit:v1
kubectl expose deployment fruit --type=LoadBalancer --port=80 --target-port=8080
kubectl autoscale deployment fruit --cpu-percent=60 --min=1 --max=3 ; kubectl get hpa
kubectl set image deployment/fruit fruit=...:v2 ; kubectl rollout status deployment/fruit
gcloud container node-pools create pool-2 --cluster=std-zonal --zone=us-central1-a --num-nodes=1   # Standard cluster only
gcloud container clusters delete fruit-gke --region=us-central1 --quiet
```

**Cost:** NAT, static IPs, the GKE cluster and the LoadBalancer Service all cost money by the hour. **Tear down everything at the end of each session.** `terraform destroy` makes that easy for anything Terraform created. The rest you remove by hand, using the names below.

**Teardown (end of every session).** GKE goes first. Delete the Kubernetes Service *before* the cluster, otherwise its load balancer can be left behind.
```bash
kubectl delete hpa fruit ; kubectl delete service fruit ; kubectl delete deployment fruit
gcloud container clusters delete fruit-gke --region=us-central1 -q
gcloud container clusters delete std-zonal --zone=us-central1-a -q            # if you made it
(cd infra && terraform destroy -auto-approve)
gcloud compute instances delete fruit-private-vm --zone=us-central1-a -q
gcloud compute routers nats delete fruit-nat --router=fruit-router --region=us-central1 -q
gcloud compute routers delete fruit-router --region=us-central1 -q
gcloud compute addresses delete fruit-ip fruit-int --region=us-central1 -q
gcloud dns record-sets delete vm.fruit.internal. --type=A --zone=fruit-internal
gcloud dns managed-zones delete fruit-internal -q
gcloud compute networks peerings delete a-to-b --network=fruit-vpc -q
gcloud compute networks peerings delete b-to-a --network=other-vpc -q
gcloud compute firewall-rules list --filter="network~fruit-vpc OR network~other-vpc" --format="value(name)"   # delete each, including gke-* rules left behind
gcloud compute firewall-rules delete fruit-iap-ssh -q
gcloud compute networks subnets delete fruit-subnet --region=us-central1 -q    # and other-vpc's subnets
gcloud compute networks delete fruit-vpc other-vpc -q
gcloud compute disks list                                                      # GKE PVC disks show up here
bash scripts/ace-leftovers.sh ace-fruit-XXXX
```

**Checkpoint**
- `terraform apply` → working fruit URL → `terraform destroy` with no leftovers.
- A diagram of `fruit-vpc`.
- 25 questions on §3.2, §3.5 and §4.5.
- **Book the exam for the end of Week 7.**

### Week 6 — Operations and security deep dive (§4.6, §5.1, §5.2, §1.1 ops suite)

**Topics**
- Cloud Logging (filters, log router, sinks, log buckets, Log Analytics, exclusions)
- Cloud Monitoring (metrics, alert policies, uptime checks, dashboards, custom and log-based metrics), Ops Agent, Managed Service for Prometheus
- Audit logs (Admin Activity, Data Access, System Event, Policy Denied), Google Cloud status page
- Custom roles, policy inheritance, conditions, SA impersonation, short-lived credentials, why SA keys are a risk, Policy Troubleshooter

**Hands-on**
1. Redeploy fruit to Cloud Run with structured JSON logging (log `fruit_not_found` events), then filter the logs in Logs Explorer.
2. Create a log-based metric `fruit_not_found` → an alert policy on it, an alert on Cloud Run 5xx, and an uptime check on `/healthz`.
3. Create a sink → BigQuery dataset `logs_ds`. Create a log bucket with 7-day retention and a sink that routes `resource.type=cloud_run_revision` to it. Query it in Log Analytics.
4. Turn on Data Access audit logs for Cloud SQL or GCS, then find your own reads.
5. Install the Ops Agent on the e2-micro VM and look at memory and disk metrics.
6. Create the custom role `fruitReader` (run.services.get, storage.objects.get) and grant it with an IAM condition (for example, expiring after 7 days).
7. Grant yourself `roles/iam.serviceAccountTokenCreator` on `fruit-run-sa`, impersonate it, and print a short-lived token. Check denied actions with Policy Troubleshooter.

**gcloud to practise**
```bash
gcloud logging read 'resource.type="cloud_run_revision" severity>=ERROR' --limit=20 --freshness=1h
gcloud logging metrics create fruit_not_found --description="404s" --log-filter='jsonPayload.event="fruit_not_found"'
gcloud logging sinks create fruit-to-bq bigquery.googleapis.com/projects/ace-fruit-XXXX/datasets/logs_ds --log-filter='resource.type="cloud_run_revision"'
gcloud logging buckets create fruit-logs --location=global --retention-days=7
gcloud monitoring uptime create fruit-up --resource-type=uptime-url --resource-labels=host=FRUIT_HOST,project_id=ace-fruit-XXXX --path=/healthz
gcloud iam roles create fruitReader --project=ace-fruit-XXXX --permissions=run.services.get,storage.objects.get --stage=GA
gcloud projects add-iam-policy-binding ace-fruit-XXXX --member=user:friend@gmail.com --role=projects/ace-fruit-XXXX/roles/fruitReader \
  --condition='expression=request.time < timestamp("2027-01-01T00:00:00Z"),title=temp'
gcloud iam service-accounts add-iam-policy-binding fruit-run-sa@... --member=user:YOU --role=roles/iam.serviceAccountTokenCreator
gcloud auth print-access-token --impersonate-service-account=fruit-run-sa@ace-fruit-XXXX.iam.gserviceaccount.com
gcloud storage ls --impersonate-service-account=fruit-run-sa@...
```
(Alert policies are easiest to create in the console or from a JSON file with `gcloud monitoring policies create --policy-from-file`.)

**Cost:** small. Watch the Data Access audit log volume and the BigQuery sink size, and turn them off afterwards.

**Teardown (end of every session):**
```bash
gcloud logging sinks delete fruit-to-bq -q ; gcloud logging sinks delete fruit-to-bucket -q
gcloud logging buckets delete fruit-logs --location=global -q
gcloud logging metrics delete fruit_not_found -q
bq rm -r -f -d ace-fruit-XXXX:logs_ds
gcloud iam roles delete fruitReader --project=ace-fruit-XXXX -q
gcloud projects remove-iam-policy-binding ace-fruit-XXXX --member=user:friend@gmail.com \
  --role=projects/ace-fruit-XXXX/roles/fruitReader --all
gcloud iam service-accounts remove-iam-policy-binding fruit-run-sa@ace-fruit-XXXX.iam.gserviceaccount.com \
  --member=user:YOU --role=roles/iam.serviceAccountTokenCreator
gcloud compute instances delete fruit-vm --zone=us-central1-a -q             # the Ops Agent VM
# Console: Monitoring → Alerting → delete alert policies and notification channels;
#          Monitoring → Uptime checks → delete fruit-up;
#          IAM & Admin → Audit Logs → turn Data Access logs back off.
# plus the Week 3 teardown block for the Cloud Run service, repo and SA
bash scripts/ace-leftovers.sh ace-fruit-XXXX
```

**Checkpoint**
- An alert email received for a forced 5xx.
- You can describe the four audit-log types.
- **Take the official sample questions** and aim for 80% or more.

### Week 7 — Revision and exam

- Days 1–2: go through the exam-guide checklist in §1. Mark each bullet green, amber or red and redo the labs for the red ones in Cloud Shell, in **one** throwaway session each.
- Days 3–4: two full timed practice exams. For every wrong answer, write the doc link and the reason in `notes/mistakes.md`.
- Day 5: rapid review of the gcloud command groups (`compute`, `container`, `run`, `sql`, `storage`, `iam`, `logging`, `billing`), plus `kubectl` and `bq`.
- Day 6: light review and exam logistics (ID, room check for an online exam).
- Day 7: **exam.** Afterwards, `gcloud projects delete ace-fruit-XXXX` and check the billing report a few days later.

---

## 4. Recommended official resources

- **Exam guide:** <https://cloud.google.com/learn/certification/guides/cloud-engineer>
- **Certification page:** sample questions, registration, renewal: <https://cloud.google.com/learn/certification/cloud-engineer>
- **Google Cloud Skills Boost:** the *Associate Cloud Engineer* learning path, including the "Preparing for Your Associate Cloud Engineer Journey" course and the hands-on labs (Qwiklabs labs run in temporary projects, so they cost you nothing): <https://www.cloudskillsboost.google>
- **gcloud CLI cheat sheet:** <https://cloud.google.com/sdk/docs/cheatsheet>
- **Free tier and pricing calculator:** <https://cloud.google.com/free>, <https://cloud.google.com/products/calculator>
- **Decision guides:** the "Choose a compute option" and "Choose a database" pages in the Google Cloud docs, and the Architecture Center
- **Optional third-party practice exams** can help with timing, but always check answers against the official docs.

## 5. Daily log template (`notes/weekN.md`)

```
## Day N – topic
- Did:
- Commands that mattered:
- Gotcha / exam fact:
- Resources created today (each one also in notes/resources.md):
- Teardown run? ace-leftovers.sh output (must be "CLEAN"):
```
