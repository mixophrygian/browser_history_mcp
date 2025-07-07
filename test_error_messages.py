#!/usr/bin/env python3
"""
Test script to demonstrate improved error messages for browser locking issues.
This script simulates the MCP server responses to show how Claude should interpret them.
"""

import json
from typing import Dict, Any

def simulate_browser_locked_response() -> Dict[str, Any]:
    """Simulate what the MCP server returns when a browser is locked."""
    return {
        "available_browsers": ["firefox", "chrome"],
        "active_browsers": ["firefox"],
        "status": "browser_locked",
        "error_message": "🔒 BROWSER LOCKED: Firefox is currently running and its database is locked.",
        "user_action_required": True,
        "recommended_action": "❗ IMPORTANT: Please close Firefox completely to analyze its history. You can restore your tabs later with Ctrl+Shift+T (Cmd+Shift+T on Mac).",
        "technical_details": "Database error: database is locked",
        "claude_instruction": "IMPORTANT: Tell the user they need to close their browser(s) as specified in the recommended_action field."
    }

def simulate_partial_success_response() -> Dict[str, Any]:
    """Simulate what the MCP server returns when some browsers work but others are locked."""
    return {
        "history_entries": [
            {"url": "https://example.com", "title": "Example", "visit_count": 1},
            # ... more entries
        ],
        "successful_browsers": ["chrome"],
        "failed_browsers": ["firefox"],
        "failure_reasons": {"firefox": "database is locked"},
        "total_entries": 150,
        "status": "partial_success",
        "user_action_required": True,
        "recommendation": "🔒 BROWSER LOCKED: Firefox is currently running. Please close this browser completely to get complete history analysis. You can restore tabs with Ctrl+Shift+T (Cmd+Shift+T on Mac). Successfully retrieved 150 entries from Chrome."
    }

def simulate_all_ready_response() -> Dict[str, Any]:
    """Simulate what the MCP server returns when all browsers are ready."""
    return {
        "available_browsers": ["firefox", "chrome", "safari"],
        "active_browsers": [],
        "status": "ready",
        "error_message": None,
        "user_action_required": False,
        "recommended_action": "✅ All browsers are available for analysis. Found: firefox, chrome, safari"
    }

def demonstrate_claude_interpretation():
    """Demonstrate how Claude should interpret these responses."""
    
    print("=== BROWSER LOCKED SCENARIO ===")
    locked_response = simulate_browser_locked_response()
    print(f"MCP Response: {json.dumps(locked_response, indent=2)}")
    print("\n🤖 Claude should say:")
    print(f"\"I can see that {locked_response['error_message']} {locked_response['recommended_action']}\"")
    
    print("\n=== PARTIAL SUCCESS SCENARIO ===")
    partial_response = simulate_partial_success_response()
    print(f"MCP Response: {json.dumps({k: v for k, v in partial_response.items() if k != 'history_entries'}, indent=2)}")
    print("\n🤖 Claude should say:")
    print(f"\"I was able to retrieve some of your browser history, but {partial_response['recommendation']}\"")
    
    print("\n=== ALL READY SCENARIO ===")
    ready_response = simulate_all_ready_response()
    print(f"MCP Response: {json.dumps(ready_response, indent=2)}")
    print("\n🤖 Claude should say:")
    print(f"\"Great! {ready_response['recommended_action']} I can now analyze your browser history.\"")

if __name__ == "__main__":
    demonstrate_claude_interpretation() 