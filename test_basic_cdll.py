#!/usr/bin/env python3
"""
Test Basic CDLL Preview Generation

Tests the CDLL generation without prioritization dependencies.
"""

import sys
sys.path.append('/home/michelle/PROJECTS/ooux/orca')

from app.core.database import get_db
from app.models.project import Project
from app.models.object import Object
from app.models.attribute import Attribute, ObjectAttribute
from app.models.cta import CTA


def test_basic_cdll():
    """Test basic CDLL generation without prioritization."""
    
    print("🔍 Testing Basic CDLL Generation...")
    
    db = next(get_db())
    
    try:
        # Get project and object
        project = db.query(Project).first()
        if not project:
            print("❌ No project found")
            return
        
        obj = db.query(Object).filter(Object.project_id == project.id).first()
        if not obj:
            print("❌ No object found")
            return
        
        print(f"📁 Project: {project.title}")
        print(f"🎯 Object: {obj.name}")
        
        # Get object attributes
        obj_attrs = db.query(ObjectAttribute, Attribute).join(Attribute).filter(
            ObjectAttribute.object_id == obj.id
        ).all()
        
        print(f"   Attributes: {len(obj_attrs)}")
        for obj_attr, attr in obj_attrs:
            print(f"     - {attr.name}: {obj_attr.value} (core: {attr.is_core})")
        
        # Get object CTAs
        ctas = db.query(CTA).filter(CTA.object_id == obj.id).all()
        
        print(f"   CTAs: {len(ctas)}")
        for cta in ctas:
            print(f"     - {cta.description} ({cta.crud_type.value}, primary: {cta.is_primary})")
        
        # Generate simple HTML previews
        print("\n🎨 Generating Previews...")
        
        # Card preview
        core_attrs = [(obj_attr, attr) for obj_attr, attr in obj_attrs if attr.is_core][:3]
        card_html = f"""
        <div class="card">
            <h3>{obj.name}</h3>
            <p>{obj.definition[:100] + '...' if obj.definition and len(obj.definition) > 100 else obj.definition or 'No description'}</p>
            <div class="attributes">
                {''.join([f'<div><strong>{attr.name}:</strong> {obj_attr.value or "—"}</div>' for obj_attr, attr in core_attrs])}
            </div>
        </div>
        """
        
        # Detail preview
        detail_html = f"""
        <div class="detail">
            <h2>{obj.name}</h2>
            <p>{obj.definition or 'No description provided'}</p>
            <h3>Attributes</h3>
            <div class="attributes">
                {''.join([f'<div><strong>{attr.name}</strong> ({attr.data_type.value}): {obj_attr.value or "—"}</div>' for obj_attr, attr in obj_attrs])}
            </div>
            <h3>Available Actions</h3>
            <div class="actions">
                {''.join([f'<button class="{"primary" if cta.is_primary else ""}">{cta.description}</button>' for cta in ctas])}
            </div>
        </div>
        """
        
        # List preview
        list_html = f"""
        <table class="list">
            <tr>
                <td><strong>{obj.name}</strong></td>
                {''.join([f'<td>{obj_attr.value or "—"}</td>' for obj_attr, attr in core_attrs])}
            </tr>
        </table>
        """
        
        # Landing preview
        landing_html = f"""
        <div class="landing">
            <header>
                <h1>{obj.name}</h1>
                <p>{obj.definition or 'No description provided'}</p>
            </header>
            <section>
                <h3>Key Information</h3>
                <div class="summary">
                    {''.join([f'<div><strong>{attr.name}:</strong> {obj_attr.value or "—"}</div>' for obj_attr, attr in core_attrs])}
                </div>
            </section>
            <section>
                <h3>Actions</h3>
                <div class="actions">
                    {''.join([f'<button class="action-btn {"primary" if cta.is_primary else ""}">{cta.description}</button>' for cta in ctas])}
                </div>
            </section>
        </div>
        """
        
        print("✅ Card preview generated")
        print("✅ Detail preview generated")
        print("✅ List preview generated")
        print("✅ Landing preview generated")
        
        # Generate warnings
        warnings = []
        if not obj.definition or len(obj.definition.strip()) < 10:
            warnings.append("Object definition is missing or too short")
        
        if len([attr for obj_attr, attr in obj_attrs if attr.is_core]) < 2:
            warnings.append("Insufficient core attributes (need 3-5 for good UI generation)")
        
        if len([cta for cta in ctas if cta.is_primary]) == 0:
            warnings.append("No primary CTAs defined")
        
        if len(ctas) == 0:
            warnings.append("No CTAs defined")
        
        print(f"\n⚠️  Warnings: {len(warnings)}")
        for warning in warnings:
            print(f"   - {warning}")
        
        # Calculate completion score
        score = 0
        max_score = 100
        
        # Definition (20 points)
        if obj.definition and len(obj.definition.strip()) >= 20:
            score += 20
        elif obj.definition and len(obj.definition.strip()) >= 10:
            score += 10
        
        # Core attributes (30 points)
        core_count = len([attr for obj_attr, attr in obj_attrs if attr.is_core])
        if core_count >= 4:
            score += 30
        elif core_count >= 2:
            score += 20
        elif core_count >= 1:
            score += 10
        
        # Primary CTAs (25 points)
        primary_count = len([cta for cta in ctas if cta.is_primary])
        if primary_count >= 3:
            score += 25
        elif primary_count >= 2:
            score += 20
        elif primary_count >= 1:
            score += 15
        
        # CRUD coverage (25 points)
        crud_types = set(cta.crud_type.value for cta in ctas)
        crud_score = len(crud_types) * 6
        if crud_types:
            crud_score += 1
        score += min(crud_score, 25)
        
        percentage = round((score / max_score) * 100)
        
        if percentage >= 90:
            grade = "A"
        elif percentage >= 80:
            grade = "B"
        elif percentage >= 70:
            grade = "C"
        elif percentage >= 60:
            grade = "D"
        else:
            grade = "F"
        
        print(f"\n📊 Completion Score: {percentage}% (Grade {grade})")
        
        # Save previews to file
        full_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>CDLL Preview - {obj.name}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .preview {{ margin: 20px 0; padding: 20px; border: 1px solid #ddd; border-radius: 8px; }}
                .card {{ max-width: 300px; }}
                .detail {{ max-width: 600px; }}
                .list table {{ width: 100%; border-collapse: collapse; }}
                .list td {{ padding: 8px; border: 1px solid #ddd; }}
                .landing {{ max-width: 800px; }}
                .primary {{ background: #007bff; color: white; }}
                button {{ margin: 5px; padding: 8px 16px; border: 1px solid #ddd; background: #f8f9fa; cursor: pointer; }}
                h1, h2, h3 {{ color: #333; }}
            </style>
        </head>
        <body>
            <h1>CDLL Previews for {obj.name}</h1>
            <p><strong>Completion:</strong> {percentage}% (Grade {grade})</p>
            
            <div class="preview">
                <h2>📱 Card View</h2>
                {card_html}
            </div>
            
            <div class="preview">
                <h2>📄 Detail View</h2>
                {detail_html}
            </div>
            
            <div class="preview">
                <h2>📋 List View</h2>
                {list_html}
            </div>
            
            <div class="preview">
                <h2>🏠 Landing View</h2>
                {landing_html}
            </div>
        </body>
        </html>
        """
        
        with open("/tmp/basic-cdll-preview.html", "w") as f:
            f.write(full_html)
        
        print(f"\n💾 Preview saved to: /tmp/basic-cdll-preview.html")
        print(f"🌐 Open in browser to view generated previews")
        
        return True
        
    except Exception as e:
        import traceback
        print(f"❌ Error: {e}")
        traceback.print_exc()
        return False
    
    finally:
        db.close()


if __name__ == "__main__":
    print("🚀 Basic CDLL Preview Test")
    print("=" * 40)
    
    success = test_basic_cdll()
    
    if success:
        print("\n✅ Basic CDLL generation test passed!")
        print("\n💡 Next steps:")
        print("   1. Add more attributes and CTAs to the test object")
        print("   2. Test with multiple objects")
        print("   3. Test the full CDLL service with prioritization")
    else:
        print("\n❌ Basic CDLL generation test failed!")
        sys.exit(1)
