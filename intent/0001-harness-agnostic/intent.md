---
id: 0001-harness-agnostic
title: Harness-independent AI-native SDLC
status: accepted
author: Repository user request
date: 2026-10-14
source: idea
record_id: none
product_owner: Repository owner; manual PR review pending
---

# Intent: Harness-independent AI-native SDLC

## Problem
The template couples instructions, policies, evaluations and automation to Claude Code.
Teams using Codex or another CLI/SDK cannot adopt the same SDLC without rewriting its controls.

## Proposed outcome
One shared SDLC core, extensible agent adapters and a clear adoption path for humans and agents.
The implementation is authorized in the conversation and will be reviewed manually in a PR.

## Affected users and systems
Template adopters, contributors, coding harnesses, CI, agent evals and maintenance automation.

## Constraints
Preserve human review and production gates, existing meaningful tests and Claude compatibility.
Do not claim unsupported native integrations or silently widen permissions. No model credentials
are required to develop/test the portable core.

## Out of scope
Implementing application/business code, production infrastructure or every vendor's SDK;
merging or approving this PR; configuring adopters' actual GitHub protections.

## Open questions
Each adopter chooses a pinned harness version, its enforced sandbox, organizational policy
owners, real evals and deployment configuration.
