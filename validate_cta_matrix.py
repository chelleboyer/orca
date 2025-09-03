#!/usr/bin/env python3
"""
OOUX ORCA CTA Matrix - Comprehensive Validation Report
Epic 4.2 Implementation Assessment
Generated: September 2, 2025
"""

import subprocess
import time
import requests
import json
from datetime import datetime

def run_validation():
    """Run comprehensive CTA Matrix validation"""
    
    print("🎯 OOUX ORCA CTA Matrix - Comprehensive Validation Report")
    print("=" * 60)
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("Epic 4.2: CTA Matrix Core Functionality")
    print()
    
    # Start server
    print("🚀 Starting validation server...")
    server = subprocess.Popen([
        'python', '-m', 'uvicorn', 'app.main:app', 
        '--host', '0.0.0.0', '--port', '8000'
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    time.sleep(3)
    
    results = {
        'endpoints': {},
        'components': {},
        'functionality': {},
        'overall_score': 0
    }
    
    try:
        base_url = 'http://localhost:8000'
        
        # Test Core Endpoints
        print("1. ENDPOINT VALIDATION")
        print("-" * 30)
        
        core_endpoints = [
            ('/health', 'Application Health Check'),
            ('/docs', 'API Documentation'), 
            ('/api/v1/demo/cta-matrix', 'Demo CTA Matrix Page'),
            ('/api/v1/demo/cta-matrix-grid', 'HTMX Matrix Grid'),
            ('/api/v1/demo/cta-cell/role1/obj1', 'Modal Dialog - User/Account'),
            ('/api/v1/demo/cta-cell/role2/obj2', 'Modal Dialog - Admin/Project'),
            ('/api/v1/demo/cta-cell/role3/obj3', 'Modal Dialog - Manager/Report')
        ]
        
        endpoint_score = 0
        for endpoint, description in core_endpoints:
            try:
                response = requests.get(f'{base_url}{endpoint}', timeout=10)
                passed = response.status_code == 200
                status = '✅ PASS' if passed else f'❌ FAIL ({response.status_code})'
                print(f"   {status} {description}")
                results['endpoints'][endpoint] = {
                    'status_code': response.status_code,
                    'passed': passed,
                    'content_length': len(response.content)
                }
                if passed:
                    endpoint_score += 1
            except Exception as e:
                print(f"   ❌ FAIL {description} - Error: {e}")
                results['endpoints'][endpoint] = {
                    'status_code': 0,
                    'passed': False,
                    'error': str(e)
                }
        
        print(f"   Score: {endpoint_score}/{len(core_endpoints)} endpoints working")
        print()
        
        # Test Static Assets
        print("2. STATIC ASSET VALIDATION") 
        print("-" * 30)
        
        static_assets = [
            ('/static/css/matrix.css', 'Matrix CSS Styles'),
            ('/static/js/cta-matrix.js', 'Matrix JavaScript'),
            ('/static/css/dashboard.css', 'Dashboard CSS')
        ]
        
        asset_score = 0
        for asset, description in static_assets:
            try:
                response = requests.get(f'{base_url}{asset}', timeout=10)
                passed = response.status_code == 200 and len(response.content) > 100
                status = '✅ PASS' if passed else f'❌ FAIL'
                print(f"   {status} {description} ({len(response.content)} bytes)")
                results['components'][asset] = {
                    'size_bytes': len(response.content),
                    'passed': passed
                }
                if passed:
                    asset_score += 1
            except Exception as e:
                print(f"   ❌ FAIL {description} - Error: {e}")
        
        print(f"   Score: {asset_score}/{len(static_assets)} assets loading")
        print()
        
        # Test HTMX Functionality
        print("3. HTMX FUNCTIONALITY VALIDATION")
        print("-" * 30)
        
        # Test grid HTMX content
        grid_response = requests.get(f'{base_url}/api/v1/demo/cta-matrix-grid')
        htmx_features = [
            ('hx-get', 'HTMX GET requests'),
            ('matrix-table', 'Matrix table structure'),
            ('matrix-cell', 'Interactive matrix cells'),
            ('crud-indicator', 'CRUD type indicators'),
            ('role1', 'Demo role data'),
            ('obj1', 'Demo object data')
        ]
        
        htmx_score = 0
        for feature, description in htmx_features:
            present = feature in grid_response.text
            status = '✅ PASS' if present else '❌ FAIL'
            print(f"   {status} {description}")
            results['functionality'][feature] = present
            if present:
                htmx_score += 1
        
        print(f"   Score: {htmx_score}/{len(htmx_features)} HTMX features working")
        print()
        
        # Test Matrix Content
        print("4. MATRIX CONTENT VALIDATION")
        print("-" * 30)
        
        main_response = requests.get(f'{base_url}/api/v1/demo/cta-matrix')
        content_features = [
            ('Call-to-Action Matrix', 'Page title'),
            ('User', 'Demo user role'),
            ('Admin', 'Demo admin role'), 
            ('Manager', 'Demo manager role'),
            ('Account', 'Demo account object'),
            ('Project', 'Demo project object'),
            ('Report', 'Demo report object'),
            ('matrix-container', 'Matrix container'),
            ('matrix-grid', 'Matrix grid element')
        ]
        
        content_score = 0
        for feature, description in content_features:
            present = feature in main_response.text
            status = '✅ PASS' if present else '❌ FAIL'
            print(f"   {status} {description}")
            if present:
                content_score += 1
        
        print(f"   Score: {content_score}/{len(content_features)} content elements present")
        print()
        
        # Calculate Overall Score
        total_tests = len(core_endpoints) + len(static_assets) + len(htmx_features) + len(content_features)
        total_passed = endpoint_score + asset_score + htmx_score + content_score
        overall_percentage = (total_passed / total_tests) * 100
        
        results['overall_score'] = overall_percentage
        
        print("5. OVERALL ASSESSMENT")
        print("-" * 30)
        print(f"   Total Tests: {total_tests}")
        print(f"   Tests Passed: {total_passed}")
        print(f"   Success Rate: {overall_percentage:.1f}%")
        print()
        
        if overall_percentage >= 95:
            print("   🎉 EXCELLENT - Production ready!")
        elif overall_percentage >= 85:
            print("   ✅ GOOD - Minor issues to address")
        elif overall_percentage >= 70:
            print("   ⚠️  FAIR - Several issues need fixing")
        else:
            print("   ❌ NEEDS WORK - Major issues present")
        
        print()
        print("6. NEXT STEPS")
        print("-" * 30)
        if overall_percentage >= 95:
            print("   • CTA Matrix is ready for user testing")
            print("   • Consider Epic 4.3 or Epic 5.1 development")
            print("   • Document user feedback and iterate")
        else:
            print("   • Address failing tests above")
            print("   • Re-run validation after fixes")
            print("   • Focus on critical functionality first")
        
    except Exception as e:
        print(f"Validation error: {e}")
        
    finally:
        server.terminate()
        server.wait()
        print()
        print("✅ Validation complete!")
        return results

if __name__ == "__main__":
    run_validation()
