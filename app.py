import streamlit as st
import pandas as pd
import sqlparse
import sqlglot
from sqlglot import parse_one, exp, dialects
from utils.llm_integration import get_llm_response
from utils.schema_manager import SchemaManager
import re
from typing import Tuple, Dict, Optional

# Initialize schema manager
schema_manager = SchemaManager()

st.set_page_config(page_title="SQL Query Assistant", page_icon="🤖", layout="wide")

# Method to auto-detect SQL dialect from query 
def detect_sql_dialect(query: str) -> str:
    try:
        dialect = parse_one(query).sql(dialect=None)
        for d in dialects.Dialect.classes:
            try:
                parse_one(query, read=d)
                return d
            except:
                continue
        return "Generic"
    except:
        return "Generic"

# Method to determine query complexity (scale of 1-5)
def rate_query_complexity(query: str) -> int:
    complexity = 1
    # Count joins
    complexity += min(query.upper().count('JOIN'), 2)
    # Count subqueries
    complexity += min(query.upper().count('SELECT') - 1, 2)
    # Check for window functions
    if any(fn in query.upper() for fn in ['OVER(', 'PARTITION BY', 'ROW_NUMBER()']):
        complexity += 1
    # Check for complex clauses
    if any(clause in query.upper() for clause in ['HAVING', 'WITH', 'RECURSIVE']):
        complexity += 1
    return min(max(complexity, 1), 5)

# Method to validate syntax of query
def validate_query(query: str, dialect: str) -> Tuple[bool, Optional[str]]:
    try:
        parse_one(query, read=dialect)
        return True, None
    except Exception as e:
        return False, str(e)

# Method to generate an explanation for SQL error and fixes 
def explain_error(query: str, error: str, dialect: str) -> str:
    prompt = f"""
You are an expert SQL assistant specializing in {dialect}.

A user submitted the following SQL query:

{query}

The query produced the following error:

{error}

Please do the following:
1. Identify and explain the error in simple, clear language.
2. Point out the specific part of the query that caused the error.
3. Return a corrected version of the query if possible.
4. Suggest best practices to avoid similar mistakes in the future.

Respond in this format:

Error Explanation:
...

Problematic Part:
...

Corrected SQL:
...

Best Practices:
...
"""
    return get_llm_response(prompt)

# Method to generate the corrected version of the SQL query 
def correct_sql(query: str, error: str, dialect: str) -> str:
    prompt = f"""
    Correct this {dialect} SQL query. Return ONLY the corrected SQL with no additional text.
    
    Original query: {query}
    
    Error: {error}
    
    The query is intended to: {st.session_state.get('query_intent', '')}
    """
    corrected = get_llm_response(prompt)
    
    # Clean up LLM response to extract just the SQL
    corrected = re.sub(r'^```sql|```$', '', corrected, flags=re.IGNORECASE).strip()
    return corrected

# If given, method will execute query on uploaded csv data 
def execute_query_on_csv(query: str, dialect: str) -> Tuple[pd.DataFrame, Optional[str]]:
    try:
        # Get the current schema and data
        tables = schema_manager.get_schema()
        if not tables:
            return None, "No CSV data uploaded"
            
        # Create SQLite in-memory database
        import sqlite3
        conn = sqlite3.connect(':memory:')
        
        # Load data into SQLite
        for table_name, df in tables.items():
            df.to_sql(table_name, conn, index=False, if_exists='replace')
        
        # Execute query
        result = pd.read_sql_query(query, conn)
        conn.close()
        return result, None
    except Exception as e:
        return None, str(e)

# Main method for program flow 
def main():
    st.title("SQL Query Assistant with Error Correction")
    
    # Sidebar for CSV upload and schema management
    with st.sidebar:
        st.header("Data Management")
        uploaded_files = st.file_uploader(
            "Upload CSV files", 
            type=["csv"], 
            accept_multiple_files=True,
            help="Upload CSV files to validate your queries against actual data"
        )
        
        if uploaded_files:
            for uploaded_file in uploaded_files:
                schema_manager.add_table(uploaded_file)
            st.success(f"Loaded {len(uploaded_files)} file(s)")
        
        if st.button("Clear All Data"):
            schema_manager.clear_all()
            st.session_state.clear()
            st.rerun()
        
        if schema_manager.get_schema():
            st.subheader("Current Schema")
            for table_name, df in schema_manager.get_schema().items():
                st.write(f"**{table_name}** ({len(df)} rows)")
                st.write(df.columns.tolist())

    # Main content area
    tab1, tab2 = st.tabs(["Query Assistant", "Query Validation"])
    
    with tab1:
        st.subheader("SQL Query Input")
        query = st.text_area(
            "Enter your SQL query", 
            height=200,
            placeholder="SELECT * FROM customers WHERE...",
            key="query_input"
        )
        
        col1, col2 = st.columns(2)
        with col1:
            dialect = st.selectbox(
                "SQL Dialect (or auto-detect)",
                options=["Auto-detect", "MySQL", "PostgreSQL", "SQLite", "MS SQL", "Oracle"],
                index=0
            )
        with col2:
            query_intent = st.text_input(
                "What are you trying to accomplish? (optional)",
                help="Helps the AI better understand your intent",
                key="query_intent"
            )
        
        if st.button("Analyze Query"):
            if not query.strip():
                st.warning("Please enter a SQL query")
                return
                
            with st.spinner("Analyzing query..."):
                # Auto-detect dialect if needed
                if dialect == "Auto-detect":
                    dialect = detect_sql_dialect(query)
                    st.info(f"Auto-detected dialect: {dialect}")
                
                # Validate query
                is_valid, error = validate_query(query, dialect)
                
                if is_valid:
                    st.success("✅ Query is valid!")
                    complexity = rate_query_complexity(query)
                    st.write(f"**Complexity rating:** {complexity}/5")
                    
                    if schema_manager.get_schema():
                        st.subheader("Query Results Preview")
                        result, error = execute_query_on_csv(query, dialect)
                        if error:
                            st.error(f"Execution error: {error}")
                        else:
                            st.dataframe(result.head(10))
                else:
                    st.error("❌ Query contains errors")
                    complexity = rate_query_complexity(query)
                    st.write(f"**Complexity rating:** {complexity}/5")
                    
                    with st.expander("Error Details"):
                        st.write(f"**Error:** `{error}`")
                        explanation = explain_error(query, error, dialect)
                        st.write("**Explanation:**")
                        st.write(explanation)
                    
                    st.subheader("Query Correction")
                    corrected = correct_sql(query, error, dialect)
                    st.code(corrected, language="sql")
                    
                    if st.button("Try corrected query"):
                        st.session_state.query_input = corrected
                        st.rerun()
    
    with tab2:
        if not schema_manager.get_schema():
            st.warning("Upload CSV files to validate queries against data")
        else:
            st.subheader("Validate Query Against Your Data")
            validation_query = st.text_area(
                "Enter SQL query to validate", 
                height=200,
                placeholder="SELECT * FROM your_table WHERE...",
                key="validation_query"
            )
            
            if st.button("Validate Query"):
                if not validation_query.strip():
                    st.warning("Please enter a SQL query")
                    return
                
                with st.spinner("Validating query..."):
                    # Auto-detect dialect if needed
                    if dialect == "Auto-detect":
                        dialect = detect_sql_dialect(validation_query)
                        st.info(f"Auto-detected dialect: {dialect}")
                    
                    # First validate syntax
                    is_valid, error = validate_query(validation_query, dialect)
                    
                    if not is_valid:
                        st.error("❌ Query contains syntax errors")
                        st.write(f"**Error:** `{error}`")
                        return
                    
                    # Then execute against data
                    result, error = execute_query_on_csv(validation_query, dialect)
                    
                    if error:
                        st.error(f"❌ Data validation error: {error}")
                        
                        with st.expander("Error Analysis"):
                            explanation = explain_error(validation_query, error, dialect)
                            st.write(explanation)
                            
                            corrected = correct_sql(validation_query, error, dialect)
                            st.write("**Suggested correction:**")
                            st.code(corrected, language="sql")
                    else:
                        st.success("✅ Query executed successfully against your data!")
                        st.write(f"Returned {len(result)} rows")
                        st.dataframe(result.head(10))

if __name__ == "__main__":
    main()