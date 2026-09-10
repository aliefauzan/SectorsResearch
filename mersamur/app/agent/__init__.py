"""The daily loop's three judging steps: adjudicate, learn, evolve.

`riset/spec.md` §6 orders the tick and this package holds its head:

    1. NILAI    warnings with status=open, judged against what actually happened
    2. PELAJARI each new outcome turned into a written lesson
    3. SETEL    the bars moved, but only when five gates are all satisfied

Only step 1 lives here today (`adjudicate.py`). Steps 2 and 3 are tasks 16 and 17
and will land beside it; nothing in this package writes a state file itself —
`app.ledger` is the only writer, and it validates every row before it reaches disk.
"""
