# Picture Status Background Selection

This context chooses a background for each generated status image while balancing
cached availability with direct retrieval latency.

## Language

**Background provider**:
A source of background-image candidates.

**Candidate**:
One background-image item produced by a provider. An intentionally empty
background is still a candidate.

**Co-iterating provider**:
A provider that produces candidates concurrently and streams them as they
arrive. Iterations are independent: each one receives a complete stream of its
own.

**No-preload provider**:
A provider explicitly selected to skip routine preloading.
_Avoid_: A fallback provider that happens to supply a candidate.

**Preloaded background**:
A candidate retained before a status-image request.

**Preload target**:
The non-negative desired count of preloaded backgrounds. Zero disables routine
background preloading.

**Fire retrieval**:
A one-candidate, immediate retrieval started when no preloaded background is
available.

**Late completion**:
A fire retrieval result that arrives after its return gate but before its fire
deadline, and remains available to a later request.

**Fire return gate**:
The configured period for which a cache-miss caller waits for a fire retrieval
candidate before receiving a local fallback.

**Fire deadline**:
The configured maximum lifetime of a fire retrieval. A retrieval that has not
produced a candidate by this deadline is cancelled.

**Retry budget**:
The maximum consecutive routine preload attempts that finish without a
candidate. Any candidate resets the budget.

**Deferred recovery**:
Resuming routine preloading after any later image-retrieval call once its retry
budget is exhausted.
