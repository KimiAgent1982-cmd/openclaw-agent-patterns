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

# Required configuration keys with validation
REQUIRED_CONFIGS = {
    "BRAVE_API_KEY": {
        "description": "Brave Search API for web searches",
        "test_method": "brave"
    },
    "MOONSHOT_API_KEY": {
        "description": "Moonshot LLM API (primary)",
        "optional": True,
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
        "test_method": "telegram"
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
    
    def test_telegram_api(self, token: str) -> Tuple[bool, str]:
        """Test Telegram bot API."""
        try:
            import requests
            response = requests.get(
                f"https://api.telegram.org/bot{token}/getMe",
                timeout=10
            )
            if response.status_code == 200 and response.json().get('ok'):
                return True, "Token valid"
            else:
                return False, "Invalid token"
        except ImportError:
            return False, "requests library not installed"
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
                    elif meta["test_method"] == "telegram":
                        success, msg = self.test_telegram_api(configs[key])
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
