#!/usr/bin/env python3
"""
State Reconciliation Service - Keep state files in sync with reality

Usage:
    python3 reconcile_state.py              # Run once
    python3 reconcile_state.py --daemon     # Run continuously
    python3 reconcile_state.py --fix        # Auto-fix mismatches
"""

import os
import sys
import json
import time
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Optional

WORKSPACE = Path("/Users/kimimini/.openclaw/workspace")
STATE_DIR = WORKSPACE / "state"
LOG_FILE = WORKSPACE / "logs/reconciliation.log"
RECONCILE_INTERVAL = 300  # 5 minutes in daemon mode


class StateReconciler:
    """Reconciles bot state files with actual process states."""
    
    def __init__(self, auto_fix: bool = False):
        self.auto_fix = auto_fix
        self.mismatches = []
        self.fixed = []
        
    def get_process_states(self) -> Dict[str, Dict]:
        """Get actual state of all bot processes."""
        states = {}
        
        try:
            import psutil
            for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'create_time']):
                try:
                    cmdline = proc.info.get('cmdline', [])
                    if not cmdline:
                        continue
                    
                    cmd_str = ' '.join(cmdline) if cmdline else ''
                    
                    # Pattern matching for different bot types
                    bot_id = self._extract_bot_id(cmd_str)
                    if bot_id:
                        states[bot_id] = {
                            'pid': proc.info['pid'],
                            'running': True,
                            'started_at': datetime.fromtimestamp(
                                proc.info['create_time'], timezone.utc
                            ).isoformat(),
                            'cmdline': cmd_str[:200]
                        }
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
        except ImportError:
            # Fallback to ps command
            import subprocess
            result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
            for line in result.stdout.split('\n'):
                bot_id = self._extract_bot_id(line)
                if bot_id and bot_id not in states:
                    states[bot_id] = {
                        'pid': None,
                        'running': True,
                        'started_at': None,
                        'cmdline': line[:200]
                    }
        
        return states
    
    def _extract_bot_id(self, cmdline: str) -> Optional[str]:
        """Extract bot ID from command line."""
        cmdline_lower = cmdline.lower()
        
        if 'mm_optimized_15m' in cmdline:
            return 'mm_15m'
        elif 'mm_optimized_1h' in cmdline:
            return 'mm_1h'
        elif 'bot_v1' in cmdline or ('python' in cmdline_lower and any(x in cmdline_lower for x in ['long', 'short'])):
            # Try to extract from filename
            if 'btc' in cmdline_lower:
                if 'long' in cmdline_lower:
                    return 'btc_long_v1'
                elif 'short' in cmdline_lower:
                    return 'btc_short_v1'
            elif 'doge' in cmdline_lower:
                if 'long' in cmdline_lower:
                    return 'doge_long_v1'
                elif 'short' in cmdline_lower:
                    return 'doge_short_v1'
        elif 'hummingbot' in cmdline_lower:
            return 'hummingbot'
        
        return None
    
    def get_file_states(self) -> Dict[str, Dict]:
        """Get states from all state files."""
        states = {}
        
        if not STATE_DIR.exists():
            return states
        
        for state_file in STATE_DIR.glob("*.json"):
            try:
                bot_id = state_file.stem
                data = json.loads(state_file.read_text())
                states[bot_id] = {
                    'status': data.get('status', 'unknown'),
                    'last_update': data.get('last_update'),
                    'file_mtime': datetime.fromtimestamp(
                        state_file.stat().st_mtime, timezone.utc
                    ).isoformat()
                }
            except (json.JSONDecodeError, IOError):
                continue
        
        return states
    
    def reconcile(self) -> Dict:
        """Compare and reconcile process states with file states."""
        process_states = self.get_process_states()
        file_states = self.get_file_states()
        
        report = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'processes_found': len(process_states),
            'state_files_found': len(file_states),
            'mismatches': [],
            'fixed': [],
            'healthy': True
        }
        
        # Check for running processes without state files
        for bot_id, proc_state in process_states.items():
            if bot_id not in file_states:
                mismatch = {
                    'bot_id': bot_id,
                    'issue': 'running_but_no_state_file',
                    'process': proc_state
                }
                report['mismatches'].append(mismatch)
                report['healthy'] = False
                
                if self.auto_fix:
                    self._create_state_file(bot_id, proc_state)
                    report['fixed'].append(bot_id)
        
        # Check for state files without running processes
        for bot_id, file_state in file_states.items():
            if bot_id not in process_states:
                if file_state['status'] in ['running', 'active']:
                    mismatch = {
                        'bot_id': bot_id,
                        'issue': 'state_says_running_but_process_missing',
                        'file_state': file_state
                    }
                    report['mismatches'].append(mismatch)
                    report['healthy'] = False
                    
                    if self.auto_fix:
                        self._update_state_to_stopped(bot_id)
                        report['fixed'].append(bot_id)
        
        return report
    
    def _create_state_file(self, bot_id: str, proc_state: Dict):
        """Create a state file for a running bot."""
        state_file = STATE_DIR / f"{bot_id}.json"
        state = {
            'bot_id': bot_id,
            'bot_name': bot_id.replace('_', ' ').title(),
            'status': 'running',
            'status_color': 'green',
            'pid': proc_state['pid'],
            'started_at': proc_state['started_at'],
            'last_update': datetime.now(timezone.utc).isoformat(),
            'reconciled': True
        }
        
        STATE_DIR.mkdir(parents=True, exist_ok=True)
        state_file.write_text(json.dumps(state, indent=2))
    
    def _update_state_to_stopped(self, bot_id: str):
        """Update state file to reflect stopped status."""
        state_file = STATE_DIR / f"{bot_id}.json"
        if state_file.exists():
            try:
                state = json.loads(state_file.read_text())
                state['status'] = 'stopped'
                state['status_color'] = 'red'
                state['last_update'] = datetime.now(timezone.utc).isoformat()
                state['reconciled'] = True
                state_file.write_text(json.dumps(state, indent=2))
            except (json.JSONDecodeError, IOError):
                pass
    
    def log_report(self, report: Dict):
        """Log reconciliation report."""
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        
        with open(LOG_FILE, 'a') as f:
            f.write(json.dumps(report) + '\n')
    
    def print_report(self, report: Dict):
        """Print human-readable report."""
        print("=" * 60)
        print("STATE RECONCILIATION REPORT")
        print("=" * 60)
        print(f"Timestamp: {report['timestamp']}")
        print(f"Processes Found: {report['processes_found']}")
        print(f"State Files Found: {report['state_files_found']}")
        
        if report['healthy']:
            print("\n✅ All states reconciled")
        else:
            print(f"\n⚠️  {len(report['mismatches'])} mismatch(es) found:")
            for m in report['mismatches']:
                print(f"  - {m['bot_id']}: {m['issue']}")
        
        if report['fixed']:
            print(f"\n🔧 Fixed: {', '.join(report['fixed'])}")
        
        print("=" * 60)


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Reconcile bot states")
    parser.add_argument("--daemon", action="store_true", help="Run continuously")
    parser.add_argument("--fix", action="store_true", help="Auto-fix mismatches")
    parser.add_argument("--json", action="store_true", help="Output JSON")
    args = parser.parse_args()
    
    reconciler = StateReconciler(auto_fix=args.fix)
    
    if args.daemon:
        print(f"Starting state reconciliation daemon (interval: {RECONCILE_INTERVAL}s)")
        while True:
            report = reconciler.reconcile()
            reconciler.log_report(report)
            
            if not args.json:
                reconciler.print_report(report)
            
            time.sleep(RECONCILE_INTERVAL)
    else:
        report = reconciler.reconcile()
        reconciler.log_report(report)
        
        if args.json:
            print(json.dumps(report, indent=2))
        else:
            reconciler.print_report(report)
        
        sys.exit(0 if report['healthy'] else 1)


if __name__ == "__main__":
    main()
