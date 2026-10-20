# Offline context packaging checks

From the repository root:

```bash
PYTHONDONTWRITEBYTECODE=1 python -m unittest discover -s tests -v
```

These stdlib tests check collection completeness, helper paths, Python syntax, disabled MCP templates, group roots, unique skill names, global-default separation and published status. They do not import helper dependencies, contact targets, access devices or start native MCP backends.

Changes to source roots must also be generated with pinned rulesync into throwaway output folders. Compare installed support assets and translated configuration against the source; unit tests alone do not prove generation or native runtime compatibility.

## Origin

Written for this repo by 280Zo.
