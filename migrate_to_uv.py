#!/usr/bin/env python3
"""
Migration script to help transition from pip to uv for the Kambo Chatbot project.
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path


def check_uv_installed():
    """Check if uv is installed and available."""
    try:
        result = subprocess.run(['uv', '--version'], 
                              capture_output=True, text=True, check=True)
        print(f"✅ uv is installed: {result.stdout.strip()}")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ uv is not installed or not in PATH")
        return False


def check_python_version():
    """Check if Python version meets requirements."""
    version = sys.version_info
    if version.major == 3 and version.minor >= 11:
        print(f"✅ Python version {version.major}.{version.minor}.{version.micro} meets requirements")
        return True
    else:
        print(f"❌ Python version {version.major}.{version.minor}.{version.micro} is too old. Need 3.11+")
        return False


def check_pyproject_toml():
    """Check if pyproject.toml exists."""
    if Path('pyproject.toml').exists():
        print("✅ pyproject.toml found")
        return True
    else:
        print("❌ pyproject.toml not found")
        return False


def check_requirements_txt():
    """Check if requirements.txt exists."""
    if Path('requirements.txt').exists():
        print("✅ requirements.txt found (will be replaced by pyproject.toml)")
        return True
    else:
        print("⚠️  requirements.txt not found")
        return False


def check_venv():
    """Check if virtual environment exists."""
    venv_paths = ['.venv', 'venv', 'env']
    for venv_path in venv_paths:
        if Path(venv_path).exists():
            print(f"⚠️  Found existing virtual environment: {venv_path}")
            return venv_path
    print("✅ No existing virtual environment found")
    return None


def install_uv():
    """Provide instructions to install uv."""
    print("\n📦 To install uv:")
    if sys.platform == "win32":
        print("   powershell -c \"irm https://astral.sh/uv/install.ps1 | iex\"")
    else:
        print("   curl -LsSf https://astral.sh/uv/install.sh | sh")
    print("   Then restart your terminal and run this script again.")


def migrate_instructions():
    """Provide migration instructions."""
    print("\n🔄 Migration Instructions:")
    print("1. Install uv (see above if not installed)")
    print("2. Remove old virtual environment (if any):")
    print("   rm -rf .venv venv env")
    print("3. Install dependencies with uv:")
    print("   uv sync")
    print("4. Run the application:")
    print("   uv run python main.py")
    print("\n📚 For more information, see the updated README.md")


def backup_requirements():
    """Backup requirements.txt if it exists."""
    if Path('requirements.txt').exists():
        backup_path = Path('requirements.txt.backup')
        shutil.copy2('requirements.txt', backup_path)
        print(f"📋 Backed up requirements.txt to {backup_path}")


def main():
    """Main migration check function."""
    print("🚀 Kambo Chatbot - Migration to uv")
    print("=" * 50)
    
    # Check prerequisites
    print("\n🔍 Checking prerequisites:")
    uv_ok = check_uv_installed()
    python_ok = check_python_version()
    
    print("\n📁 Checking project files:")
    pyproject_ok = check_pyproject_toml()
    requirements_exists = check_requirements_txt()
    venv_path = check_venv()
    
    # Provide guidance
    if not uv_ok:
        install_uv()
        return
    
    if not python_ok:
        print("\n❌ Please upgrade Python to version 3.11 or higher")
        return
    
    if not pyproject_ok:
        print("\n❌ pyproject.toml not found. Please ensure it was created properly.")
        return
    
    # Backup requirements.txt
    if requirements_exists:
        backup_requirements()
    
    # Provide migration instructions
    migrate_instructions()
    
    # Optional: Clean up old venv
    if venv_path:
        print(f"\n🧹 To clean up old virtual environment:")
        print(f"   rm -rf {venv_path}")
    
    print("\n✅ Migration check complete!")


if __name__ == "__main__":
    main() 