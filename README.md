# 🕷️ SmartServices Web Scraping Microservice

[![Python](https://img.shields.io/badge/Python-3.9%2B-blue.svg)](https://www.python.org/downloads/)
[![Docker](https://img.shields.io/badge/Docker-Enabled-2496ED?logo=docker)](https://www.docker.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

> 🚀 A robust web scraping microservice with multi-browser support and PDF processing capabilities.

## 📑 Table of Contents

- [Features](#-features)
- [Requirements](#-requirements)
- [Installation](#-installation)
- [Project Structure](#-project-structure)
- [Configuration](#-configuration)
- [Usage](#-usage)
- [Testing](#-testing)
- [Docker Support](#-docker-support)

## ✨ Features

- 🌐 Multi-browser support (Chrome & Firefox)
- 📄 PDF processing and data extraction
- 🔄 Retry mechanisms for robust scraping
- 🛠️ Configurable logging system
- 🎯 Modular and extensible architecture
- 🐋 Docker containerization
- ⚡ Asynchronous task processing

## 📋 Requirements

- Python 3.9+
- Docker & Docker Compose (optional)
- Chrome/Firefox WebDriver
- Required Python packages (see `requirements/dev.txt`)

## 🚀 Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/j0k3rd-ss-webscraping-ms.git
cd j0k3rd-ss-webscraping-ms
```

2. Set up your environment:
```bash
cp env-example .env
chmod +x install.sh
./install.sh
```

3. Install dependencies:
```bash
pip install -r requirements/dev.txt
```

## 📁 Project Structure

```
j0k3rd-ss-webscraping-ms/
├── 🐳 Dockerfile            # Docker configuration
├── 📜 boot.sh              # Boot script
├── 🔧 docker-compose.yml   # Docker Compose configuration
├── 📝 env-example          # Environment variables template
├── src/
│   ├── 🎯 main.py         # Application entry point
│   ├── core/              # Core functionality
│   ├── services/          # Service layer
│   ├── utils/             # Utility functions
│   └── workers/           # Background tasks
└── tests/                 # Test suite
```

## ⚙️ Configuration

1. Copy the environment template:
```bash
cp env-example .env
```

2. Configure the following variables in `.env`:
```ini
BROWSER_TYPE=chrome
DEBUG_MODE=False
RETRY_ATTEMPTS=3
LOG_LEVEL=INFO
```

## 🔨 Usage

### Running with Python

```bash
python src/main.py
```

### Running with Docker

```bash
docker-compose up --build
```

## 🧪 Testing

Run the test suite:

```bash
pytest tests/
```

Run specific test files:

```bash
pytest tests/test_extract.py
pytest tests/test_scrap.py
```

## 🐳 Docker Support

Build the container:
```bash
docker build -t j0k3rd-webscraping .
```

Run with Docker Compose:
```bash
docker-compose up
```

## 🔒 Security Considerations

- ⚠️ Ensure proper rate limiting when scraping
- 🔐 Keep credentials secure in environment variables
- 📝 Review and respect robots.txt
- 🛡️ Use proxy rotation when necessary

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License.

## ✍️ Authors

- **j0k3rD** - *Initial work* - [YourGithub](https://github.com/j0k3rD)

## 📮 Contact

- GitHub: [@j0k3rD](https://github.com/j0k3rD)

---

⭐ Consider starring this repo if you find it helpful!
