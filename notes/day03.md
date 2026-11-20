# Day 3 – Compute Engine: a VM that runs the fruit API (Week 2, exam §2.1, §3.1, §4.1)

**Goal:** run the fruit API on a **free-tier `e2-micro` VM** started by a **startup script**, and practise the core Compute Engine skills:
- firewall rule with a network tag
- SSH with OS Login
- inventory with filters
- stop and start
- snapshot and custom image

Then **delete everything**.

**What it costs:**
- `e2-micro` with a 10 GB **standard** disk in `us-central1` is covered by the Always Free tier (one VM per billing account per month).
- The VM's external IPv4 address, the snapshot and the image are billed per hour or per GB. Kept for a couple of hours, that's a few cents at most.
- **Everything is deleted in Step 10.**

> This file is in a **public** repo, so don't paste your home IP address or keys here. Keep them in `private/` if you need to.
> Local steps run in **PowerShell** from `D:\dev\gcp`. Quote any argument whose value contains a comma, e.g. `"--labels=course=ace,week=2"`.

## Starting point (checked 2026-11-20)

| Item | State |
|---|---|
| gcloud | `ace` config → `fn-fruits`, `us-central1-a`. Logged in as your renamed account. |
| `fn-fruits` | No VMs, disks, buckets or firewall rules of ours. Compute Engine API enabled. |
| Day 2 work | **Committed and pushed** as `4d8d7e5`, tagged `v-02`. GitHub `master` has `/healthz` and a UTF-8 `requirements.txt`, which is what the VM clones. |
| `.dockerignore` | In the root with the correct name. Committed. |

---

## Step 0 – Check GitHub has the code the VM will clone (read-only)

```powershell
cd D:\dev\gcp
git status -sb                      # expect: ## master...fn-fruit/master, nothing else
git fetch fn-fruit
git show fn-fruit/master:fruit/main.py | Select-String healthz
```
If `healthz` shows up, the VM will get the right version. At the end of the day, tag the commit (`git tag -a v-03 -m "Day 03"`) and push it with `git push fn-fruit v-03`.

## Step 1 – Look before you create (read-only)

```powershell
gcloud compute regions list --format="table(name,status)" | Select-Object -First 8
gcloud compute zones list --filter="region:us-central1" --format="value(name)"
gcloud compute machine-types list --zones=us-central1-a --filter="name~^e2-" --format="table(name,guestCpus,memoryMb)"
gcloud compute images list --filter="family~debian-12" --format="table(name,family,project)"
gcloud compute firewall-rules list --format="table(name,network,sourceRanges.list(),allowed[].map().firewall_rule().list(),targetTags.list())"
```
Exam facts:
- **Machine families:**
  - E2 is cheap, general-purpose and shared-core (`e2-micro`, `e2-small`).
  - N2/N4 are balanced.
  - C3/C4 are compute-optimised.
  - M-series are memory-optimised.
  - A/G are GPU machines.
- **Custom machine types** let you choose vCPUs and memory yourself, for example `--custom-cpu=2 --custom-memory=4GB`.
- **Spot VMs** cost much less but Google can stop them at any time (`--provisioning-model=SPOT`).
- The `default` network comes with `default-allow-ssh`, `-rdp`, `-icmp` and `-internal` rules. Port **8080 is not open**, which is why Step 3 creates a rule for it.

## Step 2 – The startup script (create the file)

Create `scripts/startup-fruit.sh`. It runs as **root on every boot**.

⚠ Save it with **LF** line endings: in VS Code, click `CRLF` in the bottom-right corner and choose `LF`. A script with CRLF fails on Linux with `$'\r': command not found`.

```bash
#!/bin/bash
# Compute Engine startup script: install and run the fruit API on port 8080.
set -euxo pipefail
APP_DIR=/opt/fn-gcp

if [ ! -d "$APP_DIR" ]; then
  apt-get update
  apt-get install -y git python3-venv
  git clone https://github.com/noorff70/fn-gcp.git "$APP_DIR"
  python3 -m venv "$APP_DIR/venv"
  "$APP_DIR/venv/bin/pip" install --no-cache-dir -r "$APP_DIR/requirements.txt"
fi

cat > /etc/systemd/system/fruit.service <<'EOF'
[Unit]
Description=Fruit FastAPI
After=network-online.target

[Service]
WorkingDirectory=/opt/fn-gcp
Environment=DATABASE_URL=data/inventory.db
ExecStart=/opt/fn-gcp/venv/bin/uvicorn fruit.main:app --host 0.0.0.0 --port 8080
Restart=always

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable --now fruit
```
Check the line endings. This must print `False`:
```powershell
(Get-Content -Raw scripts\startup-fruit.sh) -match "`r`n"
```

## Step 3 – Firewall rule: port 8080 only from your IP, only to tagged VMs

Write the ledger row first, then:
```powershell
$MYIP = (Invoke-RestMethod https://api.ipify.org).Trim()
gcloud compute firewall-rules create allow-fruit-8080 --network=default --direction=INGRESS --action=ALLOW --rules=tcp:8080 --source-ranges="$MYIP/32" --target-tags=fruit-web --description="ACE day 3: fruit API from my IP"
gcloud compute firewall-rules describe allow-fruit-8080 --format="yaml(direction,allowed,sourceRanges,targetTags,priority)"
```
Exam facts:
- Firewall rules belong to a **VPC network**, not to a VM. They pick their target VMs by **network tag** or **service account**.
- Rules are **stateful** (reply traffic is allowed automatically).
- Priority runs from 0 to 65535, and the **lower number wins**.
- Every network has two implied rules: allow all egress, and deny all ingress.

## Step 4 – Create the VM (free-tier shape)

Write the ledger row first, then:
```powershell
gcloud compute instances create fruit-vm --zone=us-central1-a --machine-type=e2-micro --image-family=debian-12 --image-project=debian-cloud --boot-disk-type=pd-standard --boot-disk-size=10GB --tags=fruit-web --metadata=enable-oslogin=TRUE --metadata-from-file=startup-script=scripts\startup-fruit.sh "--labels=course=ace,week=2"
gcloud compute instances list --format="table(name,zone.basename(),machineType.basename(),status,networkInterfaces[0].accessConfigs[0].natIP)"
```
Why each flag:
- `pd-standard` + `10GB`: the free tier covers *standard* PD. The default would be `pd-balanced`, which isn't free.
- `--tags=fruit-web`: this tag is what makes the Step 3 firewall rule apply to this VM.
- `enable-oslogin=TRUE`: SSH access is controlled by **IAM** instead of SSH keys stored in metadata.

## Step 5 – Watch it boot, then call the API

The first boot runs `apt-get` and `pip`, which takes about 2–4 minutes on an `e2-micro`.
```powershell
gcloud compute instances get-serial-port-output fruit-vm --zone=us-central1-a | Select-String "startup-script" | Select-Object -Last 10
$VMIP = gcloud compute instances describe fruit-vm --zone=us-central1-a --format="value(networkInterfaces[0].accessConfigs[0].natIP)"
Invoke-RestMethod "http://$($VMIP):8080/healthz"
Invoke-RestMethod "http://$($VMIP):8080/fruits"
```
If it times out, either the startup script is still running, or your IP changed since Step 3.

## Step 6 – SSH with OS Login and look inside

```powershell
gcloud compute ssh fruit-vm --zone=us-central1-a
```
On Windows this opens a PuTTY window. The first time, gcloud creates a key pair at `~\.ssh\google_compute_engine` and adds the **public** key to your OS Login profile. Inside the VM:
```bash
systemctl status fruit --no-pager
curl -s localhost:8080/healthz
sudo journalctl -u google-startup-scripts --no-pager | tail -20
id ; exit
```
Exam facts:
- With OS Login, SSH access comes from IAM roles: `roles/compute.osLogin`, or `roles/compute.osAdminLogin` for sudo. Your Owner role covers both.
- Other ways in: **IAP TCP forwarding** (`--tunnel-through-iap`, no external IP needed), the browser SSH button, and the serial console.

## Step 7 – Inventory with filters and formats

```powershell
gcloud compute instances list --filter="labels.course=ace AND status=RUNNING" --format="table(name,status,labels)"
gcloud compute instances describe fruit-vm --zone=us-central1-a --format="yaml(id,machineType,scheduling,disks[].source,tags,serviceAccounts[].email)"
gcloud compute disks list --format="table(name,zone.basename(),sizeGb,type.basename(),users.basename())"
```
Look at `scheduling`: `onHostMaintenance: MIGRATE` and `automaticRestart: true` together form the **availability policy**.

## Step 8 – Stop and start (see what changes)

```powershell
gcloud compute instances stop fruit-vm --zone=us-central1-a
gcloud compute instances list --format="table(name,status,networkInterfaces[0].accessConfigs[0].natIP)"
gcloud compute instances start fruit-vm --zone=us-central1-a
gcloud compute instances list --format="table(name,status,networkInterfaces[0].accessConfigs[0].natIP)"
```
Exam facts:
- A **stopped** (`TERMINATED`) VM stops billing for CPU and RAM, but its **disk is still billed**.
- An **ephemeral** external IP usually **changes** after a stop and start. Reserve a **static** IP if you need a fixed one.
- The startup script runs again on every boot. Ours skips the install because `/opt/fn-gcp` already exists.

## Step 9 – Snapshot and custom image

Write the ledger rows first, then:
```powershell
gcloud compute disks snapshot fruit-vm --zone=us-central1-a --snapshot-names=fruit-snap-day3 "--labels=course=ace,week=2"
gcloud compute images create fruit-img-day3 --source-snapshot=fruit-snap-day3 --family=fruit "--labels=course=ace,week=2"
gcloud compute snapshots list --format="table(name,diskSizeGb,storageBytes,status)"
gcloud compute images list --no-standard-images --format="table(name,family,status)"
```
Exam facts:
- A **snapshot** is an incremental backup of one disk. Use it for backup and restore, or to create a new disk.
- An **image** is a bootable template, used to create many VMs (instance templates and MIGs on Day 4).
- **Image families** always point to the newest image in the family.
- Use **snapshot schedules** (resource policies) for automatic backups.
- To create an image straight from a *running* disk you need `--force`. It's safer to stop the VM first, or to create the image from a snapshot, as we did.

---

## Step 10 – Teardown (everything created today)

Order: image → snapshot → VM (its boot disk is deleted with it) → firewall rule → OS Login key.
```powershell
gcloud compute images delete fruit-img-day3 --quiet
gcloud compute snapshots delete fruit-snap-day3 --quiet
gcloud compute instances delete fruit-vm --zone=us-central1-a --quiet
gcloud compute firewall-rules delete allow-fruit-8080 --quiet
gcloud compute os-login ssh-keys list
gcloud compute os-login ssh-keys remove --key-file="$HOME\.ssh\google_compute_engine.pub"
```
Check that nothing is left. Each command must print nothing:
```powershell
gcloud compute instances list ; gcloud compute disks list ; gcloud compute snapshots list
gcloud compute images list --no-standard-images ; gcloud compute firewall-rules list --filter="name=allow-fruit-8080"
gcloud compute os-login ssh-keys list
```
**Cloud Shell (leftovers check).** This also removes the Day 2 clone if it's still there:
```bash
rm -rf ~/fn-gcp && git clone https://github.com/noorff70/fn-gcp.git ~/fn-gcp
bash ~/fn-gcp/scripts/ace-leftovers.sh fn-fruits ; echo "exit code: $?"
rm -rf ~/fn-gcp
```
**Kept on purpose:**
- `scripts/startup-fruit.sh`, which Day 4's instance template reuses (commit it).
- The local key files `~\.ssh\google_compute_engine*` on your PC. They're harmless once they're removed from OS Login. Delete them if you want a fully clean slate.

## Checkpoint (answer without notes)

1. Which flags make a VM fit the free tier, and why does the disk type matter?
2. How does a firewall rule decide which VMs it applies to? What are the two implied rules?
3. What's still billed while a VM is stopped? Why did the external IP change?
4. Snapshot vs image: when would you use each? What is an image family?
5. With OS Login on, which IAM roles let someone SSH in, and which one gives sudo?
6. Name two ways to reach a VM that has **no** external IP.

## My log (fill in)

- Date / time spent:
- Steps done:
- Output worth remembering:
- Gotchas:
- Teardown checks + `ace-leftovers.sh` result:
