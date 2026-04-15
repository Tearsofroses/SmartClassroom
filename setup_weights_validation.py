#!/usr/bin/env python3
"""
Quick setup script for YOLO weights validation tests.
Prepares environment, extracts frames, and runs tests.

Usage:
    python setup_weights_validation.py --all
    python setup_weights_validation.py --phase phase1  # Extract frames only
    python setup_weights_validation.py --check         # Environment check only
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path

def run_command(cmd, description):
    """Run command and report results."""
    print(f"\n{'='*70}")
    print(f"▶ {description}")
    print(f"{'='*70}")
    print(f"$ {cmd}")
    print()
    
    result = os.system(cmd)
    if result == 0:
        print(f"✓ {description} - OK")
        return True
    else:
        print(f"✗ {description} - FAILED (exit code: {result})")
        return False

def check_environment():
    """Check if environment is ready for tests."""
    print("\n" + "="*70)
    print("Environment Check")
    print("="*70)
    
    checks = {
        "Python version": lambda: subprocess.run(["python", "--version"], capture_output=True, text=True).returncode == 0,
        "pip available": lambda: subprocess.run(["pip", "--version"], capture_output=True, text=True).returncode == 0,
        "Backend code exists": lambda: Path("backend/app/services/yolo_inference.py").exists(),
        "Test script exists": lambda: Path("backend/tests/test_weights_validation.py").exists(),
        "Dataset available": lambda: Path("YOLO/SCB-Dataset").exists(),
    }
    
    all_passed = True
    for check_name, check_func in checks.items():
        try:
            passed = check_func()
            status = "✓" if passed else "✗"
            print(f"{status} {check_name}")
            if not passed:
                all_passed = False
        except Exception as e:
            print(f"✗ {check_name}: {e}")
            all_passed = False
    
    return all_passed

def install_dependencies():
    """Install required Python packages."""
    print("\n" + "="*70)
    print("Installing Dependencies")
    print("="*70)
    
    cmd = "pip install pytest pillow opencv-python requests numpy ultralytics==8.0.231"
    return run_command(cmd, "Install Python packages")

def extract_frames():
    """Run Phase 1: Frame extraction."""
    cmd = "python backend/tests/test_weights_validation.py --phase phase1 --verbose"
    return run_command(cmd, "Phase 1: Extract Frames from SCB-Dataset")

def run_service_tests():
    """Run Phase 2: Service-level tests."""
    cmd = "python backend/tests/test_weights_validation.py --phase phase2 --verbose"
    return run_command(cmd, "Phase 2: Service-Level Unit Tests")

def run_all_tests():
    """Run full test suite."""
    cmd = "python backend/tests/test_weights_validation.py --phase all --verbose"
    return run_command(cmd, "YOLO Weights Validation - Full Suite")

def main():
    parser = argparse.ArgumentParser(description="Setup and run YOLO weights validation tests")
    parser.add_argument("--all", action="store_true", help="Run full test suite")
    parser.add_argument("--check", action="store_true", help="Check environment only")
    parser.add_argument("--install", action="store_true", help="Install dependencies only")
    parser.add_argument("--extract", action="store_true", help="Extract frames only (Phase 1)")
    parser.add_argument("--service", action="store_true", help="Run service tests only (Phase 2)")
    parser.add_argument("--phase", type=str, help="Run specific phase (phase1-5)")
    
    args = parser.parse_args()
    
    # Change to project root
    os.chdir(Path(__file__).parent)
    
    print("""
    ╔═══════════════════════════════════════════════════════════════════╗
    ║  YOLO Weights Validation Test Suite - Setup & Runner              ║
    ╚═══════════════════════════════════════════════════════════════════╝
    """)
    
    # Environment check (always run first)
    if not check_environment():
        print("\n⚠ Environment check failed. Some components may be missing.")
        print("  Try: python setup_weights_validation.py --install")
    
    # Determine what to run
    if args.check:
        print("\n✓ Environment check complete")
        return 0
    
    if args.install:
        return 0 if install_dependencies() else 1
    
    if args.extract:
        return 0 if extract_frames() else 1
    
    if args.service:
        return 0 if run_service_tests() else 1
    
    if args.phase:
        cmd = f"python backend/tests/test_weights_validation.py --phase {args.phase} --verbose"
        return 0 if run_command(cmd, f"Running {args.phase}") else 1
    
    if args.all:
        # Full pipeline: install → extract → service tests → all tests
        if not install_dependencies():
            print("\n✗ Failed to install dependencies")
            return 1
        
        if not extract_frames():
            print("\n✗ Failed to extract frames")
            return 1
        
        if not run_all_tests():
            print("\n✗ Test suite failed")
            return 1
        
        print("\n" + "="*70)
        print("✓ ALL TESTS PASSED")
        print("="*70)
        print("\nNext steps:")
        print("  1. Review report: backend/tests/WEIGHTS_VALIDATION_REPORT.md")
        print("  2. If PASS: Proceed to Phase 1 Reproduction (detector training)")
        print("  3. If FAIL: Check DEBUG section in report")
        return 0
    
    # Default: show help
    parser.print_help()
    print("\nExamples:")
    print("  python setup_weights_validation.py --all              # Full setup & test")
    print("  python setup_weights_validation.py --check            # Environment check")
    print("  python setup_weights_validation.py --install          # Install dependencies")
    print("  python setup_weights_validation.py --extract          # Extract frames (Phase 1)")
    print("  python setup_weights_validation.py --service          # Service tests (Phase 2)")
    print("  python setup_weights_validation.py --phase phase3     # Run Phase 3")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
