# Ollama Status API Implementation

## Overview
This implementation adds a new `/api/status` endpoint to the Ollama server that provides real-time information about the internal status during serving. This endpoint can be called by HTTP clients (including ollama-python) to monitor server activity.

## Features

The status API provides the following information:

1. **Running Requests**: List of currently executing requests with:
   - Request ID (unique identifier)
   - Number of generated tokens (updated in real-time)

2. **Pending Requests**: List of request IDs waiting in the queue to be processed

3. **Free Memory**: Total free GPU memory in bytes across all GPUs

## API Endpoint

### GET /api/status

Returns the current server status.

**Response Format:**
```json
{
  "running_requests": [
    {
      "id": "a1b2c3d4e5f6g7h8",
      "generated_tokens": 150
    }
  ],
  "pending_requests": ["x9y8z7w6v5u4t3s2"],
  "free_memory": 8589934592
}
```

## Implementation Details

### Modified Files

1. **server/sched.go**
   - Added request tracking data structures to the Scheduler
   - Added `id` and `generatedTokens` fields to `LlmRequest`
   - Added `requestMu`, `pendingRequests`, and `runningRequests` to track requests
   - Implemented `GetStatus()` method to retrieve current status
   - Implemented `UpdateRequestTokens()` method to update token counts
   - Modified `GetRunner()` to return request ID

2. **server/routes.go**
   - Added `StatusHandler()` to handle the `/api/status` endpoint
   - Modified `scheduleRunner()` to return request ID
   - Updated `GenerateHandler()` and `ChatHandler()` to track token generation
   - Registered the new `/api/status` route

3. **api/types.go**
   - Added `StatusResponse` type for the API response
   - Added `RequestStatus` type for individual request information

4. **api/client.go**
   - Added `Status()` method to the Go client for accessing the status endpoint

5. **server/sched_test.go**
   - Updated tests to handle the new return value from `GetRunner()`

### How It Works

1. **Request ID Generation**: When a new request is created, a unique ID is generated using random bytes if the id have not been provided in the requests.

2. **Request Tracking**: 
   - When a request enters the system, it's added to `pendingRequests`
   - When a request starts processing, it's moved from `pendingRequests` to `runningRequests`
   - When a request completes, it's removed from `runningRequests`

3. **Token Counting**: During generation, the completion callback updates the token count in real-time using `UpdateRequestTokens()`

4. **Memory Reporting**: Free GPU memory is calculated by summing `FreeMemory` from all available GPUs

## Usage Examples

### Shell/curl
```bash
curl http://localhost:11434/api/status
```

### Python
```python
import requests

response = requests.get("http://localhost:11434/api/status")
status = response.json()

print(f"Running requests: {len(status['running_requests'])}")
print(f"Pending requests: {len(status['pending_requests'])}")
print(f"Free memory: {status['free_memory'] / (1024**3):.2f} GB")
```

### Go
```go
client := api.NewClient()
status, err := client.Status(context.Background())
if err != nil {
    log.Fatal(err)
}

fmt.Printf("Running requests: %d\n", len(status.RunningRequests))
fmt.Printf("Pending requests: %d\n", len(status.PendingRequests))
fmt.Printf("Free memory: %.2f GB\n", float64(status.FreeMemory)/(1024*1024*1024))
```

## Testing

Two test scripts are provided:

1. **test_status_api.sh**: Shell script for testing the API with curl
2. **ollama_status_client.py**: Python client with examples and monitoring capabilities

Run the tests:
```bash
# Shell test
./test_status_api.sh

# Python test
python3 ollama_status_client.py

# Python stress test
python3 ollama_status_client.py stress
```

## Integration with ollama-python

The Python client example (`ollama_status_client.py`) demonstrates how to integrate this API into ollama-python. The key class `OllamaStatusClient` provides methods for:

- Getting current status
- Retrieving running/pending requests
- Checking free memory
- Continuous monitoring

This can be added to the ollama-python library as a new feature.

## Benefits

1. **Observability**: Provides visibility into server workload and resource usage
2. **Queue Management**: Allows clients to see if their requests are pending
3. **Resource Planning**: Free memory information helps with capacity planning
4. **Performance Monitoring**: Token generation tracking helps monitor performance
5. **Load Balancing**: Can be used to implement intelligent load balancing across multiple Ollama instances

## Future Enhancements

Potential improvements for future versions:

1. Add model information to running requests
2. Track request start time and elapsed time
3. Include CPU/GPU utilization metrics
4. Add request priority information
5. Include historical statistics
6. WebSocket support for real-time updates
7. Request cancellation by ID