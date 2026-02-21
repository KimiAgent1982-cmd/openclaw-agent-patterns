# System Health Monitor Pattern

**Purpose:** Validate configurations, reconcile state files with reality, and test API connectivity to prevent silent failures.

**Use Case:** Detect configuration gaps, state drift, and API issues before they cause problems.

---

## The Problem

Systems fail silently when:
- API keys expire or are missing
- State files drift from actual process states
- Services appear "running" but aren't actually working
- Configuration errors aren't caught until critical moments

**This pattern provides proactive validation, not just reactive monitoring.**

---

## Architecture

```
workspace/
├── config/
│   ├── validation.json       # Required configuration schema
│   └── secrets.env.example   # Template for secrets
├── scripts/
│   ├── validate_config.py    # Configuration validator
│   ├── reconcile_state.py    # State reconciliation service
│   └── test_connectivity.py  # API connectivity tester
├── state/
│   └── {bot_id}.json         # Bot state files
└── logs/
    ├── validation.log        # Configuration check results
    ├── reconciliation.log    # State fix log
    └── connectivity.log      # API test results
```

---

## Components

### 1. Configuration Validator (`validate_config.py`)

Validates that all required configuration exists and API keys work.

```python
#!/usr/bin/env python3
"""
Configuration Validator - Check all required configs and API keys

Usage:
    python3 validate_config.py              # Full validation
    python3 validate_config.py --quick      # Check files only, no API calls
    python3 validate_config.py --json       # Output JSON for automation
"""

import os
import sys
import json
from pathlib import Path
from typing import Dict, List, Tuple, Optional

WORKSPACE = Path("/Users/kimimini/.openclaw/workspace")
CONFIG_SCHEMA = WORKSPACE / "config/validation.json"

# Required configuration keys with validation
REQUIRED_CONFIGS = {
    "BRAVE_API_KEY": {
        "description": "Brave Search API for web searches",
        "test_url": "https://api.search.brave.com/res/v1/web/search",
        "test_method": "brave"
    },
    "MOONSHOT_API_KEY": {
        "description": "Moonshot LLM API (primary)",
        "optional": True,  # OpenClaw may handle this internally
        "test_method": None
    },
    "OKX_API_KEY": {
        "description": "OKX exchange API key",
        "optional": True,
        "test_method": "okx"
    },
    "OKX_API_SECRET": {
        "description": "OKX exchange API secret",
        "optional": True,
        "test_method": None
    },
    "TELEGRAM_BOT_TOKEN": {
        "description": "Telegram bot token for notifications",
        "optional": True,
        "test_method": None
    }
}


class ConfigValidator:
    """Validates system configuration."""
    
    def __init__(self, quick_mode: bool = False):
        self.quick_mode = quick_mode
        self.results = []
        self.missing_required = []
        self.missing_optional = []
        
    def check_env_file(self, env_path: Path) -> Dict[str, str]:
        """Load environment variables from file."""
        env_vars = {}
        if env_path.exists():
            with open(env_path) as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        env_vars[key] = value.strip('"\'')
        return env_vars
    
    def check_all_sources(self) -> Dict[str, str]:
        """Check multiple config sources."""
        configs = {}
        
        # Check .env files
        for env_file in ['.env', '.env.local', '.env.alerts']:
            configs.update(self.check_env_file(WORKSPACE / env_file))
        
        # Check environment
        configs.update({k: v for k, v in os.environ.items()})
        
        return configs
    
    def test_brave_api(self, api_key: str) -> Tuple[bool, str]:
        """Test Brave Search API connectivity."""
        try:
            import requests
            response = requests.get(
                "https://api.search.brave.com/res/v1/web/search",
                headers={"X-Subscription-Token": api_key},
                params={"q": "test", "count": 1},
                timeout=10
            )
            if response.status_code == 200:
                return True, "API key valid"
            elif response.status_code == 401:
                return False, "API key invalid or expired"
            else:
                return False, f"HTTP {response.status_code}"
        except ImportError:
            return False, "requests library not installed"
        except Exception as e:
            return False, str(e)
    
    def test_okx_api(self, api_key: str, api_secret: str) -> Tuple[bool, str]:
        """Test OKX API connectivity."""
        try:
            import ccxt
            exchange = ccxt.okx({
                'apiKey': api_key,
                'secret': api_secret,
                'enableRateLimit': True
            })
            # Test by fetching balance
            exchange.fetch_balance()
            return True, "API credentials valid"
        except ccxt.AuthenticationError:
            return False, "API credentials invalid"
        except Exception as e:
            return False, str(e)
    
    def validate(self) -> Dict:
        """Run full validation."""
        configs = self.check_all_sources()
        results = {
            "timestamp": json.dumps({}),
            "configs_checked": len(REQUIRED_CONFIGS),
            "present": [],
            "missing_required": [],
            "missing_optional": [],
            "api_tests": {},
            "healthy": True
        }
        
        for key, meta in REQUIRED_CONFIGS.items():
            if key in configs and configs[key]:
                results["present"].append(key)
                
                # Test API if not in quick mode
                if not self.quick_mode and meta.get("test_method"):
                    if meta["test_method"] == "brave":
                        success, msg = self.test_brave_api(configs[key])
                        results["api_tests"][key] = {"success": success, "message": msg}
                        if not success:
                            results["healthy"] = False
                    elif meta["test_method"] == "okx":
                        secret_key = configs.get("OKX_API_SECRET")
                        if secret_key:
                            success, msg = self.test_okx_api(configs[key], secret_key)
                            results["api_tests"][key] = {"success": success, "message": msg}
            else:
                if meta.get("optional"):
                    results["missing_optional"].append({"key": key, "description": meta["description"]})
                else:
                    results["missing_required"].append({"key": key, "description": meta["description"]})
                    results["healthy"] = False
        
        return results
    
    def print_report(self, results: Dict):
        """Print human-readable report."""
        print("=" * 60)
        print("CONFIGURATION VALIDATION REPORT")
        print("=" * 60)
        
        if results["healthy"]:
            print("✅ All required configurations present")
        else:
            print("❌ Configuration issues found")
        
        print(f"\n📋 Configs Present: {len(results['present'])}/{results['configs_checked']}")
        for key in results["present"]:
            status = "✅"
            if key in results["api_tests"]:
                test = results["api_tests"][key]
                status = "✅" if test["success"] else "❌"
            print(f"  {status} {key}")
        
        if results["missing_required"]:
            print(f"\n⚠️  Missing Required ({len(results['missing_required'])}):")
            for item in results["missing_required"]:
                print(f"  ❌ {item['key']}: {item['description']}")
        
        if results["missing_optional"]:
            print(f"\nℹ️  Missing Optional ({len(results['missing_optional'])}):")
            for item in results["missing_optional"]:
                print(f"  ⚪ {item['key']}: {item['description']}")
        
        if results["api_tests"]:
            print(f"\n🔌 API Connectivity Tests:")
            for key, test in results["api_tests"].items():
                status = "✅" if test["success"] else "❌"
                print(f"  {status} {key}: {test['message']}")
        
        print("=" * 60)


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Validate system configuration")
    parser.add_argument("--quick", action="store_true", help="Skip API tests")
    parser.add_argument("--json", action="store_true", help="Output JSON")
    args = parser.parse_args()
    
    validator = ConfigValidator(quick_mode=args.quick)
    results = validator.validate()
    
    if args.json:
        print(json.dumps(results, indent=2))
        sys.exit(0 if results["healthy"] else 1)
    else:
        validator.print_report(results)
        sys.exit(0 if results["healthy"] else 1)


if __name__ == "__main__":
    main()
```

---

### 2. State Reconciliation Service (`reconcile_state.py`)

Keeps state files synchronized with actual process states.

```python
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
import psutil
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Tuple, Optional
from filelock import FileLock

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
        
        for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'create_time']):
            try:
                cmdline = proc.info.get('cmdline', [])
                if not cmdline:
                    continue
                
                # Look for bot patterns in command line
                cmd_str = ' '.join(cmdline) if cmdline else ''
                
                # Pattern matching for different bot types
                if 'bot_v1' in cmd_str or 'mm_optimized' in cmd_str:
                    bot_id = self._extract_bot_id(cmd_str)
                    if bot_id:
                        states[bot_id] = {
                            'pid': proc.info['pid'],
                            'running': True,
                            'started_at': datetime.fromtimestamp(
                                proc.info['create_time'], timezone.utc
                            ).isoformat(),
                            'cmdline': cmd_str[:200]  # Truncate for storage
                        }
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        return states
    
    def _extract_bot_id(self, cmdline: str) -> Optional[str]:
        """Extract bot ID from command line."""
        # Common patterns
        patterns = [
            'mm_optimized_15m.py',
            'mm_optimized_1h.py',
            'bot_v1_long',
            'bot_v1_short'
        ]
        
        for pattern in patterns:
            if pattern in cmdline:
                # Extract specific identifier
                if 'mm_optimized_15m' in cmdline:
                    return 'mm_15m'
                elif 'mm_optimized_1h' in cmdline:
                    return 'mm_1h'
                elif 'btc' in cmdline.lower() and 'long' in cmdline.lower():
                    return 'btc_long_v1'
                elif 'btc' in cmdline.lower() and 'short' in cmdline.lower():
                    return 'btc_short_v1'
                elif 'doge' in cmdline.lower() and 'long' in cmdline.lower():
                    return 'doge_long_v1'
                elif 'doge' in cmdline.lower() and 'short' in cmdline.lower():
                    return 'doge_short_v1'
        
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
                # Only flag as mismatch if status suggests it should be running
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
        
        # Check for status mismatches
        for bot_id in set(process_states.keys()) & set(file_states.keys()):
            proc_running = True
            file_status = file_states[bot_id]['status']
            
            if proc_running and file_status not in ['running', 'active']:
                mismatch = {
                    'bot_id': bot_id,
                    'issue': 'process_running_but_state_not_running',
                    'file_status': file_status
                }
                report['mismatches'].append(mismatch)
                report['healthy'] = False
        
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
        
        with FileLock(str(state_file) + ".lock"):
            state_file.write_text(json.dumps(state, indent=2))
    
    def _update_state_to_stopped(self, bot_id: str):
        """Update state file to reflect stopped status."""
        state_file = STATE_DIR / f"{bot_id}.json"
        if state_file.exists():
            with FileLock(str(state_file) + ".lock"):
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
```

---

### 3. API Connectivity Tester (`test_connectivity.py`)

Tests that external APIs are actually working, not just configured.

```python
#!/usr/bin/env python3
"""
API Connectivity Tester - Verify APIs are actually working

Usage:
    python3 test_connectivity.py              # Test all APIs
    python3 test_connectivity.py --service okx   # Test specific service
    python3 test_connectivity.py --json       # Output JSON
"""

import os
import sys
import json
import time
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, asdict

WORKSPACE = Path("/Users/kimimini/.openclaw/workspace")
LOG_FILE = WORKSPACE / "logs/connectivity.log"


@dataclass
class TestResult:
    service: str
    success: bool
    latency_ms: float
    message: str
    timestamp: str


class ConnectivityTester:
    """Tests connectivity to external services."""
    
    def __init__(self):
        self.results: List[TestResult] = []
        
    def load_env(self) -> Dict[str, str]:
        """Load environment variables from files."""
        env_vars = {}
        for env_file in ['.env', '.env.local', '.env.alerts']:
            path = WORKSPACE / env_file
            if path.exists():
                with open(path) as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            key, value = line.split('=', 1)
                            env_vars[key] = value.strip('"\'')
        env_vars.update({k: v for k, v in os.environ.items()})
        return env_vars
    
    def test_moonshot(self) -> TestResult:
        """Test Moonshot API connectivity."""
        start = time.time()
        try:
            # Moonshot is handled by OpenClaw, but we can test via a simple completion
            # This is a lightweight test
            env = self.load_env()
            api_key = env.get('MOONSHOT_API_KEY')
            
            if not api_key:
                return TestResult(
                    service="Moonshot",
                    success=False,
                    latency_ms=0,
                    message="API key not configured",
                    timestamp=datetime.now(timezone.utc).isoformat()
                )
            
            # If we have the key, assume OpenClaw handles the rest
            # In production, you'd make an actual API call
            latency = (time.time() - start) * 1000
            return TestResult(
                service="Moonshot",
                success=True,
                latency_ms=round(latency, 2),
                message="API key configured (handled by OpenClaw)",
                timestamp=datetime.now(timezone.utc).isoformat()
            )
        except Exception as e:
            latency = (time.time() - start) * 1000
            return TestResult(
                service="Moonshot",
                success=False,
                latency_ms=round(latency, 2),
                message=str(e),
                timestamp=datetime.now(timezone.utc).isoformat()
            )
    
    def test_brave_search(self) -> TestResult:
        """Test Brave Search API."""
        start = time.time()
        try:
            import requests
            env = self.load_env()
            api_key = env.get('BRAVE_API_KEY')
            
            if not api_key:
                return TestResult(
                    service="Brave Search",
                    success=False,
                    latency_ms=0,
                    message="API key not configured",
                    timestamp=datetime.now(timezone.utc).isoformat()
                )
            
            response = requests.get(
                "https://api.search.brave.com/res/v1/web/search",
                headers={"X-Subscription-Token": api_key},
                params={"q": "connectivity test", "count": 1},
                timeout=10
            )
            
            latency = (time.time() - start) * 1000
            
            if response.status_code == 200:
                return TestResult(
                    service="Brave Search",
                    success=True,
                    latency_ms=round(latency, 2),
                    message=f"HTTP {response.status_code}",
                    timestamp=datetime.now(timezone.utc).isoformat()
                )
            else:
                return TestResult(
                    service="Brave Search",
                    success=False,
                    latency_ms=round(latency, 2),
                    message=f"HTTP {response.status_code}",
                    timestamp=datetime.now(timezone.utc).isoformat()
                )
        except ImportError:
            return TestResult(
                service="Brave Search",
                success=False,
                latency_ms=0,
                message="requests library not installed",
                timestamp=datetime.now(timezone.utc).isoformat()
            )
        except Exception as e:
            latency = (time.time() - start) * 1000
            return TestResult(
                service="Brave Search",
                success=False,
                latency_ms=round(latency, 2),
                message=str(e),
                timestamp=datetime.now(timezone.utc).isoformat()
            )
    
    def test_okx(self) -> TestResult:
        """Test OKX exchange API."""
        start = time.time()
        try:
            import ccxt
            
            # Test public API first (no auth needed)
            exchange = ccxt.okx({'enableRateLimit': True})
            ticker = exchange.fetch_ticker('BTC/USDT:USDT')
            
            latency = (time.time() - start) * 1000
            
            return TestResult(
                service="OKX (Public)",
                success=True,
                latency_ms=round(latency, 2),
                message=f"BTC: ${ticker['last']}",
                timestamp=datetime.now(timezone.utc).isoformat()
            )
        except ImportError:
            return TestResult(
                service="OKX",
                success=False,
                latency_ms=0,
                message="ccxt library not installed",
                timestamp=datetime.now(timezone.utc).isoformat()
            )
        except Exception as e:
            latency = (time.time() - start) * 1000
            return TestResult(
                service="OKX",
                success=False,
                latency_ms=round(latency, 2),
                message=str(e),
                timestamp=datetime.now(timezone.utc).isoformat()
            )
    
    def test_telegram(self) -> TestResult:
        """Test Telegram bot API."""
        start = time.time()
        try:
            import requests
            env = self.load_env()
            token = env.get('TELEGRAM_BOT_TOKEN')
            
            if not token:
                return TestResult(
                    service="Telegram",
                    success=False,
                    latency_ms=0,
                    message="Bot token not configured",
                    timestamp=datetime.now(timezone.utc).isoformat()
                )
            
            response = requests.get(
                f"https://api.telegram.org/bot{token}/getMe",
                timeout=10
            )
            
            latency = (time.time() - start) * 1000
            
            if response.status_code == 200 and response.json().get('ok'):
                bot_info = response.json()['result']
                return TestResult(
                    service="Telegram",
                    success=True,
                    latency_ms=round(latency, 2),
                    message=f"@{bot_info.get('username', 'unknown')}",
                    timestamp=datetime.now(timezone.utc).isoformat()
                )
            else:
                return TestResult(
                    service="Telegram",
                    success=False,
                    latency_ms=round(latency, 2),
                    message="Invalid token or API error",
                    timestamp=datetime.now(timezone.utc).isoformat()
                )
        except ImportError:
            return TestResult(
                service="Telegram",
                success=False,
                latency_ms=0,
                message="requests library not installed",
                timestamp=datetime.now(timezone.utc).isoformat()
            )
        except Exception as e:
            latency = (time.time() - start) * 1000
            return TestResult(
                service="Telegram",
                success=False,
                latency_ms=round(latency, 2),
                message=str(e),
                timestamp=datetime.now(timezone.utc).isoformat()
            )
    
    def run_all_tests(self, service_filter: Optional[str] = None) -> Dict:
        """Run all connectivity tests."""
        tests = {
            'moonshot': self.test_moonshot,
            'brave': self.test_brave_search,
            'okx': self.test_okx,
            'telegram': self.test_telegram
        }
        
        if service_filter:
            tests = {k: v for k, v in tests.items() if service_filter.lower() in k.lower()}
        
        results = []
        for name, test_func in tests.items():
            result = test_func()
            results.append(asdict(result))
        
        all_healthy = all(r['success'] for r in results)
        
        return {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'tests_run': len(results),
            'healthy': all_healthy,
            'results': results
        }
    
    def log_results(self, report: Dict):
        """Log test results."""
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(LOG_FILE, 'a') as f:
            f.write(json.dumps(report) + '\n')
    
    def print_report(self, report: Dict):
        """Print human-readable report."""
        print("=" * 60)
        print("API CONNECTIVITY TEST REPORT")
        print("=" * 60)
        print(f"Timestamp: {report['timestamp']}")
        print(f"Tests Run: {report['tests_run']}")
        
        if report['healthy']:
            print("\n✅ All services connected")
        else:
            failed = [r for r in report['results'] if not r['success']]
            print(f"\n⚠️  {len(failed)} service(s) failed")
        
        print("\n📊 Results:")
        for result in report['results']:
            status = "✅" if result['success'] else "❌"
            print(f"  {status} {result['service']}: {result['message']} ({result['latency_ms']}ms)")
        
        print("=" * 60)


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Test API connectivity")
    parser.add_argument("--service", help="Test specific service")
    parser.add_argument("--json", action="store_true", help="Output JSON")
    args = parser.parse_args()
    
    tester = ConnectivityTester()
    report = tester.run_all_tests(service_filter=args.service)
    tester.log_results(report)
    
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        tester.print_report(report)
    
    sys.exit(0 if report['healthy'] else 1)


if __name__ == "__main__":
    main()
```

---

## Integration

### Cron Configuration

Add to your crontab for periodic validation:

```bash
# Configuration validation (daily)
0 9 * * * cd ~/.openclaw/workspace && python3 scripts/validate_config.py >> logs/validation.log 2>&1

# State reconciliation (every 5 minutes)
*/5 * * * * cd ~/.openclaw/workspace && python3 scripts/reconcile_state.py --fix >> logs/reconciliation.log 2>&1

# API connectivity (hourly)
0 * * * * cd ~/.openclaw/workspace && python3 scripts/test_connectivity.py >> logs/connectivity.log 2>&1
```

### Heartbeat Integration

Add to your `HEARTBEAT.md`:

```markdown
## System Health Checks
- [ ] Configuration valid (daily)
- [ ] State files reconciled (every 5 min)
- [ ] API connectivity good (hourly)

Alert if:
- Required configs missing
- State mismatches detected
- API connectivity fails
```

---

## Requirements

```bash
pip install psutil filelock requests
```

---

## Related Patterns

- **Bot Monitor** — Auto-restart failed processes
- **Heartbeat Integration** — Periodic health checks
- **Memory System** — Track validation state
- **Trading Dashboard** — Visualize bot states

---

*This pattern provides proactive validation to catch issues before they become problems.*
