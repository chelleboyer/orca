# Data Models

## Core Domain Models

### Project Entity
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

### User Entity
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

### Project Membership
```python
class ProjectMembership(Base):
    id: UUID (Primary Key)
    project_id: UUID (Foreign Key → Project)
    user_id: UUID (Foreign Key → User)
    role: MembershipRole (enum: owner, editor, viewer)
    joined_at: datetime
    permissions: JSON (granular permissions)
```

## ORCA Matrix Models

### Object Entity
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

### Relationship Entity
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

### CTA (Call-to-Action) Entity
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

### Attribute Entity
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

## Prioritization Models

### Prioritization Entity
```python
class Prioritization(Base):
    id: UUID (Primary Key)
    project_id: UUID (Foreign Key → Project)
    item_type: ItemType (enum: object, cta, attribute, relationship)
    item_id: UUID (item being prioritized)
    priority_phase: PriorityPhase (enum: now, next, later, unassigned)
    score: Optional[int] (1-10 priority scoring)
    position: int (order within phase)
    notes: Optional[str] (prioritization rationale)
    assigned_by: UUID (Foreign Key → User)
    assigned_at: datetime
    updated_at: datetime
```

### Prioritization Snapshot Entity
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

## Collaboration Models

### Session Management
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

### Change Tracking
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

## Export Models

### Export Job
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
