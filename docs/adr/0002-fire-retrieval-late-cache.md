---
status: superseded
superseded_by: ['0004']
---

# Fire Retrievals Retain Late Results

Cache misses start a one-candidate fire retrieval so the current request does
not wait for routine cache replenishment. A result that arrives after the
request timeout is retained for a later request, trading a small amount of
cache growth for avoiding a discarded completed download.
