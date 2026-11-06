# Facts the OPNsense adapter relies on

Each fact comes from the official source linked under it, not from memory. Re-check a fact when its source changes, and add a new one here, with its link, when you start relying on it.

## OPNsense Unbound wildcard override

Documented: Host `*` creates a wildcard entry. Bug reports exist (opnsense/core#5828, #8051), so the guide checks `*.<domain>` with `dig` and falls back to one host override per service

Source: https://docs.opnsense.org/manual/unbound.html
