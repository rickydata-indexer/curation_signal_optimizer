# Load required libraries
library(shiny)
library(httr)
library(jsonlite)
library(tidyverse)
library(lubridate)
library(DT)
library(scales)

# Define helper functions

# Function to get subgraph deployments
get_subgraph_deployments <- function() {
  url <- "https://gateway.thegraph.com/api/040d2183b97fb279ac2cb8fb2c78beae/subgraphs/id/DZz4kDTdmzWLWsV373w2bSmoar3umKKH9y82SUKr5qmp"
  query <- '
  {
    subgraphDeployments(first: 1000, orderBy: signalAmount, orderDirection: desc) {
      ipfsHash
      signalAmount
      signalledTokens
    }
  }
  '
  response <- httr::POST(url, body = list(query = query), encode = "json")
  data <- httr::content(response, as = "text", encoding = "UTF-8")
  deployments <- jsonlite::fromJSON(data)$data$subgraphDeployments
  return(deployments)
}

# Function to process CSV files and aggregate query fees and counts
process_csv_files <- function(directory) {
  now <- Sys.time()
  week_ago <- now - days(7)
  
  query_fees <- list()
  query_counts <- list()
  
  files <- list.files(directory, pattern = "\\.csv$", full.names = TRUE)
  
  for (file in files) {
    df <- read_csv(file, show_col_types = FALSE)
    df <- df %>% mutate(end_epoch = ymd_hms(end_epoch))
    
    # Filter data for the last week
    df_week <- df %>% filter(end_epoch > week_ago)
    
    # Group by subgraph deployment and sum query fees and counts
    grouped_fees <- df_week %>%
      group_by(subgraph_deployment_ipfs_hash) %>%
      summarise(total_query_fees = sum(total_query_fees, na.rm = TRUE))
    
    grouped_counts <- df_week %>%
      group_by(subgraph_deployment_ipfs_hash) %>%
      summarise(query_count = sum(query_count, na.rm = TRUE))
    
    # Update query_fees and query_counts
    for (i in seq_len(nrow(grouped_fees))) {
      ipfs_hash <- grouped_fees$subgraph_deployment_ipfs_hash[i]
      fees <- grouped_fees$total_query_fees[i]
      if (!is.null(query_fees[[ipfs_hash]])) {
        query_fees[[ipfs_hash]] <- query_fees[[ipfs_hash]] + fees
      } else {
        query_fees[[ipfs_hash]] <- fees
      }
    }
    
    for (i in seq_len(nrow(grouped_counts))) {
      ipfs_hash <- grouped_counts$subgraph_deployment_ipfs_hash[i]
      count <- grouped_counts$query_count[i]
      if (!is.null(query_counts[[ipfs_hash]])) {
        query_counts[[ipfs_hash]] <- query_counts[[ipfs_hash]] + count
      } else {
        query_counts[[ipfs_hash]] <- count
      }
    }
  }
  
  return(list(query_fees = query_fees, query_counts = query_counts))
}

# Function to get GRT price
get_grt_price <- function() {
  url <- "https://gateway.thegraph.com/api/040d2183b97fb279ac2cb8fb2c78beae/subgraphs/id/4RTrnxLZ4H8EBdpAQTcVc7LQY9kk85WNLyVzg5iXFQCH"
  query <- '
  {
    assetPairs(
      first: 1
      where: {asset: "0xc944e90c64b2c07662a292be6244bdf05cda44a7", comparedAsset: "0x0000000000000000000000000000000000000348"}
    ) {
      currentPrice
    }
  }
  '
  response <- httr::POST(url, body = list(query = query), encode = "json")
  data <- httr::content(response, as = "text", encoding = "UTF-8")
  data_parsed <- jsonlite::fromJSON(data)
  price <- as.numeric(data_parsed$data$assetPairs[[1]]$currentPrice)
  return(price)
}

# Function to calculate opportunities
calculate_opportunities <- function(deployments, query_fees, query_counts, grt_price) {
  opportunities <- list()
  
  for (i in seq_len(nrow(deployments))) {
    deployment <- deployments[i, ]
    ipfs_hash <- deployment$ipfsHash
    signal_amount <- as.numeric(deployment$signalAmount) / 1e18
    signalled_tokens <- as.numeric(deployment$signalledTokens) / 1e18
    
    if (!is.null(query_counts[[ipfs_hash]])) {
      weekly_queries <- query_counts[[ipfs_hash]]
      annual_queries <- weekly_queries * 52
      
      # Calculate total earnings based on $4 per 100,000 queries
      total_earnings <- (annual_queries / 100000) * 4
      
      # Calculate the curator's share (10% of total earnings)
      curator_share <- total_earnings * 0.1
      
      # Calculate the portion owned by the curator
      if (signalled_tokens > 0) {
        portion_owned <- signal_amount / signalled_tokens
      } else {
        portion_owned <- 0
      }
      
      # Calculate estimated annual earnings for this curator
      estimated_earnings <- curator_share * portion_owned
      
      # Calculate APR using GRT price
      if (signal_amount > 0) {
        apr <- (estimated_earnings / (signal_amount * grt_price)) * 100
      } else {
        apr <- 0
      }
      
      opportunities[[length(opportunities) + 1]] <- list(
        ipfs_hash = ipfs_hash,
        signal_amount = signal_amount,
        signalled_tokens = signalled_tokens,
        annual_queries = annual_queries,
        total_earnings = total_earnings,
        curator_share = curator_share,
        estimated_earnings = estimated_earnings,
        apr = apr,
        weekly_queries = weekly_queries
      )
    }
  }
  
  # Convert list to dataframe
  opp_df <- bind_rows(opportunities)
  
  # Filter out subgraphs with zero signal amounts
  opp_df <- opp_df %>% filter(signal_amount > 0)
  
  # Sort opportunities by APR in descending order
  opp_df <- opp_df %>% arrange(desc(apr))
  
  return(opp_df)
}

# Function to get user's curation signal
get_user_curation_signal <- function(wallet_address) {
  url <- "https://gateway.thegraph.com/api/040d2183b97fb279ac2cb8fb2c78beae/subgraphs/id/DZz4kDTdmzWLWsV373w2bSmoar3umKKH9y82SUKr5qmp"
  query <- sprintf('
  {
    nameSignals(where: {curator: "%s"}, first: 1000, orderBy: signal, orderDirection: desc) {
      subgraph {
        currentVersion {
          subgraphDeployment {
            ipfsHash
          }
        }
      }
      signal
    }
  }
  ', wallet_address)
  response <- httr::POST(url, body = list(query = query), encode = "json")
  data <- httr::content(response, as = "text", encoding = "UTF-8")
  parsed_data <- jsonlite::fromJSON(data)
  
  name_signals <- parsed_data$data$nameSignals
  
  user_signals <- setNames(
    lapply(name_signals$signal, function(s) as.numeric(s) / 1e18),
    sapply(name_signals$subgraph$currentVersion$subgraphDeployment$ipfsHash, identity)
  )
  
  return(user_signals)
}

# Function to calculate user opportunities
calculate_user_opportunities <- function(user_signals, opportunities, grt_price) {
  user_opps <- list()
  
  for (i in seq_len(nrow(opportunities))) {
    opp <- opportunities[i, ]
    ipfs_hash <- opp$ipfs_hash
    if (!is.null(user_signals[[ipfs_hash]])) {
      user_signal <- user_signals[[ipfs_hash]]
      total_signal <- opp$signalled_tokens
      portion_owned <- if (total_signal > 0) user_signal / total_signal else 0
      estimated_earnings <- opp$curator_share * portion_owned
      apr <- if (user_signal > 0) (estimated_earnings / (user_signal * grt_price)) * 100 else 0
      
      user_opps[[length(user_opps) + 1]] <- list(
        ipfs_hash = ipfs_hash,
        user_signal = user_signal,
        total_signal = total_signal,
        portion_owned = portion_owned,
        estimated_earnings = estimated_earnings,
        apr = apr,
        weekly_queries = opp$weekly_queries
      )
    }
  }
  
  user_opp_df <- bind_rows(user_opps) %>% arrange(desc(apr))
  return(user_opp_df)
}

# Function to calculate optimal allocations
calculate_optimal_allocations <- function(opportunities, total_signal, grt_price, num_subgraphs) {
  # Sort opportunities by APR in descending order
  opps <- opportunities %>% arrange(desc(apr))
  
  # Select top opportunities
  top_opps <- opps %>% slice(1:num_subgraphs)
  
  # Initialize allocations
  allocations <- setNames(rep(0, nrow(top_opps)), top_opps$ipfs_hash)
  remaining_signal <- total_signal
  
  # Iterative allocation process
  while (remaining_signal > 0) {
    best_apr <- -1
    best_opp <- NULL
    best_ipfs_hash <- NULL
    
    for (i in seq_len(nrow(top_opps))) {
      opp <- top_opps[i, ]
      ipfs_hash <- opp$ipfs_hash
      signal_amount <- opp$signal_amount + allocations[ipfs_hash]
      signalled_tokens <- opp$signalled_tokens + allocations[ipfs_hash]
      
      # Calculate APR if we add 100 more tokens
      new_signal_amount <- signal_amount + 100
      new_signalled_tokens <- signalled_tokens + 100
      portion_owned <- new_signal_amount / new_signalled_tokens
      estimated_earnings <- opp$curator_share * portion_owned
      apr <- if (new_signal_amount > 0) (estimated_earnings / (new_signal_amount * grt_price)) * 100 else 0
      
      if (apr > best_apr) {
        best_apr <- apr
        best_opp <- opp
        best_ipfs_hash <- ipfs_hash
      }
    }
    
    # Allocate 100 tokens to the best opportunity
    if (!is.null(best_opp)) {
      alloc_amount <- min(100, remaining_signal)
      allocations[best_ipfs_hash] <- allocations[best_ipfs_hash] + alloc_amount
      remaining_signal <- remaining_signal - alloc_amount
    } else {
      break
    }
  }
  
  # Prepare data for display
  optimal_allocations <- list()
  
  for (i in seq_len(nrow(top_opps))) {
    opp <- top_opps[i, ]
    ipfs_hash <- opp$ipfs_hash
    allocated_amount <- allocations[ipfs_hash]
    
    signal_amount_before <- opp$signal_amount
    signalled_tokens_before <- opp$signalled_tokens
    curator_share <- opp$curator_share
    weekly_queries <- opp$weekly_queries
    
    # After adding tokens
    signal_amount_after <- signal_amount_before + allocated_amount
    signalled_tokens_after <- signalled_tokens_before + allocated_amount
    portion_owned_after <- signal_amount_after / signalled_tokens_after
    estimated_earnings_after <- curator_share * portion_owned_after
    apr_after <- if (signal_amount_after > 0) (estimated_earnings_after / (signal_amount_after * grt_price)) * 100 else NA
    
    optimal_allocations[[length(optimal_allocations) + 1]] <- list(
      ipfs_hash = ipfs_hash,
      allocated_signal = allocated_amount,
      new_total_signal = signalled_tokens_after,
      portion_owned = portion_owned_after,
      estimated_earnings = estimated_earnings_after,
      apr = apr_after,
      weekly_queries = weekly_queries
    )
  }
  
  optimal_allocations_df <- bind_rows(optimal_allocations)
  return(optimal_allocations_df)
}

# Function to calculate signal distribution
calculate_signal_distribution <- function(opportunities, total_signal, grt_price) {
  # Sort opportunities by APR in descending order
  opps <- opportunities %>% arrange(desc(apr))
  
  # Initialize allocations
  allocations <- setNames(rep(0, nrow(opps)), opps$ipfs_hash)
  remaining_signal <- total_signal
  
  # Iterative allocation process
  while (remaining_signal > 0) {
    best_apr <- -1
    best_opp <- NULL
    best_ipfs_hash <- NULL
    
    for (i in seq_len(nrow(opps))) {
      opp <- opps[i, ]
      ipfs_hash <- opp$ipfs_hash
      signal_amount <- opp$signal_amount + allocations[ipfs_hash]
      signalled_tokens <- opp$signalled_tokens + allocations[ipfs_hash]
      
      # Calculate APR if we add 100 more tokens
      new_signal_amount <- signal_amount + 100
      new_signalled_tokens <- signalled_tokens + 100
      portion_owned <- new_signal_amount / new_signalled_tokens
      estimated_earnings <- opp$curator_share * portion_owned
      apr <- if (new_signal_amount > 0) (estimated_earnings / (new_signal_amount * grt_price)) * 100 else 0
      
      if (apr > best_apr) {
        best_apr <- apr
        best_opp <- opp
        best_ipfs_hash <- ipfs_hash
      }
    }
    
    # Allocate 100 tokens to the best opportunity
    if (!is.null(best_opp)) {
      alloc_amount <- min(100, remaining_signal)
      allocations[best_ipfs_hash] <- allocations[best_ipfs_hash] + alloc_amount
      remaining_signal <- remaining_signal - alloc_amount
    } else {
      break
    }
  }
  
  return(allocations)
}

# Function to color APR values
color_apr <- function(value) {
  if (is.na(value) || value == "-") {
    return("")
  } else if (value > 5) {
    return("color: green;")
  } else if (value < 1) {
    return("color: red;")
  } else {
    return("color: black;")
  }
}

# Shiny UI
ui <- fluidPage(
  titlePanel("Curation Signal Allocation Optimizer"),
  sidebarLayout(
    sidebarPanel(
      textInput("wallet_address", "Enter your wallet address", value = "0x74dbb201ecc0b16934e68377bc13013883d9417b"),
      numericInput("total_signal_to_add", "Total signal amount to add (GRT)", value = 10000, min = 0),
      numericInput("num_subgraphs", "Number of subgraphs to allocate across", value = 5, min = 1),
      actionButton("optimize", "Optimize Allocations"),
      downloadButton("download_full_list", "Download Full Subgraph List")
    ),
    mainPanel(
      tabsetPanel(
        tabPanel("Summary",
                 h3("Summary"),
                 verbatimTextOutput("summary_output"),
                 h3("Low Performing Allocations (APR < 1%)"),
                 dataTableOutput("low_performing_table")
        ),
        tabPanel("Your Current Curation Signal",
                 h3("Your Current Curation Signal"),
                 dataTableOutput("user_signal_table")
        ),
        tabPanel("Optimal Allocations",
                 h3("Optimal Allocations"),
                 verbatimTextOutput("optimal_summary"),
                 dataTableOutput("optimal_allocations_table")
        ),
        tabPanel("Find Opportunities",
                 h3("Find Opportunities"),
                 dataTableOutput("opportunities_table"),
                 h3("Signal Results"),
                 verbatimTextOutput("signal_results")
        ),
        tabPanel("Full Subgraph List",
                 h3("Full Subgraph List"),
                 dataTableOutput("full_subgraph_table")
        )
      )
    )
  )
)

# Shiny Server
server <- function(input, output, session) {
  # Reactive values to store data
  rv <- reactiveValues()
  
  # Fetch data on startup
  observe({
    rv$deployments <- get_subgraph_deployments()
    rv$query_data <- process_csv_files("python_data/hourly_query_volume")
    rv$grt_price <- get_grt_price()
    rv$opportunities <- calculate_opportunities(rv$deployments, rv$query_data$query_fees, rv$query_data$query_counts, rv$grt_price)
  })
  
  # Summary tab
  output$summary_output <- renderPrint({
    wallet_address <- tolower(input$wallet_address)
    rv$user_signals <- get_user_curation_signal(wallet_address)
    rv$user_opportunities <- calculate_user_opportunities(rv$user_signals, rv$opportunities, rv$grt_price)
    
    total_signal <- sum(rv$user_opportunities$user_signal, na.rm = TRUE)
    total_earnings <- sum(rv$user_opportunities$estimated_earnings, na.rm = TRUE)
    aprs <- rv$user_opportunities$apr[rv$user_opportunities$apr > 0]
    median_apr <- median(aprs, na.rm = TRUE)
    average_apr <- mean(aprs, na.rm = TRUE)
    
    cat(sprintf("Current GRT Price: $%.4f\n", rv$grt_price))
    cat(sprintf("Total Signal: %.2f GRT\n", total_signal))
    cat(sprintf("Median APR: %.2f%%\n", median_apr))
    cat(sprintf("Average APR: %.2f%%\n", average_apr))
    cat("Estimated Earnings:\n")
    cat(sprintf("- Daily: $%.2f\n", total_earnings / 365))
    cat(sprintf("- Weekly: $%.2f\n", total_earnings / 52))
    cat(sprintf("- Monthly: $%.2f\n", total_earnings / 12))
    cat(sprintf("- Yearly: $%.2f\n", total_earnings))
  })
  
  # Low Performing Allocations
  output$low_performing_table <- renderDataTable({
    low_performing <- rv$user_opportunities %>% filter(apr < 1)
    if (nrow(low_performing) > 0) {
      low_performing %>%
        select(`IPFS Hash` = ipfs_hash, `Signal (GRT)` = user_signal, `APR (%)` = apr) %>%
        datatable(options = list(pageLength = 5))
    } else {
      datatable(data.frame(Message = "No allocations with APR below 1%"))
    }
  })
  
  # Your Current Curation Signal tab
  output$user_signal_table <- renderDataTable({
    total_signal <- sum(rv$user_opportunities$user_signal, na.rm = TRUE)
    total_earnings <- sum(rv$user_opportunities$estimated_earnings, na.rm = TRUE)
    overall_apr <- if (total_signal > 0 && rv$grt_price > 0) (total_earnings / (total_signal * rv$grt_price)) * 100 else 0
    
    rv$user_opportunities %>%
      mutate(
        `Your Signal (GRT)` = round(user_signal, 2),
        `Total Signal (GRT)` = round(total_signal, 2),
        `Portion Owned` = scales::percent(portion_owned),
        `Estimated Annual Earnings ($)` = round(estimated_earnings, 2),
        `Current APR (%)` = round(apr, 2)
      ) %>%
      select(`IPFS Hash` = ipfs_hash, `Your Signal (GRT)`, `Total Signal (GRT)`, `Portion Owned`, `Estimated Annual Earnings ($)`, `Current APR (%)`, `Weekly Queries` = weekly_queries) %>%
      datatable(options = list(pageLength = 5))
  })
  
  # Optimal Allocations tab
  observeEvent(input$optimize, {
    adjusted_opportunities <- rv$opportunities %>%
      mutate(
        signalled_tokens = signalled_tokens - coalesce(rv$user_signals[ipfs_hash], 0),
        signal_amount = 0
      )
    
    total_signal <- sum(rv$user_opportunities$user_signal, na.rm = TRUE)
    overall_apr <- if (total_signal > 0 && rv$grt_price > 0) (sum(rv$user_opportunities$estimated_earnings, na.rm = TRUE) / (total_signal * rv$grt_price)) * 100 else 0
    
    rv$optimal_allocations <- calculate_optimal_allocations(adjusted_opportunities, total_signal, rv$grt_price, num_subgraphs = 20)
    
    total_optimal_earnings <- sum(rv$optimal_allocations$estimated_earnings, na.rm = TRUE)
    optimal_apr <- if (total_signal > 0 && rv$grt_price > 0) (total_optimal_earnings / (total_signal * rv$grt_price)) * 100 else 0
    apr_improvement <- optimal_apr - overall_apr
    relative_improvement <- if (overall_apr > 0) (apr_improvement / overall_apr) * 100 else NA
    
    rv$optimal_summary_text <- sprintf("Optimal Total Annual Earnings: $%.2f\nOptimal Overall APR: %.2f%%\nAPR Improvement: %.2f%%\nRelative APR Improvement: %.2f%%", total_optimal_earnings, optimal_apr, apr_improvement, relative_improvement)
  })
  
  output$optimal_summary <- renderPrint({
    rv$optimal_summary_text
  })
  
  output$optimal_allocations_table <- renderDataTable({
    rv$optimal_allocations %>%
      mutate(
        `Optimal Signal (GRT)` = round(allocated_signal, 2),
        `New Total Signal (GRT)` = round(new_total_signal, 2),
        `Portion Owned` = scales::percent(portion_owned),
        `Estimated Annual Earnings ($)` = round(estimated_earnings, 2),
        `Optimal APR (%)` = round(apr, 2)
      ) %>%
      select(`IPFS Hash` = ipfs_hash, `Optimal Signal (GRT)`, `New Total Signal (GRT)`, `Portion Owned`, `Estimated Annual Earnings ($)`, `Optimal APR (%)`, `Weekly Queries` = weekly_queries) %>%
      datatable(options = list(pageLength = 5))
  })
  
  # Find Opportunities tab
  output$opportunities_table <- renderDataTable({
    top_opps <- rv$opportunities %>% slice(1:input$num_subgraphs)
    allocations <- calculate_signal_distribution(top_opps, input$total_signal_to_add, rv$grt_price)
    
    data <- top_opps %>%
      mutate(
        allocated_signal = allocations[match(ipfs_hash, names(allocations))],
        signal_after = signal_amount + allocated_signal,
        apr_after = ifelse(signal_after > 0, (curator_share * (signal_after / (signalled_tokens + allocated_signal)) / (signal_after * rv$grt_price)) * 100, NA)
      ) %>%
      select(
        `IPFS Hash` = ipfs_hash,
        `Signal Before (GRT)` = signal_amount,
        `Signal After (GRT)` = signal_after,
        `APR Before (%)` = apr,
        `APR After (%)` = apr_after,
        `Earnings After ($)` = estimated_earnings,
        `Allocated Signal (GRT)` = allocated_signal,
        `Weekly Queries` = weekly_queries
      )
    
    rv$opportunities_data <- data
    datatable(data, options = list(pageLength = 5))
  })
  
  output$signal_results <- renderPrint({
    total_allocated_signal <- sum(rv$opportunities_data$`Allocated Signal (GRT)`, na.rm = TRUE)
    total_estimated_earnings_after <- sum(rv$opportunities_data$`Earnings After ($)`, na.rm = TRUE)
    weighted_apr <- if (total_allocated_signal > 0) sum(rv$opportunities_data$`APR After (%)` * rv$opportunities_data$`Allocated Signal (GRT)`, na.rm = TRUE) / total_allocated_signal else 0
    
    cat(sprintf("Total GRT Signaled: %.2f GRT\n", total_allocated_signal))
    cat(sprintf("Total Value of Signaled GRT: $%.2f\n", total_allocated_signal * rv$grt_price))
    cat("Estimated Earnings:\n")
    cat(sprintf("- Per Day: $%.2f\n", total_estimated_earnings_after / 365))
    cat(sprintf("- Per Week: $%.2f\n", total_estimated_earnings_after / 52))
    cat(sprintf("- Per Month: $%.2f\n", total_estimated_earnings_after / 12))
    cat(sprintf("- Per Year: $%.2f\n", total_estimated_earnings_after))
    cat(sprintf("Overall APR: %.2f%%\n", weighted_apr))
  })
  
  # Full Subgraph List tab
  output$full_subgraph_table <- renderDataTable({
    rv$opportunities %>%
      mutate(
        `Signal (GRT)` = round(signal_amount, 2),
        `Total Signal (GRT)` = round(signalled_tokens, 2),
        `APR (%)` = round(apr, 2)
      ) %>%
      select(`IPFS Hash` = ipfs_hash, `Signal (GRT)`, `Total Signal (GRT)`, `APR (%)`, `Weekly Queries` = weekly_queries) %>%
      datatable(options = list(pageLength = 10))
  })
  
  # Download Handler for Full Subgraph List
  output$download_full_list <- downloadHandler(
    filename = function() {
      paste("full_subgraph_list", Sys.Date(), ".csv", sep = "")
    },
    content = function(file) {
      write_csv(rv$opportunities %>% 
                  mutate(
                    `Signal (GRT)` = round(signal_amount, 2),
                    `Total Signal (GRT)` = round(signalled_tokens, 2),
                    `APR (%)` = round(apr, 2)
                  ) %>%
                  select(`IPFS Hash` = ipfs_hash, `Signal (GRT)`, `Total Signal (GRT)`, `APR (%)`, `Weekly Queries` = weekly_queries), file)
    }
  )
}

# Run the Shiny app
shinyApp(ui = ui, server = server)
