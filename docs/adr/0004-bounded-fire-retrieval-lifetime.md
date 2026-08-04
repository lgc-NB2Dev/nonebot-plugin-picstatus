# Bound Fire Retrieval Lifetime

Fire retrievals return a local fallback after a configurable 15-second return gate, while a candidate that arrives before their configurable 60-second deadline remains available to a later call. Each fire retrieval requests one candidate and ends after that candidate; a retrieval without a candidate at its deadline is cancelled, preserving independent immediate requests without allowing a nonresponsive provider to retain a task indefinitely.
