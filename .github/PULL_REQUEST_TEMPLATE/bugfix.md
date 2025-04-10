---
name: Bug Fix
about: Fix a bug in the project
title: 'fix: '
labels: [bug]
assignees: ''
filename: bugfix.md
---

# Bug Fix Pull Request

## PR Title Format

<!--
IMPORTANT: Your PR title should follow the Conventional Commit format:
fix(<optional scope>): <description>

Examples:
- fix(cli): resolve argument parsing issue
- fix(core): fix environment conversion error
- fix: correct dependency resolution
-->

## Description

<!-- Provide a clear and concise description of the bug and your fix -->

<!-- Include steps to reproduce the bug before the fix -->

## Related Issues

<!-- Link to any related issues this PR addresses -->

<!-- Example: Fixes #123 -->

## Root Cause

<!-- Describe the root cause of the bug -->

<!-- Explain what was causing the issue -->

## Solution

<!-- Describe your solution to the bug -->

<!-- Explain why this approach was chosen -->

## Testing Performed

<!-- Describe the tests you ran to verify your changes -->

<!-- Include relevant details for your test configuration -->

- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] Manual testing performed
- [ ] All tests passing locally
- [ ] GitHub Actions workflows tested locally (if applicable)

## Regression Prevention

<!-- Explain how this fix prevents similar bugs in the future -->

<!-- For example, through additional validation, tests, etc. -->

## Screenshots/Examples

<!-- If applicable, add before/after screenshots or code examples -->

## Checklist

<!-- Put an x in the boxes that apply -->

- [ ] My code follows the project's style guidelines
- [ ] I have performed a self-review of my own code
- [ ] I have commented my code, particularly in hard-to-understand areas
- [ ] My changes generate no new warnings
- [ ] I have added tests that prove my fix is effective
- [ ] All new and existing tests pass locally
- [ ] My commits follow the [Conventional Commits](https://www.conventionalcommits.org/) standard
- [ ] My PR title follows the Conventional Commits format
- [ ] I have updated the documentation accordingly

## Additional Notes

<!-- Add any other context about the bug fix here -->
