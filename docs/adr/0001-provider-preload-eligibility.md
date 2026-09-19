---
status: accepted
---

# Provider-Defined Preload Eligibility

Providers declare `no_preload=True` when they should not receive routine
preloading. Eligibility is determined solely from the explicitly configured
provider, so a fallback candidate never changes the configured provider's
policy. This keeps provider capability local to the provider while preserving
the configured source's retrieval policy.
