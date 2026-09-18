# PE6201 A2 — Applied AI System

**Group 2** · Problem B: Outpatient referral coordination

---

## Quick Start

### Prerequisites
- Python 3.10+
- No API key needed for the default scripted run

### Install & Run

```bash
git clone https://github.com/leokk1905/PE6201_A2_B3.git
cd PE6201_A2_B3/A2_scaffold
python run_eval.py
```

Expected output:
- 41 scripted cases
- ~80 trials
- 100% pass rate (scripted backend is deterministic)

---

## Project Structure

```
A2_scaffold/
├── agent.py              # ReAct agent loop
├── backends.py           # Scripted + live backend
├── config.py             # Configuration (model, prices, problem)
├── guardrails.py         # Safety guardrails
├── harness.py            # Evaluation framework
├── prompt.py             # System prompt builder
├── run_eval.py           # Entry point
├── tools.py              # Tool registry & implementations
├── evaluation_cases.json # 40 evaluation cases (32 ordinary + 8 negative)
├── results/              # Model battery results
└── A2_reference_data/    # Reference data & answer key
```

---

## Evaluation Set

- **40 evaluation cases** (REF-EV001 to REF-EV040)
- 32 ordinary cases (1 trial each)
- 8 negative cases (3 trials each)
- Total: 56 trials per model run

---

## Running the Live Battery (D5b)

```bash
# Set your OpenRouter API key
export OPENROUTER_API_KEY="sk-or-..."

# Set version (v1 for D2b comparison, v2 for final)
export VERSION="v2"

# Run the full battery
python run_eval.py --battery
```

Results are written to `results_d5_live.json`.

---

## Results Summary

| Model | Version | Pass Rate | Negative Pass Rate | Cost |
|-------|---------|-----------|-------------------|------|
| gpt-4o-mini | v1 | 51.8% | 75.0% | $0.064 |

*Full results in `results/` directory.*

---

## Team

| Member | Contribution |
|--------|-------------|
| Wang Kenan | D4 (evaluation cases), D5a (scripted backend), D5b (Model A v1) |
| ... | ... |

See [CONTRIBUTIONS.md](CONTRIBUTIONS.md) for full details.

---

## License

This project is for academic use at NTU.
