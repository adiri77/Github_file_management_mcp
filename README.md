# MCP (Master Control Program)

A professional Python-based command-line tool for GitHub repository management.

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-passing-brightgreen.svg)](tests/)

## 🚀 Features

- **Clone GitHub repositories** to local directories
- **Push changes** from local repositories to GitHub
- **Create files** in specific repository sections (subdirectories)
- **Cross-platform compatibility** (Windows, macOS, Linux)
- **Secure authentication** using GitHub personal access tokens
- **Comprehensive error handling** and logging
- **Dry-run mode** for testing operations without making changes
- **Professional package structure** with proper Python packaging

## 📦 Installation

### Option 1: Development Installation

```bash
# Clone the repository
git clone <repository-url>
cd MCPTool

# Install dependencies
pip install -r requirements.txt

# Install in development mode
pip install -e .
```

### Option 2: Direct Installation

```bash
pip install -r requirements.txt
python setup.py install
```

## ⚙️ Quick Setup

1. **Initialize configuration:**
   ```bash
   mcp init
   ```

2. **Or use environment variables:**
   ```bash
   cp config/.env.example .env
   # Edit .env and add your GitHub token
   ```

## 🎯 Usage

```bash
# Clone a repository
mcp clone https://github.com/user/repo.git ./my-project

# Create files in specific sections
mcp add-file ./my-project src/utils helper.py
mcp add-file ./my-project tests test_helper.py

# Push changes
mcp push ./my-project "Added helper utilities and tests"
```

## 📁 Project Structure

```
MCPTool/
├── mcp/                    # Main package
│   ├── __init__.py        # Package initialization
│   ├── cli.py             # Command-line interface
│   ├── config.py          # Configuration management
│   ├── git_ops.py         # Git operations
│   ├── file_ops.py        # File operations
│   └── logger.py          # Logging utilities
├── tests/                  # Test suite
│   ├── __init__.py
│   └── test_mcp.py        # Unit tests
├── docs/                   # Documentation
│   └── README.md          # Detailed documentation
├── config/                 # Configuration files
│   ├── .env.example       # Environment variables template
│   └── README.md          # Configuration guide
├── scripts/                # Utility scripts
├── mcp.py                 # Main entry point
├── setup.py               # Package setup
├── requirements.txt       # Dependencies
└── README.md              # This file
```

## 🧪 Testing

```bash
# Run all tests
python -m pytest tests/ -v

# Run with coverage
python -m pytest tests/ --cov=mcp --cov-report=html

# Run specific test
python -m pytest tests/test_mcp.py::TestMCPConfig -v
```

## 📚 Documentation

- **[Full Documentation](docs/README.md)** - Complete user guide
- **[Configuration Guide](config/README.md)** - Setup instructions
- **[API Reference](mcp/)** - Code documentation

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run the test suite
6. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🔧 Development

### Setting up development environment

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Format code
black mcp/ tests/

# Lint code
flake8 mcp/ tests/

# Type checking
mypy mcp/
```

## 🐛 Troubleshooting

For common issues and solutions, see the [troubleshooting section](docs/README.md#troubleshooting) in the full documentation.

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/your-username/mcp-tool/issues)
- **Documentation**: [docs/README.md](docs/README.md)
- **Configuration Help**: [config/README.md](config/README.md)
#   G i t h u b _ f i l e _ m a n a g e m e n t _ m c p  
 #   G i t h u b _ f i l e _ m a n a g e m e n t _ m c p  
 