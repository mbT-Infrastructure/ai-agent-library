---
description: Do a retrospective on a agent session
agent: orchestrator
---

Let us do a retrospective. Please suggest improvements to the agent environment to improve future
runs.

## Steps

1. Read the primary sources for the session the user specifies. This may mean searching through
   session logs on this machine. If the user doesn't specify a session, default to the current one.
2. Look for candidates for improvement in these categories.
    - **Navigation**: how easy was it for the agent to find the right files? Are there hidden
      dependencies between files? Would a navigation pointer make it easier? _Use when_ the session
      took a long time to find a piece of information.
    - **Automated checks**: are there automated checks that could catch errors the agent made?
      Linting, typing, tests, filesystem linters? Read the repo's own check command first (its
      `package.json`/build-tool `lint`/`check` scripts, its CI workflow), so a check that already
      exists but sits unwired or silently broken is the finding, not a reinvention. _Use when_ the
      agent made a mistake an automated check could have caught, or the repo has no guardrail at
      all.
    - **Coding standards**: should the agent be given a new rule to enforce? Should an existing rule
      be removed or clarified? Classify the violation first: a mechanical one gets a deterministic
      check, full stop: a custom rule in the repo's own linter, a new pre-commit hook, or a new CI
      job, whichever the repo's language and existing guardrail make cheapest. Default to building
      the check over writing the rule. Reserve `CODING_STANDARDS.md` for genuine judgement calls.
      _Use when_ the reviewer agent failed to catch a mistake.
    - **Bloated AGENTS.md**: are there any steering instructions that should be moved to coding
      standards (or automated checks) instead? _Use when_ the AGENTS.md file is particularly large
    - **Tool economy**: did the agent make expensive tool calls that could be streamlined? Is there
      any custom tooling (CLI's, MCP's) that is particularly token-inefficient? _Use when_ the agent
      made an expensive tool call.
    - **No-ops**: look for instructions in steering files that don't modify the agent's behavior.
      _Use when_ the steering files are large and unwieldy.
    - **Information access**: look for opportunities to increase the agent's access to information.
      Teeing dev server logs, readonly access to third-party services. _Use when_ a crucial piece of
      information was not available to the agent.
3. Present these candidates in order of severity. Suggest changes to Prompts, Skills, Agents,
   repository files or anything else suited
