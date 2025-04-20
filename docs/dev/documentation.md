# Documentation Style Guide

This guide provides standards and best practices for writing and maintaining documentation
for the Conda-Forge Converter project.

## General Principles

- **Clarity**: Write clear, concise, and accurate documentation
- **Consistency**: Maintain consistent style, formatting, and terminology
- **Completeness**: Cover all necessary information without redundancy
- **Accessibility**: Make documentation accessible to users of all skill levels

## Document Structure

### Standard Sections

Each documentation file should follow this structure:

1. **Title**: Clear, descriptive title (H1)
1. **Overview**: Brief introduction to the topic (1-2 paragraphs)
1. **Main Content**: Organized with appropriate headings (H2, H3, etc.)
1. **Examples**: Practical examples where applicable
1. **Related Information**: Links to related documentation

### Heading Hierarchy

- H1 (`#`): Document title
- H2 (`##`): Major sections
- H3 (`###`): Subsections
- H4 (`####`): Minor subsections

## Formatting Guidelines

### Text Formatting

- Use **bold** for emphasis and important terms
- Use `code` for technical terms, commands, and code snippets
- Use *italics* sparingly for special terms or concepts
- Use `>` for important notes or warnings

### Code Blocks

- Use triple backticks with language specification:

  ````markdown
  ```python
  def example_function():
      return "Hello, World!"
  ```
  ````

- For command-line examples:

  ````markdown
  ```bash
  conda-forge-converter -s myenv -t myenv_forge
  ```
  ````

### Lists

- Use `-` for unordered lists
- Use `1.` for ordered lists
- Indent nested lists with 2 spaces

### Links

- Use descriptive link text: `[CLI Reference](user/cli-reference.md)`
- For external links, add a note: `[Python Documentation](https://docs.python.org/) (external)`

### Images and Diagrams

- Use Mermaid for diagrams when possible
- Include alt text for accessibility
- Place images in the `docs/images/` directory

## Terminology

### Consistent Terms

| Term | Usage |
| ----------- | ---------------------------- |
| conda-forge | Always hyphenated, lowercase |
| Anaconda | Capitalized |
| environment | Lowercase |
| package | Lowercase |
| CLI | All caps |

### Command Examples

- Use `conda-forge-converter` as the command name
- Show both short and long options: `-s, --source`
- Include examples with and without optional parameters

## Writing Style

### Tone

- Professional but approachable
- Direct and clear
- Active voice preferred
- Present tense for current features

### Language

- Use American English spelling
- Avoid jargon unless necessary
- Define technical terms on first use
- Use consistent terminology throughout

## Documentation Types

### User Documentation

- Focus on how to use the tool
- Include practical examples
- Explain concepts clearly
- Provide troubleshooting guidance

### Developer Documentation

- Include technical details
- Explain design decisions
- Document APIs and interfaces
- Provide contribution guidelines

### API Documentation

- Document all public functions and classes
- Include parameter descriptions
- Provide return value information
- Include usage examples

## Maintenance

### Review Process

1. Self-review for clarity and completeness
1. Technical review for accuracy
1. Editorial review for style and consistency

### Versioning

- Keep documentation in sync with code
- Update documentation with each release
- Mark deprecated features clearly
- Document breaking changes

## Tools and Resources

### Documentation Tools

- MkDocs for building documentation
- Material theme for styling
- Mermaid for diagrams
- Pre-commit hooks for linting

### Useful Resources

- [Markdown Guide](https://www.markdownguide.org/)
- [MkDocs Documentation](https://www.mkdocs.org/)
- [Mermaid Documentation](https://mermaid-js.github.io/mermaid/)
- [Technical Writing Guide](https://developers.google.com/tech-writing)
