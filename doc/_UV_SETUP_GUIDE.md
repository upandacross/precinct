# UV Virtual Environment Setup for Precinct App

This project uses [UV](https://github.com/astral-sh/uv) as the primary package and virtual environment manager. UV is significantly faster than pip and provides better dependency resolution.

## Quick Start

### 1. Initial Setup
```bash
# Run the setup script (installs UV if needed and sets up environment)
./setup-uv.sh

# For development setup (adds dev dependencies and tools)
./setup-dev.sh
```

### 2. Running the Application
```bash
# Start the Flask application
./run-app.sh

# Or manually with UV
uv run python main.py
```

### 3. Running Tests
```bash
# Run all tests
./run-tests.sh

# Or manually with UV
uv run pytest

# Run specific test file
uv run pytest test/test_specific.py
```

## UV Commands Reference

### Environment Management
```bash
# Create virtual environment with specific Python version
uv venv --python 3.11

# Activate environment (manual activation)
source .venv/bin/activate

# Sync dependencies from pyproject.toml
uv sync

# Sync with development dependencies
uv sync --group dev
```

### Package Management
```bash
# Add a new dependency
uv add package-name

# Add development dependency
uv add --group dev package-name

# Remove a dependency
uv remove package-name

# Update all packages
uv sync --upgrade

# Show installed packages
uv pip list
```

### Running Python Scripts
```bash
# Run any Python script with UV environment
uv run python script.py

# Run with arguments
uv run python script.py --arg value

# Run pytest
uv run pytest

# Run Flask commands
uv run flask --help
```

### Code Quality Tools
```bash
# Format code with Black
uv run black .

# Sort imports with isort
uv run isort .

# Lint with flake8
uv run flake8 .

# Type checking with mypy
uv run mypy .
```

## Project Structure for UV

```
precinct/
├── pyproject.toml          # Project configuration and dependencies
├── uv.lock                 # Locked dependency versions
├── .uvpython              # Python version specification
├── .venv/                 # Virtual environment (auto-created)
├── setup-uv.sh           # Initial UV setup script
├── setup-dev.sh          # Development environment setup
├── run-app.sh             # Application runner script
├── run-tests.sh           # Test runner script
└── requirements.txt       # Legacy requirements (for reference)
```

## Key Benefits of UV

1. **Speed**: UV is 10-100x faster than pip for package installation
2. **Reliability**: Better dependency resolution prevents conflicts
3. **Simplicity**: Single tool for environments and packages
4. **Compatibility**: Works with existing pip/requirements.txt workflows
5. **Modern**: Built in Rust with performance as a priority

## Migration from Traditional venv/pip

UV maintains compatibility with existing Python projects:
- Existing `requirements.txt` files work with `uv pip install -r requirements.txt`
- Virtual environments created by UV are standard Python venvs
- All existing Python tooling works normally within UV environments

## Troubleshooting

### UV Not Found
```bash
# Install UV
curl -LsSf https://astral.sh/uv/install.sh | sh
# or
pip install uv
```

### Environment Issues
```bash
# Remove and recreate environment
rm -rf .venv
./setup-uv.sh
```

### Dependency Conflicts
```bash
# Clear lock file and resync
rm uv.lock
uv sync
```

### Port Already in Use
```bash
# Kill processes on port 5000
lsof -ti:5000 | xargs kill -9
```

## Configuration Files

### pyproject.toml
Contains all project metadata, dependencies, and tool configurations.

### uv.lock
Lock file with exact dependency versions for reproducible builds.

### .uvpython
Specifies the Python version for this project (3.11).

## Environment Variables

The app uses environment variables from `.env` file:
- Database connection settings
- Flask configuration
- Security settings

Make sure to copy `.env.example` to `.env` and configure appropriately.

## Continuous Integration

For CI/CD pipelines, use:
```yaml
- name: Install UV
  run: curl -LsSf https://astral.sh/uv/install.sh | sh

- name: Install dependencies
  run: uv sync

- name: Run tests
  run: uv run pytest
```

This ensures consistent, fast dependency installation across all environments.