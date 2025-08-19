# k8s-assist 🤖

> **Intelligent Kubernetes Assistant powered by Llama** - Transform natural language into kubectl commands with smart analysis and troubleshooting

kubectl-ai is an intelligent Kubernetes assistant that converts natural language queries into kubectl commands and provides comprehensive cluster analysis. It combines the power of Llama LLM with expert Kubernetes knowledge to help you troubleshoot, monitor, and manage your clusters effortlessly.

## ✨ Features

### 🧠 **Intelligent Command Generation**
- **Natural Language Processing** - Ask questions in plain English
- **Llama Integration** - Powered by Ollama for smart command generation
- **Context Awareness** - Automatically detects pod names, namespaces, and resources
- **Safety First** - Only executes read-only commands to protect your cluster

### 🔧 **Advanced Troubleshooting**
- **Smart Workflows** - Predefined troubleshooting sequences for common issues
- **Pattern Detection** - K8sGPT-style intelligent issue identification
- **Root Cause Analysis** - Deep dive into problems with actionable recommendations
- **Multi-layered Analysis** - Pod, node, and cluster-level health assessment

### 📊 **Comprehensive Analysis**
- **Cluster Health Assessment** - Overall cluster status and recommendations
- **Resource Usage Analysis** - Memory, CPU, and performance monitoring
- **Failing Pod Detection** - Identify and analyze problematic workloads
- **Event Analysis** - Parse cluster events for errors and warnings

### 💬 **User-Friendly Interface**
- **Interactive CLI** - Rich console interface with helpful prompts
- **One-shot Mode** - Single command execution for scripts and automation
- **Conversational** - Handle greetings, help requests, and follow-up questions

## 🚀 Quick Start

### Prerequisites

- **Python 3.8+**
- **kubectl** configured and connected to your cluster
- **Ollama** with Llama model installed

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/kubectl-ai.git
cd kubectl-ai

# Install the package
make agent
# or
pip install -e .

# Create a demo cluster (optional)
make cluster
make bootstrap
```

### Setup Ollama

```bash
# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Pull Llama model
ollama pull llama3

# Verify installation
ollama list
```

### First Run

```bash
# Interactive mode
k8s-ai

# One-shot mode
k8s-ai "What pods are failing in my cluster?"
```

## 📋 Usage Examples

### 🏥 Cluster Health & Assessment

```bash
# Check overall cluster health
k8s-ai "What issues does my cluster have?"
k8s-ai "Give me a cluster assessment"
k8s-ai "Anything I need to improve?"

# Node health analysis
k8s-ai "Show me node status"
k8s-ai "Which nodes have problems?"
k8s-ai "Check node resource usage"
```

### 🔧 Pod Troubleshooting

```bash
# Debug specific pods
k8s-ai "Why is my nginx-pod crashing?"
k8s-ai "test pod won't start in staging"
k8s-ai "Debug failing pods in production"

# General pod issues
k8s-ai "What pods are failing?"
k8s-ai "Show me pods that are not running"
k8s-ai "Why won't my deployment start?"
```

### 📊 Resource Analysis

```bash
# Resource usage queries
k8s-ai "Which pods use most memory?"
k8s-ai "Show me node performance"
k8s-ai "Check resource usage in production namespace"
k8s-ai "What pods are consuming CPU?"
```

### 📋 Information Gathering

```bash
# Basic cluster information
k8s-ai "How many pods are running?"
k8s-ai "List pods in staging namespace"
k8s-ai "Show me all deployments"
k8s-ai "What namespaces exist?"

# Recent activity
k8s-ai "What deployments happened yesterday?"
k8s-ai "Show me events from last 24 hours"
k8s-ai "Recent activity in the cluster"
```

## 🏗️ Architecture

```
kubectl-ai/
├── kubectl_ai/
│   ├── main_agent.py          # Core agent logic with Llama integration
│   ├── llama_integration.py   # Llama command generation and processing
│   ├── query_detection.py     # Query type classification
│   ├── entity_extraction.py   # Pod/namespace detection
│   ├── analysis_engine.py     # Intelligent analysis and pattern detection
│   ├── workflows.py           # Predefined troubleshooting workflows
│   ├── safety.py              # Command safety validation
│   ├── utils.py               # Utilities and caching
│   ├── interactive_cli_new.py # Rich CLI interface
│   └── cli_new.py             # CLI entry point
├── manifests/                 # Demo Kubernetes manifests
├── requirements.txt           # Python dependencies
└── setup.py                   # Package configuration
```

### Key Components

**🧠 Smart Query Processing**
- **Query Detection** - Classifies queries into categories (troubleshooting, assessment, resource, etc.)
- **Entity Extraction** - Automatically detects pod names, namespaces, and resources from natural language
- **Llama Integration** - Uses Ollama to generate appropriate kubectl commands

**🔧 Analysis Engine**
- **Pattern Detection** - Identifies common Kubernetes issues and anti-patterns
- **Multi-layer Analysis** - Cluster, node, and pod-level health assessment
- **Root Cause Analysis** - Traces problems to their source with actionable fixes

**🛡️ Safety & Reliability**
- **Read-only Commands** - Only executes safe kubectl commands (get, describe, logs, top)
- **Command Validation** - Blocks destructive operations and validates command syntax
- **Error Handling** - Graceful handling of kubectl failures and network issues

## 🎯 Query Types

kubectl-ai automatically detects and handles different types of queries:

### Assessment Queries
- Cluster health evaluation
- Issue identification and recommendations
- Node status analysis
- Overall performance assessment

### Troubleshooting Queries
- Pod crash debugging
- Container startup failures
- Service connectivity issues
- Resource constraint problems

### Resource Queries
- Memory and CPU usage analysis
- Resource consumption patterns
- Performance bottleneck identification
- Capacity planning insights

### Informational Queries
- Pod and deployment listings
- Namespace exploration
- Recent activity tracking
- Configuration discovery

## 🔒 Security & Safety

kubectl-ai is designed with security as a priority:

- ✅ **Read-only Operations** - Never executes destructive commands
- ✅ **Command Validation** - All commands are validated before execution
- ✅ **Safe Defaults** - Conservative approach to cluster interactions
- ✅ **No Credential Storage** - Uses existing kubectl configuration
- ✅ **Audit Trail** - All commands and outputs are logged

### Blocked Operations
- `delete`, `apply`, `create`, `edit`, `patch`, `replace`, `scale`
- Commands with invalid or dangerous flags
- Anything that could modify cluster state

## 🛠️ Development

### Project Structure

```bash
# Install in development mode
pip install -e .

# Run tests (if available)
pytest tests/

# Check code quality
black kubectl_ai/
flake8 kubectl_ai/
```

### Adding New Features

1. **Query Types** - Add new patterns in `query_detection.py`
2. **Analysis** - Extend analysis functions in `analysis_engine.py`
3. **Workflows** - Add troubleshooting sequences in `workflows.py`
4. **Safety** - Update validation rules in `safety.py`

### Makefile Commands

```bash
make agent      # Install the package
make cluster    # Create kind demo cluster
make bootstrap  # Deploy demo workloads
make destroy    # Delete demo cluster
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

### Development Setup

```bash
git clone https://github.com/yourusername/kubectl-ai.git
cd kubectl-ai
pip install -e .
pip install -r requirements-dev.txt  # if available
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Ollama** - For providing the local LLM infrastructure
- **Rich** - For beautiful terminal formatting
- **Kubernetes Community** - For the amazing ecosystem
- **K8sGPT** - For inspiration on intelligent cluster analysis

## 🔮 Roadmap

- [ ] **Multi-cluster Support** - Manage multiple Kubernetes clusters
- [ ] **Web Interface** - Browser-based UI for team collaboration
- [ ] **Plugin Architecture** - Extensible plugin system
- [ ] **Prometheus Integration** - Enhanced metrics and monitoring
- [ ] **CI/CD Integration** - Automated cluster health checks
- [ ] **Mobile App** - Basic mobile interface for critical alerts

## 📞 Support

- **Issues** - [GitHub Issues](https://github.com/yourusername/kubectl-ai/issues)
- **Discussions** - [GitHub Discussions](https://github.com/yourusername/kubectl-ai/discussions)
- **Documentation** - Check the `/docs` folder (coming soon)

---

**Made with ❤️ for the Kubernetes community**