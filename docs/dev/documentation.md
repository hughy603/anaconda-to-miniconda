# Documentation Style Guide

This guide provides detailed standards and best practices for documentation in the Conda-Forge Converter project.

## Documentation Structure

- `user/`: User-focused documentation

  - `getting-started.md`: Installation and basic usage
  - `cli-reference.md`: Command-line interface reference
  - `workflows.md`: Common workflow examples
  - `troubleshooting.md`: Common issues and solutions

- `dev/`: Developer documentation

  - `architecture.md`: Architecture overview
  - `contributing.md`: Contributing guidelines
  - `testing.md`: Testing approach and running tests
  - `releasing.md`: Release process
  - `documentation.md`: Documentation guidelines (this file)

- `api/`: API documentation

  - `index.md`: API overview
  - `core.md`: Core module documentation

- `design/`: Design documentation

  - `overview.md`: High-level design decisions
  - `improvements.md`: Planned improvements

- `about/`: Project information

  - `license.md`: License information
  - `changelog.md`: Version history and changes

## Building the Documentation

We use MkDocs with the Material theme for our documentation:

1. Install MkDocs with the Material theme:

   ```bash
   pip install mkdocs mkdocs-material mkdocstrings
   ```

1. Preview the documentation locally:

   ```bash
   mkdocs serve
   ```

1. Build static site:

   ```bash
   mkdocs build
   ```

## Principles

Our documentation aims to be:

- **Accurate**: Technically correct and up-to-date
- **Clear**: Easy to understand and navigate
- **Comprehensive**: Covers all important aspects of the project
- **Consistent**: Uses consistent terminology and formatting
- **Accessible**: Usable by people with diverse backgrounds and experience levels

## Documentation Types

### User Documentation

- **Tutorials**: Step-by-step guides for beginners
- **How-to Guides**: Task-oriented guides for specific objectives
- **References**: Detailed technical descriptions of functions, classes, and APIs
- **Explanations**: Conceptual discussions that provide context and background

### Developer Documentation

- **Architecture**: System design and component relationships
- **Contributing Guide**: How to contribute to the project
- **Code Standards**: Coding conventions and best practices
- **Development Workflow**: Setting up development environment, testing, and release process

## Markdown Style

### General Formatting

- Use ATX-style headers with a space after the hash: `# Heading`
- Leave one blank line before and after headings
- Line length: 120 characters maximum (except for code blocks and tables)
- Use emphasis sparingly (`*italic*` or `**bold**`)
- Use unordered lists with dashes (`-`) and ordered lists with numbers (`1.`)
- Indent nested lists with 2 spaces

### Code Formatting

- Use backticks for inline code: `` `code` ``
- Use fenced code blocks with language identifiers:

```python
def example_function():
    """This is an example function."""
    return True
```

### Links and References

- Use reference-style links for better readability:
  ```markdown
  [link text][reference]

  [reference]: https://example.com
  ```
- Use relative links for internal documentation
- Always include descriptive link text that makes sense out of context

### Images

- Include alt text for all images:
  ```markdown
  ![Alt text describing the image](path/to/image.png)
  ```
- Keep images in an `assets` or `images` directory
- Optimize images for web (reasonable file size)
- Use SVG format for diagrams when possible

## Python Docstrings

We follow Google-style docstrings:

```python
def function_name(param1, param2):
    """Short description of function.

    Longer description explaining the function in detail.

    Args:
        param1 (type): Description of param1.
        param2 (type): Description of param2.

    Returns:
        return_type: Description of return value.

    Raises:
        ExceptionType: Description of when this exception is raised.

    Examples:
        >>> function_name("example", 123)
        "result"
    """
    return result
```

### Key Components

- **One-line summary**: Brief description ending with a period
- **Extended description**: Additional details as needed
- **Args/Parameters**: All parameters with types and descriptions
- **Returns**: Description of return value with type
- **Raises**: Exceptions that may be raised
- **Examples**: Usage examples (optional but encouraged)

## Writing Guidelines

### Voice and Tone

- Use present tense: "The function returns a value" (not "will return")
- Use active voice: "The system logs errors" (not "Errors are logged by the system")
- Use second person ("you") in user guides and tutorials
- Use imperative mood for commands: "Run the install command" (not "You should run")

### Terminology and Consistency

- Maintain a consistent vocabulary throughout the documentation
- Proper capitalization for special terms (Python, conda-forge, etc.)
- Define terms that may be unfamiliar to readers
- Use "file" not "script" when referring to Python files

### Content Guidelines

- Write in clear, concise American English
- Use present tense and active voice when possible
- Use second person ("you") for user guides and tutorials
- Use imperative mood for procedure steps ("Install the package", not "You should install the package")
- Include examples for code snippets
- Proper capitalization of special terms (Python, conda-forge, Miniconda, etc.)
- Always provide context before showing code or commands

### Structure

- Each document should have a single, clear purpose
- Begin with a brief introduction explaining the document's purpose
- Use headers to organize content hierarchically
- Include a "Related Resources" section at the end of each document

### Versioning Notes

- Clearly mark features with their minimum required version
- Use admonitions for version-specific notes:
  ```markdown
  !!! note "Available from version 1.2"
      This feature is only available in version 1.2 and later.
  ```

## Documentation Process

### Adding New Documentation

1. Identify what documentation is needed
1. Place it in the appropriate directory within `docs/`
1. Update the nav in `mkdocs.yml` if adding a new page
1. Run pre-commit checks before committing
1. Submit PR for review

### Updating Existing Documentation

1. Update content to be accurate and relevant
1. Ensure consistency with existing documentation
1. Run pre-commit checks before committing
1. Submit PR for review

### Review Process

Documentation PRs are reviewed for:

- Technical accuracy
- Completeness
- Style consistency
- Clarity and readability
- Grammar and spelling

## Automated Checks

We use pre-commit hooks to enforce documentation standards:

- **markdownlint**: Checks Markdown syntax and style
- **pydocstyle**: Validates Python docstrings follow Google style
- **mdformat**: Formats Markdown files consistently
- **pymarkdown**: Additional Markdown linting

Run checks locally with:

```bash
pre-commit run --all-files
```

For more details, see the [.pre-commit-config.yaml](../.pre-commit-config.yaml) file.

## Related Resources

- [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings)
- [Material for MkDocs Documentation](https://squidfunk.github.io/mkdocs-material/)
- [Diátaxis Documentation Framework](https://diataxis.fr/)
