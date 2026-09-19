---
status: accepted
---

# Local Backgrounds Are Never Preloaded

A local background candidate is only a pointer to a file that a request could
read directly, so preloading one duplicates work that cannot be avoided. The
built-in local provider is therefore excluded from routine preloading and
served through on-demand retrieval; a request larger than the available file
set yields every available file instead of failing.
