#!/usr/bin/env python3
"""Find and report User() instantiations missing phone and role fields."""

import os
import re
import sys

def find_user_instantiations():
    """Find all User() instantiations in test files."""
    test_dir = 'test'
    user_pattern = re.compile(r'User\s*\(\s*$', re.MULTILINE)
    
    issues = []
    
    for filename in os.listdir(test_dir):
        if filename.endswith('.py'):
            filepath = os.path.join(test_dir, filename)
            
            with open(filepath, 'r') as f:
                content = f.read()
                lines = content.split('\n')
                
                # Find User() instantiations
                for i, line in enumerate(lines):
                    if user_pattern.search(line):
                        # Look at the next several lines to see the parameters
                        param_lines = []
                        for j in range(i, min(i + 20, len(lines))):
                            param_lines.append(lines[j])
                            if ')' in lines[j] and not lines[j].strip().endswith(','):
                                break
                        
                        param_text = '\n'.join(param_lines)
                        
                        # Check if phone and role are present
                        has_phone = 'phone=' in param_text
                        has_role = 'role=' in param_text
                        
                        if not has_phone or not has_role:
                            issues.append({
                                'file': filepath,
                                'line': i + 1,
                                'missing_phone': not has_phone,
                                'missing_role': not has_role,
                                'text': param_text
                            })
    
    return issues

def main():
    """Main function."""
    print("Finding User() instantiations missing phone/role fields...")
    
    issues = find_user_instantiations()
    
    if not issues:
        print("✓ No issues found! All User() instantiations have phone and role fields.")
        return
    
    print(f"\nFound {len(issues)} User() instantiations with missing fields:\n")
    
    for issue in issues:
        print(f"File: {issue['file']}")
        print(f"Line: {issue['line']}")
        missing = []
        if issue['missing_phone']:
            missing.append('phone')
        if issue['missing_role']:
            missing.append('role')
        print(f"Missing: {', '.join(missing)}")
        print("Code:")
        for line in issue['text'].split('\n')[:10]:  # Show first 10 lines
            print(f"  {line}")
        print("-" * 50)

if __name__ == '__main__':
    main()