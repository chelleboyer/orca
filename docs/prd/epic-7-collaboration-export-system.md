# Epic 7: Collaboration & Export System

**Epic Goal:** Complete the collaborative features with real-time presence, version control through snapshots, and comprehensive export capabilities that deliver all artifacts in multiple formats for development handoff.

## Story 7.1: Real-time Presence & Activity Indicators

As a **team member**,
I want **to see who else is working on the project and what they're doing**,
so that **I can coordinate effectively and avoid conflicting work**.

### Acceptance Criteria
1. User presence indicators show who is currently active in the project
2. Activity feed displays recent changes across all artifacts
3. Current editing indicators show who is working on specific objects/relationships
4. Presence indicators appear in Object Catalog, NOM, CTA Matrix, and other key views
5. WebSocket updates provide real-time presence without page refresh
6. Idle timeout (15 minutes) removes inactive users from presence display

## Story 7.2: Project Snapshots & Version Control

As a **facilitator**,
I want **to create immutable snapshots of project state**,
so that **I can track progress, revert changes, and create milestone versions**.

### Acceptance Criteria
1. Facilitators can create named snapshots with descriptions and timestamps
2. Snapshots capture complete project state: objects, relationships, CTAs, attributes, prioritization
3. Snapshot browser allows viewing and comparing historical versions
4. Snapshot restoration creates new project branch rather than overwriting current state
5. Automatic snapshots trigger at major milestones (round completion)
6. Snapshot data includes user attribution and change summaries

## Story 7.3: Comprehensive Export Bundle Generation

As a **stakeholder**,
I want **to export complete project data in multiple formats**,
so that **I can use OOUX artifacts in development tools, presentations, and documentation**.

### Acceptance Criteria
1. Export generates ZIP bundle containing: project.json, objects.csv, relationships.csv, ctas.csv, attributes.csv
2. Bundle includes Mermaid ERD file showing complete relationship diagram
3. Object Map exports as interactive HTML with embedded styles and navigation
4. CDLL previews export as individual HTML files per object
5. Export process completes within 30 seconds for projects up to 100 objects
6. Download progress indicator and error handling provide clear user feedback
