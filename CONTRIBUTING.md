# Contributing

Thanks for considering a contribution to this repository.

## Before opening a pull request

1. Run `python3 scripts/check.py` and fix anything it flags.
2. If you changed a Dockerfile under `examples/`, make sure it still builds: `docker build -t test .` from that directory.
3. If you changed a Compose file, run `docker compose -f <file> config` to confirm it parses.
4. If you added or changed a lab, make sure it includes: objective, prerequisites, starting state, steps, expected observations, verification, cleanup, and an explanation of why the result occurs — see the existing labs for the pattern.
5. Do not include employer names, customer data, account IDs, real registry credentials, or internal URLs anywhere in the repository.

## What's welcome

- Corrections to technical inaccuracies, with a reference where possible.
- New labs that follow the existing contract (objective → steps → verification → cleanup).
- Additional interview questions with links back to working evidence in this repository.
- Additional Dockerfile/Compose examples that illustrate one concept clearly (layers, multi-stage builds, networking, secrets).

## What's not in scope here

- Auto-building and auto-pushing images to a real registry via CI — the Jenkins pipeline in `examples/jenkins/` is documented as a manual/parameterized build, not wired to run automatically on push, by design (see `docs/CI_CD_PIPELINE.md`).
- Running a live multi-node Docker Swarm cluster in CI — the Swarm labs are written to be run on your own EC2/VM instances.

Use Issues for reproducible defects or improvement proposals, and Discussions for learning questions.
