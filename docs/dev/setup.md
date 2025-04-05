# Development Setup

This guide provides instructions for setting up a development environment for the Conda-Forge Converter project.

## Prerequisites

- Python 3.8 or higher
- Git
- A code editor (VS Code recommended)
- Conda or Miniconda installed

## Setting Up the Development Environment

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/conda-forge-converter.git
cd conda-forge-converter
```

### 2. Create a Virtual Environment

```bash
# Using venv
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Or using conda
conda create -n conda-forge-converter python=3.11
conda activate conda-forge-converter
```

### 3. Install Development Dependencies

```bash
# Install development tools
pipx install uv
pipx install pre-commit

# Install project dependencies
./scripts/setup_dev.sh

# Or manually
pip install -e ".[dev]"
```

### 4. Set Up Pre-commit Hooks

```bash
pre-commit install
```

## Development Workflow

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src

# Run specific test file
pytest tests/test_env_detector.py
```

### Code Quality Tools

```bash
# Run linting
ruff check .

# Run type checking
mypy src

# Run all checks
pre-commit run --all-files
```

### Building Documentation

```bash
# Install documentation dependencies
pip install mkdocs mkdocs-material mkdocstrings

# Serve documentation locally
mkdocs serve
```

## Project Structure

```text
conda-forge-converter/
├── src/                  # Source code
│   ├── conda_forge_converter/  # Main package
│   └── tests/            # Test files
├── docs/                 # Documentation
├── scripts/              # Utility scripts
├── .pre-commit-config.yaml  # Pre-commit configuration
├── pyproject.toml        # Project configuration
└── README.md             # Project overview
```

## IDE Configuration

### VS Code

Recommended extensions:

- Python
- Pylance
- Ruff
- Markdown All in One

Recommended settings (`.vscode/settings.json`):

```json
{
  "python.linting.enabled": true,
  "python.linting.lintOnSave": true,
  "python.formatting.provider": "black",
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.organizeImports": true
  }
}
```

## Troubleshooting

### Common Issues

1. **Pre-commit hooks failing**

   - Run `pre-commit clean` to clear cache
   - Run `pre-commit run --all-files` to see detailed errors

1. **Type checking errors**

   - Ensure you have the correct type stubs installed
   - Check for missing imports in `pyproject.toml`

1. **Documentation build issues**

   - Ensure all required packages are installed
   - Check for broken links in documentation

## Next Steps

- Read the [Contributing Guide](contributing.md)
- Review the [Architecture Documentation](architecture.md)
- Set up your [Testing Environment](testing.md)
