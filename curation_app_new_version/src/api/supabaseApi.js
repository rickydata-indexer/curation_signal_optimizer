// Supabase API integration
const SUPABASE_USERNAME = import.meta.env.VITE_SUPABASE_USERNAME;
const SUPABASE_PASSWORD = import.meta.env.VITE_SUPABASE_PASSWORD;
const SUPABASE_BASE_URL = "http://supabasekong-so4w8gock004k8kw8ck84o80.94.130.17.180.sslip.io";
const SUPABASE_API_URL = `${SUPABASE_BASE_URL}/api/pg-meta/default/query`;

function getAuthHeaders() {
  const credentials = `${SUPABASE_USERNAME}:${SUPABASE_PASSWORD}`;
  const authBytes = btoa(credentials);
  
  return {
    "Authorization": `Basic ${authBytes}`,
    "Content-Type": "application/json",
    "Accept": "application/json"
  };
}

export async function querySupabase() {
  try {
    // Get data from the last week
    const weekAgo = new Date();
    weekAgo.setDate(weekAgo.getDate() - 7);
    const weekAgoISO = weekAgo.toISOString();

    // SQL query - same as Python version
    const sqlQuery = `
      SELECT 
        subgraph_deployment_ipfs_hash,
        SUM(total_query_fees) as total_query_fees,
        SUM(query_count) as query_count
      FROM qos_hourly_query_volume 
      WHERE end_epoch > '${weekAgoISO}'
      GROUP BY subgraph_deployment_ipfs_hash
    `;

    // Execute the query
    const response = await fetch(SUPABASE_API_URL, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify({ query: sqlQuery })
    });

    if (response.ok) {
      const data = await response.json();
      return data || [];
    } else {
      const errorText = await response.text();
      throw new Error(`Error executing query: HTTP ${response.status} - ${errorText}`);
    }

  } catch (error) {
    console.error('Supabase query error:', error);
    throw new Error(`Error: ${error.message}`);
  }
}

export async function processQueryData() {
  try {
    const rows = await querySupabase();
    
    // Initialize dictionaries
    const queryFees = {};
    const queryCounts = {};

    // Process results
    if (rows && Array.isArray(rows)) {
      rows.forEach(row => {
        const ipfsHash = row.subgraph_deployment_ipfs_hash;
        if (ipfsHash) {
          queryFees[ipfsHash] = parseFloat(row.total_query_fees) || 0;
          queryCounts[ipfsHash] = parseInt(row.query_count) || 0;
        }
      });
    }

    return { queryFees, queryCounts };

  } catch (error) {
    console.error('Error processing query data:', error);
    return { queryFees: {}, queryCounts: {} };
  }
}

// Additional utility function to get query data for a specific subgraph
export async function getSubgraphQueryData(ipfsHash) {
  try {
    const weekAgo = new Date();
    weekAgo.setDate(weekAgo.getDate() - 7);
    const weekAgoISO = weekAgo.toISOString();

    const sqlQuery = `
      SELECT 
        subgraph_deployment_ipfs_hash,
        SUM(total_query_fees) as total_query_fees,
        SUM(query_count) as query_count,
        DATE_TRUNC('day', end_epoch) as day
      FROM qos_hourly_query_volume 
      WHERE end_epoch > '${weekAgoISO}' 
        AND subgraph_deployment_ipfs_hash = '${ipfsHash}'
      GROUP BY subgraph_deployment_ipfs_hash, DATE_TRUNC('day', end_epoch)
      ORDER BY day ASC
    `;

    const response = await fetch(SUPABASE_API_URL, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify({ query: sqlQuery })
    });

    if (response.ok) {
      const data = await response.json();
      return data || [];
    } else {
      const errorText = await response.text();
      throw new Error(`Error executing query: HTTP ${response.status} - ${errorText}`);
    }

  } catch (error) {
    console.error('Error fetching subgraph query data:', error);
    return [];
  }
} 