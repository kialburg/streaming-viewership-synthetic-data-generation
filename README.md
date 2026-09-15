# Streaming Viewership Case Study

## Overview

This project analyzes viewership patterns and engagement metrics for a pair of synthetic datasets for TV and mobile streaming viewership. It processes digital session data, creates viewer mappings, and calculates key performance indicators across demographic segments.

## Getting Started

### Prerequisites

- Python 3.x
- SQLite3
- Required Python packages (see `requirements.txt`)

### Execution Steps

1. **Extract Data**

Download the source data and load them into the repository in the `/bucket` folder.


2. **Set up the environment**
   
   Initialize the SQLite database and create non-time-dependent tables:
   ```bash
   python code/setup_env.py
   ```

3. **Generate daily staging tables**
   
   Process data for a specific date (replace `2025-09-04` with your target date):
   ```bash
   python code/main.py 2025-09-04
   ```

4. **Run the activation logic**
   
    Process data for a specific date (replace `2025-09-04` with your target date):
   ```bash
   python code/activation_plan.py 2025-09-04
   ```

## Project Structure

- **`code/`** — Core Python scripts and notebooks
- **`KPIs/`** — SQL queries for key performance indicators
- **`EDA/`** — Exploratory data analysis notebooks and utilities
- **`output/`** — Manually curated reports and exports
- **`SQLite-db/`** — Database storage
- **`bucket/`** — Data staging area

## Documentation

- [Data Model](Data%20Model.md) — Schema and data structure documentation
- [Case Study Plan](Case%20Study%20Plan.md) — Stream of consciousness thoughts from the author trying to understand the task.