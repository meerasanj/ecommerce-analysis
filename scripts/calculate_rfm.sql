# First install required packages if not already done:
# pip3 install duckdb pandas

# Import necessary libraries
import duckdb  # For running SQL queries on data frames and CSV files
import pandas as pd  # For data manipulation

# Main SQL query for calculating RFM metrics.

query = """
-- Use a Common Table Expression (CTE) to find the single most recent purchase date in the entire dataset
-- This is the reference point for calculating recency
WITH latest_purchase AS (
    SELECT MAX(order_purchase_timestamp) AS max_purchase_date
    FROM read_csv_auto('data/raw/olist_orders_dataset.csv')
)

-- Main query to compute RFM metrics for each unique customer
SELECT
    c.customer_unique_id,

    -- Recency: Days since the customer's last purchase compared to the latest overall purchase
    CAST(DATE_PART('day', lp.max_purchase_date - MAX(o.order_purchase_timestamp)) AS INT) AS recency,

    -- Frequency: Total count of distinct orders for each customer
    COUNT(DISTINCT o.order_id) AS frequency,

    -- Monetary: Sum of all payment values for each customer
    SUM(p.payment_value) AS monetary

-- Use DuckDB's read_csv_auto to query CSVs directly as if they were tables
FROM read_csv_auto('data/raw/olist_customers_dataset.csv') AS c
-- Join customers to their orders
JOIN read_csv_auto('data/raw/olist_orders_dataset.csv') AS o
  ON c.customer_id = o.customer_id
-- Join orders to their corresponding payments
JOIN read_csv_auto('data/raw/olist_order_payments_dataset.csv') AS p
  ON o.order_id = p.order_id
-- Make the 'max_purchase_date' from CTE available to every row for recency calculation
CROSS JOIN latest_purchase AS lp

-- Filter to include only successfully delivered orders for accurate analysis
WHERE o.order_status = 'delivered'

-- Group results by each unique customer to perform aggregations (MAX, COUNT, SUM)
GROUP BY c.customer_unique_id, lp.max_purchase_date

-- After grouping, filter out any customers with no monetary value
HAVING SUM(p.payment_value) > 0

-- Order the final results for review
ORDER BY monetary DESC
"""

# Execution 

# 1. Run SQL query using DuckDB and convert the result to a Pandas DataFrame.
rfm_df = duckdb.query(query).to_df()

# 2. Save resulting DataFrame to new CSV file in the data/processed/ folder.
# note: `index=False` prevents pandas from writing row indices into the file
rfm_df.to_csv('data/processed/rfm_data.csv', index=False)

# 3. Print confirmation message to console indicating successful completion.
print("✅ RFM data exported to data/processed/rfm_data.csv")