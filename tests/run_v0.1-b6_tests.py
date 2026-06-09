#!/usr/bin/env python3
"""Automated test runner for v0.1-b6 CLAP features.

Runs the full CLAP workflow and saves results to a file.
Can be run as a cron job or manually.
"""

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

PROJECT_DIR = Path.home() / "audio-metadata-manager"
EXAMPLES_DIR = PROJECT_DIR / "examples"
FIXTURES_DIR = EXAMPLES_DIR / "fixtures"
OUTPUT_DIR = PROJECT_DIR / "out"
TEST_REPORT = OUTPUT_DIR / "v0.1-b6-test-report.json"

def run_command(cmd: list[str], capture: bool = True) -> tuple[int, str]:
    """Run a shell command and return exit code + output."""
    try:
        result = subprocess.run(
            cmd,
            cwd=PROJECT_DIR,
            capture_output=capture,
            text=True,
            timeout=300,  # 5 min timeout
        )
        output = result.stdout + result.stderr
        return result.returncode, output.strip()
    except subprocess.TimeoutExpired:
        return -1, "TIMEOUT (exceeded 5 minutes)"
    except Exception as e:
        return -1, f"ERROR: {e}"

def check_clap_installed() -> bool:
    """Check if CLAP is installed."""
    code, _ = run_command([
        sys.executable, "-c",
        "import laion_clap; print('CLAP installed')"
    ])
    return code == 0

def test_index() -> dict:
    """Test indexing fixtures."""
    output_json = OUTPUT_DIR / "test-library.json"
    code, output = run_command([
        sys.executable, str(PROJECT_DIR / "app.py"),
        "index",
        "--input", str(FIXTURES_DIR),
        "--output", str(output_json),
    ])
    return {
        "test": "index",
        "success": code == 0,
        "output": output[:500] if output else "",
        "exit_code": code,
    }

def test_compute_embeddings() -> dict:
    """Test CLAP embedding computation."""
    output_json = OUTPUT_DIR / "test-embeddings.json"
    code, output = run_command([
        sys.executable, str(PROJECT_DIR / "app.py"),
        "compute-embeddings",
        "--input", str(FIXTURES_DIR),
        "--output", str(output_json),
        "--device", "cpu",
        "-v",
    ])
    return {
        "test": "compute-embeddings",
        "success": code == 0,
        "output": output[:1000] if output else "",
        "exit_code": code,
        "embeddings_file": str(output_json) if code == 0 else None,
    }

def test_semantic_search(embeddings_file: str) -> dict:
    """Test semantic search."""
    if not Path(embeddings_file).exists():
        return {
            "test": "semantic-search",
            "success": False,
            "output": "Embeddings file not found",
            "exit_code": -1,
        }
    
    code, output = run_command([
        sys.executable, str(PROJECT_DIR / "app.py"),
        "semantic-search",
        "--query", "bright tone",
        "--embeddings", embeddings_file,
        "--top-k", "5",
        "-v",
    ])
    return {
        "test": "semantic-search",
        "success": code == 0,
        "output": output[:1000] if output else "",
        "exit_code": code,
    }

def test_hybrid_search() -> dict:
    """Test hybrid search."""
    library_file = OUTPUT_DIR / "test-library.json"
    embeddings_file = OUTPUT_DIR / "test-embeddings.json"
    
    if not Path(library_file).exists():
        return {
            "test": "hybrid-search",
            "success": False,
            "output": "Library file not found (run index first)",
            "exit_code": -1,
        }
    
    if not Path(embeddings_file).exists():
        return {
            "test": "hybrid-search",
            "success": False,
            "output": "Embeddings file not found (run compute-embeddings first)",
            "exit_code": -1,
        }
    
    code, output = run_command([
        sys.executable, str(PROJECT_DIR / "app.py"),
        "hybrid-search",
        "--query", "bright tone around 440 bpm",
        "--input", str(library_file),
        "--embeddings", str(embeddings_file),
        "--top-k", "5",
        "-v",
    ])
    return {
        "test": "hybrid-search",
        "success": code == 0,
        "output": output[:1000] if output else "",
        "exit_code": code,
    }

def main():
    """Run all tests and generate report."""
    print("=" * 60)
    print("v0.1-b6 Automated Test Runner")
    print(f"Started: {datetime.now().isoformat()}")
    print("=" * 60)
    
    # Ensure output directory exists
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Check CLAP
    clap_installed = check_clap_installed()
    print(f"\nCLAP installed: {clap_installed}")
    
    results = {
        "timestamp": datetime.now().isoformat(),
        "clap_installed": clap_installed,
        "tests": [],
    }
    
    # Test 1: Index
    print("\n[1/4] Testing index...")
    index_result = test_index()
    results["tests"].append(index_result)
    print(f"  Result: {'✅ PASS' if index_result['success'] else '❌ FAIL'}")
    
    if not clap_installed:
        print("\n⚠️  CLAP not installed. Skipping CLAP tests.")
        print("Install with: pip install -r requirements-optional.txt")
        results["skipped"] = ["compute-embeddings", "semantic-search", "hybrid-search"]
    else:
        # Test 2: Compute Embeddings
        print("\n[2/4] Testing compute-embeddings...")
        embed_result = test_compute_embeddings()
        results["tests"].append(embed_result)
        print(f"  Result: {'✅ PASS' if embed_result['success'] else '❌ FAIL'}")
        
        # Test 3: Semantic Search
        print("\n[3/4] Testing semantic-search...")
        semantic_result = test_semantic_search(embed_result.get("embeddings_file", ""))
        results["tests"].append(semantic_result)
        print(f"  Result: {'✅ PASS' if semantic_result['success'] else '❌ FAIL'}")
        
        # Test 4: Hybrid Search
        print("\n[4/4] Testing hybrid-search...")
        hybrid_result = test_hybrid_search()
        results["tests"].append(hybrid_result)
        print(f"  Result: {'✅ PASS' if hybrid_result['success'] else '❌ FAIL'}")
    
    # Summary
    passed = sum(1 for t in results["tests"] if t["success"])
    total = len(results["tests"])
    results["summary"] = {
        "passed": passed,
        "total": total,
        "all_passed": passed == total,
    }
    
    print("\n" + "=" * 60)
    print(f"SUMMARY: {passed}/{total} tests passed")
    print("=" * 60)
    
    # Save report
    with open(TEST_REPORT, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\nReport saved to: {TEST_REPORT}")
    
    # Also save human-readable summary
    summary_file = OUTPUT_DIR / "v0.1-b6-test-summary.txt"
    with open(summary_file, "w", encoding="utf-8") as f:
        f.write(f"v0.1-b6 Test Summary\n")
        f.write(f"Generated: {results['timestamp']}\n")
        f.write(f"CLAP Installed: {results['clap_installed']}\n")
        f.write(f"\nResults: {passed}/{total} passed\n\n")
        
        for test in results["tests"]:
            status = "✅ PASS" if test["success"] else "❌ FAIL"
            f.write(f"{test['test']}: {status}\n")
            if test["output"]:
                f.write(f"  Output: {test['output'][:200]}...\n")
        
        if "skipped" in results:
            f.write(f"\nSkipped (CLAP not installed): {', '.join(results['skipped'])}\n")
    
    print(f"Summary saved to: {summary_file}")
    
    return 0 if results["summary"]["all_passed"] else 1

if __name__ == "__main__":
    sys.exit(main())
