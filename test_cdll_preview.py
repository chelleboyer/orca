#!/usr/bin/env python3
"""
Test CDLL Preview Generation

Tests the CDLL (Cards/Details/Lists/Landings) preview generation system.
"""

import sys
import asyncio
import json
from pathlib import Path

# Add the app directory to path
sys.path.append('/home/michelle/PROJECTS/ooux/orca')

from app.core.database import get_db
from app.services.cdll_preview_service import CDLLPreviewService
from app.models.project import Project
from app.models.object import Object
from app.models.attribute import Attribute, ObjectAttribute
from app.models.cta import CTA, CRUDType
from app.models.prioritization import Prioritization, PriorityPhase, ItemType


def test_cdll_preview_generation():
    """Test CDLL preview generation functionality."""
    
    print("🔍 Testing CDLL Preview Generation...")
    
    # Get database session
    db = next(get_db())
    
    try:
        # Find a project to test with
        project = db.query(Project).first()
        if not project:
            print("❌ No projects found. Create a project first.")
            return False
        
        print(f"📁 Testing with project: {project.title}")
        
        # Find objects in the project
        objects = db.query(Object).filter(Object.project_id == project.id).limit(3).all()
        if not objects:
            print("❌ No objects found in project. Create some objects first.")
            return False
        
        print(f"🎯 Found {len(objects)} objects to test")
        
        # Initialize CDLL service
        cdll_service = CDLLPreviewService(db)
        
        # Test individual object preview generation
        test_obj = objects[0]
        print(f"\n🔬 Testing object: {test_obj.name}")
        
        try:
            # Generate previews for single object
            previews = cdll_service.generate_object_previews(str(project.id), str(test_obj.id))
            
            print("✅ Object preview generation successful!")
            print(f"   - Priority: {previews['priority_phase']}")
            print(f"   - Completion Score: {previews['completion_score']['percentage']}% (Grade {previews['completion_score']['grade']})")
            print(f"   - Warnings: {len(previews['warnings'])}")
            
            # Test each preview type
            for preview_type in ['card', 'detail', 'list', 'landing']:
                preview = previews[preview_type]
                print(f"   - {preview_type.title()}: {len(preview['html'])} chars HTML")
            
        except Exception as e:
            print(f"❌ Object preview generation failed: {e}")
            return False
        
        # Test project-wide preview generation
        print(f"\n🏗️ Testing project-wide preview generation...")
        
        try:
            # Generate previews for all objects
            project_previews = cdll_service.generate_project_previews(str(project.id))
            
            print(f"✅ Project preview generation successful!")
            print(f"   - Total objects processed: {len(project_previews)}")
            
            # Count successful vs error previews
            successful = sum(1 for p in project_previews if "error" not in p)
            errors = len(project_previews) - successful
            
            print(f"   - Successful: {successful}")
            print(f"   - Errors: {errors}")
            
            # Show completion score distribution
            scores = [p["completion_score"]["percentage"] for p in project_previews if "completion_score" in p]
            if scores:
                avg_score = sum(scores) / len(scores)
                print(f"   - Average completion: {avg_score:.1f}%")
        
        except Exception as e:
            print(f"❌ Project preview generation failed: {e}")
            return False
        
        # Test HTML export
        print(f"\n📄 Testing HTML export...")
        
        try:
            # Export a subset of previews
            export_data = project_previews[:2]  # Just export first 2 objects
            html_export = cdll_service.export_previews_html(str(project.id), export_data)
            
            print(f"✅ HTML export successful!")
            print(f"   - Generated HTML: {len(html_export)} characters")
            print(f"   - Contains CSS styles: {'<style>' in html_export}")
            print(f"   - Contains previews: {'object-preview' in html_export}")
            
            # Save export to file for inspection
            export_file = Path("/tmp/cdll-test-export.html")
            with open(export_file, "w") as f:
                f.write(html_export)
            print(f"   - Saved test export to: {export_file}")
        
        except Exception as e:
            print(f"❌ HTML export failed: {e}")
            return False
        
        # Test prioritized filtering
        print(f"\n🎯 Testing priority filtering...")
        
        try:
            # Test filtering by NOW priority
            now_previews = cdll_service.generate_project_previews(str(project.id), PriorityPhase.NOW)
            
            print(f"✅ Priority filtering successful!")
            print(f"   - NOW priority objects: {len(now_previews)}")
            
            # Test other priority phases
            for phase in [PriorityPhase.NEXT, PriorityPhase.LATER]:
                phase_previews = cdll_service.generate_project_previews(str(project.id), phase)
                print(f"   - {phase.value} priority objects: {len(phase_previews)}")
        
        except Exception as e:
            print(f"❌ Priority filtering failed: {e}")
            return False
        
        print(f"\n🎉 All CDLL preview tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Test setup failed: {e}")
        return False
    
    finally:
        db.close()


def analyze_cdll_readiness():
    """Analyze how ready the current data is for CDLL generation."""
    
    print("\n📊 Analyzing CDLL Generation Readiness...")
    
    db = next(get_db())
    
    try:
        # Get all projects
        projects = db.query(Project).all()
        
        for project in projects:
            print(f"\n📁 Project: {project.title}")
            
            # Get objects with their related data
            objects = db.query(Object).filter(Object.project_id == project.id).all()
            print(f"   Total objects: {len(objects)}")
            
            if not objects:
                continue
            
            # Analyze data completeness
            objects_with_definition = sum(
                1 for obj in objects
                if getattr(obj, "definition", None) is not None and isinstance(obj.definition, str) and len(obj.definition.strip()) >= 10
            )
            
            # Check attributes
            total_attributes = 0
            core_attributes = 0
            
            for obj in objects:
                obj_attrs = db.query(ObjectAttribute).join(Attribute).filter(
                    ObjectAttribute.object_id == obj.id
                ).all()
                total_attributes += len(obj_attrs)
                
                core_attrs = db.query(ObjectAttribute).join(Attribute).filter(
                    ObjectAttribute.object_id == obj.id,
                    Attribute.is_core == True
                ).all()
                core_attributes += len(core_attrs)
            
            # Check CTAs
            total_ctas = db.query(CTA).join(Object).filter(Object.project_id == project.id).count()
            primary_ctas = db.query(CTA).join(Object).filter(
                Object.project_id == project.id,
                CTA.is_primary == True
            ).count()
            
            # Check prioritization
            prioritized_objects = db.query(Prioritization).filter(
                Prioritization.project_id == project.id,
                Prioritization.item_type == ItemType.OBJECT
            ).count()
            
            print(f"   Objects with definitions: {objects_with_definition}/{len(objects)}")
            print(f"   Total attributes: {total_attributes}")
            print(f"   Core attributes: {core_attributes}")
            print(f"   Total CTAs: {total_ctas}")
            print(f"   Primary CTAs: {primary_ctas}")
            print(f"   Prioritized objects: {prioritized_objects}/{len(objects)}")
            
            # Calculate readiness score
            readiness_factors = [
                objects_with_definition / len(objects) if objects else 0,  # Definitions
                min(core_attributes / (len(objects) * 3), 1.0) if objects else 0,  # Core attrs (3 per object target)
                min(primary_ctas / len(objects), 1.0) if objects else 0,  # Primary CTAs
                prioritized_objects / len(objects) if objects else 0  # Prioritization
            ]
            
            readiness_score = sum(readiness_factors) / len(readiness_factors) * 100
            
            if readiness_score >= 80:
                readiness_level = "🟢 Excellent"
            elif readiness_score >= 60:
                readiness_level = "🟡 Good"
            elif readiness_score >= 40:
                readiness_level = "🟠 Fair"
            else:
                readiness_level = "🔴 Needs Work"
            
            print(f"   CDLL Readiness: {readiness_level} ({readiness_score:.1f}%)")
            
            # Provide recommendations
            if objects_with_definition < len(objects):
                print(f"   💡 Add definitions to {len(objects) - objects_with_definition} objects")
            
            if core_attributes < len(objects) * 2:
                print(f"   💡 Mark more attributes as 'core' (target: 3-5 per object)")
            
            if primary_ctas < len(objects):
                print(f"   💡 Mark primary CTAs for better UI generation")
            
            if prioritized_objects < len(objects):
                print(f"   💡 Prioritize objects using NOW/NEXT/LATER system")
    
    finally:
        db.close()


if __name__ == "__main__":
    print("🚀 CDLL Preview Generation Test Suite")
    print("=" * 50)
    
    # Test core functionality
    success = test_cdll_preview_generation()
    
    # Analyze readiness
    analyze_cdll_readiness()
    
    if success:
        print("\n✅ All tests completed successfully!")
        print("\n💡 Next steps:")
        print("   1. Review the generated HTML export in /tmp/cdll-test-export.html")
        print("   2. Test the API endpoints at /api/v1/cdll/")
        print("   3. Integrate CDLL previews into the dashboard")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed. Check the output above.")
        sys.exit(1)
