# API Design

## REST API Endpoints

### Project Management
```
GET    /api/v1/projects                    # List user's projects
POST   /api/v1/projects                    # Create new project
GET    /api/v1/projects/{id}              # Get project details
PUT    /api/v1/projects/{id}              # Update project
DELETE /api/v1/projects/{id}              # Delete project
GET    /api/v1/projects/{id}/members      # List project members
POST   /api/v1/projects/{id}/members      # Add project member
DELETE /api/v1/projects/{id}/members/{uid} # Remove project member
```

### ORCA Matrix Operations
```
GET    /api/v1/projects/{id}/objects       # List project objects
POST   /api/v1/projects/{id}/objects       # Create new object
GET    /api/v1/objects/{id}               # Get object details
PUT    /api/v1/objects/{id}               # Update object
DELETE /api/v1/objects/{id}               # Delete object

GET    /api/v1/objects/{id}/relationships # List object relationships
POST   /api/v1/relationships              # Create relationship
PUT    /api/v1/relationships/{id}         # Update relationship
DELETE /api/v1/relationships/{id}         # Delete relationship

GET    /api/v1/objects/{id}/ctas          # List object CTAs
POST   /api/v1/objects/{id}/ctas          # Create CTA
PUT    /api/v1/ctas/{id}                  # Update CTA
DELETE /api/v1/ctas/{id}                  # Delete CTA

GET    /api/v1/objects/{id}/attributes    # List object attributes
POST   /api/v1/objects/{id}/attributes    # Create attribute
PUT    /api/v1/attributes/{id}            # Update attribute
DELETE /api/v1/attributes/{id}            # Delete attribute
```

### Export Operations
```
POST   /api/v1/projects/{id}/export       # Request export job
GET    /api/v1/export-jobs/{id}           # Get export job status
GET    /api/v1/export-jobs/{id}/download  # Download completed export
DELETE /api/v1/export-jobs/{id}           # Cancel export job
```

## WebSocket Events

### Connection Management
```javascript
// Client connects to project workspace
connect: { project_id: UUID, auth_token: string }

// Server confirms connection
connection_confirmed: { user_id: UUID, session_id: UUID }

// User presence updates
user_joined: { user_id: UUID, user_name: string }
user_left: { user_id: UUID }
user_cursor_moved: { user_id: UUID, position: { x: number, y: number } }
```

### Matrix Collaboration
```javascript
// Object operations
object_created: { object: Object, created_by: UUID }
object_updated: { object_id: UUID, changes: object, updated_by: UUID }
object_deleted: { object_id: UUID, deleted_by: UUID }

// Relationship operations
relationship_created: { relationship: Relationship, created_by: UUID }
relationship_updated: { relationship_id: UUID, changes: object, updated_by: UUID }
relationship_deleted: { relationship_id: UUID, deleted_by: UUID }

// Real-time editing
editing_started: { entity_type: string, entity_id: UUID, user_id: UUID }
editing_ended: { entity_type: string, entity_id: UUID, user_id: UUID }
```
