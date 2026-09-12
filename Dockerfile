# KATALIS — the card, over a URL.
#
# `python:3.12-slim` is not a style choice: the Always Free Artifact Registry allowance is
# 0,5 GB in total, across every tag kept, so the base image is the one line of this file with
# a bill attached to it. No wheels are installed because the product has no dependencies —
# every module under src/katalis/ is standard library, and keeping it that way is what makes
# this image small enough to be free.
FROM python:3.12-slim

# Unbuffered, so a Cloud Run log line appears when it happens rather than when the buffer
# fills; no .pyc written, because the image is read-only in spirit and a stale cache in a
# layer is a lie about which source ran.
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    SOURCE=recorded \
    PORT=8080

WORKDIR /app

# The two directories the product actually reads, and nothing else. sources.py resolves its
# data as ROOT/research/harness/, two levels above src/katalis/, so the layout inside the
# image has to mirror the repo's — this is the reason for the src/ prefix here.
COPY src/katalis/ /app/src/katalis/
COPY research/harness/recorded/ /app/research/harness/recorded/
COPY research/harness/synth/ /app/research/harness/synth/

# A non-root user, because the process serves a public URL and needs to write nothing.
RUN useradd --create-home --shell /usr/sbin/nologin katalis \
    && chown -R katalis:katalis /app
USER katalis

WORKDIR /app/src/katalis

EXPOSE 8080

# `docker run <image> test` runs the product's own gates inside the image that will be
# deployed — the same command cloudbuild.yaml uses as its second step.
ENTRYPOINT ["/bin/bash", "run.sh"]
CMD ["serve"]
