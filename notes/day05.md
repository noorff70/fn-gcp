# Day 5 – Artifact Registry, Cloud Build, Cloud Run (Week 3, exam §2.2, §3.3, §4.3, §5.2)

**Goal:**
- Your **Dockerfile** finally runs in the cloud. You build it with **Cloud Build** (no local Docker needed), store the image in **Artifact Registry**, and run it on **Cloud Run** with its own **service account** that has no roles.
- Then: a `cloudbuild.yaml` pipeline (tests → build → push), a **v2 revision with no traffic**, a **90/10 traffic split**, a **rollback**, and switching between **public and private** access.
- **Delete everything** at the end.
- Day 6 covers the rest of Week 3: Cloud Storage and an event-driven function.

**What it costs (rough, check current pricing):**
- Cloud Run: free tier of 2 million requests and 180,000 vCPU-seconds a month. `--min-instances=0` means nothing runs when idle.
- Cloud Build: 2,500 free build-minutes a month. Each build here takes 1–3 minutes.
- Artifact Registry: 0.5 GB free. One image is about 0.15 GB, and both tags share most layers.
- `gcloud builds submit` creates a bucket `gs://fn-fruits_cloudbuild` for the uploaded source. It's a few MB in a US multi-region bucket: cents at most. **It's deleted in Step 9.**
- Expect **close to 0** for the day.

> Public repo: don't write the identity token or any URL with a token in this file.
> PowerShell from `D:\dev\gcp`. Quote arguments that contain commas.

## Starting point (checked 2026-11-23)

| Item | State |
|---|---|
| gcloud | `ace` config → `md.faizul.noor@gmail.com`, `fn-fruits`, `us-central1` |
| Git | `master` = `fn-fruit/master` = `0c77653`, tagged `v-04`, working tree clean |
| APIs | `run`, `artifactregistry`, `cloudbuild`, `iam`, `storage` already **enabled** |
| `fn-fruits` | No Artifact Registry repos, Cloud Run services or buckets. The only service account is the Compute Engine default one, `904127384278-compute@...` (has `roles/editor`; Cloud Build uses it by default). |
| Tests | 3 test files under `fruit/tests/`. **pytest isn't installed** on your PC yet (Step 4). |
| Ledger | All Day 4 rows ticked. The Day 3 Cloud Shell clone row is still `[ ]`. Tick it if the clone is gone. |

## How the pieces connect

```
 your PC ── gcloud builds submit ──► Cloud Build (uploads source to gs://fn-fruits_cloudbuild)
                                        │  runs pytest, docker build
                                        ▼
                      Artifact Registry  us-central1-docker.pkg.dev/fn-fruits/fruit-repo/fruit:v1, :v2
                                        │
                                        ▼  gcloud run deploy
                      Cloud Run service "fruit" (us-central1)
                        ├─ revision fruit-00001-xxx (v1)  ◄── 90 %
                        ├─ revision fruit-00002-xxx (v2)  ◄── 10 %   (+ tag URL https://ver2---fruit-....run.app)
                        └─ runs as fruit-run-sa (no roles)
```

---

## Step 1 – Artifact Registry repo

Write the ledger row first, then:
```powershell
gcloud artifacts repositories create fruit-repo --repository-format=docker --location=us-central1 --description="ACE day 5" "--labels=course=ace,week=3"
gcloud artifacts repositories list
$IMG = "us-central1-docker.pkg.dev/fn-fruits/fruit-repo/fruit"
```
Exam facts:
- Image path format: **`LOCATION-docker.pkg.dev/PROJECT/REPO/IMAGE:TAG`**.
- **Container Registry (`gcr.io`) is shut down.** Artifact Registry replaced it, and it stores Docker images, Maven, npm, Python and other packages.
- Pull and push access is IAM on the repo: `roles/artifactregistry.reader` and `.writer`.

## Step 2 – Check what will be uploaded, then build v1 with Cloud Build

`gcloud builds submit` uploads your folder. Make sure `private/` **never** leaves your PC. Create **`.gcloudignore`** in the repo root:
```
.gcloudignore
.git
.gitignore
private/
.env*
__pycache__/
*.pyc
notes/
venv/
.venv/
```
Then list exactly which files would be uploaded:
```powershell
gcloud meta list-files-for-upload
```
Expect to see `Dockerfile`, `requirements.txt`, `fruit\...` and `data\inventory.db`. There should be **nothing** from `private\`.

Write the ledger rows (image and Cloud Build bucket) first, then build:
```powershell
gcloud builds submit --tag="${IMG}:v1"
gcloud artifacts docker images list $IMG --include-tags
gcloud builds list --limit=3
```
- No Docker on your PC is needed. Cloud Build runs `docker build` on a Google VM and pushes the image.
- The first build creates **two** buckets, both yours, both deleted in Step 9:
  - `gs://fn-fruits_cloudbuild` holds the uploaded source.
  - `gs://904127384278-global-cloudbuild-logs` holds the build logs (seen on 2026-11-23). The `cloudbuild.yaml` in Step 4 uses `CLOUD_LOGGING_ONLY`, so it doesn't write here.
- Where the build ran: on a short-lived VM in a **Google-owned** project. It's not in `fn-fruits`, so `gcloud compute instances list` stays empty, and you pay per build-minute, not for a VM.

Exam facts:
- `gcloud builds submit --tag` needs a Dockerfile. `--config=cloudbuild.yaml` runs your own steps instead (Step 4).
- Without a `.gcloudignore`, gcloud uses your `.gitignore` rules. Writing `.gcloudignore` yourself makes it explicit.

## Step 3 – Service account with no roles, then deploy v1 to Cloud Run

Write the ledger rows (SA and Cloud Run service) first, then:
```powershell
gcloud iam service-accounts create fruit-run-sa --display-name="Fruit Cloud Run SA"
$SA = "fruit-run-sa@fn-fruits.iam.gserviceaccount.com"
gcloud run deploy fruit --image="${IMG}:v1" --region=us-central1 --service-account=$SA --allow-unauthenticated --min-instances=0 --max-instances=2 --concurrency=40 --cpu=1 --memory=512Mi "--labels=course=ace,week=3"
$URL = gcloud run services describe fruit --region=us-central1 --format="value(status.url)"
$URL
Invoke-RestMethod "$URL/fruits"
```
- **Gotcha (seen 2026-11-23):** `$URL/healthz` returns Google's own **404 "robot" page**, and the request never reaches your app. Cloud Run **reserves some paths ending in `z`**, `/healthz` among them. Use `/fruits` for v1; v2 adds a `/health` route (Step 4a). `/healthz` still works on VMs and behind the load balancer (Days 3–4).
- Cloud Run sets the `PORT` env var to 8080. Your Dockerfile's `CMD ... --port ${PORT:-8080}` already handles it.
- The app needs no Google APIs, so `fruit-run-sa` needs **no roles**. That's least privilege. If it later reads a bucket, you'd grant just that one role on just that bucket.

Exam facts:
- **Runtime identity:** without `--service-account`, Cloud Run uses the Compute Engine default SA, which has **Editor**. That's far too much power for a web app, and a typical exam trap.
- **Concurrency:** requests per container instance at the same time (default 80, max 1000). Set it to `1` for code that isn't thread-safe.
- **`--min-instances=0`** scales to zero (cold starts, no idle cost). `--min-instances=1` avoids cold starts but is billed while idle. **`--max-instances`** is your cost cap.
- Cloud Run is **stateless**. The container file system is in memory and lost when the instance stops. Anything the app writes to `inventory.db` on Cloud Run is gone later. Real data goes to Cloud SQL, Firestore or Cloud Storage (Week 4).
- **Services vs jobs:** a service answers HTTP requests. A job runs to completion and then stops (Step 8).

## Step 4 – v2 code change and a `cloudbuild.yaml` pipeline (tests → build → push)

**4a. Code change.** You make it, then I review it. In `fruit/main.py`, add a `/health` route (no `z`, so Cloud Run lets it through) that also returns a version read from an env var. Keep `/healthz` as it is, because the VM/MIG health check from Days 3–4 uses it:
```python
import os
...
@app.get("/healthz")
def healthz():
    return {"status": "ok"}

@app.get("/health")
def health():
    return {"status": "ok", "version": os.getenv("APP_VERSION", "v1")}
```

**4b. Run the tests locally first.** A failing test would stop the pipeline in the cloud too.
```powershell
python -m pip install pytest
python -m pytest -q
```
Gotcha to check: in `fruit/tests/services/test_fruit_service.py`, `def test_service_sorting():` is indented **inside** `class FakeFruitRepository`. pytest only collects test functions at module level, or in classes whose name starts with `Test`, so this test **never runs**. Move it out to the top level, with no indent.

**4c. Create `cloudbuild.yaml`** in the repo root:
```yaml
steps:
  - id: test
    name: python:3.14-slim
    entrypoint: bash
    args: ["-c", "pip install --no-cache-dir -r requirements.txt pytest && python -m pytest -q"]
  - id: build
    name: gcr.io/cloud-builders/docker
    args: ["build", "-t", "us-central1-docker.pkg.dev/$PROJECT_ID/fruit-repo/fruit:${_TAG}", "."]
images:
  - us-central1-docker.pkg.dev/$PROJECT_ID/fruit-repo/fruit:${_TAG}
substitutions:
  _TAG: dev
options:
  logging: CLOUD_LOGGING_ONLY
```
- Each step runs in its own container. They share the `/workspace` folder, which holds your uploaded source.
- `images:` tells Cloud Build to **push** the image after all steps pass.
- `$PROJECT_ID` is a built-in substitution. Your own substitutions must start with `_`, like `_TAG`.
- `gcr.io/cloud-builders/docker` is Google's builder image. It's still served from gcr.io even though Container Registry is shut down for your own images.

Build v2 (`.gcloudignore` from Step 2 still applies):
```powershell
gcloud builds submit --config=cloudbuild.yaml --substitutions=_TAG=v2
gcloud artifacts docker images list $IMG --include-tags
```
If the `test` step fails, the build stops and **nothing is pushed**. That's the point of a pipeline.

Exam facts:
- Cloud Build **triggers** can start a build on a GitHub push. That's the next step after `builds submit`; we don't set one up today.
- Build logs are in **Cloud Logging** (`options.logging`) and in the console under Cloud Build → History.

## Step 5 – v2 revision with no traffic, 90/10 split, rollback

Write down the v1 revision name, then deploy v2 **without sending it traffic**:
```powershell
$V1 = gcloud run revisions list --service=fruit --region=us-central1 --format="value(metadata.name)" --limit=1
$V1
gcloud run deploy fruit --image="${IMG}:v2" --region=us-central1 --no-traffic --tag=ver2 --set-env-vars=APP_VERSION=v2
gcloud run services describe fruit --region=us-central1 --format="yaml(status.traffic)"
```
The `ver2` tag gets its own URL, `https://ver2---fruit-<hash>.run.app` (a tag must be **at least 3 characters**: `--tag=v2` fails with "must be at least 3 characters long"). Test it there while the main URL still serves v1 to everyone:
```powershell
$V2URL = (gcloud run services describe fruit --region=us-central1 --format=json | ConvertFrom-Json).status.traffic | Where-Object { $_.tag -eq "ver2" } | Select-Object -ExpandProperty url
$V2URL
Invoke-RestMethod "$V2URL/health"        # version: v2
Invoke-RestMethod "$URL/health"          # 404 from your app: the v1 image has no /health route yet
```
If `$V2URL` comes out empty, copy the tag URL from the `status.traffic` output above.

**Canary: send 10% to v2.**
```powershell
gcloud run services update-traffic fruit --region=us-central1 --to-tags=ver2=10
1..30 | ForEach-Object { try { (Invoke-RestMethod "$URL/health").version } catch { "v1 (no /health)" } } | Group-Object | Select-Object Name,Count
```
About 3 of 30 should show `v2`. The rest show `v1 (no /health)`.

**Rollback: everything back to v1.**
```powershell
gcloud run services update-traffic fruit --region=us-central1 --to-revisions="$V1=100"
```
**Promote: everything to the newest revision.**
```powershell
gcloud run services update-traffic fruit --region=us-central1 --to-latest
gcloud run revisions list --service=fruit --region=us-central1
```
Exam facts:
- Every deploy (or config change, like a new env var) creates a new **immutable revision**. Traffic is split between revisions by percentage.
- **Rollback** means moving traffic back to an old revision. Nothing is rebuilt, so it's instant.
- `--no-traffic` + `--tag` = test a new version in production, at its own URL, before any user sees it.
- `--to-latest` makes the service follow every new deploy automatically again.

## Step 6 – Public vs private access

```powershell
gcloud run services get-iam-policy fruit --region=us-central1          # allUsers → roles/run.invoker = public
gcloud run services remove-iam-policy-binding fruit --region=us-central1 --member=allUsers --role=roles/run.invoker
Invoke-RestMethod "$URL/health"        # now fails: 403 Forbidden
$TOKEN = gcloud auth print-identity-token
Invoke-RestMethod "$URL/health" -Headers @{ Authorization = "Bearer $TOKEN" }   # works: you're Owner, which includes run.invoker
Remove-Variable TOKEN
```
- The token is a **secret** for about an hour. Keep it in the variable only. Never paste it into a file or chat.
- Making it public again would be `gcloud run services add-iam-policy-binding fruit --region=us-central1 --member=allUsers --role=roles/run.invoker`. You don't need to, since it's deleted in Step 9.

Exam facts:
- **Authentication** (`--allow-unauthenticated` / `--no-allow-unauthenticated`) is IAM: `roles/run.invoker` for `allUsers`, or for specific users and service accounts.
- **Ingress** is separate and network-based: `--ingress=all | internal | internal-and-cloud-load-balancing`.
- Service-to-service calls: the calling service's SA gets `roles/run.invoker` on the target service, and sends an identity token.

## Step 7 – Logs and the console

```powershell
gcloud run services logs read fruit --region=us-central1 --limit=20
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=fruit" --limit=5 --format="table(timestamp,httpRequest.status,httpRequest.requestUrl)"
```
If `gcloud run services logs read` isn't found, use `gcloud beta run services logs read ...`.

In the console, open **Cloud Run → fruit**. Look at the **Metrics** (request count, latency, instance count), **Revisions** (with the traffic split) and **YAML** tabs. The YAML is the Knative-style definition of everything you set with flags.

## Step 8 – (Optional, 5 min) A Cloud Run job

Write the ledger row first, then:
```powershell
gcloud run jobs create fruit-job --image="${IMG}:v2" --region=us-central1 --service-account=$SA --command=python --args=--version --max-retries=0 "--labels=course=ace,week=3"
gcloud run jobs execute fruit-job --region=us-central1 --wait
gcloud run jobs executions list --job=fruit-job --region=us-central1
gcloud logging read "resource.type=cloud_run_job AND resource.labels.job_name=fruit-job" --limit=5 --format="value(textPayload)"
```
The log should show `Python 3.14.x`. It's the same image as the service, with a different command, and it runs once and exits.

Exam facts: jobs have **tasks** (`--tasks=N` runs N copies in parallel, each with its own `CLOUD_RUN_TASK_INDEX`), `--max-retries`, and `--task-timeout`. You schedule a job with **Cloud Scheduler**.

---

## Step 9 – Teardown (everything created today)

```powershell
gcloud run jobs delete fruit-job --region=us-central1 --quiet                 # only if you did Step 8
gcloud run services delete fruit --region=us-central1 --quiet                 # deletes all its revisions
gcloud artifacts repositories delete fruit-repo --location=us-central1 --quiet   # deletes the v1 and v2 images
gcloud iam service-accounts delete fruit-run-sa@fn-fruits.iam.gserviceaccount.com --quiet
gcloud storage rm --recursive gs://fn-fruits_cloudbuild                       # source uploads + the bucket itself
gcloud storage rm --recursive gs://904127384278-global-cloudbuild-logs        # build logs from the --tag build (Step 2)
```
Check that nothing is left:
```powershell
gcloud run services list
gcloud run jobs list --region=us-central1
gcloud artifacts repositories list
gcloud iam service-accounts list --format="value(email)"        # only 904127384278-compute@... must remain
gcloud storage buckets list --format="value(name)"              # must be empty
```
- **Build history** (`gcloud builds list`) stays. It can't be deleted and costs nothing.
- **Kept on purpose:** the new files `.gcloudignore`, `cloudbuild.yaml` and your `main.py` / test change. They're code, not cloud resources. Commit them; Weeks 4–6 rebuild the image with them.
- **Cloud Shell:** if you cloned the repo there, remove the clone with `rm -rf ~/fn-gcp`.

## Checkpoint (answer without notes)

1. Write the full Artifact Registry path for image `fruit`, tag `v2`, in repo `fruit-repo`, project `fn-fruits`, region `us-central1`.
2. What does `gcloud builds submit --tag` need in the folder? What does `images:` in `cloudbuild.yaml` do?
3. Which service account does Cloud Run use when you don't pass `--service-account`, and why is that a problem?
4. How do you test a new Cloud Run version in production with zero user traffic? How do you then roll back in seconds?
5. `--allow-unauthenticated` vs `--ingress=internal`: which one is IAM, and which one is network?
6. What do `--concurrency`, `--min-instances` and `--max-instances` control? Which one is the cost cap, and which one causes idle cost?
7. Cloud Run service vs Cloud Run job: when would you use each?

## My log (fill in)

- Date / time spent:
- Steps done:
- Output worth remembering:
- Gotchas:
- Teardown checks:
