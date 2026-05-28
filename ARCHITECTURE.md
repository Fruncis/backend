# Architecture — Ports and Adapters (Hexagonal)

> **This file is the law of the codebase.**
> Every contributor must read and follow it before writing a single line of code.

---

## Top-Level Packages

| Package      | Purpose |
|--------------|---------|
| `core/`      | Pure business logic — domain entities, use-cases, port interfaces, and configuration. **Zero framework dependencies.** |
| `adapters/`  | Infrastructure glue — concrete implementations that talk to the outside world (HTTP, databases, third-party APIs). |

---

## The Golden Rule

```
core/ MUST NEVER import from adapters/
```

- Not directly.
- Not transitively.
- Not via string references, dynamic imports, or any other trick.

**This is non-negotiable.** If you find yourself needing something from `adapters/` inside `core/`, you are violating the architecture. Define a port interface in `core/ports/` and implement it in `adapters/`.

---

## Dependency Direction

```
adapters/  ──▶  core/
```

One direction only. Never reverse.

`adapters/` MAY import from `core/` — this is the correct and only allowed dependency direction. `main.py` (the composition root) is the only place where adapters and core are wired together.

---

## Package Breakdown

### `core/ports/`

Abstract interfaces defined as Python ABCs. These are the **contracts** between the business logic and the outside world. Use-cases depend on ports; adapters implement them.

### `core/domain/`

Pure Python entities and value objects. No framework imports, no I/O, no side effects. Domain exceptions also live here.

### `core/usecases/`

Orchestration layer. Use-cases coordinate domain logic by calling port interfaces. They **never** instantiate adapters directly — dependencies are injected.

> **Important:** Pure in-memory processing (e.g., PDF parsing with PyPDF2) belongs here, **not** in `adapters/`. The criterion for `adapters/outbound/` is: _does it make an outbound call (HTTP, TCP, filesystem I/O to external systems)?_ If not, it stays in `core/`.

### `core/config/`

Application settings (Pydantic models). Importable by both `adapters/` and `main.py`.

### `adapters/inbound/`

Entry points into the application — e.g., FastAPI routers, CLI commands, message consumers. They receive external requests and translate them into use-case calls.

### `adapters/outbound/`

Implementations that make **outbound calls**: database queries (Postgres), HTTP requests to third-party APIs (Gemini), message publishing, etc.

**Criterion:** If the code makes an outbound network/I/O call, it belongs in `adapters/outbound/`. If it's pure in-memory logic (e.g., `PDFSegmenter` using PyPDF2), it belongs in `core/usecases/`.

---

## Visual Summary

```
┌─────────────────────────────────────────────────┐
│                    main.py                      │
│              (composition root)                 │
└──────────┬──────────────────┬───────────────────┘
           │                  │
           ▼                  ▼
┌──────────────────┐ ┌───────────────────────────┐
│   adapters/      │ │         core/             │
│                  │ │                           │
│  inbound/        │ │  ports/    (ABCs)         │
│    fastapi/      │ │  domain/   (entities)     │
│                  │ │  usecases/ (orchestration) │
│  outbound/       │ │  config/   (settings)     │
│    postgres/     │ │                           │
│    gemini/       │ │                           │
└────────┬─────────┘ └───────────────────────────┘
         │                    ▲
         │                    │
         └────────────────────┘
         adapters/ imports core/
         (NEVER the reverse)
```

---

## Rules for New Code

1. **Adding a new external service?** Create a port in `core/ports/`, implement the adapter in `adapters/outbound/<service>/`.
2. **Adding a new entry point?** Create the adapter in `adapters/inbound/<framework>/`.
3. **Adding business logic?** It goes in `core/domain/` or `core/usecases/`. Period.
4. **No `adapters/utils/`** — utility/helper code that doesn't make outbound calls lives in `core/`.
