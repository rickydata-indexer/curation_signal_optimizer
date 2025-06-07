# Curation Signal Optimizer

A React application that optimizes curation signals using TheGraph API and Supabase for data storage. This tool analyzes curation opportunities, portfolio performance, and provides real-time data on The Graph network curation signals.

## Project Structure

This repository contains two applications:

- **`curation_app_new_version/`** - **Production React Application** (recommended)
- **`python_app/`** - Python Streamlit prototype (for development/testing)

## Prerequisites

- Node.js 18+ and npm (for React app)
- Python 3.x and pip (for Python prototype)
- Access to TheGraph API
- Access to Supabase database

## Production Setup (React App)

### 1. Navigate to the React application:
```bash
cd curation_app_new_version
```

### 2. Install dependencies:
```bash
npm install
```

### 3. Environment Variables Setup

Create a `.env` file in the `curation_app_new_version` directory:

```bash
# The Graph API Configuration
VITE_THEGRAPH_API_KEY=your_thegraph_api_key_here

# Supabase Configuration  
VITE_SUPABASE_USERNAME=your_supabase_username
VITE_SUPABASE_PASSWORD=your_supabase_password
```

**Important Notes:**
- All environment variables for Vite must be prefixed with `VITE_`
- The THEGRAPH_API_KEY is the same key used in the Python Streamlit app
- Use the Supabase credentials provided for your project

### 4. Start the Production Application:
```bash
npm run dev
```

The application will be available at `http://localhost:5174`

### 5. Build for Production:
```bash
npm run build
```

## Python Prototype Setup (Development Only)

### 1. Navigate to Python app:
```bash
cd python_app
```

### 2. Install Python dependencies:
```bash
pip install -r requirements.txt
```

### 3. Create environment file:
```bash
cp .env.example .env
```

### 4. Update the `.env` file with credentials:
- `THEGRAPH_API_KEY`: Your TheGraph API key
- `SUPABASE_USERNAME`: Your Supabase username  
- `SUPABASE_PASSWORD`: Your Supabase password

### 5. Start the Streamlit application:
```bash
streamlit run streamlit_curation.py
```

The prototype will be available at `http://localhost:8501`

## Database Schema

The application requires the following Supabase tables:

### Table: qos_hourly_query_volume

Tracks query volume and fees for subgraphs on an hourly basis.

| Column                          | Type      | Description                               |
|--------------------------------|-----------|-------------------------------------------|
| subgraph_deployment_ipfs_hash   | text      | IPFS hash of the subgraph deployment     |
| total_query_fees               | numeric   | Total fees collected for queries          |
| query_count                    | integer   | Number of queries in the time period      |
| end_epoch                      | timestamp | End time of the hourly period             |

### Table: qos_daily_query_volume

Tracks daily aggregated query volume and fees (recommended for production calculations).

| Column                          | Type      | Description                               |
|--------------------------------|-----------|-------------------------------------------|
| subgraph_deployment_ipfs_hash   | text      | IPFS hash of the subgraph deployment     |
| total_query_fees               | numeric   | Total fees collected for queries          |
| query_count                    | integer   | Number of queries in the time period      |
| end_epoch                      | timestamp | End time of the daily period              |

#### Indexes
- Primary Key: Composite key of (subgraph_deployment_ipfs_hash, end_epoch)
- Index on end_epoch for time-based queries

## Features

### React Production App Features:
- **Real-time Portfolio Analysis** - Live data from The Graph API
- **APR Calculations** - Based on actual query fees and signal values
- **Curation Opportunity Discovery** - Find profitable curation targets
- **Diversification Metrics** - Portfolio risk analysis
- **Interactive Charts** - Visual representation of performance data
- **Subgraph Performance Tracking** - Historical fee and volume data

### Core Functionality:
- Query volume analysis using real Supabase data
- Curation signal optimization algorithms
- Subgraph performance metrics
- Summary statistics and reporting
- Real-time GRT price integration

## API Integrations

- **TheGraph GraphQL API** - Real-time subgraph deployment and curator signal data
- **Supabase** - Query volume and fee data storage
- **CoinGecko** - Real-time GRT token pricing

## Development

### Running Tests (Python):
```bash
cd python_app/tests
pip install -r requirements.txt
pytest
```

### React Development:
```bash
cd curation_app_new_version
npm run lint      # Check code quality
npm run build     # Build for production
npm run preview   # Preview production build
```

## Application Architecture

### React App Structure:
- `src/api/` - API integrations (TheGraph, Supabase)
- `src/components/` - Reusable UI components  
- `src/pages/` - Main application pages
- `src/utils/` - Utility functions and calculations
- `src/lib/` - Core libraries and configurations

### Python App Structure:
- `api/` - API integrations for TheGraph and Supabase
- `models/` - Core business logic and optimization algorithms
- `ui/tabs/` - Streamlit UI components
- `utils/` - Utility functions and configuration
- `tests/` - Unit tests

## Contributing

1. Use the React production app (`curation_app_new_version/`) for new features
2. The Python app is maintained for prototyping and testing purposes
3. Ensure all environment variables are properly configured
4. Test against real production data and APIs

