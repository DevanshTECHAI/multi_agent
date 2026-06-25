#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════╗
║  MoA — Mixture of Agents                                    ║
║  Queries multiple AI models in parallel, then synthesizes   ║
║  the best combined response from all of them.               ║
╚══════════════════════════════════════════════════════════════╝

Usage:
    python moa.py "your prompt here"
    python moa.py --verbose "your prompt here"
    python moa.py --mode judge "your prompt here"
    echo "prompt" | python moa.py --stdin

Set your OpenRouter API key:
    set OPENROUTER_API_KEY=sk-or-...
"""

import urllib.request
import urllib.error
import json
import sys
import os
import time
import concurrent.futures
import argparse
import textwrap

# Fix Windows terminal encoding
if sys.platform == "win32":
    os.system("")  # Enable ANSI escape codes on Windows
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# ─── Configuration ───────────────────────────────────────────

OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".moa_config")

MODELS = [
    {"id": "nvidia/nemotron-3-ultra-550b-a55b:free",               "name": "Nemotron Ultra 550B",      "role": "reasoning"},
    {"id": "poolside/laguna-m.1:free",                              "name": "Laguna M.1",               "role": "code"},
    {"id": "openai/gpt-oss-120b:free",                              "name": "GPT-OSS 120B",             "role": "general"},
    {"id": "poolside/laguna-xs.2:free",                             "name": "Laguna XS.2",              "role": "code"},
    {"id": "google/gemma-4-31b-it:free",                            "name": "Gemma 4 31B",              "role": "general"},
    {"id": "nvidia/nemotron-3-nano-30b-a3b:free",                   "name": "Nemotron Nano 30B",        "role": "fast"},
    {"id": "cohere/north-mini-code:free",                           "name": "North Mini Code",          "role": "code"},
    {"id": "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free",    "name": "Nemotron Nano Reasoning",  "role": "reasoning"},
]

AGGREGATOR_MODEL_ID = "nvidia/nemotron-3-ultra-550b-a55b:free"


def load_api_key() -> str:
    """Load API key from env var, .env file, or config file."""
    # 1. Check environment variable
    key = os.environ.get("OPENROUTER_API_KEY", "")
    if key:
        return key

    # 2. Check .env file in same directory
    env_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    if os.path.exists(env_file):
        with open(env_file, "r") as f:
            for line in f:
                line = line.strip()
                if line.startswith("OPENROUTER_API_KEY="):
                    key = line.split("=", 1)[1].strip().strip('"').strip("'")
                    if key:
                        return key

    # 3. Check config file
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            key = f.read().strip()
            if key:
                return key

    return ""

# ─── Terminal Colors ─────────────────────────────────────────

class C:
    """ANSI color codes for terminal output."""
    RESET   = "\033[0m"
    BOLD    = "\033[1m"
    DIM     = "\033[2m"
    CYAN    = "\033[96m"
    GREEN   = "\033[92m"
    YELLOW  = "\033[93m"
    RED     = "\033[91m"
    MAGENTA = "\033[95m"
    BLUE    = "\033[94m"
    WHITE   = "\033[97m"
    BG_DARK = "\033[48;5;236m"

ROLE_COLORS = {
    "reasoning": C.MAGENTA,
    "code":      C.CYAN,
    "general":   C.GREEN,
    "fast":      C.YELLOW,
}

# ─── API Functions ───────────────────────────────────────────

def query_openrouter(api_key: str, model_id: str, messages: list, max_tokens: int = 4096, timeout: int = 120) -> dict:
    """Send a chat completion request to OpenRouter."""
    payload = json.dumps({
        "model": model_id,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": 0.7,
    }).encode("utf-8")

    req = urllib.request.Request(
        OPENROUTER_API_URL,
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
            "HTTP-Referer": "https://github.com/moa-cli",
            "X-Title": "MoA CLI",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8", errors="replace")
        return {"error": f"HTTP {e.code}: {error_body}"}
    except urllib.error.URLError as e:
        return {"error": f"Connection error: {e.reason}"}
    except Exception as e:
        return {"error": str(e)}


def extract_response(result: dict) -> str | None:
    """Extract the text response from an OpenRouter API result."""
    if "error" in result:
        return None
    try:
        return result["choices"][0]["message"]["content"]
    except (KeyError, IndexError):
        return None

# ─── Core Logic ──────────────────────────────────────────────

def query_single_model(api_key: str, model: dict, prompt: str) -> dict:
    """Query a single model and return results with metadata."""
    start = time.time()
    messages = [{"role": "user", "content": prompt}]
    result = query_openrouter(api_key, model["id"], messages)
    elapsed = time.time() - start
    response_text = extract_response(result)

    return {
        "model": model,
        "response": response_text,
        "error": result.get("error") if response_text is None else None,
        "time": elapsed,
    }


def query_all_models(api_key: str, prompt: str, models: list = None, max_workers: int = 8) -> list[dict]:
    """Query all models in parallel."""
    if models is None:
        models = MODELS
    results = []

    print(f"\n{C.BOLD}{C.CYAN}╔══════════════════════════════════════════════════════════╗{C.RESET}")
    print(f"{C.BOLD}{C.CYAN}║  🧠 MoA — Querying {len(models)} models in parallel...              ║{C.RESET}")
    print(f"{C.BOLD}{C.CYAN}╚══════════════════════════════════════════════════════════╝{C.RESET}\n")

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_model = {
            executor.submit(query_single_model, api_key, model, prompt): model
            for model in models
        }

        for future in concurrent.futures.as_completed(future_to_model):
            result = future.result()
            model = result["model"]
            color = ROLE_COLORS.get(model["role"], C.WHITE)
            status = f"{C.GREEN}✓{C.RESET}" if result["response"] else f"{C.RED}✗{C.RESET}"
            time_str = f"{result['time']:.1f}s"

            print(f"  {status}  {color}{model['name']:.<35}{C.RESET} {C.DIM}{time_str:>6}{C.RESET}  {C.DIM}[{model['role']}]{C.RESET}")
            results.append(result)

    return results


def aggregate_synthesize(api_key: str, prompt: str, results: list[dict]) -> str:
    """Synthesize the best combined response from all model outputs."""
    successful = [r for r in results if r["response"]]

    if not successful:
        return "❌ All models failed. Check your API key and rate limits."

    if len(successful) == 1:
        return successful[0]["response"]

    # Build the aggregation prompt
    responses_text = ""
    for i, r in enumerate(successful, 1):
        model_name = r["model"]["name"]
        role = r["model"]["role"]
        responses_text += f"\n--- Response {i} from {model_name} ({role} specialist) ---\n"
        responses_text += r["response"]
        responses_text += "\n"

    aggregation_prompt = f"""You are an expert aggregator. You have received responses from {len(successful)} different AI models to the same user prompt. Your job is to synthesize the BEST possible response by:

1. Identifying the strongest points from each response
2. Combining the best reasoning, code, and explanations
3. Resolving any contradictions by picking the most accurate answer
4. Producing a single, polished, comprehensive response

IMPORTANT: Output ONLY the final synthesized response. Do NOT mention that you're aggregating or reference the individual models.

=== ORIGINAL USER PROMPT ===
{prompt}

=== MODEL RESPONSES ==={responses_text}

=== YOUR SYNTHESIZED BEST RESPONSE ==="""

    print(f"\n{C.BOLD}{C.MAGENTA}  ⚡ Synthesizing with {AGGREGATOR_MODEL_ID.split('/')[1].split(':')[0]}...{C.RESET}")

    start = time.time()
    messages = [{"role": "user", "content": aggregation_prompt}]
    result = query_openrouter(api_key, AGGREGATOR_MODEL_ID, messages, max_tokens=8192, timeout=180)
    elapsed = time.time() - start

    response = extract_response(result)
    if response:
        print(f"  {C.GREEN}✓{C.RESET}  Synthesis complete in {elapsed:.1f}s")
        return response
    else:
        # Fallback: return the longest successful response
        print(f"  {C.YELLOW}⚠{C.RESET}  Aggregator failed, returning best individual response")
        return max(successful, key=lambda r: len(r["response"]))["response"]


def aggregate_judge(api_key: str, prompt: str, results: list[dict]) -> str:
    """Have the aggregator pick the single best response."""
    successful = [r for r in results if r["response"]]

    if not successful:
        return "❌ All models failed. Check your API key and rate limits."

    if len(successful) == 1:
        return successful[0]["response"]

    responses_text = ""
    for i, r in enumerate(successful, 1):
        model_name = r["model"]["name"]
        responses_text += f"\n--- Response {i} from {model_name} ---\n"
        responses_text += r["response"]
        responses_text += "\n"

    judge_prompt = f"""You are a judge. You have {len(successful)} responses to the same prompt. 
Pick the SINGLE BEST response. Output ONLY the number of the best response on the first line, 
then explain briefly why it's the best.

=== ORIGINAL PROMPT ===
{prompt}

=== RESPONSES ==={responses_text}

=== YOUR JUDGMENT (response number first, then brief reasoning) ==="""

    print(f"\n{C.BOLD}{C.MAGENTA}  ⚖️  Judging with {AGGREGATOR_MODEL_ID.split('/')[1].split(':')[0]}...{C.RESET}")

    start = time.time()
    messages = [{"role": "user", "content": judge_prompt}]
    result = query_openrouter(api_key, AGGREGATOR_MODEL_ID, messages, max_tokens=2048, timeout=120)
    elapsed = time.time() - start

    judgment = extract_response(result)
    if judgment:
        # Try to extract the winning response number
        try:
            first_line = judgment.strip().split("\n")[0]
            winner_num = int("".join(c for c in first_line if c.isdigit())[:1])
            if 1 <= winner_num <= len(successful):
                winner = successful[winner_num - 1]
                print(f"  {C.GREEN}✓{C.RESET}  Winner: {winner['model']['name']} (judged in {elapsed:.1f}s)")
                return f"{winner['response']}\n\n{C.DIM}---\n🏆 Selected: {winner['model']['name']}\n📝 Reason: {judgment}{C.RESET}"
        except (ValueError, IndexError):
            pass

        print(f"  {C.YELLOW}⚠{C.RESET}  Could not parse winner, returning judgment")
        return judgment
    else:
        return max(successful, key=lambda r: len(r["response"]))["response"]

# ─── Display ─────────────────────────────────────────────────

def print_individual_responses(results: list[dict]):
    """Print each model's individual response (verbose mode)."""
    successful = [r for r in results if r["response"]]

    print(f"\n{C.BOLD}{C.BLUE}{'═' * 60}{C.RESET}")
    print(f"{C.BOLD}{C.BLUE}  📋 Individual Model Responses ({len(successful)}/{len(results)} succeeded){C.RESET}")
    print(f"{C.BOLD}{C.BLUE}{'═' * 60}{C.RESET}")

    for r in results:
        model = r["model"]
        color = ROLE_COLORS.get(model["role"], C.WHITE)

        print(f"\n{color}{'─' * 50}{C.RESET}")
        print(f"{C.BOLD}{color}  {model['name']}{C.RESET}  {C.DIM}[{model['role']}] {r['time']:.1f}s{C.RESET}")
        print(f"{color}{'─' * 50}{C.RESET}")

        if r["response"]:
            # Indent the response slightly
            for line in r["response"].split("\n"):
                print(f"  {line}")
        else:
            print(f"  {C.RED}Error: {r['error']}{C.RESET}")


def print_final_response(response: str, mode: str):
    """Print the final synthesized/judged response."""
    mode_label = "🧬 Synthesized" if mode == "synthesize" else "⚖️  Judged"

    print(f"\n{C.BOLD}{C.GREEN}{'═' * 60}{C.RESET}")
    print(f"{C.BOLD}{C.GREEN}  {mode_label} Final Response{C.RESET}")
    print(f"{C.BOLD}{C.GREEN}{'═' * 60}{C.RESET}\n")
    print(response)
    print(f"\n{C.BOLD}{C.GREEN}{'═' * 60}{C.RESET}")

# ─── Main ────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="MoA — Mixture of Agents: Query multiple AI models and get one best answer.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""
        Examples:
          python moa.py "explain quicksort"
          python moa.py --verbose "write a web server in Python"
          python moa.py --mode judge "what is the best sorting algorithm?"
          echo "hello" | python moa.py --stdin
        """),
    )
    parser.add_argument("prompt", nargs="?", help="The prompt to send to all models")
    parser.add_argument("--mode", choices=["synthesize", "judge"], default="synthesize",
                        help="Aggregation mode: 'synthesize' (combine best parts) or 'judge' (pick winner)")
    parser.add_argument("--verbose", "-v", action="store_true",
                        help="Show individual model responses before the final answer")
    parser.add_argument("--stdin", action="store_true",
                        help="Read prompt from stdin")
    parser.add_argument("--models", nargs="+", type=int,
                        help="Only use specific models by index (1-8)")
    parser.add_argument("--list-models", action="store_true",
                        help="List all available models and exit")
    parser.add_argument("--timeout", type=int, default=120,
                        help="Timeout per model in seconds (default: 120)")

    args = parser.parse_args()

    # List models
    if args.list_models:
        print(f"\n{C.BOLD}  Available Models:{C.RESET}\n")
        for i, m in enumerate(MODELS, 1):
            color = ROLE_COLORS.get(m["role"], C.WHITE)
            print(f"  {C.BOLD}{i}.{C.RESET}  {color}{m['name']:.<35}{C.RESET}  {C.DIM}{m['id']}{C.RESET}  [{m['role']}]")
        print()
        return

    # Get prompt
    if args.stdin:
        prompt = sys.stdin.read().strip()
    elif args.prompt:
        prompt = args.prompt
    else:
        parser.print_help()
        sys.exit(1)

    if not prompt:
        print(f"{C.RED}Error: Empty prompt{C.RESET}")
        sys.exit(1)

    # Get API key
    api_key = load_api_key()
    if not api_key:
        print(f"\n{C.RED}  ❌ OPENROUTER_API_KEY not found!{C.RESET}")
        print(f"  {C.DIM}Fix: Create a .env file in this folder with:{C.RESET}")
        print(f"  {C.DIM}  OPENROUTER_API_KEY=sk-or-...{C.RESET}")
        print(f"  {C.DIM}Or set env var: set OPENROUTER_API_KEY=sk-or-...{C.RESET}\n")
        sys.exit(1)

    # Filter models if specified
    active_models = list(MODELS)
    if args.models:
        selected = []
        for idx in args.models:
            if 1 <= idx <= len(MODELS):
                selected.append(MODELS[idx - 1])
            else:
                print(f"{C.YELLOW}Warning: Model index {idx} out of range (1-{len(MODELS)}){C.RESET}")
        if selected:
            active_models = selected

    # Show prompt
    print(f"\n{C.DIM}  Prompt: {prompt[:80]}{'...' if len(prompt) > 80 else ''}{C.RESET}")

    # Query all models
    total_start = time.time()
    results = query_all_models(api_key, prompt, active_models)
    total_time = time.time() - total_start

    successful = sum(1 for r in results if r["response"])
    print(f"\n  {C.DIM}📊 {successful}/{len(results)} models responded in {total_time:.1f}s{C.RESET}")

    # Show individual responses in verbose mode
    if args.verbose:
        print_individual_responses(results)

    # Aggregate
    if args.mode == "judge":
        final = aggregate_judge(api_key, prompt, results)
    else:
        final = aggregate_synthesize(api_key, prompt, results)

    # Display final response
    print_final_response(final, args.mode)

    # Summary
    print(f"\n  {C.DIM}⏱  Total time: {time.time() - total_start:.1f}s | Models: {successful}/{len(results)} | Mode: {args.mode}{C.RESET}\n")


if __name__ == "__main__":
    main()
