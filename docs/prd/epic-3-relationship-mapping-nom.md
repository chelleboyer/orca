# Epic 3: Relationship Mapping & NOM

**Epic Goal:** Build the Nested Object Matrix (NOM) that enables teams to map relationships between objects with proper cardinality and directional labeling. This epic transforms the object catalog into a connected domain model.

## Story 3.1: Basic Nested Object Matrix Interface

As a **contributor**,
I want **to view objects in a matrix format to define relationships**,
so that **I can systematically map how domain objects connect to each other**.

### Acceptance Criteria
1. NOM displays all objects as both rows and columns in an interactive grid
2. Matrix cells are clickable and show relationship status (none, defined, bidirectional)
3. Diagonal cells (object to itself) are disabled or marked as self-references
4. Grid supports scrolling and is responsive for different screen sizes
5. Matrix updates dynamically when objects are added/removed from catalog
6. Visual indicators distinguish between empty, unidirectional, and bidirectional relationships

## Story 3.2: Relationship Definition with Cardinality

As a **contributor**,
I want **to define relationships between objects with proper cardinality labels**,
so that **the domain model accurately reflects real-world constraints**.

### Acceptance Criteria
1. Clicking a matrix cell opens relationship editor with cardinality options (1:1, 1:N, N:M)
2. Users can set directional labels (e.g., "User owns Account", "Account belongs to User")
3. Relationships can be bidirectional with different labels each direction
4. Cardinality settings persist and display in matrix cell summaries
5. Relationship editor supports saving, canceling, and deleting relationships
6. Matrix cells show abbreviated relationship info (hover for full details)

## Story 3.3: Collaborative Editing & Cell Locking

As a **contributor working with teammates**,
I want **to see when others are editing relationships and avoid conflicts**,
so that **our team can collaborate efficiently without overwriting each other's work**.

### Acceptance Criteria
1. Matrix cells show presence indicators when other users are viewing/editing
2. Active editing locks cells temporarily to prevent simultaneous edits
3. Lock timeout (5 minutes) automatically releases abandoned edits
4. Users can see who is currently editing which relationships
5. Optimistic updates show changes immediately with conflict resolution
6. WebSocket communication enables real-time presence and lock updates
