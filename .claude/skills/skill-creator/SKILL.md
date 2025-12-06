---
name: skill-creator
description: Creates well-structured Claude Code skills following best practices from Anthropic and the community. Automatically generates SKILL.md files with proper YAML frontmatter, instructions, templates, and validation scripts.
version: "1.0.0"
---

# Skill Creator

You are an expert at creating Claude Code skills. When asked to create a new skill, follow this comprehensive workflow.

## When to Use This Skill

- User explicitly asks to "create a skill" or "build a skill"
- User describes a repetitive workflow that could be automated
- User wants to package domain knowledge for reuse
- User mentions creating instructions for a specific task

## Skill Creation Workflow

### 1. Gather Requirements

Ask clarifying questions to understand:
- **Task name**: What should this skill be called? (lowercase, hyphens, max 64 chars)
- **Purpose**: What specific task does this skill accomplish?
- **Context**: When should Claude automatically invoke this skill?
- **Inputs**: What information/files does the skill need?
- **Outputs**: What should the skill produce?
- **Examples**: Are there example inputs/outputs to include?
- **Validation**: Does this skill need validation scripts?

### 2. Create Directory Structure

```bash
.claude/skills/
└── skill-name/
    ├── SKILL.md          # Required: Main skill file
    ├── templates/        # Optional: Code/document templates
    ├── examples/         # Optional: Example inputs/outputs
    ├── scripts/          # Optional: Python validation scripts
    └── resources/        # Optional: Reference documentation
```

### 3. Write SKILL.md with Proper Structure

Every SKILL.md must have:

```yaml
---
name: skill-name                    # Required: lowercase, hyphens, max 64 chars
description: Brief description      # Required: max 1024 chars, describes WHEN to use
version: "1.0.0"                   # Optional: for tracking
allowed-tools: [Read, Write, Bash] # Optional: restrict tool access
model: claude-sonnet-4-5           # Optional: request specific model
---

# Skill Title

Clear description of what this skill does.

## When to Use This Skill

- Bullet points describing trigger conditions
- Keywords that should invoke this skill
- Context where this skill is relevant

## Instructions

### Step 1: [Action]
Detailed instructions...

### Step 2: [Action]
More instructions...

## Decision Trees

If [condition]:
- Do [action A]
Else:
- Do [action B]

## Templates

[Include inline templates or reference external files]

## Examples

### Example 1: [Scenario]
**Input:**
```
example input
```

**Output:**
```
expected output
```

## Best Practices

- Guideline 1
- Guideline 2

## Questions to Ask Users

1. Question 1?
2. Question 2?

## Output Format

Describe the expected output format clearly.

## Keywords

keyword1, keyword2, keyword3

## Resources

- [Template Name](./templates/template.md)
- [Example File](./examples/example.txt)
- [Validation Script](./scripts/validate.py)
```

### 4. Create Supporting Files (If Needed)

#### Templates
Create reusable templates in `templates/` directory:
- Document templates (Markdown, YAML, JSON)
- Code templates (Python, JavaScript, shell scripts)
- Configuration templates

#### Examples
Provide concrete examples in `examples/` directory:
- Example inputs
- Expected outputs
- Edge cases

#### Validation Scripts
Create Python scripts in `scripts/` directory for:
- Input validation
- Output verification
- Format checking
- Structure validation

Example validation script:
```python
#!/usr/bin/env python3
"""Validation script for skill-name"""

import sys
import yaml

def validate_skill(skill_path):
    """Validate skill structure and content"""
    errors = []

    # Check SKILL.md exists
    skill_file = skill_path / "SKILL.md"
    if not skill_file.exists():
        errors.append("SKILL.md not found")
        return errors

    # Validate YAML frontmatter
    content = skill_file.read_text()
    if not content.startswith("---"):
        errors.append("Missing YAML frontmatter")

    # Add more validation...

    return errors

if __name__ == "__main__":
    # Validation logic here
    pass
```

### 5. Test the Skill

After creating the skill:
1. Verify file structure is correct
2. Check YAML frontmatter is valid
3. Run validation scripts if present
4. Test invocation with example inputs
5. Verify Claude discovers and uses the skill appropriately

### 6. Document the Skill

Create a summary including:
- Skill name and location
- What it does
- How to invoke it (keywords/context)
- Example usage
- Any special configuration needed

## Skill Design Best Practices

### Progressive Disclosure Architecture

Use three-tier loading:
1. **Metadata (~100 tokens)**: Always loaded - name and description
2. **Instructions (~5000 tokens)**: Loaded when skill is invoked
3. **Resources (0 tokens until used)**: Templates, scripts load on-demand

This means you can create extensive skills without bloating context.

### Clear Invocation Triggers

Make the description and keywords very clear about WHEN to use this skill:
- ✅ "Use when user asks to create API endpoints"
- ❌ "A skill for APIs"

### Least Privilege Tool Access

Restrict tools using `allowed-tools` if possible:
```yaml
allowed-tools: [Read, Grep, Glob]  # Read-only skill
```

### Include Decision Trees

Help Claude make decisions within the skill:
```markdown
## Decision Tree

1. Check if project type is web app:
   - If yes: Use REST API template
   - If no: Check if CLI tool...
```

### Provide Concrete Examples

Always include at least 2-3 examples showing:
- Different input formats
- Expected outputs
- Edge cases

### Ask Clarifying Questions

Include a section of questions Claude should ask:
```markdown
## Questions to Ask

1. What programming language? (Python, JavaScript, Go)
2. What framework? (Django, Express, Gin)
3. Authentication method? (JWT, OAuth, API Key)
```

### Use Validation Scripts for Consistency

For skills that generate structured output, include Python scripts to validate:
- Syntax correctness
- Required fields present
- Format compliance
- File structure

### Reference Official Documentation

For skills dealing with specific technologies, include links to:
- Official documentation
- Version-specific syntax
- Best practices guides

Example:
```markdown
## Resources

- [Docker Compose Spec](https://docs.docker.com/compose/compose-file/)
- [Traefik v2.11 Docs](https://doc.traefik.io/traefik/v2.11/)
```

## Common Skill Patterns

### Documentation Generator Skills
- Input: Code/project context
- Output: Markdown documentation
- Templates: README.md, API docs, ADRs

### Code Generator Skills
- Input: Requirements/specifications
- Output: Source code files
- Validation: Syntax checking, linting

### Workflow Automation Skills
- Input: Task description
- Output: Sequence of commands/scripts
- Decision trees: Branch based on environment

### Analysis Skills
- Input: Code/logs/data
- Output: Analysis report with recommendations
- Examples: Security review, performance analysis

### Configuration Skills
- Input: Service requirements
- Output: Configuration files (YAML, JSON, TOML)
- Validation: Schema validation, syntax checking

## Skill Naming Conventions

- Use lowercase with hyphens: `skill-name`
- Be specific and descriptive: `docker-compose-validator` not `docker-skill`
- Use action verbs: `create-api`, `validate-config`, `generate-docs`
- Keep under 64 characters
- Avoid generic names: `helper`, `utility`, `tool`

## Output

After creating a skill, provide:

1. **Confirmation**: "Created skill: [name] in .claude/skills/[name]/"
2. **Description**: What the skill does
3. **Invocation**: How to trigger it (keywords/phrases)
4. **Files Created**: List all files generated
5. **Testing Instructions**: How to test the skill
6. **Next Steps**: Suggestions for improvement or related skills

## Examples

### Example 1: Simple Documentation Skill

**User Request**: "Create a skill for generating README files"

**Output**:
```
Created skill: readme-generator in .claude/skills/readme-generator/

What it does:
- Generates comprehensive README.md files for projects
- Includes badges, installation, usage, and contributing sections

How to invoke:
- "Generate a README for this project"
- "Create project documentation"
- Keywords: readme, documentation, getting started

Files created:
- SKILL.md (main skill file)
- templates/readme-template.md
- examples/example-readme.md

Test it: Try saying "Generate a README for this project"
```

### Example 2: Complex Validation Skill

**User Request**: "Create a skill that validates Docker Compose files against current documentation"

**Output**:
```
Created skill: docker-compose-validator in .claude/skills/docker-compose-validator/

What it does:
- Validates docker-compose.yml files
- Checks against current Docker Compose specification
- Identifies deprecated syntax
- Suggests fixes for errors

How to invoke:
- "Validate the docker-compose.yml file"
- "Check Docker Compose configuration"
- Automatically triggered when docker-compose.yml is created/edited

Files created:
- SKILL.md (main skill file)
- scripts/validate_compose.py (Python validator)
- examples/valid-compose.yml
- examples/invalid-compose.yml
- resources/compose-spec.md (reference docs)

Test it: Run "Validate the docker-compose.yml file"
```

## Keywords

skill, create skill, build skill, new skill, skill generator, make skill, develop skill, skill template
