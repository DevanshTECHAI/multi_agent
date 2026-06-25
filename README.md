# 🧬 Mixture of Agents (MoA) CLI

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A lightweight, zero-dependency command-line interface implementation of **Mixture of Agents (MoA)**. This tool queries multiple LLMs in parallel and aggregates or judges their responses to produce a single, highly refined output.

It runs entirely on Python's standard library (no `pip install` required!) and integrates with **OpenRouter** to access state-of-the-art models.

---

## ✨ Features

- **Zero Dependencies**: Written using Python's native `urllib` and `concurrent.futures`. Just run it immediately!
- **Mixture of Agents Architecture**: 
  - **Synthesize Mode** (Default): Queries specialized models in parallel, then uses a primary aggregator model to synthesize their outputs into a single, comprehensive response.
  - **Judge Mode**: Queries models in parallel, then uses the aggregator to select the single best response and explain why.
- **Beautiful Terminal Output**: Features rich color-coded status, timing indicators, and formatted output wrappers.
- **Cross-Platform**: Ready-to-use setup scripts for Windows (`.ps1`) and macOS/Linux/WSL (`.sh`).
- **Flexible Inputs**: Supports command arguments, piping inputs from standard input (`stdin`), or filtering queries to specific model indexes.

---

## 🔑 Getting Your OpenRouter API Key

This project uses **OpenRouter** to query various models in parallel.

1. Go to [OpenRouter.ai](https://openrouter.ai/).
2. Create an account or sign in.
3. Navigate to **Keys** in the sidebar or go to [openrouter.ai/keys](https://openrouter.ai/keys).
4. Click **Create Key**, give it a name, and copy the generated key (`sk-or-v1-...`).
5. Ensure you have some free credits or balance on your account to run queries (many models configured in `moa.py` are free!).

---

## 🚀 Setup Instructions

Clone the repository (or copy the files into a directory) and choose one of the setup methods below:

### Option A: Automatic Setup (Recommended)

#### **Windows (PowerShell)**
Run the setup PowerShell script:
```powershell
./setup_moa.ps1
```
*This will securely prompt you for your API key, configure it for your current PowerShell session, and persist it in your User Environment Variables.*

#### **macOS / Linux / WSL (Terminal)**
Run the setup Bash script:
```bash
chmod +x setup_moa.sh
./setup_moa.sh
```
*This script prompts you for your API key and automatically creates a `.env` file in the project directory.*

---

### Option B: Manual Setup

You can manually configure your key in one of three ways:

1. **Create a `.env` file** in the project root:
   ```env
   OPENROUTER_API_KEY=sk-or-v1-...
   ```
2. **Set a temporary environment variable** in your terminal:
   - **Bash/Zsh (macOS/Linux)**: `export OPENROUTER_API_KEY=sk-or-v1-...`
   - **PowerShell (Windows)**: `$env:OPENROUTER_API_KEY="sk-or-v1-..."`
   - **Command Prompt (Windows)**: `set OPENROUTER_API_KEY=sk-or-v1-...`
3. **Use a `.moa_config` file** in the project root containing just your key:
   ```text
   sk-or-v1-...
   ```

---

## 📖 How to Use

Run the script using `python moa.py` followed by your prompt.

### 1. Basic Synthesis (Default)
Queries all active models in parallel and synthesizes the best output using the aggregator model.
```bash
python moa.py "Write a short poem about coding at midnight."
```

### 2. Verbose Mode
Shows the individual responses from each model before printing the final synthesized answer.
```bash
python moa.py --verbose "Compare Python and Go for web servers."
```

### 3. Judge Mode
Instead of combining the answers, the aggregator acts as a judge, selects the single best response, and explains its reasoning.
```bash
python moa.py --mode judge "What is the time complexity of bubble sort vs quicksort?"
```

### 4. Standard Input (Piping)
Pipe prompts from other commands. Useful for scripting.
```bash
echo "Summarize the history of space travel in 3 bullet points" | python moa.py --stdin
```

### 5. Filter Models
You can run a query using only specific models by passing their indexes (1-8):
```bash
# Query only the 1st and 3rd models
python moa.py "Write a hello world program in Rust" --models 1 3
```

### 6. List Models
Show all available models, their roles, and their corresponding index:
```bash
python moa.py --list-models
```

---

## 🛠️ Configuration

You can customize the models and the aggregator by modifying the variables at the top of [moa.py](file:///c:/Users/devan/OneDrive/Desktop/anti/moa.py):

* **`MODELS`**: The list of models to run in parallel.
* **`AGGREGATOR_MODEL_ID`**: The model responsible for synthesizing or judging the results.

By default, the script is configured to use free models from OpenRouter:
- Nemotron Ultra 550B (Aggregator & Reasoning)
- Laguna M.1 (Code)
- GPT-OSS 120B (General)
- Laguna XS.2 (Code)
- Gemma 4 31B (General)
- Nemotron Nano 30B (Fast)
- North Mini Code (Code)
- Nemotron Nano Reasoning (Reasoning)

---

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.
