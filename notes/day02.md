# Day 2 – Make the app container-ready, IAM bindings, quotas, first Cloud Shell run (Week 1, exam §1.1, §5.1)

**Goal:**
- Fix the project so it runs in a container: UTF-8 requirements, a clean git index, the DB path from settings, `/healthz`, `$PORT`.
- Build and run it in **local Docker**.
- Practise IAM bindings on `fn-fruits` (grant, then **remove**).
- Read quotas.
- Run `scripts/ace-leftovers.sh` in **Cloud Shell** for the first time.

**Billable GCP resources created today: none.** IAM bindings, quota reads and Cloud Shell are free.
**Everything created today is torn down at the end** (Step 8), except the code changes, which are meant to stay.

> This file is in a **public** repo. The second account's email address goes in `private/`, not here.
> Local steps run in **PowerShell** from `D:\dev\gcp`. Cloud Shell steps are marked **(Cloud Shell)** and use bash.
> In PowerShell, quote any argument whose value contains a comma: `"--labels=a=b,c=d"`.

## Starting point (checked 2026-11-19)

| Item | State |
|---|---|
| gcloud | `ace` configuration active → project `fn-fruits`, `us-central1` / `us-central1-a` |
| Git | Branch `master`, in sync with `fn-fruit/master` on GitHub |
| `requirements.txt` | **UTF-16** (starts with bytes `FF FE`). Needs converting. |
| Tracked by mistake | `__pycache__/` folders (`*.pyc`) and `.env.dev` |
| `location_api.py` | Hard-codes `"data/inventory.db"` instead of `settings.DATABASE_URL` |
| `db_context.py` | Imports `fruit.repositories.interfaces`, which doesn't exist. Nothing uses the file. |
| Local Python 3.14 | `fastapi` / `pytest` **not installed**, so we run the app in Docker instead |
| Docker Desktop | Running (engine 29.9.2) |

---

## Step 1 – Re-save `requirements.txt` as UTF-8 (no BOM)

```powershell
cd D:\dev\gcp
$lines = Get-Content requirements.txt
[IO.File]::WriteAllLines("$PWD\requirements.txt", $lines, (New-Object Text.UTF8Encoding $false))
Format-Hex requirements.txt | Select-Object -First 1      # should now start with 61 6E 6E ("ann…"), not FF FE
git diff --stat requirements.txt
```
Why not `Set-Content -Encoding utf8`? In Windows PowerShell 5.1 that writes a UTF-8 **BOM**. pip copes with a BOM, but other tools don't. The .NET call writes plain UTF-8.

## Step 2 – Stop tracking files that shouldn't be in git

Add these lines to the end of `.gitignore`:
```
# Python build output
__pycache__/
*.pyc
```
Then remove them from the git index. The files stay on disk.
```powershell
git rm -r --cached -q __pycache__ fruit .env.dev
git add fruit .gitignore
git status --short          # expect: deleted .env.dev + many *.pyc, nothing else deleted
```
`.env.dev` is already covered by `.env*` in `.gitignore`. It stays on your PC for local runs, and real values belong in `private/`.

## Step 3 – Small code fixes

**3a.** `fruit/api/location_api.py`: use the same setting as `fruit_api.py`:
```python
from fruit.config.settings import settings
...
def get_service():
    repo = SQLiteLocationRepository(settings.DATABASE_URL)
    return LocationService(repo)
```

**3b.** Delete the broken, unused module:
```powershell
git rm fruit/repositories/db_context.py
```

**3c.** `fruit/main.py`: add a health endpoint for load balancers, MIGs, Cloud Run and GKE probes:
```python
@app.get("/healthz")
def healthz():
    return {"status": "ok"}
```

## Step 4 – Dockerfile and `.dockerignore`

`Dockerfile` (project root):
```dockerfile
FROM python:3.14-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY fruit ./fruit
COPY data/inventory.db ./data/inventory.db

# Settings come from env vars in containers (no .env file inside the image)
ENV DATABASE_URL=data/inventory.db ENVIRONMENT=docker

# Don't run as root
RUN useradd --create-home appuser && chown -R appuser /app
USER appuser

EXPOSE 8080
# Cloud Run (and others) tell the app which port to use via $PORT
CMD exec uvicorn fruit.main:app --host 0.0.0.0 --port ${PORT:-8080}
```

`.dockerignore` (project root). It keeps secrets, git history and notes out of the image:
```
.git
**/__pycache__
*.pyc
.env*
private/
notes/
scripts/
*.md
data/inventory1.db
```

## Step 5 – Build and run locally

Write the ledger rows (image, container) in `notes/resources.md` first, then:
```powershell
docker build -t fruit:day2 .
docker images fruit
docker run -d --name fruit-day2 -p 8080:8080 fruit:day2
docker ps --filter name=fruit-day2
Invoke-RestMethod http://localhost:8080/healthz
Invoke-RestMethod http://localhost:8080/fruits
Invoke-RestMethod http://localhost:8080/locations
docker logs fruit-day2
```
Test the `$PORT` contract, the way Cloud Run will start the container:
```powershell
docker run -d --name fruit-day2-port -e PORT=9090 -p 9090:9090 fruit:day2
Invoke-RestMethod http://localhost:9090/healthz
```
Exam / Cloud Run facts:
- Cloud Run sets `PORT` (default 8080). The container must listen on `0.0.0.0:$PORT`.
- Containers should be stateless. A SQLite file inside the image is read-only per instance, which is why Week 4 moves to Cloud SQL.

## Step 6 – IAM: grant a role, check it, remove it

Use a second Google account you own. Keep its email private:
```powershell
"user:SECOND_ACCOUNT@gmail.com" | Out-File -Encoding ascii private\second-member.txt    # edit to the real address
$MEMBER = (Get-Content private\second-member.txt).Trim()
```
Write the ledger rows first, then:
```powershell
gcloud projects add-iam-policy-binding fn-fruits --member=$MEMBER --role=roles/viewer --condition=None
gcloud projects add-iam-policy-binding fn-fruits --member=$MEMBER --role=roles/run.invoker --condition=None
gcloud projects get-iam-policy fn-fruits --flatten="bindings[].members" --filter="bindings.members:'$MEMBER'" --format="table(bindings.role)"
```
Optional: open an Incognito window, sign in as the second account and go to `console.cloud.google.com`. It can **see** `fn-fruits` but can't change anything.

Compare what the two roles allow:
```powershell
gcloud iam roles describe roles/run.invoker
gcloud iam roles describe roles/viewer --format="value(includedPermissions)" | Measure-Object -Line
```
Exam facts:
- An IAM **policy** is a list of **bindings**. Each binding is a role plus members, with an optional **condition**.
- Policies are inherited downwards: org → folder → project → resource. A child can't remove a role granted higher up (except with deny policies).
- **Basic roles** (Owner/Editor/Viewer) are broad. Prefer **predefined** roles, or **custom** roles for least privilege.
- `add-iam-policy-binding` changes one binding. `set-iam-policy` replaces the whole policy and uses the **etag** to avoid overwriting someone else's change.

## Step 7 – Quotas (read-only)

```powershell
gcloud compute project-info describe --project=fn-fruits --flatten=quotas --format="table(quotas.metric,quotas.limit,quotas.usage)"
gcloud compute regions describe us-central1 --flatten=quotas --format="table(quotas.metric,quotas.limit,quotas.usage)" | Select-String "CPUS|IN_USE_ADDRESSES|SSD|INSTANCES"
```
Exam facts:
- **Allocation** quotas (CPUs, IPs) cap how much you can have.
- **Rate** quotas (API requests per minute) cap how fast you can call.
- Some quotas are **global** per project, others are **per region**.
- Increase requests go through **IAM & Admin → Quotas** in the console. Free-trial accounts can't raise some quotas.

## Step 8 – First run of the leftovers check (Cloud Shell)

Console → `>_` (Activate Cloud Shell). Click **Authorize** if asked.
```bash
git clone https://github.com/noorff70/fn-gcp.git
cd fn-gcp
bash scripts/ace-leftovers.sh fn-fruits ; echo "exit code: $?"
```
Expected: `CLEAN` and exit code `0`. Keep this Cloud Shell tab open; Step 9 runs it again after the teardown.

---

## Step 9 – Teardown (everything created today)

**GCP:** remove both IAM bindings and check they're gone:
```powershell
gcloud projects remove-iam-policy-binding fn-fruits --member=$MEMBER --role=roles/run.invoker --condition=None
gcloud projects remove-iam-policy-binding fn-fruits --member=$MEMBER --role=roles/viewer --condition=None
gcloud projects get-iam-policy fn-fruits --flatten="bindings[].members" --filter="bindings.members:'$MEMBER'" --format="table(bindings.role)"   # must print nothing
```

**Local Docker:** remove only today's containers and image:
```powershell
docker rm -f fruit-day2 fruit-day2-port
docker rmi fruit:day2
docker ps -a --filter name=fruit-day2      # must be empty
docker images fruit                        # must be empty
```
⚠ Don't use `docker system prune` or `docker image prune -a`. They would also delete your Study Aid images and containers.

**Cloud Shell:** run the check again, then remove the clone:
```bash
bash ~/fn-gcp/scripts/ace-leftovers.sh fn-fruits ; echo "exit code: $?"
cd ~ && rm -rf ~/fn-gcp
```

**Kept on purpose:**
- the code changes from Steps 1–4 (commit them)
- `private/second-member.txt`, for reuse on later days. It's git-ignored.

## Checkpoint (answer without notes)

1. What three parts make up an IAM binding?
2. Why prefer `add-iam-policy-binding` over `set-iam-policy` for a single change? What does the etag protect against?
3. A user has Viewer on the project, but an org-level policy grants them Editor. What can they do in the project?
4. What must a container do to run on Cloud Run (port, interface, state)?
5. What's the difference between an allocation quota and a rate quota? Give one example of each.

## My log (fill in)

- Date / time spent:
- Steps done:
- Output worth remembering:
- Gotchas:
- `ace-leftovers.sh` result (before / after teardown):
