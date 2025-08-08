#!/usr/bin/env python3
"""
OpenAI to Ollama CLI Proxy Server

This proxy uses the Ollama CLI to handle requests since it has
built-in authentication via SSH keys.
"""

from flask import Flask, request, jsonify, Response
import subprocess
import json
import logging
from datetime import datetime
import uuid
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Set OLLAMA_HOST environment variable
os.environ['OLLAMA_HOST'] = 'ollama.com'

@app.route('/v1/chat/completions', methods=['POST'])
def chat_completions():
    """Handle OpenAI-style chat completion requests using Ollama CLI"""
    try:
        # Get the request data
        data = request.json
        logger.info(f"Received request for model: {data.get('model')}")
        
        # Extract parameters
        model = data.get('model', 'gpt-oss:20b')
        messages = data.get('messages', [])
        stream = data.get('stream', False)
        temperature = data.get('temperature', 0.7)
        max_tokens = data.get('max_tokens', 500)
        
        # Build the prompt from messages
        prompt = ""
        for msg in messages:
            role = msg['role']
            content = msg.get('content', '')
            if role == 'system':
                prompt += f"System: {content}\n\n"
            elif role == 'assistant':
                prompt += f"Assistant: {content}\n\n"
            else:
                prompt += f"User: {content}\n\n"
        
        prompt += "Assistant: "
        
        # Prepare Ollama CLI command
        cmd = [
            'ollama', 'run', model,
            '--verbose=false'
        ]
        
        logger.info(f"Running command: {' '.join(cmd)}")
        logger.info(f"Prompt: {prompt[:100]}...")
        
        if stream:
            # Handle streaming response
            def generate():
                process = subprocess.Popen(
                    cmd,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    env={**os.environ, 'OLLAMA_HOST': 'ollama.com'}
                )
                
                # Send the prompt
                stdout, stderr = process.communicate(input=prompt, timeout=30)
                
                if process.returncode != 0:
                    logger.error(f"Ollama CLI error: {stderr}")
                    yield f"data: {json.dumps({'error': stderr})}\n\n"
                else:
                    # Send the response in chunks
                    response_text = stdout.strip()
                    chunk_size = 10  # Send 10 characters at a time
                    
                    for i in range(0, len(response_text), chunk_size):
                        chunk = response_text[i:i+chunk_size]
                        openai_response = {
                            'id': f"chatcmpl-{uuid.uuid4().hex[:8]}",
                            'object': 'chat.completion.chunk',
                            'created': int(datetime.now().timestamp()),
                            'model': model,
                            'choices': [{
                                'index': 0,
                                'delta': {
                                    'content': chunk
                                },
                                'finish_reason': None
                            }]
                        }
                        yield f"data: {json.dumps(openai_response)}\n\n"
                    
                    # Send final chunk
                    openai_response = {
                        'id': f"chatcmpl-{uuid.uuid4().hex[:8]}",
                        'object': 'chat.completion.chunk',
                        'created': int(datetime.now().timestamp()),
                        'model': model,
                        'choices': [{
                            'index': 0,
                            'delta': {},
                            'finish_reason': 'stop'
                        }]
                    }
                    yield f"data: {json.dumps(openai_response)}\n\n"
                    yield "data: [DONE]\n\n"
            
            return Response(generate(), mimetype='text/event-stream')
        
        else:
            # Handle non-streaming response
            try:
                # Run the command with timeout
                process = subprocess.run(
                    cmd,
                    input=prompt,
                    capture_output=True,
                    text=True,
                    timeout=60,
                    env={**os.environ, 'OLLAMA_HOST': 'ollama.com'}
                )
                
                if process.returncode != 0:
                    logger.error(f"Ollama CLI error: {process.stderr}")
                    return jsonify({
                        'error': {
                            'message': f"Ollama CLI error: {process.stderr}",
                            'type': 'cli_error',
                            'code': 500
                        }
                    }), 500
                
                response_text = process.stdout.strip()
                logger.info(f"Got response: {response_text[:100]}...")
                
                # Convert to OpenAI format
                openai_response = {
                    'id': f"chatcmpl-{uuid.uuid4().hex[:8]}",
                    'object': 'chat.completion',
                    'created': int(datetime.now().timestamp()),
                    'model': model,
                    'choices': [{
                        'index': 0,
                        'message': {
                            'role': 'assistant',
                            'content': response_text
                        },
                        'finish_reason': 'stop'
                    }],
                    'usage': {
                        'prompt_tokens': len(prompt.split()),
                        'completion_tokens': len(response_text.split()),
                        'total_tokens': len(prompt.split()) + len(response_text.split())
                    }
                }
                
                return jsonify(openai_response)
            
            except subprocess.TimeoutExpired:
                logger.error("Command timed out")
                return jsonify({
                    'error': {
                        'message': 'Request timed out',
                        'type': 'timeout_error',
                        'code': 504
                    }
                }), 504
    
    except Exception as e:
        logger.error(f"Error processing request: {e}", exc_info=True)
        return jsonify({
            'error': {
                'message': str(e),
                'type': 'internal_error',
                'code': 500
            }
        }), 500

@app.route('/v1/models', methods=['GET'])
def list_models():
    """List available models in OpenAI format"""
    models = [
        {
            'id': 'gpt-oss:20b',
            'object': 'model',
            'created': int(datetime.now().timestamp()),
            'owned_by': 'ollama'
        },
        {
            'id': 'gpt-oss:120b',
            'object': 'model',
            'created': int(datetime.now().timestamp()),
            'owned_by': 'ollama'
        }
    ]
    
    return jsonify({
        'object': 'list',
        'data': models
    })

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    # Test if ollama CLI works
    try:
        result = subprocess.run(
            ['ollama', '--version'],
            capture_output=True,
            text=True,
            timeout=5
        )
        ollama_available = result.returncode == 0
    except:
        ollama_available = False
    
    return jsonify({
        'status': 'healthy' if ollama_available else 'degraded',
        'ollama_cli': ollama_available
    })

if __name__ == '__main__':
    print("Starting Ollama CLI Proxy Server...")
    print("Proxy running at: http://localhost:8080")
    print("OpenAI endpoint: http://localhost:8080/v1/chat/completions")
    print("\nTesting Ollama CLI availability...")
    
    # Test ollama
    result = subprocess.run(['ollama', '--version'], capture_output=True, text=True)
    if result.returncode == 0:
        print(f"✓ Ollama CLI available: {result.stdout.strip()}")
    else:
        print("✗ Ollama CLI not found!")
    
    print("\nPress Ctrl+C to stop the server")
    
    app.run(host='0.0.0.0', port=8080, debug=False)