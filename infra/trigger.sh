#!/usr/bin/env bash
#
# D5. Run this AFTER connecting aliefauzan/SectorsResearch in the Cloud Build console —
# the GitHub OAuth handshake is the one step with no CLI form.
#
# The branch is `master`. This repository has never had a `main`, and a trigger watching
# `^main$` is a trigger that never fires and never says why.
set -euo pipefail

gcloud builds triggers create github \
  --name=katalis-master \
  --region=global \
  --repo-owner=aliefauzan \
  --repo-name=SectorsResearch \
  --branch-pattern='^master$' \
  --build-config=cloudbuild.yaml \
  --description='push ke master: build, gate di dalam image, push, deploy katalis-api'

gcloud builds triggers list --region=global \
  --format='table(name,github.push.branch,filename,disabled)'
