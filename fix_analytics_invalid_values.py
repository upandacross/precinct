#!/usr/bin/env python3
"""
Fix Invalid Values in Analytics Dashboard
=======================================

This script adds robust error handling to prevent invalid values
from appearing in the analytics dashboard charts.
"""

def fix_analytics_invalid_values():
    """Add error handling to prevent invalid chart values."""
    
    # Read the current dash_analytics.py file
    with open('dash_analytics.py', 'r') as f:
        content = f.read()
    
    # Add a data validation function at the top
    validation_function = '''
def validate_chart_data(data, chart_name="Chart"):
    """Validate chart data to prevent invalid values."""
    if not data:
        return None
    
    # Handle different data types
    if isinstance(data, dict):
        validated = {}
        for key, value in data.items():
            if isinstance(value, list):
                # Clean list data
                cleaned = []
                for item in value:
                    if item is None or str(item) in ['inf', '-inf', 'nan', 'null', 'undefined']:
                        cleaned.append(0)  # Replace invalid with 0
                    elif isinstance(item, (int, float)) and str(item) == 'nan':
                        cleaned.append(0)
                    else:
                        cleaned.append(item)
                validated[key] = cleaned
            elif value is None or str(value) in ['inf', '-inf', 'nan', 'null', 'undefined']:
                validated[key] = 0
            else:
                validated[key] = value
        return validated
    elif isinstance(data, list):
        # Clean list data
        return [0 if (item is None or str(item) in ['inf', '-inf', 'nan', 'null', 'undefined']) else item for item in data]
    
    return data

'''
    
    # Find where to insert the validation function (after imports)
    import_end = content.find('def get_analytics_data')
    if import_end != -1:
        new_content = content[:import_end] + validation_function + content[import_end:]
        
        # Add validation calls to chart update functions
        chart_functions = [
            'update_user_distribution_chart',
            'update_password_strength_chart', 
            'update_monthly_signups_chart',
            'update_login_activity_chart',
            'update_recent_activity_chart'
        ]
        
        for func_name in chart_functions:
            # Find the function and add validation
            func_start = new_content.find(f'def {func_name}(')
            if func_start != -1:
                # Find the data extraction part and add validation
                if 'password_strength' in func_name:
                    old_pattern = "data = stored_data['password_strength']"
                    new_pattern = "data = validate_chart_data(stored_data['password_strength'], 'Password Strength')"
                elif 'monthly_signups' in func_name:
                    old_pattern = "data = stored_data['monthly_signups']"
                    new_pattern = "data = validate_chart_data(stored_data['monthly_signups'], 'Monthly Signups')"
                elif 'user_distribution' in func_name:
                    old_pattern = "stats = stored_data['user_stats']"
                    new_pattern = "stats = validate_chart_data(stored_data['user_stats'], 'User Stats')"
                elif 'login_activity' in func_name:
                    old_pattern = "data = stored_data['login_activity']"
                    new_pattern = "data = validate_chart_data(stored_data['login_activity'], 'Login Activity')"
                elif 'recent_activity' in func_name:
                    old_pattern = "data = stored_data['recent_activity']"
                    new_pattern = "data = validate_chart_data(stored_data['recent_activity'], 'Recent Activity')"
                else:
                    continue
                
                new_content = new_content.replace(old_pattern, new_pattern)
        
        # Write the fixed content
        with open('dash_analytics_fixed.py', 'w') as f:
            f.write(new_content)
        
        print("✅ Created dash_analytics_fixed.py with invalid value protection")
        print("📝 Added validation for:")
        for func in chart_functions:
            print(f"   - {func}")
    else:
        print("❌ Could not find insertion point in dash_analytics.py")

if __name__ == "__main__":
    fix_analytics_invalid_values()