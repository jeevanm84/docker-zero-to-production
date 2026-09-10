# Roadmap

## Position in the jeevanm84 portfolio

This repository is the containerization and orchestration layer of the [`jeevanm84`](https://github.com/jeevanm84) portfolio, sitting alongside [`kubernetes-zero-to-production`](https://github.com/jeevanm84/kubernetes-zero-to-production) (the next layer up in orchestration) and [`cicd-gitops-platform-engineering`](https://github.com/jeevanm84/cicd-gitops-platform-engineering) (the CI/CD and GitOps track this repo's Jenkins pipeline feeds into). Where [`aws-cloudfront-waf-shield-cdn-security`](https://github.com/jeevanm84/aws-cloudfront-waf-shield-cdn-security) covers the edge/CDN layer and [`terraform-aws-ha-web-platform`](https://github.com/jeevanm84/terraform-aws-ha-web-platform) covers infrastructure provisioning, this repository covers how the *application workload itself* gets packaged, run, and orchestrated.

## Within this repository

| Stage | Item | Status |
|---:|---|---|
| 1 | Architecture documentation and diagram | Published |
| 2 | Dockerfile reference (layers, caching, multi-stage builds) | Published |
| 3 | Storage and networking guide | Published |
| 4 | Compose and Swarm guide | Published |
| 5 | Security guide | Published |
| 6 | Lab 1 — container fundamentals | Published |
| 7 | Lab 2 — Dockerfile build and optimization | Published |
| 8 | Lab 3 — volumes and persistence | Published |
| 9 | Lab 4 — networking | Published |
| 10 | Lab 5 — Compose multi-service bank app | Published |
| 11 | Lab 6 — Swarm HA cluster | Published |
| 12 | Lab 7 — Jenkins image pipeline | Published |
| 13 | Portainer GUI walkthrough (Swarm + standalone) | Planned |
| 14 | Docker Scout / Trivy scanning wired into the CI workflow | Planned |
| 15 | Kubernetes migration notes (Swarm → EKS) cross-linked with `kubernetes-zero-to-production` | Planned |

## Next repository in the portfolio sequence

Following the roadmap published in the [`jeevanm84`](https://github.com/jeevanm84) profile, the CI/CD pipeline documented here (`docs/CI_CD_PIPELINE.md`) is the hand-off point into `cicd-gitops-platform-engineering`, which picks up GitOps-driven, promotion-gated deployment on top of the same containerized workloads. `docs/TROUBLESHOOTING.md` here is written in the same incident-contract format used across the portfolio, so scenarios can be cross-linked once a dedicated troubleshooting handbook is published.
