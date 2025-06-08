// Supabase API integration
const SUPABASE_USERNAME = import.meta.env.VITE_SUPABASE_USERNAME;
const SUPABASE_PASSWORD = import.meta.env.VITE_SUPABASE_PASSWORD;
// Multiple fallback options for API access
const SUPABASE_DIRECT_URL = "http://supabasekong-so4w8gock004k8kw8ck84o80.94.130.17.180.sslip.io/api/pg-meta/default/query";
const SUPABASE_PROXY_URL = "/api/supabase"; // Uses Vite proxy
const SUPABASE_CORS_PROXY_URL = "https://cors-anywhere.herokuapp.com/http://supabasekong-so4w8gock004k8kw8ck84o80.94.130.17.180.sslip.io/api/pg-meta/default/query";

// Try direct connection first, fallback to proxy if needed
const SUPABASE_API_URL = SUPABASE_DIRECT_URL;

function getAuthHeaders() {
  const credentials = `${SUPABASE_USERNAME}:${SUPABASE_PASSWORD}`;
  const authBytes = btoa(credentials);
  
  return {
    "Authorization": `Basic ${authBytes}`,
    "Content-Type": "application/json",
    "Accept": "application/json"
  };
}

async function fetchWithFallback(url, options, fallbackUrls = []) {
  const urls = [url, ...fallbackUrls];

  for (let i = 0; i < urls.length; i++) {
    try {
      console.log(`🔄 Attempting API call to: ${urls[i]}`);
      const response = await fetch(urls[i], options);

      if (response.ok) {
        console.log(`✅ Success with URL: ${urls[i]}`);
        return response;
      } else {
        console.warn(`❌ Failed with URL: ${urls[i]} - Status: ${response.status}`);
        if (i === urls.length - 1) {
          throw new Error(`All URLs failed. Last status: ${response.status}`);
        }
      }
    } catch (error) {
      console.warn(`❌ Error with URL: ${urls[i]} - ${error.message}`);
      if (i === urls.length - 1) {
        throw error;
      }
    }
  }
}

export async function querySupabase() {
  try {
    // Get data from the last 30 days for more accurate calculations
    const thirtyDaysAgo = new Date();
    thirtyDaysAgo.setDate(thirtyDaysAgo.getDate() - 30);
    const thirtyDaysAgoISO = thirtyDaysAgo.toISOString();

    // SQL query using daily data table for more accurate fee calculations
    const sqlQuery = `
      SELECT
        subgraph_deployment_ipfs_hash,
        SUM(total_query_fees) as total_query_fees,
        SUM(query_count) as query_count,
        COUNT(*) as days_with_data
      FROM qos_daily_query_volume
      WHERE end_epoch > '${thirtyDaysAgoISO}'
      GROUP BY subgraph_deployment_ipfs_hash
      HAVING COUNT(*) >= 7
    `;

    const requestOptions = {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify({ query: sqlQuery })
    };

    // Try multiple URLs with fallback
    const fallbackUrls = [SUPABASE_PROXY_URL];
    const response = await fetchWithFallback(SUPABASE_API_URL, requestOptions, fallbackUrls);

    const data = await response.json();
    return data || [];

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

    // Process results - convert to daily averages then to annual projections
    if (rows && Array.isArray(rows)) {
      console.log('🗄️ Processing Supabase query fee data...');
      rows.forEach((row, index) => {
        const ipfsHash = row.subgraph_deployment_ipfs_hash;
        if (ipfsHash) {
          const totalFees = parseFloat(row.total_query_fees) || 0;
          const totalQueries = parseInt(row.query_count) || 0;
          const daysWithData = parseInt(row.days_with_data) || 1;
          
          // Calculate daily averages
          const dailyQueryFees = totalFees / daysWithData;
          const dailyQueryCount = totalQueries / daysWithData;
          
          // Project to annual figures (365 days)
          const annualFees = dailyQueryFees * 365;
          const annualQueries = dailyQueryCount * 365;
          
          queryFees[ipfsHash] = annualFees;
          queryCounts[ipfsHash] = annualQueries;
          
          // Log details for high-fee subgraphs
          if (totalFees > 1000 || ipfsHash === 'QmdKXcBUHR3UyURqVRQHu1oV6VUkBrhi2vNvMx3bNDnUCc') {
            console.log(`💰 Query Fees for ${ipfsHash}:`);
            console.log(`  📊 Raw total_query_fees: ${totalFees} (over ${daysWithData} days)`);
            console.log(`  📈 Daily average: ${dailyQueryFees.toFixed(6)}`);
            console.log(`  📅 Annual projection: ${annualFees.toFixed(6)}`);
            console.log(`  ❓ UNITS: Are these GRT tokens or USD? Check your Supabase schema!`);
            console.log(`  🔢 Daily queries: ${dailyQueryCount.toLocaleString()}`);
          }
        }
      });
      console.log(`✅ Processed ${rows.length} subgraphs from Supabase`);
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
    const thirtyDaysAgo = new Date();
    thirtyDaysAgo.setDate(thirtyDaysAgo.getDate() - 30);
    const thirtyDaysAgoISO = thirtyDaysAgo.toISOString();

    const sqlQuery = `
      SELECT 
        subgraph_deployment_ipfs_hash,
        total_query_fees,
        query_count,
        end_epoch as day
      FROM qos_daily_query_volume 
      WHERE end_epoch > '${thirtyDaysAgoISO}' 
        AND subgraph_deployment_ipfs_hash = '${ipfsHash}'
      ORDER BY end_epoch ASC
    `;

    const requestOptions = {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify({ query: sqlQuery })
    };

    const fallbackUrls = [SUPABASE_PROXY_URL];
    const response = await fetchWithFallback(SUPABASE_API_URL, requestOptions, fallbackUrls);

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