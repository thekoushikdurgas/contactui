# Code Review Guidelines

**Last Updated**: January 26, 2026

---

## Overview

This document outlines the code review process and guidelines for the Documentation AI project. Code reviews ensure code quality, knowledge sharing, and maintainability.

---

## Review Process

### 1. Before Submitting a PR

- [ ] All tests pass locally
- [ ] Code follows style guidelines (run `ruff check .` and `black .`)
- [ ] Type hints added for new Python functions
- [ ] Docstrings added for new functions/classes
- [ ] No linting errors (`ruff check .`)
- [ ] No type checking errors (`mypy .`)
- [ ] Self-review completed
- [ ] PR description is clear and complete

### 2. PR Requirements

- **Title**: Clear, descriptive title (e.g., "Add health check endpoints")
- **Description**: Use the PR template with all sections filled
- **Size**: Keep PRs focused and reasonably sized (< 500 lines ideally)
- **Tests**: Include tests for new functionality
- **Documentation**: Update docs if needed

### 3. Review Checklist

#### Code Quality
- [ ] Code is readable and maintainable
- [ ] Follows project conventions and patterns
- [ ] No code duplication
- [ ] Appropriate error handling
- [ ] Security considerations addressed
- [ ] Performance implications considered

#### Testing
- [ ] Tests cover new functionality
- [ ] Tests are clear and maintainable
- [ ] Edge cases are tested
- [ ] Test coverage is adequate

#### Documentation
- [ ] Code is well-commented
- [ ] Docstrings are present and accurate
- [ ] README/docs updated if needed
- [ ] API documentation updated if needed

#### Architecture
- [ ] Changes align with project architecture
- [ ] No unnecessary dependencies added
- [ ] Proper separation of concerns
- [ ] Follows existing patterns

---

## Review Focus Areas

### Security
- Input validation and sanitization
- Authentication and authorization
- SQL injection prevention
- XSS prevention
- Sensitive data handling
- API security

### Performance
- Database query optimization
- Caching strategies
- N+1 query issues
- Memory usage
- Response times

### Maintainability
- Code clarity
- Naming conventions
- Code organization
- Error messages
- Logging

### Testing
- Test coverage
- Test quality
- Edge cases
- Integration tests
- E2E tests

---

## Review Comments

### Types of Comments

1. **Must Fix**: Critical issues that must be addressed
   - Security vulnerabilities
   - Bugs that break functionality
   - Performance issues
   - Breaking changes

2. **Should Fix**: Important improvements
   - Code quality issues
   - Better error handling
   - Missing tests
   - Documentation gaps

3. **Nice to Have**: Optional improvements
   - Code style suggestions
   - Refactoring opportunities
   - Performance optimizations

### Comment Guidelines

- Be constructive and respectful
- Explain the "why" behind suggestions
- Provide examples when possible
- Acknowledge good work
- Focus on the code, not the person

---

## Approval Criteria

A PR can be approved when:

1. ✅ All "Must Fix" comments are addressed
2. ✅ All tests pass
3. ✅ Code quality checks pass
4. ✅ At least one approval from a team member
5. ✅ No merge conflicts
6. ✅ CI/CD pipeline passes

---

## Common Issues to Watch For

### Python-Specific
- Missing type hints
- Missing docstrings
- Improper exception handling
- Unused imports
- Missing error handling
- Hardcoded values

### Django-Specific
- Missing migrations
- N+1 query issues
- Missing CSRF protection
- Improper use of `@login_required`
- Missing input validation
- Security headers

### General
- Code duplication
- Magic numbers/strings
- Poor naming
- Missing tests
- Incomplete error handling
- Missing documentation

---

## Review Tools

### Automated Checks
- **Linting**: `ruff check .`
- **Formatting**: `black . --check`
- **Type Checking**: `mypy .`
- **Tests**: `pytest`
- **Coverage**: `pytest --cov`

### Manual Checks
- Code readability
- Architecture alignment
- Security review
- Performance review

---

## Review Response

### As a PR Author

1. **Acknowledge** all comments
2. **Address** "Must Fix" items immediately
3. **Discuss** "Should Fix" items if unclear
4. **Consider** "Nice to Have" suggestions
5. **Update** PR description if needed
6. **Request re-review** when ready

### As a Reviewer

1. **Be timely** - Review within 24-48 hours
2. **Be thorough** - Check all aspects
3. **Be constructive** - Provide helpful feedback
4. **Be respectful** - Focus on code, not person
5. **Be decisive** - Approve or request changes clearly

---

## Best Practices

### For Authors
- Keep PRs focused and small
- Write clear commit messages
- Respond to feedback promptly
- Test thoroughly before submitting
- Update documentation

### For Reviewers
- Review promptly
- Be constructive
- Ask questions if unclear
- Approve when satisfied
- Learn from reviews

---

## Resources

- [Python Style Guide (PEP 8)](https://pep8.org/)
- [Django Best Practices](https://docs.djangoproject.com/en/stable/misc/design-philosophies/)
- [Type Hints (PEP 484)](https://www.python.org/dev/peps/pep-0484/)
- [Code Review Best Practices](https://google.github.io/eng-practices/review/)

---

## Questions?

If you have questions about the review process or guidelines, please:
1. Check this document first
2. Ask in team chat
3. Discuss with team lead
