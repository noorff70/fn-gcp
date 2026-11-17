# Day 1 – gcloud setup, project, billing and budget (Week 1, exam §1.1–1.2)

**Goal:** a clean gcloud configuration pointing at the practice project, billing checked, a budget
alert in place, the core APIs enabled, and one practice project created and deleted again.
**Billable resources created today: none.** (Projects, budgets, configurations and enabled APIs are free.)

> This file is in a **public** repo. Billing account ID, passwords and keys go in `private/` only.
> Run the commands below in **PowerShell** on your PC (one line each; no `\` line continuations).

## Starting point (checked 2026-11-16)

| Item | State |
|---|---|
| Google Cloud CLI | Installed, SDK 593.0.0 (plus `bq`, `gsutil`) |
| Docker Desktop | Installed, 29.9.2 |
| gcloud login | Logged in with one account |
| gcloud config | Only `default`; its project is set to `fn-gcp`, which **doesn't exist / no access**. Fix in step 1. |
| Practice project | **`fn-fruits`** exists with billing enabled. |
| Billing accounts | One open account (currency **CAD**) and one closed one. The open account's ID is in `private/billing-id.txt` (not in this public file). |
| Resources in `fn-fruits` | None (no VMs, disks, IPs, buckets, load balancers) |

---

## Step 1 – A clean gcloud configuration called `ace`

```powershell
gcloud config configurations create ace
gcloud config set account YOUR_GOOGLE_ACCOUNT
gcloud config set project fn-fruits
gcloud config set compute/region us-central1
gcloud config set compute/zone us-central1-a
gcloud config list
gcloud config configurations list
```
Notes:
- `gcloud config configurations activate default` / `ace` switches between configurations.
- Exam fact: a configuration is a named set of properties (account, project, region, zone).
  `CLOUDSDK_CORE_PROJECT` env var or `--project` flag override it for one command.

## Step 2 – Look around the project

```powershell
gcloud projects describe fn-fruits
gcloud projects get-iam-policy fn-fruits --format=json
gcloud services list --enabled
gcloud services list --available --filter="name:run.googleapis.com"
```
Observed: about 27 APIs are already enabled (BigQuery, Compute, Logging, Monitoring, Cloud SQL
component, Storage, OS Login …). Enabling an API is free; using it is what costs.

## Step 3 – Billing: account ID into `private/`, check the link

```powershell
gcloud billing accounts list
gcloud billing accounts list --filter="open=true" --format="value(name.basename())" | Out-File -Encoding ascii private\billing-id.txt
$BILLING = (Get-Content private\billing-id.txt).Trim()
gcloud billing projects describe fn-fruits
```
Exam facts:
- One billing account can pay for many projects; a project has at most one billing account.
- Roles: **Billing Account Administrator** (manage the account), **Billing Account User** (link
  projects to it), **Project Billing Manager** (link/unlink a project), **Billing Account Viewer**.
- Linking needs *Billing Account User* on the account **and** *Project Billing Manager* (or Owner) on the project.

## Step 4 – Budget alert (the cost-safety net)

**Done 2026-11-16.** This is the command that was run:
```powershell
$BILLING = (Get-Content private\billing-id.txt).Trim()
gcloud billing budgets create --billing-account=$BILLING --display-name="ace-study" --budget-amount=15CAD --threshold-rule=percent=0.5 --threshold-rule=percent=1.0 --billing-project=fn-fruits
# -> Created [f9c8671c-2547-4aa1-8cd8-d23c86bcb2fa]
gcloud billing budgets list --billing-account=$BILLING --billing-project=fn-fruits
gcloud billing budgets describe f9c8671c-2547-4aa1-8cd8-d23c86bcb2fa --billing-account=$BILLING --billing-project=fn-fruits
```
Result: budget **`ace-study`**, **15 CAD per month**, email alerts at **50% (7.50 CAD)** and **100% (15 CAD)** of actual spend.

Optional extra: an early warning based on *forecast* spend. You can add it in the console, or with `gcloud billing budgets update ... "--add-threshold-rule=percent=1.0,basis=forecasted-spend"` (the quotes are needed in PowerShell; see the gotcha in Step 6).

Notes:
- **Why `--billing-project=fn-fruits`?** The Budgets API bills its own API calls to a "quota project". Without the flag, gcloud uses the active config's project. That was still the non-existent `fn-gcp`, so the call failed. Once step 1 sets the `ace` config to `fn-fruits`, the flag isn't needed.
- The amount must be in the billing account's currency (**CAD**).
- With no `--filter-projects`, the budget covers **all projects** on the billing account – what we want.
- Exam fact: budgets **only send alerts** (email to billing admins, optionally Pub/Sub). They never
  stop spending; to cap costs you'd wire a Pub/Sub topic to a function that disables billing.
- The budget is **kept** until the exam (allowed exception to the teardown rule).

Optional (console only): **Billing → Billing export → BigQuery export** to a dataset named
`billing_export` in `fn-fruits`. Exam fact: export only contains data from the day it's turned on.

## Step 5 – Enable the APIs for the coming weeks

```powershell
gcloud services enable run.googleapis.com artifactregistry.googleapis.com cloudbuild.googleapis.com iam.googleapis.com cloudresourcemanager.googleapis.com
gcloud services list --enabled --filter="name:(run OR artifactregistry OR cloudbuild)"
```

## Step 6 – Practise the project lifecycle (create → inspect → delete)

Write the ledger row in `notes/resources.md` **first**, then:
```powershell
$SCRATCH = "fn-scratch-$(Get-Random -Minimum 1000 -Maximum 9999)"
gcloud projects create $SCRATCH --name="ACE scratch" "--labels=course=ace,week=1"
gcloud projects list
gcloud projects describe $SCRATCH
gcloud projects delete $SCRATCH --quiet
gcloud projects list --filter="lifecycleState=DELETE_REQUESTED"
```
Exam facts:
- Project **ID** is globally unique and permanent; project **name** can change; project **number** is assigned by Google.
- A deleted project sits in `DELETE_REQUESTED` for ~30 days; `gcloud projects undelete ID` restores it.
- Without an organization, projects have no parent – folders and org policies need an org (Cloud Identity / Workspace).
- Label keys and values may only contain lowercase letters, numbers, `-` and `_`.

**PowerShell gotcha (hit on Day 1):** unquoted, `--labels=course=ace,week=1` fails with
*"Bad value [ace week=1]"*. In PowerShell a comma builds an **array**, so the argument is split and
gcloud receives `ace week=1` as a value containing a space. Fix: wrap the whole argument in quotes,
`"--labels=course=ace,week=1"`. This applies to every flag whose value contains a comma
(`--labels`, `--threshold-rule=...,basis=...`, `--tags=a,b`, `--allow=tcp:22,tcp:80`, …).
Bash / Cloud Shell doesn't have this problem.

## Step 7 – IAM warm-up (read-only)

```powershell
gcloud iam roles list --filter="name:roles/billing" --format="value(name,title)"
gcloud iam roles describe roles/billing.projectManager
gcloud iam roles describe roles/viewer --format="value(includedPermissions)" | Measure-Object -Line
```
Exam fact: prefer **predefined** roles over **basic** roles (Owner/Editor/Viewer) – least privilege.

## Step 8 – Teardown and proof

- Nothing billable was created. The scratch project was deleted in step 6.
- Kept on purpose: the `ace` configuration, budget `ace-study`, enabled APIs.
- Leftovers check: open **Cloud Shell** (console, top-right `>_`), then
  ```bash
  git clone https://github.com/noorff70/fn-gcp && cd fn-gcp && bash scripts/ace-leftovers.sh fn-fruits
  ```
  Expected: `CLEAN`. Record the result below.

---

## Checkpoint (answer without notes)

1. What is the difference between project ID, name and number?
2. Which role lets someone link *any* project to a billing account, and what else do they need on the project?
3. Does a budget stop spending at 100%? What would you use if you needed a hard cap?
4. How do you run one command against a different project without changing your configuration?
5. Where do folders and organization policies come from, and why doesn't a plain Gmail account have them?

## My log (fill in)

- Date / time spent: 2026-11-16
- Steps done:
  - Step 1: `ace` configuration created and active (project `fn-fruits`, `us-central1` / `us-central1-a`). The old `default` config (project `fn-gcp`) is still there but inactive.
  - Step 3: billing account ID saved in `private/billing-id.txt`.
  - Step 4: budget `ace-study` created (15 CAD, 50% / 100%, ID `f9c8671c-2547-4aa1-8cd8-d23c86bcb2fa`).
  - Step 5: APIs enabled: `run`, `artifactregistry`, `cloudbuild`, `billingbudgets`.
  - Step 6: project `fn-scratch-8998` created with labels, described, deleted (now `DELETE_REQUESTED`).
- Output worth remembering:
  - Asking about a project that doesn't exist gives *"does not have permission … (or it may not exist)"*. Google doesn't reveal which, on purpose.
  - A deleted project disappears from `gcloud projects list` (active only) but `gcloud projects describe` still shows `DELETE_REQUESTED`.
- Gotchas:
  - With the active config still on `fn-gcp`, every command failed until Step 1 was done. The budget needed `--billing-project=fn-fruits` as a workaround.
  - PowerShell splits `--labels=course=ace,week=1` at the comma, so quote the whole argument.
  - `$SCRATCH = "fn-scratch-$(Get-Random ...)"` makes a new ID each time it runs. The first describe used `fn-scratch-5269`, which never existed. Print `$SCRATCH` right after creating it.
- `ace-leftovers.sh` result: not run (needs Cloud Shell). Manual check of `fn-fruits` was clean.
