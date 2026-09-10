"""The product's output surface: paragraphs, not a dashboard.

Track 03 rules out the obvious shape directly — *"A product that only displays raw
Sectors data in a different visual form, however well presented, does not qualify."*
A chart of `top_buyers[].buy_idr` is the API response with a different font on it;
the reader still has to do the reading. So the deliverable here is a sentence: what
was measured, how far past its bar it landed, and where every figure came from.

Two rules shape everything in this package, and both come from
`riset/red-team.md` §D11:

  * **descriptive without exception.** "Pangsa broker teratas 83,8%, volume 24,5x
    median" is a statement about the tape. "Saham ini digoreng" is an accusation
    about an issuer, and a public video showing a live ticker beside that word is a
    legal problem for the team and for the organiser. `paragraph.BANNED` is the
    written form of that rule, and `app/tests/test_paragraph.py` enforces it against
    every symbol the product can render.
  * **every number traceable.** A figure a reader cannot walk back to an endpoint
    and a field is a figure they have to take on trust, and this product's whole
    claim is that they should not have to. The verifier is fail-closed: an
    unattributed number stops the output rather than shipping with a guess beside it.

If a visual surface is ever wanted, it is a *list of these paragraphs*. Nothing in
this package draws.

Zero credits: rendering reads a `Profile`, which reads `research/harness/recorded/`.
No socket is opened here.
"""
