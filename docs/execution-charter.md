# Project execution charter

## Source of truth order

1. Approved project specification
2. Approved current step
3. Current repository state
4. ntracts
5. AI suggestions

## Working rules

- One step at a time
- Smallest safe change set only
- No scope creep
- Human review before commit
- No feature work before the foundation is clean
- No hidden architectural expansion

## Tool roles

### ChatGPT

- Defines the next step
- Writes code, tests, docs, and config
- Debugs failures from terminal output
- Decides when repo inspection is needed

### Cursor

- Inspects current file contents
- Shows diffs and repository state when needed
- Does not drive primary implementation

## Coding rules

- No comments in code
- Use descriptive and consistent names
- Keep functions small, focused, and readable
- Prefer reusable modules over large multi-purpose files
- Write production-grade code with strong typing, validation, and error handling
- State assumptions explicitly instead of guessing requirements
- Avoid hardcoded values, hacks, and tight coupling
- Keep code modular, testable, and scalable
- Do not overengineer or introduce unnecessary abstraction
- Follow existing architecture and naming conventions unless intentionally improving them
- Keep commit messages under 140 characters

## Definition of done for each step

- Files match the approved scope
- Local verification passes
- Repository state is reviewed
- Commit is scoped to one logical change
