# Conventional Commits Guide

This guide provides detailed information on using conventional commits in the Conda-Forge Converter project. Following these standards helps automate versioning, changelog generation, and ensures consistent commit messages across the project.

## What are Conventional Commits?

Conventional Commits is a specification for adding human and machine-readable meaning to commit messages. It provides a simple set of rules for creating commit messages that make it easier to automate processes like:

- Generating changelogs
- Determining semantic version bumps
- Communicating the nature of changes to teammates and users

## Commit Message Format

Each commit message consists of:

```
<type>(<scope>): <description>

[optional body]

[optional footer(s)]
```

### Type

The `type` field must be one of the following:

| Type       | Description                                                   | Version Bump |
| ---------- | ------------------------------------------------------------- | ------------ |
| `feat`     | A new feature                                                 | MINOR        |
| `fix`      | A bug fix                                                     | PATCH        |
| `docs`     | Documentation only changes                                    | -            |
| `style`    | Changes that do not affect the meaning of the code            | -            |
| `refactor` | A code change that neither fixes a bug nor adds a feature     | -            |
| `perf`     | A code change that improves performance                       | PATCH        |
| `test`     | Adding missing tests or correcting existing tests             | -            |
| `build`    | Changes that affect the build system or external dependencies | -            |
| `ci`       | Changes to our CI configuration files and scripts             | -            |
| `chore`    | Other changes that don't modify src or test files             | -            |

### Scope

The `scope` is optional and should be a noun describing a section of the codebase:

- `cli`: Command-line interface
- `core`: Core functionality
- `utils`: Utility functions
- `deps`: Dependencies
- `tests`: Test suite
- `docs`: Documentation

### Description

The `description` is a short summary of the code changes:

- Use the imperative, present tense: "change" not "changed" nor "changes"
- Don't capitalize the first letter
- No period (.) at the end

### Body

The body is optional and should provide context about the change:

- Use the imperative, present tense
- Include motivation for the change
- Compare with previous behavior

### Footer

The footer is optional and should contain:

- Breaking changes
- References to GitHub issues

For breaking changes, start with `BREAKING CHANGE:` followed by a description.

To reference issues, use `Fixes #123` or `Closes #123`.

## Examples

### Simple Feature

```
feat(cli): add verbose output option
```

### Bug Fix with Issue Reference

```
fix(core): resolve package resolution error

Fixes #123
```

### Documentation Change

```
docs: update installation instructions
```

### Breaking Change

```
feat(api): change environment creation interface

BREAKING CHANGE: The environment creation API now requires a configuration object instead of individual parameters.
```

### Multiple Scopes

If a change affects multiple scopes, you can use comma separation:

```
refactor(core,utils): move shared functions to utils
```

### Revert Commit

```
revert: feat(cli): add verbose output option

This reverts commit abc123.
```

## Common Mistakes to Avoid

1. **Forgetting the type**

   - ❌ `(cli): add verbose output option`
   - ✅ `feat(cli): add verbose output option`

1. **Capitalizing the description**

   - ❌ `feat(cli): Add verbose output option`
   - ✅ `feat(cli): add verbose output option`

1. **Using past tense**

   - ❌ `feat(cli): added verbose output option`
   - ✅ `feat(cli): add verbose output option`

1. **Adding a period at the end**

   - ❌ `feat(cli): add verbose output option.`
   - ✅ `feat(cli): add verbose output option`

1. **Vague descriptions**

   - ❌ `fix: update code`
   - ✅ `fix(core): resolve package resolution error`

## Commitizen Integration

We use [Commitizen](https://commitizen-tools.github.io/commitizen/) to enforce conventional commits. It's integrated into our pre-commit hooks, so you'll be prompted to follow the format when committing.

### Using Commitizen CLI

You can use the Commitizen CLI to help format your commits:

```bash
# Install Commitizen
pip install commitizen

# Commit using the interactive prompt
cz commit
```

The interactive prompt will guide you through creating a properly formatted commit message.

## How Conventional Commits Drive Our Workflow

### Automated Versioning

Commitizen analyzes commit messages to determine the next version number:

- `feat`: Bumps the MINOR version
- `fix`, `perf`: Bumps the PATCH version
- `BREAKING CHANGE`: Bumps the MAJOR version

### Automated Changelog Generation

Commit messages are used to generate the CHANGELOG.md file, categorizing changes by type:

- Added: `feat`
- Fixed: `fix`
- Changed: `refactor`, `perf`
- Documentation: `docs`

### Pull Request Titles

PR titles should also follow the conventional commits format, as they're used when squash-merging PRs.

## Commit Message Template

You can set up a commit message template to help you follow the format:

```bash
git config --local commit.template .github/commit-template.txt
```

Our template file (.github/commit-template.txt) contains:

```
# <type>(<scope>): <description>
# |<----  Using a Maximum Of 50 Characters  ---->|

# Explain why this change is being made
# |<----   Try To Limit Each Line to a Maximum Of 72 Characters   ---->|

# Provide links or keys to any relevant tickets, articles or other resources
# Example: Fixes #123, Relates to #456, Closes #789

# --- COMMIT END ---
# Type can be
#    feat     (new feature)
#    fix      (bug fix)
#    docs     (changes to documentation)
#    style    (formatting, missing semi colons, etc; no code change)
#    refactor (refactoring production code)
#    test     (adding missing tests, refactoring tests; no production code change)
#    chore    (updating grunt tasks etc; no production code change)
#    perf     (performance improvements)
#    build    (changes to build process)
#    ci       (changes to CI configuration)
# --------------------
# Remember to
#    Use the imperative mood in the subject line
#    Do not end the subject line with a period
#    Separate subject from body with a blank line
#    Use the body to explain what and why vs. how
#    Can use multiple lines with "-" for bullet points in body
# --------------------
```

## Additional Resources

- [Conventional Commits Specification](https://www.conventionalcommits.org/)
- [Commitizen Documentation](https://commitizen-tools.github.io/commitizen/)
- [Angular Commit Message Guidelines](https://github.com/angular/angular/blob/master/CONTRIBUTING.md#commit)
