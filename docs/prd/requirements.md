# Requirements

## Functional Requirements

**FR1:** Users can create, list, and open projects with role-based access (Facilitator/Lead, Contributor, Viewer)

**FR2:** The system supports guided mode with step-by-step progression and "definition of done" checkpoints for each ORCA round

**FR3:** The system supports freeform mode allowing users to jump to any artifact with gap flagging but no blocking

**FR4:** Users can manage an Object Catalog with CRUD operations for objects including definitions, synonyms, and states

**FR5:** The system provides a Nested Object Matrix (NOM) for defining object relationships with cardinality (1:1, 1:N, N:M) and directional labels

**FR6:** Users can create and manage a CTA Matrix mapping objects to roles with call-to-action verbs, CRUD tags, primary flags, and pre/post conditions

**FR7:** The system supports attribute management with data types, required flags, and core attribute designation for Object Map display

**FR8:** Users can prioritize items (Objects/CTAs/Attributes) into "Now/Next/Later" slices with optional scoring

**FR9:** The system generates CDLL (Cards/Details/Lists/Landings) representation previews using core attributes and CTAs

**FR10:** The system provides real-time presence indicators and per-cell locking on collaborative matrices to prevent overwrites

**FR11:** Users can create immutable project snapshots for version control and milestone tracking

**FR12:** The system exports comprehensive bundles including JSON, CSV files, Mermaid ERD, Object Map HTML, and CDLL HTML

**FR13:** The system displays dependency banners summarizing gaps with "Proceed anyway" options in freeform mode

**FR14:** Progress tracking shows completion status across all ORCA rounds and artifacts

## Non-Functional Requirements

**NFR1:** The system must support real-time collaboration for up to 10 concurrent users per project without performance degradation

**NFR2:** All data operations must persist immediately with automatic save functionality (no manual save required)

**NFR3:** The web application must be responsive and functional on desktop, tablet, and mobile devices

**NFR4:** Export operations must complete within 30 seconds for projects with up to 100 objects

**NFR5:** The system must maintain 99.9% uptime during business hours (9 AM - 6 PM local time)

**NFR6:** All user inputs must be validated client-side and server-side to prevent data corruption

**NFR7:** The system must support concurrent editing with conflict resolution for matrix cells

**NFR8:** Page load times must not exceed 3 seconds on standard broadband connections
