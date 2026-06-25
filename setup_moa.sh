#!/bin/bash

# ═══════════════════════════════════════════════════════
#  MoA Setup — Sets environment variable for OpenRouter
#  (macOS / Linux / WSL)
# ═══════════════════════════════════════════════════════

# ANSI colors
RED='\033[91m'
GREEN='\033[92m'
YELLOW='\033[93m'
CYAN='\033[96m'
RESET='\033[0m'

echo -e ""
echo -e "  ${CYAN}╔══════════════════════════════════════╗${RESET}"
echo -e "  ${CYAN}║  MoA — Mixture of Agents Setup       ║${RESET}"
echo -e "  ${CYAN}║  (macOS / Linux / WSL)               ║${RESET}"
echo -e "  ${CYAN}╚══════════════════════════════════════╝${RESET}"
echo -e ""

# Prompt user for API key
read -p "  Enter your OpenRouter API key: " api_key

if [ -z "$api_key" ]; then
    echo -e "  ${RED}Error: API key cannot be empty.${RESET}"
    exit 1
fi

# Save to .env in the script's directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
ENV_FILE="$SCRIPT_DIR/.env"

echo "OPENROUTER_API_KEY=$api_key" > "$ENV_FILE"

echo -e ""
echo -e "  ${GREEN}✓ API key saved to .env file!${RESET}"
echo -e ""
echo -e "  ${YELLOW}Usage:${RESET}"
echo -e "    python moa.py \"your prompt here\""
echo -e "    python moa.py --verbose \"your prompt\""
echo -e "    python moa.py --mode judge \"your prompt\""
echo -e "    python moa.py --list-models"
echo -e ""
