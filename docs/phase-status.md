# Phase status

## Current step

Step 10 - Run mutation commands and execution progress endpoints

## Goal

Add mutation commands and endpoints so runs can register tasks, progress task execution, and record evidence through the service and repository boundaries.

## Exit criteria

- [ ] task registration command exists
- [ ] task lifecycle command models exist
- [ ] evidence recording command exists
- [ ] repository update path is used by mutation services
- [ ] service layer supports task registration, start, complete, and evidence recording
- [ ] API exposes mutation endpoints
- [ ] API, service, and orchestration tests cover mutation flow
- [ ] `make check` passes
- [ ] human review is complete
- [ ] commit is created
