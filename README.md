# GigaAlpha Pipeline

A professional quant backtesting and alpha scanning pipeline.

## 🚀 Setup & Installation

### 1. Environment Setup

It is highly recommended to use a separate **Conda** environment.

**Step-by-step Setup:**
```bash
# Create atmosphere manually
conda create -n GigaAlpha python=3.10 -y

# Activate the environment
conda activate GigaAlpha

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration (Secrets)

Copy the template secrets file to the project root and fill in your credentials:

```bash
cp configs/.env.example .env
```

**Required Credentials:**
- **MongoDB**: For downloading tick data.
- **Google Drive**: For uploading reports (requires `OAuth2_token.pickle`).

---

## ⚡ Quick Start (Run with Sample Data)

You can run a quick scan using the provided sample data to verify your installation:
```bash
python gigaalpha/scripts/scan.py --config configs/scan_sample.yaml
```

---

## 📊 Usage

### Run Scan Pipeline
Run the main scanning pipeline with a specific configuration:
```bash
python gigaalpha/scripts/scan.py --config configs/default.yaml
```

### Run Sequential Backtest
Run a simple backtest for a single configuration:
```bash
python gigaalpha/scripts/run.py --config configs/default.yaml
```

---

## 📂 Project Structure

- `gigaalpha/scripts/`: Entry point scripts.
- `gigaalpha/services/`: Business logic (Backtest, Upload, Scoring, etc.)
- `gigaalpha/core/`: Low-level engine (Simulator, Registry).
- `gigaalpha/helpers/`: Third-party integrations (Google Drive, System utilities).
- `configs/`: YAML configuration files.
- `logs/`: System and debug logs.
- `outputs/`: Generated HTML charts and Excel reports.
