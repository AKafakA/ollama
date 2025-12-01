#!/usr/bin/env python3
"""
Example Python client for the Ollama status API endpoint.
This can be integrated into ollama-python library.
"""

import json
import time
import threading
import requests
from typing import Dict, List, Any, Optional


class OllamaStatusClient:
    """Client for interacting with Ollama's status API."""
    
    def __init__(self, host: str = "http://localhost:11434"):
        """
        Initialize the Ollama status client.
        
        Args:
            host: The Ollama server host URL
        """
        self.host = host.rstrip('/')
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get the current status of the Ollama server.
        
        Returns:
            Dictionary containing:
            - running_requests: List of running requests with ID and generated tokens
            - pending_requests: List of pending request IDs
            - free_memory: Free GPU memory in bytes
        """
        response = requests.get(f"{self.host}/api/status")
        response.raise_for_status()
        return response.json()
    
    def get_running_requests(self) -> List[Dict[str, Any]]:
        """Get list of currently running requests."""
        status = self.get_status()
        return status.get('running_requests', [])
    
    def get_pending_requests(self) -> List[str]:
        """Get list of pending request IDs."""
        status = self.get_status()
        return status.get('pending_requests', [])
    
    def get_free_memory(self) -> int:
        """Get free GPU memory in bytes."""
        status = self.get_status()
        return status.get('free_memory', 0)
    
    def get_free_memory_gb(self) -> float:
        """Get free GPU memory in gigabytes."""
        return self.get_free_memory() / (1024 ** 3)
    
    def monitor_status(self, interval: float = 1.0, duration: Optional[float] = None):
        """
        Monitor and print status continuously.
        
        Args:
            interval: Time between status checks in seconds
            duration: Total monitoring duration in seconds (None for infinite)
        """
        start_time = time.time()
        
        try:
            while duration is None or (time.time() - start_time) < duration:
                status = self.get_status()
                
                print("\n" + "="*50)
                print(f"Ollama Server Status - {time.strftime('%Y-%m-%d %H:%M:%S')}")
                print("="*50)
                
                # Running requests
                running = status.get('running_requests', [])
                if running:
                    print(f"\nRunning Requests ({len(running)}):")
                    for req in running:
                        print(f"  - ID: {req['id']}, Tokens: {req['generated_tokens']}")
                else:
                    print("\nNo running requests")
                
                # Pending requests
                pending = status.get('pending_requests', [])
                if pending:
                    print(f"\nPending Requests ({len(pending)}):")
                    for req_id in pending:
                        print(f"  - {req_id}")
                else:
                    print("\nNo pending requests")
                
                # Memory
                free_mem_gb = status.get('free_memory', 0) / (1024 ** 3)
                print(f"\nFree GPU Memory: {free_mem_gb:.2f} GB")
                
                time.sleep(interval)
                
        except KeyboardInterrupt:
            print("\n\nMonitoring stopped by user")


def example_usage():
    """Example usage of the OllamaStatusClient."""
    
    # Initialize client
    client = OllamaStatusClient()
    
    print("Ollama Status API Client Example")
    print("=" * 40)
    
    # Get current status
    print("\n1. Getting current status:")
    status = client.get_status()
    print(json.dumps(status, indent=2))
    
    # Get specific information
    print("\n2. Getting specific information:")
    print(f"   Running requests: {len(client.get_running_requests())}")
    print(f"   Pending requests: {len(client.get_pending_requests())}")
    print(f"   Free memory: {client.get_free_memory_gb():.2f} GB")
    
    # Monitor for 10 seconds
    print("\n3. Monitoring status for 10 seconds...")
    print("   (Press Ctrl+C to stop)")
    client.monitor_status(interval=2.0, duration=10.0)


def stress_test_example():
    """Example showing status monitoring during concurrent requests."""
    
    client = OllamaStatusClient()
    
    def make_request(prompt: str, request_id: int):
        """Make a generation request."""
        try:
            response = requests.post(
                f"{client.host}/api/generate",
                json={
                    "model": "llama2",
                    "prompt": f"Request {request_id}: {prompt}",
                    "stream": False
                }
            )
            print(f"Request {request_id} completed")
        except Exception as e:
            print(f"Request {request_id} failed: {e}")
    
    print("Stress Test: Monitoring during concurrent requests")
    print("=" * 50)
    
    # Start monitoring in a separate thread
    monitor_thread = threading.Thread(
        target=client.monitor_status,
        kwargs={"interval": 0.5, "duration": 15.0}
    )
    monitor_thread.start()
    
    # Wait a moment then start requests
    time.sleep(1)
    
    # Start multiple concurrent requests
    threads = []
    prompts = [
        "Count from 1 to 10",
        "List the days of the week",
        "Name 5 colors",
        "What is 2+2?",
        "Say hello in 3 languages"
    ]
    
    print("\nStarting concurrent requests...")
    for i, prompt in enumerate(prompts):
        thread = threading.Thread(target=make_request, args=(prompt, i+1))
        thread.start()
        threads.append(thread)
        time.sleep(0.5)  # Stagger the requests slightly
    
    # Wait for all requests to complete
    for thread in threads:
        thread.join()
    
    # Wait for monitoring to complete
    monitor_thread.join()
    
    print("\nStress test completed!")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "stress":
        stress_test_example()
    else:
        example_usage()