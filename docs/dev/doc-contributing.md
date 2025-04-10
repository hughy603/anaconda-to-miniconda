# Documentation Contribution Guide

This guide explains how to contribute to the project's documentation. It complements the [Documentation Style Guide](documentation.md) which covers writing standards and formatting.

## Getting Started

1. **Fork and Clone**: Fork the repository and clone it locally
1. **Create a Branch**: Create a new branch for your documentation changes
   ```bash
   git checkout -b docs/your-feature-name
   ```
1. **Set Up Environment**: Install documentation dependencies
   ```bash
   uvx pip install -e ".[docs]"
   ```

## Documentation Structure

```
docs/
├── dev/           # Developer documentation
├── user/          # User documentation
├── images/        # Images and diagrams
└── index.md       # Main documentation page
```

## Types of Documentation

### 1. User Documentation

- Located in `docs/user/`
- Focus on end-user features and workflows
- Include practical examples
- Add to `docs/user/getting-started.md` for new features

### 2. Developer Documentation

- Located in `docs/dev/`
- Technical details and implementation
- API documentation
- Architecture decisions

### 3. API Documentation

- Use docstrings following Google style
- Include type hints
- Document exceptions and edge cases
- Example:
  ```python
  def convert_environment(source: str, target: str) -> bool:
      """Convert a conda environment to conda-forge format.

      Args:
          source: Source environment name
          target: Target environment name

      Returns:
          bool: True if conversion successful

      Raises:
          EnvironmentNotFoundError: If source environment doesn't exist
          ConversionError: If conversion fails
      """
  ```

## Writing Process

1. **Plan Your Changes**

   - Identify the documentation type
   - Determine the target audience
   - Outline the key points to cover

1. **Write the Content**

   - Follow the [Documentation Style Guide](documentation.md)
   - Use clear, concise language
   - Include examples and diagrams
   - Add links to related documentation

1. **Add Diagrams**

   - Use Mermaid for diagrams
   - Place in `docs/images/`
   - Example:
     ```mermaid
     graph TD
         A[Start] --> B{Check Environment}
         B -->|Exists| C[Convert]
         B -->|Missing| D[Error]
     ```

1. **Review Your Changes**

   - Run documentation checks:
     ```bash
     pre-commit run --all-files
     mkdocs build --strict
     ```
   - Check for broken links
   - Verify formatting
   - Test code examples

## Pull Request Process

1. **Prepare Your PR**

   - Update the changelog
   - Add tests if needed
   - Ensure all checks pass

1. **PR Description**

   - Summarize changes
   - Link related issues
   - List any breaking changes
   - Include screenshots for UI changes

1. **Review Process**

   - Address reviewer comments
   - Update documentation as needed
   - Ensure all checks pass

## Documentation Tools

### MkDocs

- Build documentation: `mkdocs build`
- Serve locally: `mkdocs serve`
- Deploy: `mkdocs gh-deploy`

### Pre-commit Hooks

- Markdown linting
- Link checking
- Code block validation

### Testing Documentation

```bash
# Run all documentation checks
pre-commit run --all-files

# Build documentation
mkdocs build --strict

# Check for broken links
mkdocs build --strict --verbose
```

## Best Practices

1. **Keep Documentation Updated**

   - Update docs with code changes
   - Remove outdated information
   - Mark deprecated features

1. **Use Version Control**

   - Commit messages: `docs: brief description`
   - Reference issues in commits
   - Keep changes focused

1. **Maintain Quality**

   - Follow style guide
   - Include examples
   - Test code snippets
   - Check for broken links

1. **Collaborate**

   - Request reviews
   - Address feedback
   - Help others

## Getting Help

- Ask in the project's discussion forum
- Tag maintainers for urgent issues
- Check existing documentation first
- Reference specific sections when asking questions

## Resources

- [Documentation Style Guide](documentation.md)
- [MkDocs Documentation](https://www.mkdocs.org/)
- [Mermaid Documentation](https://mermaid-js.github.io/mermaid/)
- [Google Developer Documentation Style Guide](https://developers.google.com/tech-writing)
