# tests

`vitest run` covers the seam this fork actually changed: the mapper from a KATALIS reply to
the shapes the screen renders, the engine that orders and answers over those cards, and the
three route handlers.

`fixtures/` was written by `src/katalis/jsonapi.py` itself — one symbol listing, one served
card, one refusal — so a shape change on the Python side breaks these tests instead of
sliding past them. Regenerate them by calling `symbols_response` and `card_response` and
dumping the bodies; do not hand-edit them.

The upstream Playwright suite was removed rather than left failing: every one of its
assertions was written against the fixture app's six static events and its eighteen-symbol
universe, neither of which exists here. A browser suite for this surface has to be written
against what the API actually serves, and has not been yet.
