"""Read-only view over the payloads that were already paid for.

`research/harness/recorded/` holds real API responses captured on 6 September 2026
and 9 September 2026, together with `_manifest.json` — the index that says which
`(path, params, method)` triple produced which file. This module is the only way
the product reads them, and it is deliberately read-only: nothing here writes into
the harness, so a product run can never contaminate the record of what was bought.

Two kinds of hit matter, and they are not the same thing:

  * a **2xx hit** carries the payload, and the caller is done;
  * a **404 hit** carries no payload but is still authoritative — that lookup ran
    on the live API and cost a credit. Re-asking pays again for the same answer.

So `Cache.get()` returns a `Hit` in both cases and the client branches on
`hit.found`. A miss is `None`, which is the only state that may justify a network
call.

Everything here is keyed by `slug()`, which reproduces the naming scheme of
`research/harness/src/capture.py` byte for byte. If that ever drifts, every lookup
silently misses and the product starts paying for data it already owns — hence the
parity test in `tests/test_client.py`.
"""
import json
import os
import re

from app import config


def slug(path, params=None, method="GET"):
    """Stable filename for a (path, params, method) triple.

    Copied from `capture.py` rather than imported: the harness is a research tool
    the product must not depend on at runtime, and this is the one piece of it the
    product genuinely needs. The rules are the harness's, including the quirks —
    the method suffix only appears for non-GET, and `path.strip("/")` makes
    `/v2/subsectors` and `/v2/subsectors/` the same key.
    """
    base = path.strip("/").replace("/", "_")
    if not path.endswith("/"):
        base += "__noslash"
    if method != "GET":
        base += f"__{method.lower()}"
    if params:
        tail = "_".join(f"{k}-{str(v)[:24]}" for k, v in sorted(params.items()))
        base = f"{base}__{tail}"
    return re.sub(r"[^A-Za-z0-9_.-]+", "-", base)[:180]


class Hit:
    """One settled outcome from the recording. `found` is False for a settled 404."""

    __slots__ = ("key", "status", "payload", "meta")

    def __init__(self, key, status, payload, meta):
        self.key, self.status, self.payload, self.meta = key, status, payload, meta

    @property
    def found(self):
        return 200 <= self.status < 300

    def __repr__(self):
        return f"<Hit {self.key} {self.status}>"


class Cache:
    """The recorded corpus, addressed the way the live API is addressed.

    `root` is injectable so tests can build a three-file corpus in a temp directory
    instead of asserting against whatever the harness happens to hold today.
    """

    def __init__(self, root=None):
        self.root = root or config.RECORDED_DIR
        self._manifest = None

    # --- manifest ----------------------------------------------------------
    @property
    def manifest_path(self):
        return os.path.join(self.root, "_manifest.json")

    def manifest(self, reload=False):
        """The index, loaded once. A missing or corrupt index means an empty cache.

        Corrupt rather than absent is worth tolerating: the harness writes the file
        whole, but a crash mid-write would otherwise take the product down instead
        of merely costing it a cache hit.
        """
        if self._manifest is None or reload:
            try:
                with open(self.manifest_path, encoding="utf-8") as fh:
                    self._manifest = json.load(fh)
            except (OSError, ValueError):
                self._manifest = {}
        return self._manifest

    # --- lookup ------------------------------------------------------------
    def entry(self, path, params=None, method="GET"):
        """The manifest row for a call, or None."""
        return self.manifest().get(slug(path, params, method))

    def get(self, path, params=None, method="GET"):
        """A `Hit` when this call is settled, else None.

        Settled means exactly what it means in `capture.py`: a 2xx whose payload is
        on disk, or a 404 that was already billed. A recorded 400, 402, 429 or
        network failure is *not* settled — it cost nothing, so it is a miss and the
        caller is free to try again.
        """
        key = slug(path, params, method)
        entry = self.manifest().get(key)
        if not entry:
            return None

        status = entry.get("status")
        if not isinstance(status, int):
            return None

        if 200 <= status < 300:
            # An `incomplete` sweep is only settled when it stopped on a billed 404;
            # anything else is a prefix that the harness intends to resume, and the
            # product must not present a partial universe as the whole one.
            if entry.get("incomplete") and entry.get("stopped_on") != 404:
                return None
            payload = self._payload(key)
            if payload is None:
                return None
            return Hit(key, status, payload, entry)

        if status == 404:
            return Hit(key, 404, None, entry)

        return None

    def _payload(self, key):
        try:
            with open(os.path.join(self.root, key + ".json"), encoding="utf-8") as fh:
                return json.load(fh)
        except (OSError, ValueError):
            # The manifest claims a payload the directory does not have. Report a
            # miss rather than an exception — the caller can still decide to pay.
            return None

    def __len__(self):
        return len(self.manifest())

    def __repr__(self):
        return f"<Cache {self.root} ({len(self)} entries)>"
