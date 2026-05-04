# ================================
# NO2 Forecasting Pipeline Makefile
# ================================

# Python environment
PYTHON = .venv/bin/python
PIP = .venv/bin/pip

# Default target
.DEFAULT_GOAL := help

# ----------------
# ENVIRONMENT SETUP
# ----------------

venv:
    python3 -m venv .venv
    @echo "✔ Virtual environment created"

install: venv
    $(PIP) install --upgrade pip
    $(PIP) install -r requirements.txt
    @echo "✔ Dependencies installed"

env: install
    @echo "✔ Environment ready"

# ----------------
# PIPELINE COMMANDS
# ----------------

run:
    $(PYTHON) run_pipeline.py
    @echo "✔ Pipeline executed"

train:
    $(PYTHON) pipeline/model_train.py
    @echo "✔ Model trained"

forecast:
    $(PYTHON) pipeline/forecast.py
    @echo "✔ Forecast generated"

evaluate:
    $(PYTHON) pipeline/evaluate.py
    @echo "✔ Evaluation complete"

# ----------------
# QUALITY & LINTING
# ----------------

lint:
    $(PYTHON) -m pylint api pipeline --disable=R,C
    @echo "✔ Linting complete"

format:
    $(PYTHON) -m black api pipeline
    @echo "✔ Code formatted"

# ----------------
# CLEANUP
# ----------------

clean:
    rm -rf __pycache__ */__pycache__ .pytest_cache
    @echo "✔ Cache cleaned"

clean-all: clean
    rm -rf .venv models/*.cbm output/*.csv
    @echo "✔ Full cleanup complete"

# ----------------
# HELP
# ----------------

help:
    @echo ""
    @echo "NO2 Forecasting Pipeline — Makefile Commands"
    @echo ""
    @echo "Environment:"
    @echo "  make venv          Create virtual environment"
    @echo "  make install       Install dependencies"
    @echo "  make env           Full environment setup"
    @echo ""
    @echo "Pipeline:"
    @echo "  make run           Run full pipeline"
    @echo "  make train         Train CatBoost model"
    @echo "  make forecast      Generate forecast"
    @echo "  make evaluate      Evaluate model"
    @echo ""
    @echo "Quality:"
    @echo "  make lint          Run pylint"
    @echo "  make format        Format code with black"
    @echo ""
    @echo "Cleanup:"
    @echo "  make clean         Remove caches"
    @echo "  make clean-all     Remove env, models, outputs"
    @echo ""
