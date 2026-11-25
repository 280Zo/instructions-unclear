# Facts the OPNsense adapter relies on

Each fact comes from the official source linked under it, not from memory. Re-check a fact when its source changes, and add a new one here, with its link, when you start relying on it.

## Host overrides and the search domain

Documented: an Unbound host override takes a Host (the name without the domain part), a Domain, a Type (A for IPv4) and an IP. With Dnsmasq as the DHCP service, a DHCP range has a Domain, and Dnsmasq offers the domain-name option (15) to clients, "to construct short names to FQDNs in DNS lookups"; a host that gets a lease from the range and advertises a hostname is registered under that domain. With KEA, a subnet's options have a Domain name and a Domain search list "to offer to the client". The adapter's `lan_hostname` step uses these fields. The desktop-side result (`getent hosts <name>` resolving the short name) was not tested here

Source: https://docs.opnsense.org/manual/unbound.html (Host override settings) · https://docs.opnsense.org/manual/dnsmasq.html (DHCP ranges, DHCP options) · https://docs.opnsense.org/manual/kea.html (Options: Domain name, Domain search)

## OPNsense Unbound wildcard override

Documented: Host `*` creates a wildcard entry. Bug reports exist (opnsense/core#5828, #8051), so the guide checks `*.<domain>` with `dig` and falls back to one host override per service

Source: https://docs.opnsense.org/manual/unbound.html
