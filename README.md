# AI Dev Companion

> **Next-Generation AI Code Analysis & Improvement System**  
> A production-ready, serverless multi-agent system that analyzes, explains, and **automatically improves** Kotlin code using AWS Bedrock (Claude 3). Includes a native Android client.

[![Deploy](https://github.com/Amehran/AIDevCompanionDev/workflows/Deploy%20to%20AWS%20Lambda%20(Container)/badge.svg)](https://github.com/Amehran/AIDevCompanionDev/actions)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/)
[![Kotlin](https://img.shields.io/badge/kotlin-1.9-purple.svg)](https://kotlinlang.org/)

---

## 🚀 Overview

**AI Dev Companion** goes beyond simple code completion. It employs a **Multi-Agent Architecture** where specialized AI agents (Syntax, Security, Performance) collaborate to provide deep, expert-level analysis of your code.

Unlike standard chatbots, this system maintains **conversational context**, allowing you to discuss the findings, ask for explanations, and **apply fixes automatically** through an interactive dialogue.

### ✨ Key Features

- **🤖 Multi-Agent Swarm**: Three specialized agents analyze code in parallel for comprehensive coverage.
- **🛠️ Automated Improvements**: The system can rewrite your code to fix security vulnerabilities, performance bottlenecks, and style issues upon request.
- **📱 Native Android Client**: A full-featured Jetpack Compose app to take your AI companion on the go.
- **🧠 Contextual Memory**: Remembers previous turns in the conversation for a natural, flowing dialogue.
- **☁️ Serverless Architecture**: Built on AWS Lambda with container images, scaling to 1000+ concurrent requests with zero infrastructure management.
- **⚡ Real-time Streaming**: Powered by AWS Bedrock for fast, streaming responses.

---

## 🏗️ Architecture

The system uses a swarm of agents orchestrated to deliver a unified analysis report.

```mermaid
graph TB
    Client[Client (Web/Android)] -->|POST /chat| Lambda[AWS Lambda]
    Lambda -->|Parallel Invocation| Swarm[Agent Swarm]
    
    subgraph "Agent Swarm"
        Syntax[Syntax Agent]
        Security[Security Agent]
        Perf[Performance Agent]
    end
    
    Swarm -->|Findings| Orch[Orchestrator]
    Orch -->|Synthesized Report| Lambda
    Lambda -->|JSON Response| Client
    
    Swarm & Orch -->|LLM Calls| Bedrock[AWS Bedrock - Claude 3]
```

For a deep dive into the design patterns and decisions, see [**ARCHITECTURE.md**](./ARCHITECTURE.md).

---

## ⚡ Quick Start

### Backend Setup

1. **Prerequisites**: Python 3.11+, Docker, AWS Account.
2. **Clone & Install**:
   ```bash
   git clone https://github.com/Amehran/AIDevCompanionDev.git
   cd AIDevCompanionDev
   python3 -m venv .venv && source .venv/bin/activate
   pip install -r requirements-aws.txt
   ```
3. **Run Locally**:
   ```bash
   ./scripts/local_run.sh
   ```
   The API will be available at `http://localhost:8000`.

### Android Client

The project includes a modern Android application built with Jetpack Compose.
See [**android-client/README.md**](./android-client/README.md) for installation instructions.

---

## 📖 Usage Guide

### 1. Code Analysis
Send Kotlin code to the API to receive a structured analysis.

**Request:**
```bash
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "source_code": "fun main() { val password = \"secret123\" }"
  }'
```

**Response:**
```json
{
  "summary": "Analysis complete. Found 1 critical security issue.",
  "issues": [
    {
      "type": "SECURITY",
      "description": "Hardcoded credentials detected",
      "suggestion": "Use environment variables"
    }
  ],
  "conversation_id": "550e8400-e29b-..."
}
```

### 2. Interactive Improvements
You can ask the AI to fix the issues found.

**Request:**
```bash
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "conversation_id": "550e8400-e29b-...",
    "message": "Fix the security issue",
    "apply_improvements": true
  }'
```

**Response:**
```json
{
  "summary": "Code improvements applied successfully.",
  "improved_code": "fun main() { val password = System.getenv(\"PASSWORD\") }",
  "awaiting_user_input": false
}
```

---

## 🧪 Testing

The project maintains high test coverage using `pytest`.

```bash
# Run all tests
pytest

# Run specific suite
pytest tests/test_crew.py -v
```

See [**TESTING.md**](./TESTING.md) for detailed testing strategies.

---

## 🛠️ Tech Stack

| Component | Technology |
|-----------|------------|
| **Backend** | FastAPI, Python 3.11 |
| **AI / LLM** | AWS Bedrock (Claude 3 Sonnet) |
| **Orchestration** | Custom Multi-Agent Swarm |
| **Mobile** | Android (Kotlin, Jetpack Compose) |
| **Infrastructure** | AWS Lambda (Docker), ECR |
| **CI/CD** | GitHub Actions |

---

## 🗺️ Roadmap

- [x] **Multi-Agent Analysis**
- [x] **Contextual Conversation**
- [x] **Automated Code Improvements**
- [x] **Android Client**
- [ ] **RAG Integration** (Vector DB for knowledge retrieval)
- [ ] **IDE Plugin** (IntelliJ/VS Code)
- [ ] **User Authentication** (Cognito/Auth0)

---

## 🤝 Contributing

Contributions are welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) for details on our code of conduct and the process for submitting pull requests.

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

**Built with ❤️ by [Armin Mehran](https://github.com/Amehran)**
