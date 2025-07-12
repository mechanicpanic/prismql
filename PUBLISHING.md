# Publishing Guide

This document describes how to publish PrismQL to PyPI.

## Prerequisites

1. **Environment Setup**:
   ```bash
   uv sync --dev
   ```

2. **PyPI Account**: You need access to the PrismQL PyPI project

3. **GitHub Secrets**: The following secrets must be configured:
   - `PYPI_API_TOKEN`: API token for PyPI publishing
   - `CODECOV_TOKEN`: Token for code coverage reporting

## Development Workflow

### Before Every Commit

```bash
# Format and lint code
uv run ruff format .
uv run ruff check . --fix

# Type checking
uv run mypy src/prismql

# Run tests
uv run pytest
```

### Pre-commit Hooks (Recommended)

Install pre-commit hooks to automate checks:

```bash
uv run pre-commit install
```

This will automatically run formatting, linting, and type checking before each commit.

## Release Process

### Manual Release

1. **Prepare Release**:
   ```bash
   # Ensure you're on main and up to date
   git checkout main
   git pull origin main
   
   # Run full test suite
   uv run pytest --cov=prismql
   
   # Check code quality
   uv run ruff format .
   uv run ruff check .
   uv run mypy src/prismql
   ```

2. **Build and Test**:
   ```bash
   # Clean previous builds
   rm -rf dist/
   
   # Build package
   uv build
   
   # Check package
   uv run python -m twine check dist/*
   ```

3. **Release**:
   ```bash
   # Use the release script
   python scripts/release.py 0.2.0
   
   # Or manually create tag
   git tag v0.2.0
   git push origin v0.2.0
   ```

### Automated Release

The release process is automated via GitHub Actions:

1. **Push a tag** to trigger the release:
   ```bash
   git tag v0.2.0
   git push origin v0.2.0
   ```

2. **GitHub Actions will**:
   - Run the full test suite on multiple Python versions
   - Build the package
   - Create a GitHub release
   - Publish to PyPI

## Version Management

PrismQL follows [Semantic Versioning](https://semver.org/):

- **MAJOR** version for incompatible API changes
- **MINOR** version for backward-compatible functionality
- **PATCH** version for backward-compatible bug fixes

Update the version in `pyproject.toml` before releasing:

```toml
[project]
version = "0.2.0"
```

## Testing the Release

### Test on TestPyPI (Optional)

```bash
# Build package
uv build

# Upload to TestPyPI
uv run python -m twine upload --repository testpypi dist/*

# Test installation
pip install --index-url https://test.pypi.org/simple/ prismql
```

### Test Local Installation

```bash
# Install from local wheel
uv pip install dist/prismql-*.whl

# Test import
python -c "import prismql; print(prismql.__version__)"
```

## Troubleshooting

### Build Issues

- **Missing files**: Check `tool.hatch.build.targets.sdist.include` in `pyproject.toml`
- **Import errors**: Ensure all dependencies are listed in `dependencies`

### Publishing Issues

- **Authentication**: Check PyPI API token in GitHub secrets
- **Permissions**: Ensure you have publish permissions on the PyPI project

### CI/CD Issues

- **Test failures**: All tests must pass before publishing
- **Lint/format issues**: Code must pass ruff and mypy checks

## Monitoring

After release:

1. **Check PyPI**: Verify the package appears on [PyPI](https://pypi.org/project/prismql/)
2. **Test installation**: `pip install prismql`
3. **Monitor downloads**: Check PyPI download stats
4. **Watch for issues**: Monitor GitHub issues for bug reports