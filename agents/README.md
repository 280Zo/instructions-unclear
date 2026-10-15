# Agents

Agents and agent sets, each with the skills, rules and commands that go with them. Each README has its install command.

| Folder | Adds |
| --- | --- |
| [`second-opinion`](second-opinion/) | `second-opinion`, `evaluator` and `metacognitive`: a second check on the main agent's work. Installed by default |
| [`local-model`](local-model/) | Small working increments, scoped delegation and fast safe pause/resume handoffs. Installed by default; use as primary or delegated worker |
| [`security-compliance`](security-compliance/) | A security auditor and a compliance-check command. Profile |
| [`security-scanning`](security-scanning/) | Security auditor and threat-modeling agents, 5 skills, 3 scanning commands. Profile |
| [`reverse-engineering`](reverse-engineering/) | Reverse-engineer, firmware and malware agents, 4 skills. Profile |

A profile installs into one folder you choose, not your home folder. To install several profiles into the same folder, run each one's command with the same `--output-roots`.
