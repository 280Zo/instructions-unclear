# Facts the Authentik module relies on

Each fact comes from the official source linked under it, not from memory. Re-check a fact when its source changes, and add a new one here, with its link, when you start relying on it.

## Authentik proxy provider and blueprints

Models: `authentik_providers_proxy.proxyprovider` (attrs `mode: forward_single`, `external_host`, `skip_path_regex`, `authorization_flow`), `authentik_core.application` (`slug`, `name`, `provider`), `authentik_outposts.outpost` (the embedded outpost is named `authentik Embedded Outpost`, serves on ports 9000/9443 of the server, and has a `providers` list). Blueprint files mounted into the worker's blueprint folder are discovered at worker start and at an hourly rescan; the file watcher reacts only to created and modified files, so a file renamed into place (how the push replaces files) is picked up only if the discovery its temp file triggers races the rename, else at the hourly rescan. `ak apply_blueprint` applies a file's contents but never registers it, so an outpost file's required metaapplyblueprint fails for a new app. After a push the guide restarts the worker, which rescans at startup (`send_on_startup`), then checks each file's `BlueprintInstance`: `status` successful and `last_applied_hash` equal to the sha512 of the file now (an invalid file is recorded only as status error, never logged; `tools/authgw/authentik_rules_status.py`, run inside the worker with `ak shell -c`; the VM passes the files' hashes in, because a `podman exec` process lacks the worker's extra group 3201 and can't list the 0750 rules folder) `skip_path_regex` is one regex per line, matched against the request path in `forward_single` mode. A bad regex is skipped silently, leaving that path *authenticated*

Source: https://docs.goauthentik.io/add-secure-apps/providers/proxy/ · https://docs.goauthentik.io/customize/blueprints/ · https://github.com/goauthentik/authentik/blob/version/2026.8.5/authentik/blueprints/v1/tasks.py · https://github.com/goauthentik/authentik/blob/version/2026.8.5/authentik/blueprints/apps.py · https://github.com/goauthentik/authentik/blob/version/2026.8.5/authentik/blueprints/models.py · https://github.com/goauthentik/authentik/blob/version/2026.8.5/authentik/blueprints/management/commands/apply_blueprint.py

## Authentik facts used by the login front end (release 2026.8.5)

Official compose for 2026.8.5: server and worker share `/data` and `/templates`, `shm_size: 512mb` each, the worker also mounts `/certs`; Postgres image `postgres:16-alpine`; no Redis. Postgres passwords over 99 characters are not supported. Since 2026.8 the server uses forwarded headers only from `AUTHENTIK_LISTEN__TRUSTED_PROXY_CIDRS` (default: `127.0.0.0/8`, the three RFC 1918 private IPv4 ranges, `fe80::/10`, `::1/128`); not yet checked on a real VM which source address rootless Podman shows for Traefik's connection. Admin recovery: `ak create_recovery_key <minutes> <user>` prints a one-time login link valid for that many minutes (docs show it run in the server or worker container). Initial setup page: `/if/flow/initial-setup/`. Blueprints are applied in no fixed order; `authentik_blueprints.metaapplyblueprint` (attrs `identifiers`, `required`) applies another blueprint instance first

Source: https://raw.githubusercontent.com/goauthentik/authentik/version/2026.8.5/lifecycle/container/compose.yml · https://docs.goauthentik.io/install-config/install/docker-compose/ · https://docs.goauthentik.io/releases/2026.8/ · https://docs.goauthentik.io/install-config/configuration/ · https://docs.goauthentik.io/troubleshooting/login/ · https://docs.goauthentik.io/customize/blueprints/v1/meta/

## Authentik dashboard links for apps on their own login

An application appears on a user's Application Dashboard when the user has access (no bindings: everyone) and it has a launch URL starting with `http://` or `https://`. Application fields include `meta_launch_url`, `open_in_new_tab`, `meta_description`, `provider`. An application without a provider works as a plain link (confirmed by authentik's lead developer in issue 8018; the docs say applications "typically" pair with a provider: secondary source, from the project). Single sign-on for such apps needs the app to support OIDC (authentik's OAuth 2.0/OIDC provider) or trusted proxy headers (`X-authentik-username` and others, sent by the proxy outpost)

Source: https://docs.goauthentik.io/add-secure-apps/applications/ · https://docs.goauthentik.io/add-secure-apps/applications/manage_apps/ · https://github.com/goauthentik/authentik/blob/main/authentik/core/api/applications.py · https://github.com/goauthentik/authentik/issues/8018 · https://docs.goauthentik.io/add-secure-apps/providers/oauth2/ · https://docs.goauthentik.io/add-secure-apps/providers/proxy/

## Sign-up and sign-in with an existing account (authentik 2026.8.5)

Sign-up page: the example flow `flows-enrollment-2-stage.yaml` (prompt, user_write `always_create`, user_login); user_write has `create_users_group` and `create_users_as_inactive`; the identification stage has `enrollment_flow` and `sources`. Sources: `authentik_sources_oauth.oauthsource` with `provider_type`, `consumer_key`, `consumer_secret`; new people go through an enrollment flow like `default-source-enrollment`; blueprint tag `!Env` reads the worker's environment. Google: return URL `/source/oauth/callback/google/`; with only name/email/profile scopes no test-user list, warning or verification. Apple: consumer key `<services id>;<team id>;<key id>`, secret = key file contents, public domain required

Source: https://github.com/goauthentik/authentik/blob/version/2026.8.5/blueprints/example/flows-enrollment-2-stage.yaml · https://github.com/goauthentik/authentik/blob/version/2026.8.5/authentik/stages/user_write/models.py · https://github.com/goauthentik/authentik/blob/version/2026.8.5/authentik/stages/identification/models.py · https://github.com/goauthentik/authentik/blob/version/2026.8.5/authentik/sources/oauth/models.py · https://github.com/goauthentik/authentik/blob/version/2026.8.5/blueprints/default/flow-default-source-enrollment.yaml · https://docs.goauthentik.io/customize/blueprints/v1/tags/ · https://docs.goauthentik.io/users-sources/sources/social-logins/google/cloud/ · https://docs.goauthentik.io/users-sources/sources/social-logins/apple/ · https://support.google.com/cloud/answer/15549945

## Outpost binding (a design note, not a sourced fact)

The embedded outpost's `providers` list is replaced as a whole. One generated rules file
(`outpost-providers`) lists every proxy provider and is regenerated from the configuration whenever a
service is added or removed.

## Upgrading Authentik

Upgrades must follow the sequence of major releases: do not skip from an older release directly to the most recent one. Upgrade to the latest minor version (`.x`) within each `major.minor` release before the next (from `2025.2.1`: the latest `2025.2.x`, then the latest `2025.4.x`, then `2025.6.x`). Authentik does not support downgrading, so back up the PostgreSQL database before upgrading. The authentik server and all outposts must be the same version.

Source: https://docs.goauthentik.io/install-config/upgrade/
