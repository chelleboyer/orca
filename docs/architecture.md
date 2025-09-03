# OOUX ORCA Project Builder - System Architecture

## Introduction

The OOUX ORCA Project Builder is a collaborative web application designed to guide teams through the Object-Oriented UX methodology. The system enables multiple users to work simultaneously on ORCA matrices, providing real-time collaboration, structured workflows, and comprehensive export capabilities.

This architecture document outlines the technical foundation, system design, and implementation strategy for delivering a scalable, maintainable solution that supports the complex requirements of OOUX practitioners.

## Technology Stack

### Backend Framework
- **FastAPI**: High-performance async framework for REST API development
- **Python 3.11+**: Modern Python with enhanced performance and type hints
- **Pydantic**: Data validation and serialization with automatic OpenAPI generation

### Database & Storage
- **PostgreSQL**: Primary relational database for domain model persistence
- **SQLAlchemy 2.0**: Modern ORM with async support and improved type safety
- **Alembic**: Database migration management
- **Redis**: Session management, real-time presence, and caching layer

### Real-Time Communication
- **WebSockets**: Native FastAPI WebSocket support for collaborative features
- **Connection Management**: Custom WebSocket manager for user presence and real-time updates
- **Message Broadcasting**: Event-driven architecture for matrix synchronization

### Frontend Technology
- **Python-based Solution**: Leveraging server-side rendering for rapid development
- **HTMX**: Dynamic content updates without full page refreshes
- **Jinja2 Templates**: Template engine for server-side rendering
- **Tailwind CSS**: Utility-first CSS framework for responsive design

### Development & Deployment
- **Docker**: Containerized deployment with multi-stage builds
- **pytest**: Comprehensive testing framework with async support
- **GitHub Actions**: CI/CD pipeline for automated testing and deployment
- **Environment Management**: python-dotenv for configuration management

### Export & Integration
- **ReportLab**: PDF generation for ORCA reports
- **openpyxl**: Excel export functionality
- **Mermaid.js**: Diagram generation for object maps
- **JSON/CSV**: Standard data exchange formats

## High-Level System Design

### System Architecture Overview

The OOUX ORCA Project Builder follows a modern web application architecture with the following key characteristics:

- **Layered Architecture**: Clear separation between presentation, business logic, and data layers
- **Event-Driven Design**: Real-time collaboration through WebSocket events and message broadcasting
- **RESTful API**: Standard HTTP endpoints for CRUD operations and resource management
- **Database-First Approach**: Relational data modeling reflecting OOUX domain concepts

### Core System Components

#### 1. Web Application Layer
- **FastAPI Application**: Main application server handling HTTP requests and WebSocket connections
- **Template Engine**: Jinja2-based server-side rendering with HTMX enhancement
- **Static Asset Management**: CSS, JavaScript, and image serving with proper caching headers
- **Authentication & Authorization**: Session-based authentication with role-based access control

#### 2. Business Logic Layer
- **Project Management**: Project lifecycle, user access, and workspace management
- **ORCA Matrix Engine**: Core logic for Objects, Relationships, CTAs, and Attributes
- **Collaboration Engine**: Real-time synchronization, conflict resolution, and user presence
- **Export Engine**: Multi-format document generation and data transformation

#### 3. Data Access Layer
- **Database Models**: SQLAlchemy ORM models representing OOUX domain entities
- **Repository Pattern**: Data access abstraction for testability and maintainability
- **Connection Pooling**: Optimized database connection management
- **Caching Strategy**: Redis-based caching for frequently accessed data

#### 4. Real-Time Communication Layer
- **WebSocket Manager**: Connection lifecycle management and message routing
- **Event Broadcasting**: Pub/sub pattern for real-time matrix updates
- **Presence Management**: User online status and active workspace tracking
- **Conflict Resolution**: Operational transformation for concurrent edits

### Data Flow Architecture

#### Request Processing Flow
1. **HTTP Request** → FastAPI Router → Business Logic → Data Layer → Response
2. **WebSocket Event** → Connection Manager → Event Handler → Broadcast → Clients
3. **Database Transaction** → SQLAlchemy Session → PostgreSQL → Commit/Rollback
4. **Cache Operations** → Redis Client → In-Memory Storage → Response

#### Real-Time Collaboration Flow
1. **User Action** → Frontend Event → WebSocket Message → Server Processing
2. **Server Processing** → Business Logic → Database Update → Event Generation
3. **Event Broadcasting** → WebSocket Manager → Connected Clients → UI Update
4. **Conflict Detection** → Merge Strategy → Resolution → State Synchronization

## Data Models

### Core Domain Models

#### Project Entity
```python
class Project(Base):
    id: UUID (Primary Key)
    name: str
    description: Optional[str]
    owner_id: UUID (Foreign Key → User)
    created_at: datetime
    updated_at: datetime
    status: ProjectStatus (enum)
    settings: JSON (project-specific configurations)
```

#### User Entity
```python
class User(Base):
    id: UUID (Primary Key)
    email: str (Unique)
    name: str
    password_hash: str
    created_at: datetime
    last_login: Optional[datetime]
    is_active: bool
    role: UserRole (enum)
```

#### Project Membership
```python
class ProjectMembership(Base):
    id: UUID (Primary Key)
    project_id: UUID (Foreign Key → Project)
    user_id: UUID (Foreign Key → User)
    role: MembershipRole (enum: owner, editor, viewer)
    joined_at: datetime
    permissions: JSON (granular permissions)
```

### ORCA Matrix Models

#### Object Entity
```python
class Object(Base):
    id: UUID (Primary Key)
    project_id: UUID (Foreign Key → Project)
    name: str
    description: Optional[str]
    position_x: int (matrix coordinates)
    position_y: int
    object_type: ObjectType (enum)
    complexity: ComplexityLevel (enum)
    created_by: UUID (Foreign Key → User)
    created_at: datetime
    updated_at: datetime
    metadata: JSON (extensible properties)
```

#### Relationship Entity
```python
class Relationship(Base):
    id: UUID (Primary Key)
    project_id: UUID (Foreign Key → Project)
    source_object_id: UUID (Foreign Key → Object)
    target_object_id: UUID (Foreign Key → Object)
    relationship_type: RelationshipType (enum)
    cardinality: CardinalityType (enum)
    description: Optional[str]
    created_at: datetime
    updated_at: datetime
```

#### CTA (Call-to-Action) Entity
```python
class CTA(Base):
    id: UUID (Primary Key)
    object_id: UUID (Foreign Key → Object)
    name: str
    description: Optional[str]
    priority: Priority (enum)
    user_story: Optional[str]
    acceptance_criteria: Optional[str]
    created_at: datetime
    updated_at: datetime
```

#### Attribute Entity
```python
class Attribute(Base):
    id: UUID (Primary Key)
    object_id: UUID (Foreign Key → Object)
    name: str
    data_type: AttributeDataType (enum)
    is_required: bool
    default_value: Optional[str]
    validation_rules: JSON
    description: Optional[str]
    created_at: datetime
    updated_at: datetime
```

#### Prioritization Entity
```python
class Prioritization(Base):
    id: UUID (Primary Key)
    project_id: UUID (Foreign Key → Project)
    item_type: ItemType (enum: object, cta, attribute, relationship)
    item_id: UUID (item being prioritized)
    priority_phase: PriorityPhase (enum: now, next, later, unassigned)
    score: Optional[int] (1-10 priority scoring)
    position: int (order within phase)
    notes: Optional[str]
    assigned_by: UUID (Foreign Key → User)
    assigned_at: datetime
    updated_at: datetime
```

#### Prioritization Snapshot Entity
```python
class PrioritizationSnapshot(Base):
    id: UUID (Primary Key)
    project_id: UUID (Foreign Key → Project)
    snapshot_name: str
    description: Optional[str]
    created_by: UUID (Foreign Key → User)
    created_at: datetime
    snapshot_data: JSON (serialized prioritization state)
```

### Collaboration Models

#### Session Management
```python
class UserSession(Base):
    id: UUID (Primary Key)
    user_id: UUID (Foreign Key → User)
    project_id: UUID (Foreign Key → Project)
    connection_id: str (WebSocket connection identifier)
    joined_at: datetime
    last_activity: datetime
    cursor_position: JSON (current focus in matrix)
    active_editing: Optional[UUID] (entity being edited)
```

#### Change Tracking
```python
class ChangeLog(Base):
    id: UUID (Primary Key)
    project_id: UUID (Foreign Key → Project)
    user_id: UUID (Foreign Key → User)
    entity_type: str (Object, Relationship, CTA, Attribute)
    entity_id: UUID
    action: ChangeAction (enum: create, update, delete)
    changes: JSON (field-level change details)
    timestamp: datetime
    session_id: Optional[UUID]
```

### Export Models

#### Export Job
```python
class ExportJob(Base):
    id: UUID (Primary Key)
    project_id: UUID (Foreign Key → Project)
    requested_by: UUID (Foreign Key → User)
    export_type: ExportType (enum)
    format: ExportFormat (enum)
    status: JobStatus (enum)
    parameters: JSON (export configuration)
    created_at: datetime
    completed_at: Optional[datetime]
    file_path: Optional[str]
    error_message: Optional[str]
```

## Component Architecture

### Backend Components

#### API Layer Components
- **FastAPI Application**: Main application server with automatic OpenAPI documentation
- **Route Handlers**: Organized by domain (projects, users, matrices, exports)
- **Middleware Stack**: Authentication, CORS, logging, and error handling
- **WebSocket Handlers**: Real-time collaboration event processing

#### Business Logic Components
- **Project Service**: Project lifecycle, membership, and access control
- **Matrix Service**: ORCA matrix operations, validation, and business rules
- **Prioritization Service**: Now/Next/Later prioritization, scoring, and bulk operations
- **Collaboration Service**: Real-time synchronization and conflict resolution
- **Export Service**: Multi-format document generation and job management
- **User Service**: Authentication, authorization, and user management

#### Data Access Components
- **Database Models**: SQLAlchemy ORM entities with relationships
- **Repository Layer**: Data access abstraction with async support
- **Migration System**: Alembic-based database schema management
- **Cache Layer**: Redis integration for session and performance optimization

### Frontend Components

#### Page Templates
- **Project Dashboard**: Project overview, recent activity, team members
- **Matrix Workspace**: Interactive ORCA matrix with real-time collaboration
- **Project Settings**: Configuration, permissions, and export options
- **User Profile**: Account settings, preferences, and activity history

#### Interactive Components
- **Matrix Grid**: Drag-and-drop objects with relationship visualization
- **Object Editor**: Form-based object creation and modification
- **Relationship Mapper**: Visual relationship creation and editing
- **Export Dialog**: Format selection and parameter configuration

#### Real-Time Features
- **Presence Indicators**: Show active users and their current focus
- **Live Cursors**: Real-time cursor position tracking
- **Change Notifications**: Toast notifications for collaborative updates
- **Conflict Resolution UI**: Merge conflict resolution interface

## API Design

### REST API Endpoints

#### Project Management
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

#### ORCA Matrix Operations
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

GET    /api/v1/projects/{id}/prioritizations      # List project prioritizations
POST   /api/v1/projects/{id}/prioritizations      # Create prioritization
GET    /api/v1/prioritizations/{id}              # Get prioritization details
PUT    /api/v1/prioritizations/{id}              # Update prioritization
DELETE /api/v1/prioritizations/{id}              # Delete prioritization
GET    /api/v1/projects/{id}/prioritizations/board    # Get prioritization board
GET    /api/v1/projects/{id}/prioritizations/stats    # Get prioritization statistics
POST   /api/v1/projects/{id}/prioritizations/bulk-update  # Bulk update prioritizations
POST   /api/v1/projects/{id}/prioritizations/snapshots   # Create prioritization snapshot
GET    /api/v1/projects/{id}/prioritizations/snapshots   # List prioritization snapshots
```

#### Export Operations
```
POST   /api/v1/projects/{id}/export       # Request export job
GET    /api/v1/export-jobs/{id}           # Get export job status
GET    /api/v1/export-jobs/{id}/download  # Download completed export
DELETE /api/v1/export-jobs/{id}           # Cancel export job
```

### WebSocket Events

#### Connection Management
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

#### Matrix Collaboration
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

## Deployment Strategy

### Containerization

#### Docker Configuration
- **Multi-stage Builds**: Optimized production images with minimal attack surface
- **Base Images**: Official Python slim images for security and performance
- **Dependency Management**: Poetry for reproducible dependency resolution
- **Health Checks**: Built-in container health monitoring

#### Container Services
```yaml
services:
  web:
    image: ooux-orca-web:latest
    environment:
      - DATABASE_URL=postgresql://...
      - REDIS_URL=redis://...
    depends_on:
      - database
      - redis
    
  database:
    image: postgres:15-alpine
    environment:
      - POSTGRES_DB=ooux_orca
      - POSTGRES_USER=app_user
    volumes:
      - postgres_data:/var/lib/postgresql/data
    
  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data
```

### Environment Configuration

#### Development Environment
- **Local Development**: Docker Compose with hot-reload and debug capabilities
- **Database Seeding**: Test data fixtures for development and testing
- **Debug Tools**: FastAPI debug mode with automatic reload
- **Live Reloading**: File watching for template and static asset changes

#### Production Environment
- **Process Management**: Gunicorn with Uvicorn workers for async support
- **Reverse Proxy**: Nginx for static file serving and load balancing
- **SSL Termination**: Let's Encrypt certificates with automatic renewal
- **Monitoring**: Prometheus metrics and health check endpoints

### Scalability Considerations

#### Horizontal Scaling
- **Stateless Design**: Session data stored in Redis for multi-instance deployment
- **Load Balancing**: Sticky sessions for WebSocket connections
- **Database Scaling**: Read replicas for query distribution
- **Cache Distribution**: Redis Cluster for high-availability caching

#### Performance Optimization
- **Connection Pooling**: Optimized database connection management
- **Query Optimization**: Eager loading and index strategies
- **CDN Integration**: Static asset delivery via content delivery network
- **Compression**: Gzip compression for API responses and static content

## Security Architecture

### Authentication & Authorization
- **Session-based Authentication**: Secure session management with Redis storage
- **Password Security**: Argon2 hashing with salt for credential storage
- **Role-based Access Control**: Hierarchical permissions (owner, editor, viewer)
- **API Security**: Request rate limiting and input validation

### Data Protection
- **Database Security**: Encrypted connections and parameterized queries
- **HTTPS Enforcement**: TLS 1.3 for all client-server communication
- **CORS Configuration**: Restricted cross-origin access policies
- **Input Sanitization**: Comprehensive validation for all user inputs

### Operational Security
- **Secrets Management**: Environment-based configuration with secret rotation
- **Audit Logging**: Comprehensive change tracking and access logging
- **Backup Strategy**: Automated database backups with encryption
- **Vulnerability Scanning**: Regular dependency and container security scans

## Performance Requirements

### Response Time Targets
- **Page Load**: < 2 seconds for initial page rendering
- **API Responses**: < 500ms for standard CRUD operations
- **Real-time Updates**: < 100ms WebSocket message propagation
- **Export Generation**: < 30 seconds for standard project exports

### Concurrency Support
- **Concurrent Users**: Support 50+ simultaneous users per project
- **WebSocket Connections**: 1000+ concurrent real-time connections
- **Database Load**: Optimized for 100+ queries per second
- **File Operations**: Parallel export processing for multiple formats

### Resource Optimization
- **Memory Usage**: < 512MB base memory footprint per container
- **Database Connections**: Connection pooling with max 20 connections per instance
- **Cache Hit Ratio**: > 90% cache hit rate for frequently accessed data
- **Network Efficiency**: Compressed payloads and efficient WebSocket messaging

This architecture provides a solid foundation for building the OOUX ORCA Project Builder with scalability, security, and performance in mind. The design supports the collaborative nature of OOUX methodology while maintaining the technical requirements outlined in the PRD.
