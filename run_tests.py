#!/usr/bin/env python3
"""
Simple test runner for all modifications
"""

import subprocess
import sys
import os

def run_test_suite():
    """Run the comprehensive test suite"""
    print("🧪 Running comprehensive test suite for all modifications...")
    print("=" * 60)
    
    try:
        # Run the test suite
        result = subprocess.run([
            sys.executable, "test_all_modifications.py"
        ], capture_output=True, text=True)
        
        # Print output
        print(result.stdout)
        if result.stderr:
            print("Errors:")
            print(result.stderr)
        
        # Return exit code
        return result.returncode == 0
        
    except Exception as e:
        print(f"❌ Error running tests: {e}")
        return False

def run_quick_checks():
    """Run quick checks to verify basic functionality"""
    print("\n🔍 Running quick checks...")
    
    checks = [
        ("Import models", "from models.candidate import Candidate"),
        ("Import exceptions", "from core.exceptions import ValidationException"),
        ("Import skill matcher", "from services.skill_matcher import AdvancedSkillMatcher"),
        ("Import cache service", "from services.cache_service import RedisCacheService"),
        ("Import database config", "from config.database import DatabaseMonitor"),
    ]
    
    all_passed = True
    
    for check_name, import_statement in checks:
        try:
            exec(import_statement)
            print(f"✅ {check_name}")
        except Exception as e:
            print(f"❌ {check_name}: {e}")
            all_passed = False
    
    return all_passed

def main():
    """Main test runner"""
    print("🚀 CV-Matcher Modification Test Suite")
    print("=" * 60)
    
    # Run quick checks first
    quick_passed = run_quick_checks()
    
    if not quick_passed:
        print("\n❌ Quick checks failed. Please fix import issues before running full tests.")
        return False
    
    # Run comprehensive test suite
    print("\n" + "=" * 60)
    test_passed = run_test_suite()
    
    if test_passed:
        print("\n🎉 All tests passed! All modifications are working correctly.")
        print("\n✅ Summary of fixes verified:")
        print("   • Code quality improvements (dead code removal, error handling, type hints)")
        print("   • AI/ML logic fixes (configurable thresholds, enhanced validation, model versioning)")
        print("   • Database performance fixes (connection monitoring, query optimization)")
        print("   • Caching improvements (adaptive compression, intelligent invalidation, memory leak prevention)")
        print("   • Performance optimizations (async CPU operations, chunked processing)")
        print("   • Backward compatibility maintained")
    else:
        print("\n💥 Some tests failed. Please review the errors above.")
        print("\n🔧 Common troubleshooting steps:")
        print("   1. Ensure all dependencies are installed")
        print("   2. Check that all modified files are in the correct locations")
        print("   3. Verify environment variables are set correctly")
        print("   4. Check for any import path issues")
    
    return test_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 