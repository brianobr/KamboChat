# uv Commands Quick Reference

This guide provides quick reference for common uv commands used in the Kambo Chatbot project.

## Installation

### Install uv
```bash
# Windows (PowerShell)
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh
```

## Project Setup

### Install dependencies
```bash
# Install all dependencies
uv sync

# Install with development dependencies
uv sync --dev

# Install with all optional dependencies
uv sync --all-extras
```

### Create virtual environment
```bash
# Create virtual environment
uv venv

# Activate virtual environment
# On Windows:
.venv\Scripts\activate
# On macOS/Linux:
source .venv/bin/activate
```

## Running the Application

### Run with uv
```bash
# Run main application
uv run python main.py

# Run tests
uv run python test_api.py
uv run python test_explicit_graph.py
uv run python test_langchain.py

# Run setup scripts
uv run python setup_key_vault.py
```

### Run with virtual environment
```bash
# Activate virtual environment first
source .venv/bin/activate  # or .venv\Scripts\activate on Windows

# Then run normally
python main.py
```

## Package Management

### Add new dependencies
```bash
# Add to main dependencies
uv add package-name

# Add to development dependencies
uv add --dev package-name

# Add specific version
uv add "package-name>=1.0.0"
```

### Remove dependencies
```bash
# Remove package
uv remove package-name
```

### Update dependencies
```bash
# Update all dependencies
uv sync --upgrade

# Update specific package
uv add --upgrade package-name
```

### List dependencies
```bash
# Show installed packages
uv pip list

# Show dependency tree
uv tree
```

## Development Tools

### Run tests
```bash
# Run all tests
uv run pytest

# Run specific test file
uv run pytest test_api.py

# Run with coverage
uv run pytest --cov=src
```

### Code formatting
```bash
# Format code with black
uv run black src/

# Check formatting
uv run black --check src/
```

### Linting
```bash
# Run flake8
uv run flake8 src/

# Run mypy (if configured)
uv run mypy src/
```

## Troubleshooting

### Clear cache
```bash
# Clear uv cache
uv cache clean
```

### Reinstall dependencies
```bash
# Remove lock file and reinstall
rm uv.lock
uv sync
```

### Check uv version
```bash
uv --version
```

### Get help
```bash
uv --help
uv sync --help
uv add --help
```

## Migration from pip

### Convert requirements.txt to pyproject.toml
```bash
# Install dependencies from requirements.txt
uv pip install -r requirements.txt

# Generate pyproject.toml
uv init --name kambo-chatbot --python 3.11
```

### Install from requirements.txt
```bash
# Install from requirements.txt (temporary)
uv pip install -r requirements.txt
```

## Environment Variables

### Set environment variables
```bash
# Set for current session
export OPENAI_API_KEY=your_key_here

# Or use .env file
echo "OPENAI_API_KEY=your_key_here" > .env
```

## Azure Deployment

### Install for production
```bash
# Install production dependencies only
uv sync --production
```

### Generate requirements.txt for deployment
```bash
# Export dependencies to requirements.txt
uv pip freeze > requirements.txt
```

## Best Practices

1. **Always use `uv sync`** instead of `pip install -r requirements.txt`
2. **Use `uv run`** to run scripts with the correct environment
3. **Keep `pyproject.toml`** as the source of truth for dependencies
4. **Use virtual environments** for development isolation
5. **Commit `uv.lock`** to version control for reproducible builds 