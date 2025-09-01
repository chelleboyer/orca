# Component Architecture

## Backend Components

### API Layer Components
- **FastAPI Application**: Main application server with automatic OpenAPI documentation
- **Route Handlers**: Organized by domain (projects, users, matrices, exports)
- **Middleware Stack**: Authentication, CORS, logging, and error handling
- **WebSocket Handlers**: Real-time collaboration event processing

### Business Logic Components
- **Project Service**: Project lifecycle, membership, and access control
- **Matrix Service**: ORCA matrix operations, validation, and business rules
- **Collaboration Service**: Real-time synchronization and conflict resolution
- **Export Service**: Multi-format document generation and job management
- **User Service**: Authentication, authorization, and user management

### Data Access Components
- **Database Models**: SQLAlchemy ORM entities with relationships
- **Repository Layer**: Data access abstraction with async support
- **Migration System**: Alembic-based database schema management
- **Cache Layer**: Redis integration for session and performance optimization

## Frontend Components

### Page Templates
- **Project Dashboard**: Project overview, recent activity, team members
- **Matrix Workspace**: Interactive ORCA matrix with real-time collaboration
- **Project Settings**: Configuration, permissions, and export options
- **User Profile**: Account settings, preferences, and activity history

### Interactive Components
- **Matrix Grid**: Drag-and-drop objects with relationship visualization
- **Object Editor**: Form-based object creation and modification
- **Relationship Mapper**: Visual relationship creation and editing
- **Export Dialog**: Format selection and parameter configuration

### Real-Time Features
- **Presence Indicators**: Show active users and their current focus
- **Live Cursors**: Real-time cursor position tracking
- **Change Notifications**: Toast notifications for collaborative updates
- **Conflict Resolution UI**: Merge conflict resolution interface
