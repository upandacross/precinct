#!/usr/bin/env python3
"""
Test HSTS implementation and security headers.
"""
import requests
import sys

def test_security_headers():
    """Test security headers on the application."""
    url = "http://localhost:8080/login"
    
    try:
        response = requests.get(url, timeout=5)
        headers = response.headers
        
        print("🔒 Security Headers Analysis")
        print("=" * 50)
        
        # Required security headers
        security_checks = {
            'Strict-Transport-Security': {
                'present': 'Strict-Transport-Security' in headers,
                'value': headers.get('Strict-Transport-Security', 'Not set'),
                'recommended': 'max-age=31536000; includeSubDomains',
                'description': 'Forces HTTPS connections'
            },
            'X-Frame-Options': {
                'present': 'X-Frame-Options' in headers,
                'value': headers.get('X-Frame-Options', 'Not set'),
                'recommended': 'DENY or SAMEORIGIN',
                'description': 'Prevents clickjacking attacks'
            },
            'X-Content-Type-Options': {
                'present': 'X-Content-Type-Options' in headers,
                'value': headers.get('X-Content-Type-Options', 'Not set'),
                'recommended': 'nosniff',
                'description': 'Prevents MIME type confusion attacks'
            },
            'Content-Security-Policy': {
                'present': 'Content-Security-Policy' in headers,
                'value': headers.get('Content-Security-Policy', 'Not set')[:100] + '...',
                'recommended': 'Restrictive policy',
                'description': 'Prevents XSS and injection attacks'
            },
            'Referrer-Policy': {
                'present': 'Referrer-Policy' in headers,
                'value': headers.get('Referrer-Policy', 'Not set'),
                'recommended': 'strict-origin-when-cross-origin',
                'description': 'Controls referrer information'
            },
            'Permissions-Policy': {
                'present': 'Permissions-Policy' in headers,
                'value': headers.get('Permissions-Policy', 'Not set'),
                'recommended': 'Restrictive policy for sensitive features',
                'description': 'Controls browser feature permissions'
            }
        }
        
        all_good = True
        for header_name, check in security_checks.items():
            status = "✅" if check['present'] else "❌"
            print(f"{status} {header_name}")
            print(f"   Current: {check['value']}")
            print(f"   Purpose: {check['description']}")
            if not check['present']:
                all_good = False
            print()
        
        # HSTS specific analysis
        print("🔒 HSTS Implementation Analysis")
        print("=" * 50)
        
        if 'Strict-Transport-Security' in headers:
            hsts_value = headers['Strict-Transport-Security']
            print(f"✅ HSTS Header Present: {hsts_value}")
            
            # Check HSTS components
            hsts_checks = {
                'max-age': 'max-age=' in hsts_value,
                'includeSubDomains': 'includeSubDomains' in hsts_value,
                'preload': 'preload' in hsts_value
            }
            
            for check, present in hsts_checks.items():
                status = "✅" if present else "⚠️ "
                print(f"   {status} {check}: {'Present' if present else 'Missing (optional for preload)'}")
            
            # Extract max-age value
            if 'max-age=' in hsts_value:
                try:
                    max_age = hsts_value.split('max-age=')[1].split(';')[0].strip()
                    max_age_seconds = int(max_age)
                    max_age_days = max_age_seconds / (24 * 60 * 60)
                    print(f"   📅 Max-age: {max_age_seconds} seconds ({max_age_days:.1f} days)")
                    
                    if max_age_seconds >= 31536000:  # 1 year
                        print("   ✅ Max-age is sufficient (≥1 year)")
                    else:
                        print("   ⚠️  Max-age should be at least 1 year (31536000 seconds)")
                except ValueError:
                    print("   ❌ Invalid max-age value")
        else:
            print("❌ HSTS Header Missing!")
            print("   HSTS should be implemented for production HTTPS deployments")
            all_good = False
        
        print("\n🎯 HSTS Implementation Status")
        print("=" * 50)
        
        if all_good:
            print("✅ HSTS and security headers are properly implemented!")
            print("✅ Application is ready for HTTPS deployment")
            print("\n📋 Next Steps for HTTPS:")
            print("   1. Deploy with HTTPS/TLS certificate")
            print("   2. Test HSTS behavior in browser")
            print("   3. Consider HSTS preloading for maximum security")
        else:
            print("⚠️  Some security headers need attention")
        
        print(f"\n📊 Total Headers Checked: {len(security_checks)}")
        print(f"✅ Headers Present: {sum(1 for c in security_checks.values() if c['present'])}")
        print(f"❌ Headers Missing: {sum(1 for c in security_checks.values() if not c['present'])}")
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Error connecting to server: {e}")
        print("Make sure the server is running on http://localhost:8080")
        return False
    
    return True

if __name__ == "__main__":
    success = test_security_headers()
    sys.exit(0 if success else 1)
