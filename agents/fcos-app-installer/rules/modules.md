---
root: true
targets: ["*"]
description: "How to add support for a tool the toolkit has no module for, without choosing for the user"
---

# Adding support for another tool

The toolkit has one module per product: adapters for systems the user runs by hand (a hypervisor, a
router, a file server, a DNS provider) and service modules for things it deploys (a reverse proxy,
an auth gateway). Each is a skill folder with a `module.yaml` or `adapter.yaml` that says what it
provides, what it needs and what it pairs with.

- **Never choose a product for the user.** Run `python3 tools/modules.py list` (and
  `python3 tools/adapters.py show --role <role>`), say what each option provides and what it pairs
  with, recommend from the pairings marked tested, and ask. The site file records the choice.
- **When the user wants a product with no module,** build one. Follow `docs/guide/12-add-a-module.md`:
  read the product's official documentation, not memory; copy the closest existing module; write the
  tests first; generate with the fixtures and run the whole suite.
- **Record every fact you rely on** with its source link, without a date, in the module's
  `reference.md`. A fact about FCOS itself goes on the guide page that depends on it.
- **Keep the user's own values out of the module.** Their names, addresses, domains and rendered
  files stay in their workspace. A module holds only what any user of that product needs.
- **Mark a pairing `tested: false`** until the user has built it on a real install and told you it
  worked. An untested pairing gets no glue.
- **Ask before you change the toolkit's files.** Editing `tools/`, `templates/`, a skill or a guide
  page needs the user's yes; show the change first.
