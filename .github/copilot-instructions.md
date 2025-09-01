# GitHub Copilot Instructions for BMad Method Framework

## Project Overview

This is the **BMad Method Framework** - a comprehensive AI-agent orchestration system for structured agile planning and development. The project consists of specialized AI agents, templates, tasks, and workflows designed for both web-based planning and IDE-based development.

## Architecture Patterns

### Agent System Architecture
- **Core Directory**: `.bmad-core/` contains all framework components
- **Web Bundles**: `web-bundles/` contains distributable agent packages for web platforms
- **Agent Definitions**: Each agent has YAML configuration in `.bmad-core/agents/` with specialized personas, commands, and dependencies
- **Dependency Resolution**: Agents load resources on-demand via dependency mappings (e.g., `tasks: create-doc` → `.bmad-core/tasks/create-doc.md`)

### Key Agent Types
- **BMad Master** (`bmad-master`): Universal executor, can run any task without persona transformation
- **BMad Orchestrator** (`bmad-orchestrator`): Workflow coordinator, morphs into specialized agents
- **Specialized Agents**: PM, Architect, Dev, QA, UX Expert, etc. with domain-specific capabilities

### Bundle System
- **Teams**: `.bmad-core/agent-teams/` define agent collections (fullstack, no-ui, ide-minimal)
- **Expansion Packs**: `web-bundles/expansion-packs/` add domain-specific capabilities (game dev, creative writing, DevOps)
- **Web Distribution**: Agents bundled into self-contained `.txt` files for web AI platforms

## Development Workflow Patterns

### Configuration-Driven Behavior
- **Core Config**: `.bmad-core/core-config.yaml` defines project-specific paths and settings
- **Agent Activation**: Agents follow strict YAML-defined activation instructions and command prefixes (typically `*`)
- **Template System**: All outputs use YAML templates from `.bmad-core/templates/`

### Document Management
- **Sharding Strategy**: Large documents split into focused components (PRD → epics → stories)
- **Standard Paths**: `docs/prd.md`, `docs/architecture.md`, `docs/stories/`, `docs/qa/`
- **File Naming**: Pattern-based naming like `{epic}.{story}` for stories, timestamped assessments

### Agent Command Patterns
```bash
# Command examples (web platforms use / prefix, IDE uses @)
*help                    # Show available commands
*create-doc {template}   # Generate document from template
*task {task-name}        # Execute specific task
*agent {agent-name}      # Transform to specialized agent (orchestrator)
```

## Critical Development Rules

### Agent Implementation
- **Stay in Character**: Agents must maintain persona until explicitly told to exit
- **Lazy Loading**: Only load dependency files when specifically requested
- **Numbered Lists**: Always present choices as numbered options for user selection
- **Section Updates**: Dev agent can ONLY update specific story sections (Tasks, Dev Agent Record, File List, Change Log)

### Quality System (QA Agent)
- **Test Architect**: QA agent focuses on risk assessment, test design, and quality gates
- **Gate Decisions**: PASS/CONCERNS/FAIL/WAIVED status in `docs/qa/gates/`
- **Assessment Types**: Risk profile, test design, requirements tracing, NFR assessment
- **Command Aliases**: `*risk`, `*design`, `*trace`, `*nfr`, `*review`, `*gate`

### File Organization Standards
- **Core Framework**: Everything in `.bmad-core/` (agents, tasks, templates, data, workflows)
- **Web Distribution**: Self-contained bundles in `web-bundles/`
- **IDE Integration**: Cursor rules in `.cursor/rules/bmad/`
- **Documentation**: Always in `docs/` with standardized structure

## Common Integration Patterns

### Template-Task Coupling
- Templates define structure (`prd-tmpl.yaml`)
- Tasks define execution logic (`create-doc.md`)
- Agents orchestrate template + task combinations

### Workflow Execution
- **Sequential Phases**: Planning (web) → Development (IDE)
- **Agent Handoffs**: Orchestrator routes to specialist → specialist completes work → returns to orchestrator
- **State Management**: Workflow status tracked in agent context

### Bundle Generation
- Individual agent files concatenated with resource dependencies
- Self-contained with navigation instructions and resource markers
- Platform-agnostic (works with Claude, GPT, Gemini)

## Testing & Validation Approach

### Built-in Validation
- **Story Definition of Done**: Checklist-driven validation in `checklists/story-dod-checklist.md`
- **Anti-Hallucination**: All technical claims must trace to source documents
- **Template Compliance**: Stories validated against `story-tmpl.yaml` structure

### Quality Gates
- **Risk-Based Testing**: Priority P0/P1/P2 based on risk assessment
- **Coverage Tracking**: Requirements traceability matrix maintained by QA agent
- **NFR Validation**: Security, Performance, Reliability, Maintainability checks

## Key Files to Reference

### Essential Configuration
- `.bmad-core/core-config.yaml` - Project-specific settings
- `.bmad-core/install-manifest.yaml` - Installation tracking and version info
- `.bmad-core/user-guide.md` - Complete framework documentation

### Agent Entry Points
- `.bmad-core/agents/bmad-master.md` - Universal agent configuration
- `.bmad-core/agents/dev.md` - Development agent with story implementation logic
- `.bmad-core/agents/qa.md` - Test architect with quality assessment capabilities

### Templates & Patterns
- `.bmad-core/templates/story-tmpl.yaml` - Story structure template
- `.bmad-core/tasks/develop-story.md` - Core development workflow
- `.bmad-core/tasks/apply-qa-fixes.md` - QA integration pattern

When working with this codebase, always consider the agent context, follow the established YAML-driven patterns, and respect the lazy-loading dependency system.
