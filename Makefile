# Swarmia MCP Server Makefile

# Virtual environment configuration
VENV_DIR = venv
VENV_PYTHON = $(VENV_DIR)/bin/python
VENV_PIP = $(VENV_DIR)/bin/pip

.PHONY: help install test run clean check-env setup venv venv-create venv-activate venv-install

# Default target
help:
	@echo "Swarmia MCP Server - Available targets:"
	@echo ""
	@echo "  venv-create - Create a new virtual environment"
	@echo "  venv        - Create virtual environment and install dependencies"
	@echo "  install     - Install dependencies in virtual environment"
	@echo "  test        - Test the API connection and server functionality"
	@echo "  run         - Run the MCP server"
	@echo "  check-env   - Check if required environment variables are set"
	@echo "  setup       - Complete setup (venv + install + check-env)"
	@echo "  clean       - Clean up temporary files and virtual environment"
	@echo "  help        - Show this help message"
	@echo ""
	@echo "Environment variables:"
	@echo "  SWARMIA_API_TOKEN - Your Swarmia API token (required)"

# Check Python version
check-python:
	@echo "Checking Python version..."
	@python3 -c "import sys; exit(0 if sys.version_info >= (3, 8) else 1)" || \
		(echo "❌ Error: Python 3.8 or higher is required" && exit 1)
	@python3 -c "import sys; print('✅ Python version:', sys.version.split()[0])"

# Create virtual environment
venv-create: check-python
	@echo "🐍 Creating virtual environment..."
	@if [ -d "$(VENV_DIR)" ]; then \
		echo "⚠️  Virtual environment already exists at $(VENV_DIR)"; \
	else \
		python3 -m venv $(VENV_DIR); \
		echo "✅ Virtual environment created at $(VENV_DIR)"; \
	fi

# Install dependencies in virtual environment
venv-install: venv-create
	@echo "📦 Installing dependencies in virtual environment..."
	$(VENV_PIP) install --upgrade pip
	$(VENV_PIP) install -r requirements.txt
	@echo "✅ Dependencies installed successfully in virtual environment"

# Install dependencies (alias for venv-install)
install: venv-install

# Convenience target to create virtual environment only
venv: venv-create

# Check environment variables
check-env:
	@echo "Checking environment variables..."
	@if [ -f .env ]; then \
		echo "📄 Loading environment variables from .env file..."; \
		export $$(grep -v '^#' .env | xargs); \
	fi
	@if [ -z "$$SWARMIA_API_TOKEN" ]; then \
		echo "⚠️  Warning: SWARMIA_API_TOKEN environment variable is not set"; \
		echo "Please set your Swarmia API token in the .env file:"; \
		echo "SWARMIA_API_TOKEN=your_token_here"; \
		echo ""; \
		echo "You can get your API token from:"; \
		echo "https://app.swarmia.com/settings/api-tokens"; \
	else \
		echo "✅ SWARMIA_API_TOKEN is set"; \
	fi

# Complete setup
setup: install check-env
	@echo ""
	@echo "🎉 Setup complete!"
	@echo ""
	@echo "To activate the virtual environment:"
	@echo "  source $(VENV_DIR)/bin/activate"
	@echo ""
	@echo "To test the server:"
	@echo "  make test"
	@echo ""
	@echo "To run the MCP server:"
	@echo "  make run"

# Test the server
test: check-env
	@echo "🧪 Testing Swarmia MCP Server..."
	@if [ ! -d "$(VENV_DIR)" ]; then \
		echo "❌ Virtual environment not found. Run 'make setup' first."; \
		exit 1; \
	fi
	@if [ -f .env ]; then \
		env $$(grep -v '^#' .env | xargs) $(VENV_PYTHON) test_server.py; \
	else \
		$(VENV_PYTHON) test_server.py; \
	fi

# Run the MCP server
run: check-env
	@echo "🚀 Starting Swarmia MCP Server..."
	@if [ ! -d "$(VENV_DIR)" ]; then \
		echo "❌ Virtual environment not found. Run 'make setup' first."; \
		exit 1; \
	fi
	@if [ -f .env ]; then \
		env $$(grep -v '^#' .env | xargs) $(VENV_PYTHON) swarmia_mcp_server.py; \
	else \
		$(VENV_PYTHON) swarmia_mcp_server.py; \
	fi

# Clean up temporary files and virtual environment
clean:
	@echo "🧹 Cleaning up..."
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type f -name "*.pyo" -delete
	@if [ -d "$(VENV_DIR)" ]; then \
		echo "🗑️  Removing virtual environment..."; \
		rm -rf $(VENV_DIR); \
	fi
	@echo "✅ Cleanup complete"

# Development targets
dev-install: install
	@echo "📦 Installing development dependencies..."
	@if [ ! -d "$(VENV_DIR)" ]; then \
		echo "❌ Virtual environment not found. Run 'make setup' first."; \
		exit 1; \
	fi
	$(VENV_PIP) install -r requirements-dev.txt 2>/dev/null || echo "No dev requirements found"

# Format code (if black is available)
format:
	@if [ ! -d "$(VENV_DIR)" ]; then \
		echo "❌ Virtual environment not found. Run 'make setup' first."; \
		exit 1; \
	fi
	@if $(VENV_PYTHON) -c "import black" 2>/dev/null; then \
		echo "🎨 Formatting code with black..."; \
		$(VENV_PYTHON) -m black *.py; \
	else \
		echo "⚠️  black not found in virtual environment, skipping formatting"; \
	fi

# Lint code (if flake8 is available)
lint:
	@if [ ! -d "$(VENV_DIR)" ]; then \
		echo "❌ Virtual environment not found. Run 'make setup' first."; \
		exit 1; \
	fi
	@if $(VENV_PYTHON) -c "import flake8" 2>/dev/null; then \
		echo "🔍 Linting code with flake8..."; \
		$(VENV_PYTHON) -m flake8 *.py; \
	else \
		echo "⚠️  flake8 not found in virtual environment, skipping linting"; \
	fi

# Type check (if mypy is available)
type-check:
	@if [ ! -d "$(VENV_DIR)" ]; then \
		echo "❌ Virtual environment not found. Run 'make setup' first."; \
		exit 1; \
	fi
	@if $(VENV_PYTHON) -c "import mypy" 2>/dev/null; then \
		echo "🔍 Type checking with mypy..."; \
		$(VENV_PYTHON) -m mypy *.py; \
	else \
		echo "⚠️  mypy not found in virtual environment, skipping type checking"; \
	fi

# Run all quality checks
quality: format lint type-check

# Show project info
info:
	@echo "Swarmia MCP Server"
	@echo "=================="
	@echo "Python version: $$(python3 --version)"
	@echo "Project directory: $$(pwd)"
	@if [ -d "$(VENV_DIR)" ]; then \
		echo "Virtual environment: ✅ $(VENV_DIR)"; \
		echo "Virtual env Python: $$($(VENV_PYTHON) --version)"; \
	else \
		echo "Virtual environment: ❌ Not created (run 'make setup')"; \
	fi
	@echo "Files:"
	@ls -la *.py *.txt *.md *.json 2>/dev/null || echo "No matching files found"
