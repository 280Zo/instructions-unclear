# career

Career work: career records and work history, master resume, tailored resumes and cover letters, job applications, LinkedIn, interview coaching, salary negotiation and offer comparison. Keeps career records in the working folder.

One agent file for every tool. In OpenCode it can use only its own skills (skills/resume-skills, skills/interview-coach and skills/career-workspace), the shared ones every agent gets, and the Exa, PMB, Docling servers; other tools get its instructions without those limits. See [how agents keep skills out of each other's requests](../README.md#how-agents-keep-skills-out-of-each-others-requests) and [what each assistant enforces](../README.md#what-each-assistant-enforces).

## Install

Part of the [`default` group](../../groups/README.md#default), which also installs its skills. For another tool, add `--targets`; see [what each assistant enforces](../README.md#what-each-assistant-enforces) for why the skills are better installed with their folder group there.

## Use

Pick `career` with `/agents` in OpenCode, or ask your main agent to hand it a task. Start your tool in your career folder (for example `~/AI/career`): the skills keep records relative to it. Say "Use career-start-application" to start an application; the [career-workspace README](../../skills/career-workspace/README.md#workflow) shows the workflow.

## For agents: install, remove and update

`subagents/career.md` is written by [`agents/generate.py`](../generate.py); change the agent in its manifest and follow [its update steps](../README.md#update). To remove it, follow [Remove](../README.md#remove).

## Origin

Written for this repo by 280Zo. [MIT](../../LICENSE).
