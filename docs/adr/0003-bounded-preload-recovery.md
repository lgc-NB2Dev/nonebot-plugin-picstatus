---
status: accepted
---

# Bounded Preload Recovery

Routine preloading has a configurable default retry budget of three empty or
failed attempts. Once exhausted, it waits for a later image-retrieval call to
resume; this avoids continuously retrying an unavailable provider while
retaining direct retrieval for the request that needs a background.
