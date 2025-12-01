#!/bin/bash

# Test script for the new /api/status endpoint
# This script demonstrates how to use the new status API

echo "Testing Ollama Status API"
echo "========================="
echo ""

# Configuration
OLLAMA_HOST="${OLLAMA_HOST:-http://localhost:11434}"

echo "Using Ollama host: $OLLAMA_HOST"
echo ""

# Test 1: Get current status
echo "1. Getting current status:"
echo "--------------------------"
curl -s "$OLLAMA_HOST/api/status" | python3 -m json.tool 2>/dev/null || curl -s "$OLLAMA_HOST/api/status"
echo ""
echo ""

# Test 2: Start a generation request and check status
echo "2. Starting a generation request and checking status:"
echo "------------------------------------------------------"
echo "Starting generation in background..."

# Start a generation request in the background
(curl -s -X POST "$OLLAMA_HOST/api/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama2",
    "prompt": "Why is the sky blue? Explain in detail.",
    "stream": false
  }' > /tmp/ollama_gen_response.json 2>/dev/null) &

GEN_PID=$!

# Wait a moment for the request to start
sleep 1

echo "Checking status while generation is running:"
curl -s "$OLLAMA_HOST/api/status" | python3 -m json.tool 2>/dev/null || curl -s "$OLLAMA_HOST/api/status"
echo ""

# Wait for generation to complete
wait $GEN_PID

echo ""
echo "3. Status after generation completes:"
echo "--------------------------------------"
curl -s "$OLLAMA_HOST/api/status" | python3 -m json.tool 2>/dev/null || curl -s "$OLLAMA_HOST/api/status"
echo ""

# Test 3: Multiple concurrent requests
echo ""
echo "4. Testing with multiple concurrent requests:"
echo "----------------------------------------------"
echo "Starting 3 concurrent generation requests..."

# Start multiple requests
for i in 1 2 3; do
  (curl -s -X POST "$OLLAMA_HOST/api/generate" \
    -H "Content-Type: application/json" \
    -d "{
      \"model\": \"llama2\",
      \"prompt\": \"Request $i: Count from 1 to 10.\",
      \"stream\": false
    }" > /tmp/ollama_gen_response_$i.json 2>/dev/null) &
done

# Wait a moment for requests to start
sleep 1

echo "Status with multiple running requests:"
curl -s "$OLLAMA_HOST/api/status" | python3 -m json.tool 2>/dev/null || curl -s "$OLLAMA_HOST/api/status"
echo ""

# Wait for all background jobs to complete
wait

echo ""
echo "5. Final status (all requests completed):"
echo "------------------------------------------"
curl -s "$OLLAMA_HOST/api/status" | python3 -m json.tool 2>/dev/null || curl -s "$OLLAMA_HOST/api/status"
echo ""

echo ""
echo "Test completed!"
echo ""
echo "API Documentation:"
echo "=================="
echo "Endpoint: GET /api/status"
echo ""
echo "Response format:"
echo "{"
echo "  \"running_requests\": ["
echo "    {"
echo "      \"id\": \"<request_id>\","
echo "      \"generated_tokens\": <number>"
echo "    }"
echo "  ],"
echo "  \"pending_requests\": [\"<request_id>\", ...],"
echo "  \"free_memory\": <bytes>"
echo "}"
echo ""
echo "This API can be called by HTTP clients to monitor:"
echo "- List of running requests with their IDs and generated token counts"
echo "- List of pending request IDs waiting to be processed"
echo "- Total free GPU memory in bytes"