# Day 4 – Instance template, managed instance group, autoscaling, HTTP load balancer (Week 2, exam §2.1, §2.3, §3.1, §4.1)

**Goal:**
- Turn Day 3's single VM into a **self-healing, autoscaling group** behind a **global external Application Load Balancer**:
  instance template → health check → regional MIG (autohealing and autoscaling) → backend service → URL map → HTTP proxy → forwarding rule.
- Then try a **rolling update**, and spend 5 minutes on a **Spot VM with a custom machine type**.
- **Delete everything** at the end.

**What it costs (rough, check current pricing):**
- MIG instances are `e2-micro` with 10 GB `pd-standard` disks. These count against the same free-tier allowance as Day 3: 730 e2-micro hours and 30 GB of standard disk per month.
- Not free:
  - the LB forwarding rule (about US$0.025/hour)
  - each instance's ephemeral external IP (about US$0.005/hour)
  - the short-lived Spot VM (a few cents)
- For a 3-hour session, expect **well under US$0.50**. **Everything is deleted in Step 11.**

> Public repo: don't write your IP address in this file.
> PowerShell from `D:\dev\gcp`. Quote arguments that contain commas: `"--source-ranges=a,b"`, `"--labels=a=b,c=d"`.

## Starting point (checked 2026-11-22)

| Item | State |
|---|---|
| gcloud | `ace` config → `md.faizul.noor@gmail.com`, `fn-fruits`, `us-central1` / `us-central1-a` |
| Git | `master` = `fn-fruit/master` = `be77a44`, tagged `v-03`. `scripts/startup-fruit.sh` is on GitHub. |
| `fn-fruits` | Clean: 0 VMs, disks, snapshots, images, templates, MIGs, health checks, backend services, URL maps, proxies, forwarding rules, static IPs, custom firewall rules |
| Quotas (us-central1) | CPUs 200 (32 across all regions), in-use IPs 8, forwarding rules 15, health checks 75. Plenty for today. |
| Ledger | Day 3 rows- Ticked. Tick them before adding Day 4. |

## How the pieces connect

```
 browser ──► forwarding rule fruit-fr (global IP, port 80)
               └─► target HTTP proxy fruit-proxy
                     └─► URL map fruit-map (all paths → default service)
                           └─► backend service fruit-be (port name "http", health check fruit-hc)
                                 └─► regional MIG fruit-mig (us-central1, 1–3 VMs from template fruit-tpl)
                                       └─► each VM: startup-fruit.sh → uvicorn on :8080, tag fruit-web
 firewall allow-fruit-hc: tcp:8080 from Google's health-check/LB ranges → tag fruit-web
```

---

## Step 1 – Instance template (reuse the Day 3 startup script)

Write the ledger row first, then:
```powershell
gcloud compute instance-templates create fruit-tpl --machine-type=e2-micro --image-family=debian-12 --image-project=debian-cloud --boot-disk-type=pd-standard --boot-disk-size=10GB --tags=fruit-web --metadata=enable-oslogin=TRUE --metadata-from-file=startup-script=scripts\startup-fruit.sh "--labels=course=ace,week=2"
gcloud compute instance-templates describe fruit-tpl --format="yaml(name,properties.machineType,properties.tags,properties.disks[0].initializeParams)"
```
Exam facts:
- A template is a **read-only** recipe. To change one, create a new template (Step 9).
- `instance-templates create` makes a **global** template by default; add `--instance-template-region` for a regional one.
- Templates can point at an image **family**, so new VMs always get the newest image in it.

## Step 2 – Health check and the firewall rule it needs

Write both ledger rows first, then:
```powershell
gcloud compute health-checks create http fruit-hc --port=8080 --request-path=/healthz --check-interval=10s --timeout=5s --healthy-threshold=2 --unhealthy-threshold=3
gcloud compute firewall-rules create allow-fruit-hc --network=default --direction=INGRESS --action=ALLOW --rules=tcp:8080 "--source-ranges=35.191.0.0/16,130.211.0.0/22" --target-tags=fruit-web --description="ACE day 4: Google health checks and LB to fruit"
```
Exam facts:
- **Health-check probes and Application Load Balancer traffic** come from **`35.191.0.0/16` and `130.211.0.0/22`**. Without a firewall rule for these ranges, every backend shows UNHEALTHY. This is a classic exam question.
- A VM counts as healthy after `healthy-threshold` successful checks in a row, and unhealthy after `unhealthy-threshold` failures in a row.

## Step 3 – Regional managed instance group (MIG) with autohealing

Write the ledger row first, then:
```powershell
gcloud compute instance-groups managed create fruit-mig --region=us-central1 --template=fruit-tpl --size=1 --health-check=fruit-hc --initial-delay=300
gcloud compute instance-groups managed set-named-ports fruit-mig --region=us-central1 --named-ports=http:8080
gcloud compute instance-groups managed list-instances fruit-mig --region=us-central1
```
- `--initial-delay=300` gives the startup script about 5 minutes (apt and pip) before autohealing starts judging the VM.
- The **named port** `http:8080` is how the backend service knows which port to send traffic to.

Exam facts:
- **Zonal vs regional MIG:** a regional MIG spreads VMs across zones, so it survives a zone outage.
- **Managed vs unmanaged:** unmanaged groups have no template, no autoscaling and no autohealing.
- Google recommends separate health checks for autohealing and for load balancing. Using one for both is fine for a lab.

## Step 4 – Autoscaling

```powershell
gcloud compute instance-groups managed set-autoscaling fruit-mig --region=us-central1 --min-num-replicas=1 --max-num-replicas=3 --target-cpu-utilization=0.6 --cool-down-period=90
gcloud compute instance-groups managed describe fruit-mig --region=us-central1 --format="yaml(name,targetSize,autoscaler,namedPorts,autoHealingPolicies)"
```
Exam facts:
- The autoscaler can scale on **CPU utilization**, **load-balancer serving capacity**, **Cloud Monitoring metrics** or **schedules**.
- It scales **out** quickly, but **in** slowly: there's a 10-minute stabilization window, so VMs aren't removed too soon.
- `--max-num-replicas` is your cost cap.

## Step 5 – The load balancer: backend → URL map → proxy → forwarding rule

Write the ledger rows first, then:
```powershell
gcloud compute backend-services create fruit-be --global --load-balancing-scheme=EXTERNAL_MANAGED --protocol=HTTP --port-name=http --health-checks=fruit-hc
gcloud compute backend-services add-backend fruit-be --global --instance-group=fruit-mig --instance-group-region=us-central1 --balancing-mode=UTILIZATION --max-utilization=0.8
gcloud compute url-maps create fruit-map --default-service=fruit-be
gcloud compute target-http-proxies create fruit-proxy --url-map=fruit-map
gcloud compute forwarding-rules create fruit-fr --global --load-balancing-scheme=EXTERNAL_MANAGED --target-http-proxy=fruit-proxy --ports=80
$LBIP = gcloud compute forwarding-rules describe fruit-fr --global --format="value(IPAddress)"
$LBIP
```
Exam facts, choosing a load balancer:

| Need | Load balancer |
|---|---|
| HTTP(S) from the internet, global, URL-based routing | **Global external Application LB** (today's) |
| TCP/UDP, keep the client's source IP | External passthrough Network LB (regional) |
| TCP with SSL offload or proxy | External proxy Network LB |
| Private, inside the VPC | Internal Application LB / Internal passthrough Network LB |

- `EXTERNAL_MANAGED` is the current Envoy-based scheme. `EXTERNAL` is the classic one.
- HTTPS would also need an SSL certificate on a `target-https-proxies` resource.

## Step 6 – Wait for healthy backends, then call the API through the LB

The first VM needs about 3–5 minutes for its startup script. The LB itself takes another few minutes to start serving; until then you'll see 404 or 502.
```powershell
gcloud compute backend-services get-health fruit-be --global          # look for healthState: HEALTHY
Invoke-RestMethod "http://$LBIP/healthz"
Invoke-RestMethod "http://$LBIP/fruits"
```
Repeat `get-health` until it shows `HEALTHY`.

## Step 7 – Load test and watch it autoscale (Cloud Shell)

Cloud Shell has a better connection than home Wi-Fi and includes `ab`. If it's missing, install it with `sudo apt-get install -y apache2-utils`.
```bash
LBIP=<paste the IP from Step 5>
curl -s http://$LBIP/healthz                # must print {"status":"ok"} before you load-test
ab -r -t 300 -n 1000000 -c 50 http://$LBIP/fruits
```
- `-r` means: don't stop on socket errors. Without it, `ab` stops at the **first** `apr_socket_recv: Connection refused (111)`, which can happen now and then under heavy parallel load, or while the LB is still rolling out in the first ~10 minutes. Failed requests are then just counted in the report.
- `-t 300` means: keep up the load for **5 minutes**. The autoscaler looks at CPU averaged over a minute or more, so a short burst never triggers it.
Meanwhile, in PowerShell, check every minute or so:
```powershell
gcloud compute instance-groups managed list-instances fruit-mig --region=us-central1 --format="table(instance.basename():label=NAME,instanceStatus:label=STATUS,currentAction:label=ACTION)"
gcloud compute instances list --filter="name~^fruit-mig" --format="table(name,zone.basename(),status)"
```
You should see a 2nd and maybe a 3rd VM appear (`CREATING`, then `RUNNING`). In a regional MIG they're spread across zones. After the test, it takes about 10 minutes or more to scale back to 1.

## Step 8 – Autohealing demo: break one VM and watch the MIG fix it

```powershell
$VM = gcloud compute instances list --filter="name~^fruit-mig" --limit=1 --format="value(name)"
$Z  = gcloud compute instances list --filter="name=$VM" --format="value(zone.basename())"
"$VM in $Z"
gcloud compute ssh $VM --zone=$Z --command="sudo systemctl stop fruit"
```
Then watch `list-instances` (as in Step 7). Within about a minute the health check fails three times in a row, and the MIG **recreates** that VM, which shows as `currentAction: RECREATING`.

`gcloud compute ssh` adds your OS Login key again; Step 11 removes it. The `default-allow-ssh` rule allows port 22.

## Step 9 – Rolling update to a new template version

Write the ledger row first, then:
```powershell
gcloud compute instance-templates create fruit-tpl-v2 --machine-type=e2-micro --image-family=debian-12 --image-project=debian-cloud --boot-disk-type=pd-standard --boot-disk-size=10GB --tags=fruit-web --metadata=enable-oslogin=TRUE --metadata-from-file=startup-script=scripts\startup-fruit.sh "--labels=course=ace,week=2,version=v2"
gcloud compute instance-groups managed rolling-action start-update fruit-mig --region=us-central1 --version=template=fruit-tpl-v2 --max-surge=3 --max-unavailable=0
gcloud compute instance-groups managed describe fruit-mig --region=us-central1 --format="yaml(versions,status.versionTarget,updatePolicy)"
```
Exam facts:
- `max-surge` is how many extra VMs may be created during the update. `max-unavailable` is how many may be offline at once.
- In a **regional** MIG, `max-surge` must be **0 or at least the number of zones** (3 here).
- `--canary-version=template=X,target-size=1` is used for canary updates.
- `rolling-action replace` and `restart` re-create or restart VMs **without** a new template.

## Step 10 – Five minutes with a Spot VM and a custom machine type

Write the ledger row first, then:
```powershell
gcloud compute instances create fruit-spot --zone=us-central1-a --machine-type=e2-custom-2-4096 --provisioning-model=SPOT --instance-termination-action=DELETE --image-family=debian-12 --image-project=debian-cloud --boot-disk-type=pd-standard --boot-disk-size=10GB "--labels=course=ace,week=2"
gcloud compute instances describe fruit-spot --zone=us-central1-a --format="yaml(machineType.basename(),scheduling)"
gcloud compute instances delete fruit-spot --zone=us-central1-a --quiet
```
Exam facts:
- **Spot VMs** cost far less, but Google can stop them at any time with 30 seconds' notice. There's no 24-hour limit; that limit was the old *preemptible* VMs. Spot VMs have no live migration and no SLA.
- `--instance-termination-action` is **STOP** or **DELETE**.
- **Custom machine types** (`<family>-custom-<vCPUs>-<memory MB>`) let you choose vCPUs and memory yourself, when no predefined size fits.

---

## Step 11 – Teardown (everything created today)

Order matters: each resource below is in use by the one listed before it.
```powershell
gcloud compute forwarding-rules delete fruit-fr --global --quiet
gcloud compute target-http-proxies delete fruit-proxy --quiet
gcloud compute url-maps delete fruit-map --quiet
gcloud compute backend-services delete fruit-be --global --quiet
gcloud compute instance-groups managed delete fruit-mig --region=us-central1 --quiet     # deletes its VMs and their disks
gcloud compute health-checks delete fruit-hc --quiet
gcloud compute instance-templates delete fruit-tpl fruit-tpl-v2 --quiet
gcloud compute firewall-rules delete allow-fruit-hc --quiet
gcloud compute instances delete fruit-spot --zone=us-central1-a --quiet                  # only if Step 10's delete didn't run
gcloud compute os-login ssh-keys remove --key-file="$HOME\.ssh\google_compute_engine.pub"
```
Check that nothing is left. Every count must be **0**:
```powershell
foreach ($c in "instances","disks","instance-templates","instance-groups managed","health-checks","backend-services","url-maps","target-http-proxies","forwarding-rules","addresses") { "{0,-25} {1}" -f $c, (Invoke-Expression "gcloud compute $c list --format='value(name)'" | Measure-Object).Count }
gcloud compute firewall-rules list --filter="name=allow-fruit-hc" --format="value(name)"
gcloud compute os-login ssh-keys list
```
**Cloud Shell:** run `bash ~/fn-gcp/scripts/ace-leftovers.sh fn-fruits` if you have a clone, then remove the clone with `rm -rf ~/fn-gcp`.

**Kept on purpose:** nothing new. `scripts/startup-fruit.sh` is already committed.

## Checkpoint (answer without notes)

1. List the six resources that make up a global external Application LB, from the client inwards.
2. All backends show UNHEALTHY but the app works when you SSH in. What's the most likely cause, and which source ranges fix it?
3. Regional vs zonal MIG: which one survives a zone outage? What does that mean for `max-surge` in a rolling update?
4. Name three signals a MIG autoscaler can scale on. Why does scale-in take longer than scale-out?
5. How do you change the machine type of every VM in a MIG?
6. Spot vs preemptible VMs: what changed? What are the two termination actions?

## My log (fill in)

- Date / time spent:
- Steps done:
- Output worth remembering:
- Gotchas:
- Teardown counts + `ace-leftovers.sh` result:
