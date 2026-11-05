---
description: "Add a service to a Fedora CoreOS VM following docs/guide (args: <service>)"
targets: ["*"]
opencode:
  agent: fcos-app-installer
---

Add the service "$1", following docs/guide/03-add-a-service.md. Start with the
requirement check your instructions begin with, then by asking where the
workspace is. Ask which server and which VM it goes on; don't assume either.
