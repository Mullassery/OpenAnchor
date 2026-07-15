# Contributing to OpenAnchor

Thank you for your interest in contributing to OpenAnchor! This document provides guidelines and instructions for contributing.

## Code of Conduct

Be respectful, inclusive, and professional in all interactions. We are committed to providing a welcoming and inclusive environment for all contributors.

## Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/YOUR_USERNAME/openanchor.git
   cd openanchor
   ```
3. **Create a development environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -e ".[dev]"
   ```
4. **Install pre-commit hooks**:
   ```bash
   pre-commit install
   ```

## Development Workflow

### Before You Start
- Create an issue to discuss your proposed changes
- Ensure you're working on the latest `main` branch
- Create a feature branch: `git checkout -b feature/your-feature-name`

### Code Style

We follow these standards:

- **Formatting**: Black (100 char line length)
- **Linting**: Ruff
- **Type Checking**: mypy (strict mode preferred)
- **Security**: bandit

### Running Checks Locally

```bash
# Run all checks
make all

# Run individually
make lint      # Ruff, Black, mypy
make format    # Auto-format code
make test      # Run tests with coverage
make security  # Bandit, safety checks
```

Pre-commit hooks will run these checks automatically on commit.

## Testing Requirements

- All new features must include tests
- Minimum coverage: 80%
- Run tests before submitting PR:
  ```bash
  make test
  ```

## Commit Messages

Follow these conventions:

```
type: short description (50 chars max)

Longer explanation if needed (wrap at 72 chars).
Explain what and why, not how.

- Use bullet points for multiple changes
- Reference issues: Fixes #123
- Reference PRs: Related to #456
```

**Types:**
- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation
- `test:` Tests
- `refactor:` Code reorganization
- `perf:` Performance improvement
- `chore:` Maintenance, dependencies

## Pull Request Process

1. **Create PR** with clear title and description
2. **Link issues** with "Fixes #123"
3. **Provide context** about what changed and why
4. **Run tests locally** before pushing
5. **Keep PR focused** - one feature per PR
6. **Respond to reviews** promptly
7. **Update based on feedback**

## PR Requirements

Your PR will be checked automatically for:
- ✅ Code style (Black, Ruff)
- ✅ Type safety (mypy)
- ✅ Tests (80%+ coverage)
- ✅ Security (bandit)
- ✅ Documentation

## Documentation

- Update README.md if adding features
- Add docstrings to new functions/classes
- Follow Google-style docstrings:
  ```python
  def function(arg1, arg2):
      """Short description.
      
      Longer description if needed.
      
      Args:
          arg1: Description of arg1
          arg2: Description of arg2
          
      Returns:
          Description of return value
          
      Raises:
          ValueError: When something is wrong
      """
  ```

## Reporting Issues

When reporting bugs, include:
- Python version and OS
- Steps to reproduce
- Expected vs actual behavior
- Error messages/tracebacks
- Minimal reproducible example

## Questions?

- Open an issue with the `question` label
- Check existing issues and discussions
- Read the documentation

## Thank You!

Your contributions make OpenAnchor better for everyone. Thank you for your effort!

---

**Happy coding! 🚀**
