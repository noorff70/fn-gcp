#!/usr/bin/env bash
# ace-leftovers.sh - list every resource still present in the ACE practice project.
#
# READ-ONLY: this script only runs list/describe commands. It never creates,
# changes or deletes anything, and it never enables an API.
#
# Usage (Cloud Shell or Git Bash with the gcloud CLI):
#   bash scripts/ace-leftovers.sh fn-fruits
#
# Exit codes: 0 = CLEAN (nothing billable left)
#             1 = billable resources still exist (marked !!)
#             2 = could not check (wrong project id, not logged in, ...)
#
# Items marked "--" cost nothing (or next to nothing) but should still be
# removed so every session starts from an empty project.
# Kept on purpose and therefore ignored: the default VPC and its default-allow-*
# firewall rules, Google-managed service accounts, the _Default/_Required log
# sinks and buckets, and the billing_export BigQuery dataset.
#
# Not checked (no GA list command): Monitoring alert policies, notification
# channels and uptime checks. Check them in the console under Monitoring.

set -u

P="${1:-$(gcloud config get-value project 2>/dev/null)}"
if [ -z "$P" ]; then
  echo "usage: bash $0 PROJECT_ID" >&2
  exit 2
fi

if ! gcloud projects describe "$P" --format="value(projectId)" >/dev/null 2>&1; then
  echo "Cannot read project '$P' (wrong id, not logged in, or project already deleted)." >&2
  exit 2
fi

G="gcloud --project=$P --quiet"
billable=0
tidy=0

# check <1=billable|0=free> <label> <shell command that prints one resource per line>
check() {
  local bill="$1" label="$2" cmd="$3" out
  out="$(eval "$cmd" 2>/dev/null | sed '/^[[:space:]]*$/d')"
  [ -z "$out" ] && return
  if [ "$bill" = 1 ]; then
    echo "!! $label"
    billable=1
  else
    echo "-- $label (free, but tidy up)"
    tidy=1
  fi
  echo "$out" | sed 's/^/     /'
}

echo "Checking project $P ..."
echo

# --- Compute Engine ---------------------------------------------------------
check 1 "VM instances"            "$G compute instances list --format='value(name,zone.basename(),status)'"
check 1 "Managed instance groups" "$G compute instance-groups managed list --format='value(name)'"
check 1 "Persistent disks"        "$G compute disks list --format='value(name,zone.basename(),sizeGb)'"
check 1 "Snapshots"               "$G compute snapshots list --format='value(name)'"
check 1 "Custom images"           "$G compute images list --no-standard-images --format='value(name)'"
check 1 "Machine images"          "$G compute machine-images list --format='value(name)'"
check 0 "Instance templates"      "$G compute instance-templates list --format='value(name)'"
check 0 "Resource policies (snapshot schedules)" "$G compute resource-policies list --format='value(name)'"

# --- Load balancing ---------------------------------------------------------
check 1 "Forwarding rules (load balancers)" "$G compute forwarding-rules list --format='value(name,region.basename())'"
check 0 "Target HTTP(S) proxies"  "{ $G compute target-http-proxies list --format='value(name)'; $G compute target-https-proxies list --format='value(name)'; }"
check 0 "URL maps"                "$G compute url-maps list --format='value(name)'"
check 0 "Backend services"        "$G compute backend-services list --format='value(name)'"
check 0 "Health checks"           "$G compute health-checks list --format='value(name)'"
check 0 "SSL certificates"        "$G compute ssl-certificates list --format='value(name)'"

# --- Networking -------------------------------------------------------------
check 1 "Static IP addresses"     "$G compute addresses list --format='value(name,addressType,status)'"
check 1 "Cloud Routers (Cloud NAT lives here)" "$G compute routers list --format='value(name,region.basename())'"
check 1 "VPN tunnels"             "$G compute vpn-tunnels list --format='value(name)'"
check 1 "VPN gateways"            "{ $G compute vpn-gateways list --format='value(name)'; $G compute target-vpn-gateways list --format='value(name)'; }"
check 1 "Cloud DNS zones"         "$G dns managed-zones list --format='value(name)'"
check 0 "VPC networks (non-default)" "$G compute networks list --format='value(name)' | grep -vx default"
check 0 "Firewall rules (non-default)" "$G compute firewall-rules list --format='value(name)' | grep -v '^default-allow-'"

# --- Containers and serverless ---------------------------------------------
check 1 "GKE clusters"            "$G container clusters list --format='value(name,location)'"
check 1 "Cloud Run services"      "$G run services list --format='value(metadata.name)'"
check 1 "Cloud Run jobs"          "$G run jobs list --format='value(metadata.name)'"
check 1 "Cloud Functions"         "$G functions list --format='value(name)'"
check 0 "Eventarc triggers"       "$G eventarc triggers list --location=- --format='value(name)'"
check 1 "Artifact Registry repos" "$G artifacts repositories list --format='value(name)'"

# --- Data -------------------------------------------------------------------
check 1 "Cloud SQL instances"     "$G sql instances list --format='value(name,state)'"
check 1 "Cloud Storage buckets"   "$G storage buckets list --format='value(name)'"
check 1 "Pub/Sub topics"          "$G pubsub topics list --format='value(name.basename())'"
check 1 "Pub/Sub subscriptions"   "$G pubsub subscriptions list --format='value(name.basename())'"
check 1 "Secret Manager secrets"  "$G secrets list --format='value(name.basename())'"
check 1 "BigQuery datasets (billing_export ignored)" \
  "bq ls --project_id='$P' -n 1000 | tail -n +3 | awk '{print \$1}' | grep -vx billing_export"

# --- Logging ----------------------------------------------------------------
check 1 "Log sinks (custom)"      "$G logging sinks list --format='value(name)' | grep -vx -e _Default -e _Required"
check 1 "Log buckets (custom)"    "$G logging buckets list --format='value(name.basename())' | grep -vx -e _Default -e _Required"
check 0 "Log-based metrics"       "$G logging metrics list --format='value(name)'"

# --- IAM --------------------------------------------------------------------
check 0 "Service accounts (user-created)" \
  "$G iam service-accounts list --format='value(email)' | grep -v -e '-compute@developer.gserviceaccount.com' -e '@appspot.gserviceaccount.com'"
check 0 "Custom IAM roles"        "$G iam roles list --project='$P' --format='value(name.basename())'"

echo
echo "Reminder: check Monitoring > Alerting and Monitoring > Uptime checks in the console."
if [ "$billable" = 1 ]; then
  echo "NOT CLEAN - billable resources remain (!!). Run the week's teardown block."
  exit 1
elif [ "$tidy" = 1 ]; then
  echo "CLEAN (nothing billable) - but tidy up the free items (--) too."
  exit 0
else
  echo "CLEAN"
  exit 0
fi
