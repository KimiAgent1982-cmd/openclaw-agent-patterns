#!/usr/bin/env python3
"""
Bot State Writer - Standardized state management for trading bots

Writes bot state to JSON files that the dashboard reads.
Each bot gets its own state file: state/{bot_id}.json

Usage:
    from bot_state import BotStateWriter
    
    state = BotStateWriter("mm_1h")
    state.update({
        "status": "running",
        "pnl_24h": 12.45,
        "position": {"side": "long", "size": 0.5}
    })
"""

import json
import time
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, Optional

STATE_DIR = Path("/Users/kimimini/.openclaw/workspace/state")


class BotStateWriter:
    """Handles writing bot state to JSON files for dashboard consumption."""
    
    def __init__(self, bot_id: str, bot_name: Optional[str] = None):
        """
        Initialize state writer for a bot.
        
        Args:
            bot_id: Unique identifier (e.g., "mm_1h", "btc_long_v1")
            bot_name: Human-readable name (e.g., "Market Maker 1H")
        """
        self.bot_id = bot_id
        self.bot_name = bot_name or bot_id
        self.state_file = STATE_DIR / f"{bot_id}.json"
        
        # Ensure state directory exists
        STATE_DIR.mkdir(parents=True, exist_ok=True)
        
        # Initialize with default state
        self._default_state = {
            "bot_id": bot_id,
            "bot_name": self.bot_name,
            "status": "initializing",
            "status_color": "yellow",
            "pnl_total": 0.0,
            "pnl_24h": 0.0,
            "trades_total": 0,
            "trades_24h": 0,
            "position": None,
            "last_update": None,
            "last_error": None,
            "uptime_seconds": 0,
            "version": "1.0.0"
        }
        
        # Create initial state file if it doesn't exist
        if not self.state_file.exists():
            self._write(self._default_state)
    
    def _write(self, state: Dict[str, Any]) -> None:
        """Write state to JSON file atomically."""
        # Write to temp file first, then rename (atomic operation)
        temp_file = self.state_file.with_suffix('.tmp')
        state["last_update"] = datetime.now(timezone.utc).isoformat()
        temp_file.write_text(json.dumps(state, indent=2))
        temp_file.replace(self.state_file)
    
    def update(self, updates: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update bot state with new values.
        
        Args:
            updates: Dictionary of fields to update
            
        Returns:
            Complete current state
        """
        # Read current state
        current = self._default_state.copy()
        if self.state_file.exists():
            current.update(json.loads(self.state_file.read_text()))
        
        # Apply updates
        current.update(updates)
        
        # Set status color based on status
        status = current.get("status", "unknown")
        color_map = {
            "running": "green",
            "active": "green",
            "initializing": "yellow",
            "paused": "yellow",
            "stopped": "red",
            "error": "red",
            "offline": "gray"
        }
        current["status_color"] = color_map.get(status, "yellow")
        
        # Write updated state
        self._write(current)
        return current
    
    def set_running(self, extra_fields: Optional[Dict] = None) -> Dict[str, Any]:
        """Set bot status to running."""
        updates = {"status": "running"}
        if extra_fields:
            updates.update(extra_fields)
        return self.update(updates)
    
    def set_error(self, error_message: str) -> Dict[str, Any]:
        """Set bot status to error."""
        return self.update({
            "status": "error",
            "last_error": error_message
        })
    
    def set_paused(self) -> Dict[str, Any]:
        """Set bot status to paused."""
        return self.update({"status": "paused"})
    
    def set_stopped(self) -> Dict[str, Any]:
        """Set bot status to stopped."""
        return self.update({"status": "stopped"})
    
    def record_trade(self, pnl: float, side: str) -> Dict[str, Any]:
        """Record a completed trade."""
        current = json.loads(self.state_file.read_text()) if self.state_file.exists() else self._default_state
        
        current["trades_total"] = current.get("trades_total", 0) + 1
        current["trades_24h"] = current.get("trades_24h", 0) + 1
        current["pnl_total"] = current.get("pnl_total", 0) + pnl
        current["pnl_24h"] = current.get("pnl_24h", 0) + pnl
        current["last_trade"] = {
            "time": datetime.now(timezone.utc).isoformat(),
            "pnl": pnl,
            "side": side
        }
        
        self._write(current)
        return current
    
    def update_position(self, side: Optional[str], size: float, entry_price: Optional[float] = None) -> Dict[str, Any]:
        """Update current position."""
        if side is None:
            position = None
        else:
            position = {
                "side": side,
                "size": size,
                "entry_price": entry_price,
                "opened_at": datetime.now(timezone.utc).isoformat()
            }
        return self.update({"position": position})
    
    def get_state(self) -> Dict[str, Any]:
        """Read current state."""
        if self.state_file.exists():
            return json.loads(self.state_file.read_text())
        return self._default_state.copy()


def get_all_bot_states() -> Dict[str, Dict[str, Any]]:
    """
    Get state of all bots.
    
    Returns:
        Dictionary mapping bot_id to state
    """
    states = {}
    if STATE_DIR.exists():
        for state_file in STATE_DIR.glob("*.json"):
            try:
                bot_id = state_file.stem
                states[bot_id] = json.loads(state_file.read_text())
            except (json.JSONDecodeError, IOError):
                continue
    return states


def clear_all_states() -> None:
    """Clear all bot states (useful for testing)."""
    if STATE_DIR.exists():
        for state_file in STATE_DIR.glob("*.json"):
            state_file.unlink()


if __name__ == "__main__":
    # Example usage and test
    print("Testing BotStateWriter...")
    
    # Create a test bot state
    test_bot = BotStateWriter("test_bot", "Test Market Maker")
    test_bot.set_running({
        "pnl_total": 123.45,
        "pnl_24h": 12.34,
        "trades_total": 50,
        "trades_24h": 5
    })
    test_bot.update_position("long", 0.5, 45000.00)
    
    print(f"Created test bot state: {test_bot.state_file}")
    print(json.dumps(test_bot.get_state(), indent=2))
    
    # Show all bot states
    print("\nAll bot states:")
    all_states = get_all_bot_states()
    for bot_id, state in all_states.items():
        print(f"  {bot_id}: {state.get('status', 'unknown')}")
    
    # Clean up test file
    test_bot.state_file.unlink()
    print("\nTest complete. Test state file removed.")
