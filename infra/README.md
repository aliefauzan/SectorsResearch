# infra/ — the four commands this project's deploy needs

Everything here is a command, not a framework. There is no Terraform, no Pulumi, and no
state file, because there are seven cloud objects in total and a state file that disagrees
with reality is worse than a README that a person reads before running it.

The project is `ada-sectors-508410`. Cloud Run is `asia-southeast2`; the bucket is
`us-east1`, because Always Free Cloud Storage is a single US region and not the US
multi-region. That split is deliberate and is recorded in `plan/PROGRESS.md`.

## What already exists

```bash
gcloud artifacts repositories describe katalis --location=asia-southeast2   # D6, 5-tag policy
gcloud storage buckets describe gs://katalis-recorded                       # D7, us-east1
gcloud secrets versions list SECTORS_API_KEY                                # D4, one version
gcloud run services  list                                                   # D1 katalis-api
gcloud run jobs      list --region=asia-southeast2                          # D2 katalis-refresh
gcloud scheduler jobs list --location=asia-southeast2                       # D3, one job
```

## D5 — the build trigger, and the one step a person has to take

Cloud Build needs an OAuth handshake with GitHub that only a human in a browser can complete:

1. Console → Cloud Build → Triggers → **Connect repository** → `aliefauzan/SectorsResearch`.
2. Then, from a terminal, one command — **the branch is `master`, not `main`**:

```bash
gcloud builds triggers create github \
  --name=katalis-master \
  --region=global \
  --repo-owner=aliefauzan \
  --repo-name=SectorsResearch \
  --branch-pattern='^master$' \
  --build-config=cloudbuild.yaml \
  --description='push ke master: build, gate di dalam image, push, deploy katalis-api'
```

`infra/trigger.sh` is that command in a file, so it is run and not retyped.

## Rebuild by hand, without a push

```bash
gcloud builds submit --config cloudbuild.yaml --substitutions=SHORT_SHA=manual .
```

The gates run *inside* the image in step 2, so a manual build proves the same thing a
triggered build proves about the artifact — what it does not prove is that a push starts it.
