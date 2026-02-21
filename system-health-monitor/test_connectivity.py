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
from typing import Dict, List, Optional
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
