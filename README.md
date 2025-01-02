# Curation Signal Optimizer

A Python application that optimizes curation signals using TheGraph API and Supabase for data storage.

## Prerequisites

- Python 3.x
- pip (Python package installer)
- Access to TheGraph API
- Access to Supabase database

## Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/curation_signal_optimizer.git
cd curation_signal_optimizer
```

2. Install Python dependencies:
```bash
cd python_app
pip install -r requirements.txt
```

3. Create a `.env` file in the root directory using the provided `.env.example` as a template:
```bash
cp .env.example .env
```

4. Update the `.env` file with your credentials:
- `THEGRAPH_API_KEY`: Your TheGraph API key
- `SUPABASE_USERNAME`: Your Supabase username
- `SUPABASE_PASSWORD`: Your Supabase password

## Running the Application

1. Start the Streamlit application:
```bash
cd python_app
streamlit run streamlit_curation.py
```

2. The application will open in your default web browser.

## Running Tests

```bash
cd python_app/tests
pip install -r requirements.txt
pytest
```

## Database Schema

The application requires the following Supabase table structure:

### Table: qos_hourly_query_volume

Tracks query volume and fees for subgraphs on an hourly basis.

| Column                          | Type      | Description                               |
|--------------------------------|-----------|-------------------------------------------|
| subgraph_deployment_ipfs_hash   | text      | IPFS hash of the subgraph deployment     |
| total_query_fees               | numeric   | Total fees collected for queries          |
| query_count                    | integer   | Number of queries in the time period      |
| end_epoch                      | timestamp | End time of the hourly period             |

#### Indexes
- Primary Key: Composite key of (subgraph_deployment_ipfs_hash, end_epoch)
- Index on end_epoch for time-based queries

## Application Structure

- `api/`: API integrations for TheGraph and Supabase
- `models/`: Core business logic and optimization algorithms
- `ui/tabs/`: Streamlit UI components
- `utils/`: Utility functions and configuration
- `tests/`: Unit tests

## Features

- Query volume analysis
- Curation signal optimization
- Subgraph list management
- Summary statistics and reporting
