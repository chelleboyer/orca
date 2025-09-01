# Epic 2: Core Object Modeling & Catalog

**Epic Goal:** Implement the foundational Object Catalog that allows teams to create, manage, and define the core domain objects that form the basis of all OOUX work. This epic delivers the essential object management capabilities needed for subsequent relationship mapping and attribute definition.

## Story 2.1: Object Catalog CRUD Operations

As a **contributor**,
I want **to create, view, edit, and delete objects in the project catalog**,
so that **I can build and maintain the foundational object model for our domain**.

### Acceptance Criteria
1. Contributors can create new objects with name and initial definition
2. Object Catalog displays all project objects in a searchable, sortable table
3. Users can edit object names and definitions with inline editing
4. Object deletion requires confirmation and checks for dependencies
5. Object names must be unique within a project
6. System tracks creation and modification timestamps for audit

## Story 2.2: Object Definitions & Synonyms Management

As a **contributor**,
I want **to add detailed definitions and synonyms to objects**,
so that **the team has clear, shared understanding of each domain concept**.

### Acceptance Criteria
1. Objects support multi-line definition text with formatting
2. Contributors can add multiple synonyms per object
3. Synonym search helps users find objects by alternative names
4. Definitions support basic markdown formatting for clarity
5. System prevents duplicate synonyms within a project
6. Object detail view shows full definition and all synonyms

## Story 2.3: Object States & Lifecycle Management

As a **domain expert**,
I want **to define possible states for objects that have lifecycle changes**,
so that **we can model dynamic objects that change over time**.

### Acceptance Criteria
1. Objects can have optional state definitions (e.g., Draft, Published, Archived)
2. States are defined as simple text labels with optional descriptions
3. Object view indicates if states are defined vs. stateless objects
4. State management is optional - not all objects require states
5. States can be added, edited, or removed after object creation
6. Export includes state information when defined
