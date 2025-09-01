# Epic 4: Roles & Call-to-Action Matrix

**Epic Goal:** Implement role definition and the Call-to-Action Matrix that maps user roles to object interactions, defining the behavioral layer of the domain model.

## Story 4.1: Role Definition & Management

As a **facilitator**,
I want **to define user roles relevant to our domain**,
so that **we can map role-specific interactions with domain objects**.

### Acceptance Criteria
1. Facilitators can create, edit, and delete project roles
2. Roles have names and optional descriptions
3. Role list supports reordering for CTA Matrix display
4. System includes common default roles (User, Admin, Guest) as starting templates
5. Roles can be archived rather than deleted if used in CTAs
6. Role management is accessible from project settings

## Story 4.2: CTA Matrix Core Functionality

As a **contributor**,
I want **to map roles to objects and define their possible actions**,
so that **we can model the behavioral requirements of our domain**.

### Acceptance Criteria
1. CTA Matrix displays roles as rows and objects as columns
2. Cell editing allows adding multiple CTAs per role-object intersection
3. CTAs include verb (action), CRUD classification, and primary flag
4. Users can add, edit, delete, and reorder CTAs within cells
5. Matrix supports filtering by CRUD type or primary actions only
6. Cell expansion shows full CTA details with formatting

## Story 4.3: CTA Pre/Post Conditions & Context

As a **business analyst**,
I want **to define conditions and context around call-to-actions**,
so that **we capture the business rules governing user interactions**.

### Acceptance Criteria
1. Each CTA supports optional preconditions (what must be true before action)
2. Each CTA supports optional postconditions (what changes after action)
3. Conditions are free-text fields supporting business rule descriptions
4. CTA detail view shows full context including conditions
5. Export includes all CTA context and conditions
6. Search functionality helps find CTAs by verb, conditions, or context
