# Facts the Traefik module relies on

Each fact comes from the official source linked under it, not from memory. Re-check a fact when its source changes, and add a new one here, with its link, when you start relying on it.

## Traefik forward-auth for Authentik

Middleware `forwardAuth.address: http://<outpost>:9000/outpost.goauthentik.io/auth/traefik`, `trustForwardHeader: true`, `maxResponseBodySize: 4194304`, `authResponseHeaders` X-authentik-username/groups/entitlements/email/name/uid/meta-jwks/meta-outpost/meta-provider/meta-app/meta-version (the docs' X-authentik-jwt is left out: the proxy scope puts all user attributes into it, `blueprints/system/providers-proxy.yaml`, so it grows with them, and apps refuse headers over ~8 KB; no app here uses it). Each app also needs a router for `PathPrefix(/outpost.goauthentik.io/)` at priority 15 to the outpost

Source: https://docs.goauthentik.io/add-secure-apps/providers/proxy/server_traefik/

## Device routes (dashboard links with a web name)

`ipAllowList.sourceRange` lists the allowed addresses or CIDR ranges; with no `ipStrategy` it matches the request's remote address, and refused requests get 403 (`rejectStatusCode`). An HTTP `serversTransports.<name>` with `rootCAs` (a list of `FileOrContent`: a file path if one exists at that path, else the PEM itself) is the only set of CAs used to verify the server's certificate (`insecureSkipVerify` defaults to false); `serverName` sets the SNI and the name the certificate is checked against (for a device whose certificate names a host rather than its address); a load balancer service uses it with `serversTransport: <name>`. WebSocket connections (a hypervisor's console) are proxied without extra settings

Source: https://doc.traefik.io/traefik/reference/routing-configuration/http/middlewares/ipallowlist/ · https://doc.traefik.io/traefik/reference/routing-configuration/http/load-balancing/serverstransport/ · https://github.com/traefik/traefik/blob/v3.6/pkg/types/file_or_content.go · https://github.com/traefik/traefik/blob/v3.6/pkg/config/dynamic/http_config.go · https://doc.traefik.io/traefik/expose/overview/

## Break-glass for an app that forces its own https address

Monica's `APP_ENV=production` makes https mandatory (its docker README and `.env.example`), and it builds links from `APP_URL`. Through an SSH tunnel to its plain HTTP port, pages load (`200`) but signing in redirects to `https://localhost:<port>`. Removing the one `middlewares: [authentik]` line from the app's Traefik route file on the login VM opened the app at its normal https address with its own login; sign-in worked; restoring the file brought back the `302` to the login page. Traefik's file provider reloaded the edited file without a restart. Not tested: with Authentik itself stopped

Source: https://raw.githubusercontent.com/monicahq/monica/4.x/.env.example · https://github.com/monicahq/docker · https://doc.traefik.io/traefik/providers/file/
