---
name: documentation-generator
description: Generates comprehensive documentation including READMEs, API docs, Architecture Decision Records (ADRs), and project guides. Follows documentation-first philosophy and maintains consistency across projects.
version: "1.0.0"
---

# Documentation Generator

You are an expert at creating clear, comprehensive, and maintainable documentation.

## When to Use This Skill

- User asks to "generate documentation" or "create docs"
- User mentions "README", "API docs", or "ADR"
- User wants to "document this feature" or "write documentation"
- New project needs documentation structure
- Documentation updates needed after changes

## Documentation Types

### 1. README.md
**Purpose**: Project overview and getting started guide
**Audience**: New users and developers
**Includes**: Installation, usage, examples, contribution guidelines

### 2. Architecture Decision Records (ADR)
**Purpose**: Document significant architectural decisions
**Audience**: Technical team, future maintainers
**Includes**: Context, decision, consequences, alternatives

### 3. API Documentation
**Purpose**: Endpoint specifications and usage
**Audience**: API consumers, frontend developers
**Includes**: Endpoints, parameters, responses, examples

### 4. User Guides
**Purpose**: How-to instructions for end users
**Audience**: End users, support teams
**Includes**: Step-by-step instructions, screenshots, examples

### 5. Developer Guides
**Purpose**: Setup and development workflows
**Audience**: Contributing developers
**Includes**: Setup, architecture, coding standards, workflows

### 6. CLAUDE.md
**Purpose**: AI assistant guidance for the project
**Audience**: Claude Code, development team
**Includes**: Conventions, architecture, common tasks, gotchas

## README.md Template

```markdown
# [Project Name]

> [One-sentence tagline]

[![Build Status](badge-url)](link)
[![Coverage](badge-url)](link)
[![License](badge-url)](link)

## Overview

[2-3 paragraph description of what this project does, why it exists, and who it's for]

## Features

- ✨ Feature 1: Brief description
- ✨ Feature 2: Brief description
- ✨ Feature 3: Brief description

## Prerequisites

- [Tool 1] `version X.Y+`
- [Tool 2] `version X.Y+`
- [Required service]

## Installation

### Quick Start

```bash
# Clone the repository
git clone [repo-url]
cd [project-name]

# Install dependencies
[install-command]

# Set up environment
cp .env.example .env
# Edit .env with your values

# Run
[run-command]
```

### Development Setup

```bash
# Install dev dependencies
[dev-install-command]

# Run tests
[test-command]

# Start development server
[dev-server-command]
```

## Usage

### Basic Usage

```bash
# Example 1: [Description]
[command]

# Example 2: [Description]
[command]
```

### Configuration

Configuration options available:

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| VAR_1 | Description | value | Yes |
| VAR_2 | Description | value | No |

### Examples

#### Example 1: [Scenario]

```[language]
[code example]
```

Output:
```
[expected output]
```

## Architecture

[Brief overview or link to detailed architecture docs]

```
┌─────────────┐      ┌─────────────┐      ┌─────────────┐
│   Client    │─────▶│     API     │─────▶│  Database   │
└─────────────┘      └─────────────┘      └─────────────┘
```

## API Reference

[Brief overview or link to detailed API docs]

## Development

### Project Structure

```
project-name/
├── src/          # Source code
├── tests/        # Tests
├── docs/         # Documentation
├── config/       # Configuration
└── scripts/      # Utility scripts
```

### Running Tests

```bash
# All tests
[test-command]

# Specific test
[specific-test-command]

# With coverage
[coverage-command]
```

### Code Style

This project follows [style guide name].

```bash
# Lint
[lint-command]

# Format
[format-command]
```

### Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## Deployment

[Deployment instructions or link to deployment guide]

## Troubleshooting

### Common Issues

**Issue**: [Problem description]
**Solution**: [How to fix]

**Issue**: [Problem description]
**Solution**: [How to fix]

## FAQ

**Q**: [Question]?
**A**: [Answer]

**Q**: [Question]?
**A**: [Answer]

## License

[License information]

## Acknowledgments

- [Credit 1]
- [Credit 2]

## Support

- Documentation: [link]
- Issues: [link]
- Discussions: [link]

---

🤖 Generated with [Claude Code](https://claude.com/claude-code)
```

## ADR Template (Nygard Format)

```markdown
# ADR-XXX: [Title]

**Date**: YYYY-MM-DD
**Status**: [Proposed | Accepted | Deprecated | Superseded by ADR-YYY]
**Deciders**: [List of people involved]

## Context

What is the issue we're trying to solve? What factors are influencing this decision?

[Background information, problem statement, and context]

## Decision

What change are we making?

[Clear statement of the decision]

## Rationale

Why this decision?

[Reasoning behind the decision]

## Consequences

### Positive

- ✅ Benefit 1
- ✅ Benefit 2

### Negative

- ❌ Trade-off 1
- ❌ Trade-off 2

### Risks

- ⚠️ Risk 1: [Mitigation strategy]
- ⚠️ Risk 2: [Mitigation strategy]

## Alternatives Considered

### Alternative 1: [Name]

[Description]

**Rejected because**: [Reason]

### Alternative 2: [Name]

[Description]

**Rejected because**: [Reason]

## Implementation Notes

[Any implementation details, constraints, or considerations]

## References

- [Link 1]
- [Link 2]

---

🤖 Generated with [Claude Code](https://claude.com/claude-code)
```

## API Documentation Template

```markdown
# API Documentation

## Overview

Base URL: `https://api.example.com/v1`

## Authentication

All requests require authentication via Bearer token:

```bash
curl -H "Authorization: Bearer YOUR_TOKEN" https://api.example.com/v1/endpoint
```

## Endpoints

### GET /resource

Retrieves a list of resources.

**Parameters**:

| Name | Type | Required | Description |
|------|------|----------|-------------|
| page | integer | No | Page number (default: 1) |
| limit | integer | No | Items per page (default: 20) |

**Example Request**:

```bash
curl -X GET https://api.example.com/v1/resource?page=1&limit=20 \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Example Response** (200 OK):

```json
{
  "data": [
    {
      "id": "123",
      "name": "Example"
    }
  ],
  "pagination": {
    "page": 1,
    "total_pages": 5
  }
}
```

**Error Responses**:

- `401 Unauthorized`: Invalid or missing token
- `429 Too Many Requests`: Rate limit exceeded

### POST /resource

Creates a new resource.

**Request Body**:

```json
{
  "name": "string (required)",
  "description": "string (optional)"
}
```

**Example Request**:

```bash
curl -X POST https://api.example.com/v1/resource \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"Example","description":"Test"}'
```

**Example Response** (201 Created):

```json
{
  "id": "124",
  "name": "Example",
  "description": "Test",
  "created_at": "2025-12-02T10:00:00Z"
}
```

## Rate Limiting

- 1000 requests per hour per API key
- Header `X-RateLimit-Remaining` shows remaining requests
- Header `X-RateLimit-Reset` shows reset time (Unix timestamp)

## Error Handling

All errors return:

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable message"
  }
}
```

## SDKs

- [JavaScript/TypeScript](link)
- [Python](link)
- [Go](link)

---

🤖 Generated with [Claude Code](https://claude.com/claude-code)
```

## Documentation Best Practices

### General Principles

1. **Start with Why**: Explain purpose before details
2. **Show, Don't Just Tell**: Include examples
3. **Be Concise**: Remove unnecessary words
4. **Be Specific**: Avoid vague language
5. **Keep Updated**: Documentation rots quickly

### Writing Style

- Use active voice: "Run this command" not "This command should be run"
- Use present tense: "The API returns" not "The API will return"
- Be direct: "Install Node.js" not "You might want to install Node.js"
- Avoid jargon unless necessary and defined

### Code Examples

- Show complete, runnable examples
- Include expected output
- Cover common use cases
- Show error handling

### Structure

```markdown
1. Overview (What is it?)
2. Quick Start (Get running in 5 minutes)
3. Core Concepts (Understanding the system)
4. Detailed Guides (How to do specific things)
5. API Reference (Complete technical reference)
6. Troubleshooting (Common issues)
```

## Documentation Workflow

### 1. Understand Audience

- Who will read this?
- What do they need to know?
- What's their technical level?
- What's their goal?

### 2. Gather Information

```bash
# For existing code, analyze:
- File structure
- Configuration options
- API endpoints
- Dependencies
- Environment variables
```

### 3. Create Outline

```markdown
# Document Title

## Section 1
- Point 1
- Point 2

## Section 2
- Point 1
- Point 2
```

### 4. Write Content

- Start with overview
- Add examples early
- Build from simple to complex
- Include code samples

### 5. Review and Refine

- Test all examples
- Check links
- Verify accuracy
- Get feedback

### 6. Maintain

- Update with code changes
- Add new examples
- Remove outdated content
- Track questions/issues

## Output Format

After generating documentation:

```markdown
## ✓ Documentation Generated

**Created**:
- README.md
- docs/architecture/ADR-XXX-[topic].md
- docs/api/README.md
- [Other files]

**Includes**:
- Project overview
- Installation instructions
- Usage examples
- API reference
- Architecture decisions
- Troubleshooting guide

**Next Steps**:
1. Review generated docs for accuracy
2. Add project-specific examples
3. Update with environment-specific details
4. Test all code examples
5. Add screenshots if applicable

**Maintenance**:
- Update README with feature changes
- Create ADRs for architectural decisions
- Keep API docs in sync with code
- Review docs quarterly
```

## Keywords

generate documentation, create docs, write README, API documentation, ADR, architecture decision record, document feature, documentation

## Resources

- [ADR Guide](https://adr.github.io/)
- [OpenAPI Specification](https://swagger.io/specification/)
- [Write the Docs](https://www.writethedocs.org/)
