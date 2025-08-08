# OpenAI-Compatible Ollama Proxy

A lightweight proxy server that translates OpenAI API requests to Ollama CLI commands, enabling seamless integration with Ollama Turbo's cloud-hosted models through an OpenAI-compatible interface.

## Features

- **OpenAI API Compatibility**: Drop-in replacement for OpenAI's chat completion endpoint
- **Ollama CLI Integration**: Uses Ollama CLI for built-in SSH key authentication
- **Streaming Support**: Supports both streaming and non-streaming responses
- **Docker Support**: Ready-to-deploy Docker configuration
- **Cloud Model Access**: Direct access to Ollama Turbo's high-performance models (gpt-oss:20b, gpt-oss:120b)

## Prerequisites

- Python 3.11+
- Ollama CLI installed and configured with SSH keys
- Docker and Docker Compose (for containerized deployment)
- Access to Ollama Turbo (ollama.com)

## Installation

### Local Development

1. Clone the repository:
```bash
git clone <repository-url>
cd openai-compatible-proxy
```

2. Install dependencies using UV:
```bash
uv sync
```

Or with pip:
```bash
pip install -e .
```

3. Ensure Ollama CLI is configured:
```bash
ollama --version
OLLAMA_HOST=ollama.com ollama list
```

### Docker Deployment

1. Build and run with Docker Compose:
```bash
docker-compose up -d
```

The proxy will be available at `http://localhost:8080`

## Usage

### Starting the Server

#### Local:
```bash
python ollama_cli_proxy.py
```

#### With Shell Script:
```bash
./start-ollama-turbo.sh
```

#### With Docker:
```bash
docker-compose up
```

### API Endpoints

#### Chat Completions
```bash
curl -X POST http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-oss:20b",
    "messages": [
      {"role": "system", "content": "You are a helpful assistant."},
      {"role": "user", "content": "Hello!"}
    ],
    "stream": false
  }'
```

#### List Models
```bash
curl http://localhost:8080/v1/models
```

#### Health Check
```bash
curl http://localhost:8080/health
```

### Using with OpenAI SDK

```python
from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:8080/v1",
    api_key="not-needed"  # API key not required for Ollama
)

response = client.chat.completions.create(
    model="gpt-oss:20b",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "What is the capital of France?"}
    ]
)

print(response.choices[0].message.content)
```

## Configuration

### Environment Variables

- `OLLAMA_HOST`: Set to `ollama.com` for Ollama Turbo (default)
- `FLASK_ENV`: Set to `production` for production deployments

### Docker Volume Mounts

The Docker configuration requires mounting your Ollama SSH keys:
```yaml
volumes:
  - ~/.ollama:/root/.ollama:ro
```

This provides the container with read-only access to your Ollama authentication keys.

## Available Models

- `gpt-oss:20b` - 20 billion parameter model
- `gpt-oss:120b` - 120 billion parameter model

## Architecture

The proxy works by:
1. Accepting OpenAI-formatted API requests
2. Converting messages to Ollama CLI format
3. Executing Ollama CLI commands with proper authentication
4. Translating responses back to OpenAI format

This approach leverages Ollama CLI's built-in SSH key authentication, eliminating the need for manual token management.

## Development

### Running Tests
```bash
# Test the health endpoint
curl http://localhost:8080/health

# Test a simple completion
curl -X POST http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "gpt-oss:20b", "messages": [{"role": "user", "content": "Hi"}]}'
```

### Project Structure
```
openai-compatible-proxy/
├── ollama_cli_proxy.py    # Main proxy server
├── docker-compose.yml      # Docker composition
├── Dockerfile             # Container definition
├── pyproject.toml         # Python package configuration
├── start-ollama-turbo.sh  # Helper startup script
└── README.md              # This file
```

## Troubleshooting

### Ollama CLI Not Found
Ensure Ollama is installed and in your PATH:
```bash
which ollama
ollama --version
```

### Authentication Issues
Verify your SSH keys are properly configured:
```bash
ls ~/.ollama/
OLLAMA_HOST=ollama.com ollama list
```

### Docker Permission Issues
Ensure the Docker container can read your SSH keys:
```bash
ls -la ~/.ollama/
```

### Connection Timeouts
The proxy has default timeouts:
- Streaming: 30 seconds
- Non-streaming: 60 seconds

Adjust these in `ollama_cli_proxy.py` if needed for longer-running requests.

## Security Considerations

- SSH keys are mounted read-only in Docker
- No API keys are stored in the code
- All authentication is handled through Ollama's SSH mechanism
- The proxy binds to `0.0.0.0:8080` - restrict access as needed in production

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

[Specify your license here]

## Support

For issues or questions:
- Check the [Troubleshooting](#troubleshooting) section
- Open an issue on GitHub
- Contact Ollama support for Turbo-specific issues