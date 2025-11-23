#!/usr/bin/env python3
"""
NET WORTH Tennis Ladder - Pre-Deployment Validation
Validates that everything is ready for deployment
"""

import os
import sys
import subprocess
import sqlite3

def check(description, condition, error_message=None, warning=False):
    """Check a condition and print result"""
    symbol = "✓" if condition else ("⚠️ " if warning else "✗")
    status = "PASS" if condition else ("WARN" if warning else "FAIL")
    color = "\033[92m" if condition else ("\033[93m" if warning else "\033[91m")
    reset = "\033[0m"

    print(f"  {symbol} {description}... {color}{status}{reset}")

    if not condition and error_message:
        print(f"      {error_message}")

    return condition


def run_command(command):
    """Run a shell command and return True if successful"""
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=5)
        return result.returncode == 0
    except:
        return False


def validate_environment():
    """Validate development environment"""
    print("\n" + "=" * 60)
    print("1. Development Environment")
    print("=" * 60)

    checks_passed = 0
    total_checks = 0

    # Python version
    total_checks += 1
    python_version = sys.version_info
    if check("Python 3.9+", python_version >= (3, 9)):
        checks_passed += 1
        print(f"      Version: {python_version.major}.{python_version.minor}.{python_version.micro}")
    else:
        print(f"      Found: {python_version.major}.{python_version.minor}.{python_version.micro}")
        print(f"      Required: 3.9+")

    # pip3
    total_checks += 1
    if check("pip3 installed", run_command("pip3 --version")):
        checks_passed += 1

    # git
    total_checks += 1
    if check("git installed", run_command("git --version")):
        checks_passed += 1

    return checks_passed, total_checks


def validate_dependencies():
    """Validate Python dependencies"""
    print("\n" + "=" * 60)
    print("2. Python Dependencies")
    print("=" * 60)

    checks_passed = 0
    total_checks = 0

    # Check requirements file exists
    total_checks += 1
    if check("requirements_backend.txt exists", os.path.exists("requirements_backend.txt")):
        checks_passed += 1

    # Check each dependency
    required_packages = ['flask', 'flask_cors', 'gunicorn', 'jinja2', 'psycopg2']

    for package in required_packages:
        total_checks += 1
        try:
            __import__(package)
            if check(f"{package} installed", True):
                checks_passed += 1
        except ImportError:
            check(f"{package} installed", False, f"Run: pip3 install -r requirements_backend.txt")

    return checks_passed, total_checks


def validate_files():
    """Validate required files exist"""
    print("\n" + "=" * 60)
    print("3. Required Files")
    print("=" * 60)

    checks_passed = 0
    total_checks = 0

    required_files = {
        'production_server.py': 'Main Flask application',
        'init_database.py': 'Database initialization',
        'requirements_backend.txt': 'Python dependencies',
        'Procfile': 'Railway deployment config',
        'railway.json': 'Railway settings',
        '.gitignore': 'Git exclusions',
        'README.md': 'Main documentation',
        'START_HERE.md': 'Deployment guide',
        'LOCAL_TESTING.md': 'Testing guide',
    }

    for file, description in required_files.items():
        total_checks += 1
        if check(f"{file}", os.path.exists(file)):
            checks_passed += 1
        else:
            print(f"      Missing: {description}")

    return checks_passed, total_checks


def validate_templates():
    """Validate template files"""
    print("\n" + "=" * 60)
    print("4. Template Files")
    print("=" * 60)

    checks_passed = 0
    total_checks = 0

    required_templates = [
        'templates/base.html',
        'templates/login.html',
        'templates/dashboard.html',
        'templates/report_score.html',
        'templates/history.html',
        'templates/admin_dashboard.html',
        'templates/admin_players.html',
        'templates/admin_add_player.html',
        'templates/admin_edit_player.html',
        'templates/admin_scores.html',
    ]

    for template in required_templates:
        total_checks += 1
        if check(template, os.path.exists(template)):
            checks_passed += 1

    return checks_passed, total_checks


def validate_database():
    """Validate database if it exists"""
    print("\n" + "=" * 60)
    print("5. Database (if initialized)")
    print("=" * 60)

    checks_passed = 0
    total_checks = 0

    db_path = 'networth_tennis.db'

    total_checks += 1
    if not os.path.exists(db_path):
        check("Database initialized", False, "Run: python3 init_database.py --force", warning=True)
        print("      Skipping database checks (database not found)")
        return 0, 1

    checks_passed += 1
    check("Database file exists", True)

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Check tables exist
        required_tables = ['players', 'match_reports', 'match_history', 'monthly_matches']

        for table in required_tables:
            total_checks += 1
            cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,))
            if check(f"Table '{table}' exists", cursor.fetchone() is not None):
                checks_passed += 1

        # Check for players
        total_checks += 1
        cursor.execute("SELECT COUNT(*) FROM players")
        player_count = cursor.fetchone()[0]
        if check(f"Players in database ({player_count} found)", player_count > 0, warning=True):
            checks_passed += 1
        else:
            print("      Run: python3 init_database.py --force")

        conn.close()

    except Exception as e:
        total_checks += 1
        check("Database accessible", False, str(e))

    return checks_passed, total_checks


def validate_code():
    """Validate Python code syntax"""
    print("\n" + "=" * 60)
    print("6. Code Validation")
    print("=" * 60)

    checks_passed = 0
    total_checks = 0

    python_files = [
        'production_server.py',
        'init_database.py',
        'import_players.py',
        'migrate_sqlite_to_postgresql.py',
        'validate.py'
    ]

    for file in python_files:
        total_checks += 1
        if os.path.exists(file):
            result = run_command(f"python3 -m py_compile {file}")
            if check(f"{file} syntax", result):
                checks_passed += 1
        else:
            check(f"{file} syntax", False, "File not found", warning=True)

    return checks_passed, total_checks


def validate_git():
    """Validate git repository status"""
    print("\n" + "=" * 60)
    print("7. Git Repository")
    print("=" * 60)

    checks_passed = 0
    total_checks = 0

    # Check if git repo
    total_checks += 1
    if check("Git repository initialized", os.path.exists(".git")):
        checks_passed += 1

    # Check for uncommitted changes
    total_checks += 1
    result = run_command("git diff-index --quiet HEAD --")
    if check("No uncommitted changes", result, "Commit changes before deployment", warning=True):
        checks_passed += 1

    # Check remote configured
    total_checks += 1
    result = run_command("git remote -v | grep origin")
    if check("Git remote configured", result):
        checks_passed += 1

    # Check .gitignore exists
    total_checks += 1
    if check(".gitignore exists", os.path.exists(".gitignore")):
        checks_passed += 1

    return checks_passed, total_checks


def validate_security():
    """Validate security configurations"""
    print("\n" + "=" * 60)
    print("8. Security Checks")
    print("=" * 60)

    checks_passed = 0
    total_checks = 0

    # Check .env not in repo
    total_checks += 1
    if check(".env not in repository", not os.path.exists(".env") or run_command("git ls-files .env | wc -l | grep -q '^0$'")):
        checks_passed += 1
    else:
        print("      WARNING: .env should not be committed to git")

    # Check database not in repo
    total_checks += 1
    if check("Database not in repository", run_command("git ls-files *.db | wc -l | grep -q '^0$'")):
        checks_passed += 1
    else:
        print("      WARNING: Database files should not be committed")

    # Check for hardcoded secrets
    total_checks += 1
    result = not run_command("grep -r 'password.*=.*[\"\\'][^\\$]' production_server.py")
    if check("No hardcoded passwords in code", result):
        checks_passed += 1

    return checks_passed, total_checks


def main():
    """Run all validations"""
    print("=" * 60)
    print("NET WORTH Tennis Ladder - Pre-Deployment Validation")
    print("=" * 60)

    all_checks = []

    # Run all validation categories
    all_checks.append(validate_environment())
    all_checks.append(validate_dependencies())
    all_checks.append(validate_files())
    all_checks.append(validate_templates())
    all_checks.append(validate_database())
    all_checks.append(validate_code())
    all_checks.append(validate_git())
    all_checks.append(validate_security())

    # Calculate totals
    total_passed = sum(c[0] for c in all_checks)
    total_checks = sum(c[1] for c in all_checks)
    percentage = (total_passed / total_checks * 100) if total_checks > 0 else 0

    # Print summary
    print("\n" + "=" * 60)
    print("VALIDATION SUMMARY")
    print("=" * 60)
    print(f"  Total Checks: {total_checks}")
    print(f"  Passed: {total_passed}")
    print(f"  Failed: {total_checks - total_passed}")
    print(f"  Success Rate: {percentage:.1f}%")
    print()

    if percentage == 100:
        print("✓ ALL CHECKS PASSED!")
        print("  Your project is ready for deployment.")
        print()
        print("Next steps:")
        print("  1. Review PRE_DEPLOYMENT_CHECKLIST.md")
        print("  2. Follow START_HERE.md to deploy to Railway")
        print()
        return 0
    elif percentage >= 80:
        print("⚠️  MOSTLY READY")
        print("  Most checks passed, but review failures above.")
        print("  Fix critical issues before deploying.")
        print()
        return 1
    else:
        print("✗ NOT READY FOR DEPLOYMENT")
        print("  Too many checks failed. Review errors above.")
        print()
        print("Quick fixes:")
        print("  - Install dependencies: pip3 install -r requirements_backend.txt")
        print("  - Initialize database: python3 init_database.py --force")
        print("  - Commit changes: git add . && git commit -m 'message'")
        print()
        return 2


if __name__ == '__main__':
    sys.exit(main())
