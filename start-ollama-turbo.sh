#!/bin/bash
# Start the Ollama Turbo proxy server for OpenCode

echo "Starting Ollama Turbo Proxy Server..."
echo "=================================="
echo ""

# Check if proxy is already running
if pgrep -f ollama_cli_proxy.py > /dev/null; then
    echo "✓ Proxy is already running"
else
    echo "Starting proxy server..."
    uv run python ollama_cli_proxy.py > cli_proxy.log 2>&1 &
    PID=$!
    sleep 2
    
    # Check if it started successfully
    if curl -s http://localhost:8080/health | jq -e '.status == "healthy"' > /dev/null 2>&1; then
        echo "✓ Proxy started successfully (PID: $PID)"
    else
        echo "✗ Failed to start proxy server"
        exit 1
    fi
fi

echo ""
echo "You can now use OpenCode with Ollama Turbo:"
echo "  opencode run --model ollama-turbo/gpt-oss:20b \"Your prompt\""
echo "  opencode run --model ollama-turbo/gpt-oss:120b \"Your prompt\""
echo ""
echo "To stop the proxy: pkill -f ollama_cli_proxy.py"
echo ""