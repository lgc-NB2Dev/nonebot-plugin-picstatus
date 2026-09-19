---
status: accepted
---

# Iteration-Owned Producers

A co-iterating provider may be iterated concurrently and repeatedly, so each
iteration owns its queue and its producer task instead of sharing instance
state. Iterations therefore cannot leak each other's end-of-stream marker, and
the stream terminator stays reserved: an intentionally empty background is
still an ordinary candidate.
