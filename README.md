# Olist E-Commerce Customer Segmentation Analysis

## Project Overview

This project performs a customer segmentation analysis for Olist, a large Brazilian e-commerce platform that connects small businesses with customers across major marketplaces. The goal is to move beyond treating all customers as a single entity and instead identify distinct, actionable groups based on their purchasing behavior.

By leveraging RFM (Recency, Frequency, Monetary) analysis and K-Means clustering, I segmented the customer base into meaningful personas. These insights provide a data-driven foundation for developing targeted marketing strategies, improving customer retention, and maximizing customer lifetime value.

The final output of this project includes a detailed analytical report and an interactive Tableau dashboard designed for business stakeholders to explore the customer segments.

## Key Business Questions

This analysis seeks to answer the following questions:
1.  Can we identify distinct groups of customers based on their transaction history?
2.  What are the key characteristics (Recency, Frequency, Monetary value) of each customer group?
3.  How large is each customer segment, and what is its overall contribution to total revenue?
4.  What targeted marketing actions can be taken to engage each segment effectively?

## Tools and Technologies

* Database: SQL for data extraction and preparation.
* Analysis: R (with RStudio or VS Code) for statistical analysis and clustering.
    * *Key R Packages:* `dplyr`, `ggplot2`, `knitr`, `factoextra`
* Reporting: R Markdown for creating the final PDF report.
* Visualization: Tableau for creating the interactive dashboard.

## Methodology

The analysis was conducted in three main stages:

1.  **Data Preparation (SQL):** The initial raw data from the Olist dataset was processed using SQL. The `calculate_rfm.sql` script joins the customer, order, and payment tables to calculate the core RFM metrics for each unique customer. The new CSV file `rfm_data.csv` is then saved to `data/processed/`.
* The dataset used for this project can be found on [Kaggle](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce?resource=download).
2.  **Clustering and Analysis (R):** The aggregated RFM data was analyzed with R using the `analysis_and_report.Rmd` script, which exports the final report on Olist's Customer Segmentation into `output/analysis_and_report.pdf`.
* **Data Transformation:** To prepare the data for clustering, skewed RFM values were log-transformed and then scaled.
* **K-Means Clustering:** The K-Means algorithm was applied to group customers into distinct clusters. The optimal number of clusters was determined using the Elbow Method.
* **Persona Creation:** Each cluster was assigned a descriptive persona based on its average RFM characteristics, providing a clear business identity for each group.
3.  **Visualization and Dashboarding (Tableau):** The final, segmented data was exported to a CSV file located in `output/olist_tableau_data.csv`. An interactive dashboard was built in Tableau to visualize the segments and allow for dynamic exploration of the data.

## Identified Customer Segments

The analysis successfully identified four key customer personas:

| **Persona**                 | **Key Characteristics**                                                                                  | **Recommended Action**                                                                                                   |
|----------------------------|-----------------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------------------------|
| **Loyal Customers**        | High frequency, high monetary value, recent purchasers. They are repeat buyers and the backbone of the business. | Reward with loyalty programs, offer exclusive access to new products, and send personalized "thank you" offers.          |
| **Hibernating High Spenders** | High monetary value but have not purchased in a long time (high recency). They are a high-value, high-risk segment. | Launch targeted win-back campaigns with compelling discounts to encourage their return.                                  |
| **New Customers**          | Very recent, single-purchase customers with modest spending. They have the potential to become loyal.     | Nurture with a welcome email series and targeted follow-up promotions to encourage a second purchase.                    |
| **At-Risk Low Spenders**   | High recency, single purchase, and low monetary value. This is the largest but least engaged segment.     | Engage with low-touch, automated email campaigns. Avoid high-cost marketing efforts.                                     |

## How to Run This Project

### Prerequisites
* An environment to run SQL queries (e.g., VS Code with a SQL extension or directly via a Python script).
* R and an IDE like RStudio or VS Code with the R extension.
* A LaTeX distribution for rendering PDFs from R Markdown (`tinytex` is used for this project).

### Setup
1.  **Clone the repository:**
    ```bash
    git clone [https://github.com/meerasanj/ecommerce-analysis.git](https://github.com/meerasanj/ecommerce-analysis.git)
    cd ecommerce-analysis
    ```
2.  **Install Python Packages:** Open a terminal and run:
    ```bash
    pip3 install duckdb pandas # Installs DuckDB and Pandas packages
    ```
3.  **Install R Packages:** Open an R console and run:
    ```r
    install.packages(c("dplyr", "ggplot2", "knitr", "factoextra", "tinytex"))
    tinytex::install_tinytex()
    ```

### Execution
1.  **Run the SQL Script:** Execute the `calculate_rfm.sql` script against the Olist database. This can be done in your preferred SQL environment or by running a Python script that uses the DuckDB library. The output should be saved as `rfm_data.csv` inside the `data/processed/` directory.
2.  **Run the R Markdown Analysis:** Render the R Markdown file using the command line terminal. This will generate the PDF report and the CSV for Tableau in the `output/` folder.
    ```bash
    Rscript -e "rmarkdown::render('scripts/analysis_and_report.Rmd', output_dir = 'output')"
    ```
    Alternatively, open `analysis_and_report.Rmd` in RStudio or VS Code and click the **"Knit"** or **"Render"** button.
3.  **Optional: Build the Tableau Dashboard:**
    * Open Tableau and connect to the `olist_tableau_data.csv` file generated in the previous step.
    * Follow the methodology described in the report to build the worksheets and the final interactive dashboard.

## Final Outputs

1.  **Analytical Report:** A detailed PDF report (`analysis_and_report.pdf`) located in the `output/` directory, outlining the methodology, findings, and recommendations.
2.  **Interactive Dashboard:** A Tableau Public dashboard for exploring the customer segments.
    * **[Link to Live Dashboard](https://public.tableau.com/views/Olist_Customer_Analysis_Dashboard/Dashboard1?:language=en-US&:sid=&:redirect=auth&:display_count=n&:origin=viz_share_link)** 

## License
Copyright (c) 2025 Meera Sanjeevirao

This project uses the "Brazilian E-Commerce Public Dataset by Olist," which is available on [Kaggle](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce?resource=download). The dataset is made available under the Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International license (CC BY-NC-SA 4.0).
