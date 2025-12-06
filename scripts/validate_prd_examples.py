#!/usr/bin/env python3
"""
Automated PRD Examples Validation Script

Validates PRD examples against ONE_SHOT v1.7 enhanced validation patterns.
"""

import sys
import os
import glob
from pathlib import Path

def load_validation_patterns():
    """Load the enhanced validation patterns from ONE_SHOT v1.7"""
    return {
        'specific_frequency_indicators': [
            'weekly', 'monthly', 'quarterly'
        ],
        'measurable_outcomes': [
            'process_x_minutes_instead_of_y',
            'save_time_amount',
            'quantifiable_improvement'
        ],
        'concrete_use_cases': [
            'specific_task_description',
            'tomorrow_morning_test'
        ],
        'clear_problem_statements': [
            'current_pain_points',
            'existing_workarounds'
        ]
    }

def validate_prd_examples():
    """Validate all PRD examples against v1.7 enhanced patterns"""

    # Load context
    sys.path.append(os.getcwd())
    sys.path.append('/home/khamel83/github/oneshot')

    try:
        # Try to import claude_skills if available
        from claude_skills import load_oneshot_context, read_skill_md
        context = load_oneshot_context()
    except ImportError:
        # Fallback: load ONE_SHOT context directly
        try:
            with open('one_shot.md', 'r', encoding='utf-8') as f:
                context = {'oneshot_content': f.read()}
            print("✅ Loaded ONE_SHOT context directly from one_shot.md")
        except FileNotFoundError:
            print("❌ Error: Could not find one_shot.md")
            return False
    except Exception as e:
        print(f"❌ Error: Could not load ONE_SHOT context: {e}")
        return False

    validation_patterns = load_validation_patterns()

    print("🔍 Validating PRD Examples against ONE_SHOT v1.7 patterns...")

    # Find all example files
    agent_files = glob.glob('.claude/agents/*.md')

    # Also check for examples directly in ONE_SHOT
    main_oneshot_file = 'one_shot.md'

    total_files = 0
    validated_files = 0
    failed_files = 0

    # Process main ONE_SHOT file first
    file_path = Path(main_oneshot_file)
    total_files += 1

        if not file_path.exists():
            print(f"❌ Missing file: {agent_file}")
            failed_files += 1
            continue

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Check for v1.7 specific validation patterns
            validation_score = 0
            pattern_matches = {}

            for pattern_name, pattern_list in validation_patterns.items():
                pattern_matches[pattern_name] = []

                if pattern_name == 'specific_frequency_indicators':
                    indicators = ['weekly', 'monthly', 'quarterly', 'annually']
                    for indicator in indicators:
                        if indicator.lower() in content.lower():
                            pattern_matches[pattern_name].append(indicator)

                elif pattern_name == 'measurable_outcomes':
                    outcomes = ['process_x_minutes_instead_of_y', 'save_time_amount', 'quantifiable_improvement']
                    for outcome in outcomes:
                        if any(outcome in content.lower() for outcome in outcomes):
                            pattern_matches[pattern_name].append(outcome)

                elif pattern_name == 'concrete_use_cases':
                    use_cases = ['specific_task_description', 'tomorrow_morning_test']
                    for use_case in use_cases:
                        if any(use_case in content.lower() for use_case in use_cases):
                            pattern_matches[pattern_name].append(use_case)

                elif pattern_name == 'clear_problem_statements':
                    statements = ['current_pain_points', 'existing_workarounds']
                    for statement in statements:
                        if any(statement in content.lower() for statement in statements):
                            pattern_matches[pattern_name].append(statement)

            # Calculate validation score
            validation_score = sum(len(pattern_matches[p]) for p in validation_patterns.values())

            # Determine validation level
            if validation_score >= 4:
                status = f"🎯 {agent_file}: fully validated with {validation_score}/4 patterns"
                validated_files += 1
            elif validation_score >= 2:
                status = f"✅ {agent_file}: partially validated with {validation_score}/4 patterns"
                validated_files += 1
            else:
                status = f"⚠️  {agent_file}: poor validation with {validation_score}/4 patterns"

            print(f"{status} ({validation_score}/4)")

        except Exception as e:
            print(f"❌ Error processing {agent_file}: {e}")
            failed_files += 1

    # Summary
    print(f"\n📊 Validation Summary:")
    print(f"  Total files: {total_files}")
    print(f"  Validated: {validated_files}")
    print(f"  Failed: {failed_files}")

    return validated_files == total_files

if __name__ == "__main__":
    validate_prd_examples()