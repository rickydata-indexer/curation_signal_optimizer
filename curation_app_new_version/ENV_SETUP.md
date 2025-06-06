# Environment Variables Setup

This React application requires the following environment variables to be set:

## Required Environment Variables

Create a `.env` file in the `curation_app_new_version` directory with the following variables:

```bash
# The Graph API Configuration
VITE_THEGRAPH_API_KEY=add

# Supabase Configuration  
VITE_SUPABASE_USERNAME=add
VITE_SUPABASE_PASSWORD=add
```

## Notes

- All environment variables for Vite must be prefixed with `VITE_`
- The THEGRAPH_API_KEY is the same key used in the Python Streamlit app
- The Supabase credentials are from Option 1 provided by the user
- These variables are used by the API modules in `src/api/graphApi.js` and `src/api/supabaseApi.js`

## Supabase Database Requirements

The app expects the following table to exist in the Supabase database:

```sql
CREATE TABLE qos_hourly_query_volume (
    id SERIAL PRIMARY KEY,
    subgraph_deployment_ipfs_hash TEXT NOT NULL,
    total_query_fees DECIMAL(20,6) NOT NULL DEFAULT 0,
    query_count INTEGER NOT NULL DEFAULT 0,
    end_epoch TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Add indexes for better performance
CREATE INDEX idx_qos_hourly_query_volume_end_epoch ON qos_hourly_query_volume(end_epoch);
CREATE INDEX idx_qos_hourly_query_volume_ipfs_hash ON qos_hourly_query_volume(subgraph_deployment_ipfs_hash);
```

## Installation and Running

1. Copy the environment variables to your `.env` file
2. Install dependencies: `npm install`
3. Start the development server: `npm run dev`

The app should be accessible at `http://localhost:5173` (Vite default port). 