#!/usr/bin/env python3
"""
ONE_SHOT v1.7 Validation Script

Validates ONE_SHOT.md against v1.7 enhanced validation patterns.
"""

import sys
import os
from pathlib import Path

def load_validation_patterns():
    """Load the enhanced validation patterns from ONE_SHOT v1.7"""
    return {
        'specific_frequency_indicators': [
            'weekly', 'monthly', 'quarterly', 'annually', 'daily', 'bi-weekly'
        ],
        'measurable_outcomes': [
            'save', 'reduce', 'increase', 'improve', 'minutes', 'hours',
            'percent', '%', 'faster', 'slower', 'more', 'less', 'quantifiable'
        ],
        'concrete_use_cases': [
            'user can', 'admin can', 'system will', 'feature allows',
            'example', 'use case', 'scenario', 'workflow', 'specific task'
        ],
        'clear_problem_statements': [
            'problem', 'issue', 'challenge', 'pain point', 'currently',
            'existing', 'manual', 'time-consuming', 'error-prone', 'workaround'
        ]
    }

def validate_oneshot_file():
    """Validate ONE_SHOT.md against v1.7 enhanced patterns"""

    validation_patterns = load_validation_patterns()

    print("🔍 Validating ONE_SHOT.md against ONE_SHOT v1.7 patterns...")

    # Load ONE_SHOT.md
    oneshot_file = 'one_shot.md'
    file_path = Path(oneshot_file)

    if not file_path.exists():
        print(f"❌ Error: {oneshot_file} not found")
        return False

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"❌ Error reading {oneshot_file}: {e}")
        return False

    print(f"📄 Loaded {oneshot_file} ({len(content)} characters)")

    # Validation results
    validation_results = {}
    total_matches = 0

    for pattern_name, pattern_list in validation_patterns.items():
        validation_results[pattern_name] = []

        content_lower = content.lower()

        # Count matches for each pattern
        if pattern_name == 'specific_frequency_indicators':
            for indicator in pattern_list:
                if indicator in content_lower:
                    count = content_lower.count(indicator)
                    validation_results[pattern_name].append((indicator, count))

        elif pattern_name == 'measurable_outcomes':
            for outcome in pattern_list:
                if outcome in content_lower:
                    count = content_lower.count(outcome)
                    validation_results[pattern_name].append((outcome, count))

        elif pattern_name == 'concrete_use_cases':
            for use_case in pattern_list:
                if use_case in content_lower:
                    count = content_lower.count(use_case)
                    validation_results[pattern_name].append((use_case, count))

        elif pattern_name == 'clear_problem_statements':
            for statement in pattern_list:
                if statement in content_lower:
                    count = content_lower.count(statement)
                    validation_results[pattern_name].append((statement, count))

        # Count total unique matches for this pattern
        total_matches += len(validation_results[pattern_name])

    # Display validation results
    print("\n📊 Validation Results:")
    print("=" * 50)

    for pattern_name, matches in validation_results.items():
        if matches:
            print(f"\n✅ {pattern_name.replace('_', ' ').title()}:")
            for match, count in matches:
                print(f"   • '{match}' (found {count} times)")
        else:
            print(f"\n❌ {pattern_name.replace('_', ' ').title()}: No matches found")

    # Calculate validation score
    max_possible_patterns = len(validation_patterns)
    found_patterns = sum(1 for matches in validation_results.values() if matches)

    print(f"\n🎯 Validation Summary:")
    print(f"   Patterns Found: {found_patterns}/{max_possible_patterns}")
    print(f"   Total Matches: {total_matches}")

    # Determine validation level
    if found_patterns >= 4 and total_matches >= 10:
        status = "🎯 FULLY VALIDATED - Excellent v1.7 compliance"
        validation_passed = True
    elif found_patterns >= 3 and total_matches >= 5:
        status = "✅ PARTIALLY VALIDATED - Good v1.7 compliance"
        validation_passed = True
    elif found_patterns >= 2:
        status = "⚠️  MINIMALLY VALIDATED - Some v1.7 patterns found"
        validation_passed = True
    else:
        status = "❌ NOT VALIDATED - Insufficient v1.7 patterns"
        validation_passed = False

    print(f"   Status: {status}")

    # Additional checks for v1.7 specific content
    print(f"\n🔍 Additional v1.7 Features Check:")

    v1_7_features = {
        'Reality Check (Q2.5)': ['reality check', 'q2.5', 'validation'],
        'Required Observability': ['observability', 'status', 'health', 'monitoring'],
        'Three-Tier AI Strategy': ['ai strategy', 'tier', 'cost-conscious'],
        'Validation-Before-Build': ['validation before build', 'validate then build'],
        'Future-You Documentation': ['future you', 'documentation standards'],
        'Claude Skills Integration': ['claude skills', 'skills', 'autonomous']
    }

    feature_count = 0
    for feature, keywords in v1_7_features.items():
        found = any(keyword in content_lower for keyword in keywords)
        if found:
            print(f"   ✅ {feature}")
            feature_count += 1
        else:
            print(f"   ❌ {feature}")

    print(f"\n   v1.7 Features: {feature_count}/{len(v1_7_features)}")

    return validation_passed

if __name__ == "__main__":
    success = validate_oneshot_file()
    if success:
        print(f"\n🎉 ONE_SHOT v1.7 validation completed successfully!")
        sys.exit(0)
    else:
        print(f"\n💡 ONE_SHOT v1.7 validation completed with issues to address.")
        sys.exit(1)