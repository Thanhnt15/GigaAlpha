# 🚀 GigaAlpha: Advanced Trading Strategy Backtesting & Analytics

GigaAlpha is a high-performance, modular backtesting engine designed for rapid strategy exploration and quantitative analysis. It leverages parallel processing to scan thousands of parameter combinations and generates interactive, cloud-ready reports.

---

## ✨ Key Features

- **High-Performance Parallel Engine**: Utilize multi-core processing for hyper-fast backtesting and scoring.
- **Interactive 3D Visualization**: Generate professional-grade Plotly charts for strategy parameter optimization.
- **Unified Service Architecture**: Modular design separating business logic (Services) from atomic tools (Utils) and core simulation.
- **Automated Cloud Integration**: 
  - **Google Drive**: Seamlessly upload Excel reports with link tracking.
  - **GitHub Pages**: Automatically host interactive HTML charts for online access.
- **Flexible Configuration**: Full control via structured YAML manifests.

---

## 🛠 Project Architecture

GigaAlpha follows a **Service-Oriented Architecture (SOA)** for scalability and maintainability:

- `gigaalpha/services/`: Core business logic orchestration (e.g., `backtest_service.py`, `upload_service.py`).
- `gigaalpha/core/`: The underlying simulation engine and parameter registry.
- `gigaalpha/helpers/`: Third-party integration handlers (Google Drive, Git).
- `gigaalpha/utils/`: Atomic, side-effect-free utility functions for formatting and metrics.
- `configs/`: Centralized YAML configuration management.

---

## 🚀 Getting Started

### 1. Installation
Ensure you have Python 3.8+ installed. Clone the repository and install dependencies:

```bash
git clone https://github.com/Thanhnt15/GigaAlpha.git
cd GigaAlpha
pip install -r requirements.txt
```

### 2. Environment Configuration
Copy the template environment file and fill in your credentials:

```bash
cp .env.example .env
```

**Required Environment Variables:**
- `GDRIVE_TOKEN_PATH`: Absolute path to your Google Drive `token.json`.

### 3. Google Drive Authentication
If using automated uploads, ensure your `credentials.json` is configured in the root directory and run a local scan to authorize the first time.

---

## 📊 Usage

### Running the Scan Pipeline
The main entry point for batch strategy analysis:

```bash
python gigaalpha/scripts/scan.py --config configs/default.yaml
```

### Configuration Management
Strategies are managed via YAML files. A typical pipeline flow includes:
1. **Data**: Point to your dataset.
2. **Backtest**: Define parameters and core counts.
3. **Scoring**: Enable automated strategy ranking.
4. **Storage/Visualize**: Local artifact generation.
5. **Upload/Deploy**: Cloud synchronization.

---

## 🌐 Advanced Integration

### Interactive Web Reports
GigaAlpha can automatically host your 3D charts on the web. 
See [HTML Chart Deployment Guide](docs/HTML_CHARTS_DEPLOYMENT.md) for detailed setup instructions.

---

## 📂 Directory Layout

- `gigaalpha/`: Main package source code.
- `configs/`: YAML manifest files for different scenarios.
- `docs/`: Technical documentation and guides.
- `logs/`: Execution logs and link tracking (ignored by Git).
- `outputs/`: Generated Excel and HTML artifacts (ignored by Git).

---
*GigaAlpha — Empowering Quantitative Research with Performance and Automation.* 🚀
