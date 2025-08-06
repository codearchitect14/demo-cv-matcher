#!/usr/bin/env python3
"""
Script to fix router prefixes by removing them since they're added in main.py
"""

import os
import re

# Files to fix
files_to_fix = [
    "api/routers/analytics.py",
    "api/routers/candidates.py", 
    "api/routers/applications.py",
    "api/routers/gdpr.py",
    "api/routers/interactions.py",
    "api/routers/recommendations.py",
    "api/routers/jobs.py",
    "api/routers/recruiter.py",
    "api/routers/system.py",
    "api/routers/search.py"
]

def fix_router_prefix(file_path):
    """Remove prefix from router definition"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Replace APIRouter(prefix="/something", tags=["Something"]) with APIRouter(tags=["Something"])
        pattern = r'APIRouter\(prefix="[^"]+",\s*tags=\[([^\]]+)\]\)'
        replacement = r'APIRouter(tags=[\1])'
        
        new_content = re.sub(pattern, replacement, content)
        
        if new_content != content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print(f"✅ Fixed {file_path}")
            return True
        else:
            print(f"⚠️  No changes needed for {file_path}")
            return False
            
    except Exception as e:
        print(f"❌ Error fixing {file_path}: {e}")
        return False

def main():
    print("🔧 Fixing router prefixes...")
    
    fixed_count = 0
    for file_path in files_to_fix:
        if os.path.exists(file_path):
            if fix_router_prefix(file_path):
                fixed_count += 1
        else:
            print(f"⚠️  File not found: {file_path}")
    
    print(f"\n🎯 Fixed {fixed_count} router files")
    print("✅ All router prefixes have been removed!")

if __name__ == "__main__":
    main() 