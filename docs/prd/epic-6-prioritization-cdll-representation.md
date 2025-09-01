# Epic 6: Prioritization & CDLL Representation

**Epic Goal:** Implement prioritization workflows and generate CDLL (Cards/Details/Lists/Landings) representation previews that show how the domain model translates to user interface patterns.

## Story 6.1: Now/Next/Later Prioritization

As a **product owner**,
I want **to prioritize objects, CTAs, and attributes into development phases**,
so that **we can plan implementation based on business value and dependencies**.

### Acceptance Criteria
1. Prioritization interface allows dragging items between Now/Next/Later columns
2. All objects, CTAs, and attributes can be independently prioritized
3. Optional scoring (1-10) provides additional prioritization detail
4. Prioritization view supports filtering by item type and current assignment
5. Bulk operations enable efficient categorization of multiple items
6. Priority changes reflect immediately in other views and exports

## Story 6.2: CDLL Preview Generation

As a **designer/developer**,
I want **to see how objects translate to user interface patterns**,
so that **I can understand the implementation implications of our domain model**.

### Acceptance Criteria
1. System generates Card, Detail, List, and Landing previews for each object
2. Previews use core attributes and primary CTAs to build realistic interfaces
3. Missing core attributes trigger warnings with suggestions for completion
4. Preview styling follows basic design patterns appropriate for object types
5. CDLL previews export as HTML with embedded CSS for developer handoff
6. Preview generation respects prioritization (Now items get full previews)

## Story 6.3: Representation Validation & Completeness

As a **facilitator**,
I want **to validate that our domain model is ready for implementation**,
so that **I can confidently hand off complete specifications to development teams**.

### Acceptance Criteria
1. System checks each object for minimum viable attributes and CTAs
2. Validation reports identify gaps in object definitions, relationships, or attributes
3. Dependency analysis shows objects that lack sufficient detail for CDLL generation
4. Completion dashboard shows percentage complete across all ORCA dimensions
5. Export readiness indicator confirms all critical artifacts are sufficiently defined
6. Validation rules are configurable based on project-specific requirements
