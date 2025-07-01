import streamlit as st
import pandas as pd
import sqlglot
from sqlglot import parse_one, exp
import re
import json
from typing import Tuple, Optional
from utils.llm_integration import get_llm_response
from utils.schema_manager import SchemaManager

# Initialize schema manager
schema_manager = SchemaManager()

st.set_page_config(page_title="SQL Query Assistant", page_icon="🤖", layout="wide")

# Helper functions
def get_dialect_display_name(dialect: str) -> str:
    return {
        "postgres": "PostgreSQL",
        "mysql": "MySQL",
        "sqlite": "SQLite",
        "tsql": "MS SQL Server",
        "oracle": "Oracle"
    }.get(dialect, "PostgreSQL")

def detect_sql_dialect(query: str) -> Optional[str]:
    for dialect in ["postgres", "mysql", "sqlite", "tsql", "oracle"]:
        try:
            parse_one(query, read=dialect)
            return dialect
        except:
            continue
    return None

def rate_query_complexity(query: str) -> int:
    complexity = 1
    complexity += min(query.upper().count('JOIN'), 2)
    complexity += min(query.upper().count('SELECT') - 1, 2)
    if any(fn in query.upper() for fn in ['OVER(', 'PARTITION BY', 'ROW_NUMBER()']):
        complexity += 1
    if any(clause in query.upper() for clause in ['HAVING', 'WITH', 'RECURSIVE']):
        complexity += 1
    return min(max(complexity, 1), 5)

def should_deep_analyze(query: str) -> bool:
    """Determine if we need LLM analysis"""
    triggers = ['HAVING', 'GROUP BY', 'JOIN', 'WHERE', 'WITH', 'CASE']
    return any(t in query.upper() for t in triggers)

def analyze_with_llm(query: str, dialect: str) -> Tuple[bool, str]:
    """Use LLM for semantic validation"""
    prompt = f"""Analyze this {dialect} SQL query for logical errors. Return JSON with:
    {{
        "valid": boolean,
        "error": "error description" | null,
        "correction": "fixed SQL" | null
    }}

    Check for:
    - Incorrect HAVING usage
    - Missing GROUP BY with aggregates
    - Type mismatches
    - Invalid joins
    - Unqualified column names
    - {dialect}-specific issues

    Query: {query}"""

    try:
        response = get_llm_response(prompt)
        result = json.loads(response.strip())
        if not result['valid']:
            return False, result.get('error', 'Logical error detected')
        return True, ""
    except Exception as e:
        return True, ""  # Fail-safe if LLM fails

def validate_query(query: str, dialect: str) -> Tuple[bool, str]:
    """Hybrid validation with SQLGlot + LLM"""
    try:
        # Basic syntax validation
        parsed = parse_one(query, read=dialect)
        
        # Critical semantic checks (fast)
        if not any(t in query.upper() for t in ['SELECT', 'FROM']):
            return False, "Query must contain SELECT and FROM clauses"
        
        # Deeper analysis for complex queries
        if should_deep_analyze(query):
            is_valid, error = analyze_with_llm(query, dialect)
            if not is_valid:
                return False, error
        
        return True, ""
    except Exception as e:
        return False, str(e)

def explain_error(query: str, error: str, dialect: str) -> str:
    prompt = f"""As a {dialect} SQL expert, explain this error clearly:
    
    Query: {query}
    Error: {error}
    
    Provide:
    1. Simple error explanation
    2. Problem location
    3. Corrected query
    4. Best practices
    
    Format with clear section headings."""
    return get_llm_response(prompt)

def correct_sql(query: str, error: str, dialect: str) -> str:
    prompt = f"""Correct this {dialect} SQL query. Return ONLY the SQL:
    
    Error: {error}
    Intent: {st.session_state.get('query_intent', '')}
    Query: {query}"""
    corrected = get_llm_response(prompt)
    return re.sub(r'^```sql|```$', '', corrected, flags=re.IGNORECASE).strip()

def execute_query_on_csv(query: str, dialect: str) -> Tuple[pd.DataFrame, Optional[str]]:
    try:
        tables = schema_manager.get_schema()
        if not tables:
            return None, "No CSV data uploaded"
            
        conn = sqlite3.connect(':memory:')
        for table_name, df in tables.items():
            df.to_sql(table_name, conn, index=False, if_exists='replace')
        
        result = pd.read_sql_query(query, conn)
        conn.close()
        return result, None
    except Exception as e:
        return None, str(e)

def main():
    st.title("SQL Query Assistant with Error Correction")
    st.subheader("Built with Meta Llama 3")
    
    # Sidebar
    with st.sidebar:
        st.header("Data Management")
        uploaded_files = st.file_uploader("Upload CSV files", type=["csv"], accept_multiple_files=True)
        
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

    # Main tabs
    tab1, tab2 = st.tabs(["Query Assistant", "Query Validation"])
    
    with tab1:
        st.subheader("SQL Query Input")
        query = st.text_area("Enter your SQL query", height=200, key="query_input")
        
        col1, col2 = st.columns(2)
        with col1:
            dialect = st.selectbox(
                "SQL Dialect",
                options=["auto-detect", "postgres", "mysql", "sqlite", "tsql", "oracle"],
                format_func=lambda x: {
                    "auto-detect": "Auto-detect",
                    "postgres": "PostgreSQL",
                    "mysql": "MySQL",
                    "sqlite": "SQLite",
                    "tsql": "MS SQL Server",
                    "oracle": "Oracle"
                }[x],
                index=0
            )
        with col2:
            query_intent = st.text_input("Query intent (optional)", key="query_intent")
        
        if st.button("Analyze Query"):
            if not query.strip():
                st.warning("Please enter a SQL query")
                return
        
            with st.spinner("Analyzing..."):
                if dialect == "auto-detect":
                    detected_dialect = detect_sql_dialect(query)
                    dialect = detected_dialect or "postgres"
                    st.info(f"Using dialect: {get_dialect_display_name(dialect)}")
                
                is_valid, error = validate_query(query, dialect)
                
                if is_valid:
                    st.success("✅ Valid SQL")
                    complexity = rate_query_complexity(query)
                    st.write(f"**Complexity:** {complexity}/5")
                    
                    if schema_manager.get_schema():
                        result, error = execute_query_on_csv(query, dialect)
                        if error:
                            st.error(f"Execution error: {error}")
                        else:
                            st.dataframe(result.head(10))
                else:
                    st.error("❌ Invalid SQL")
                    with st.expander("Error Details"):
                        st.write(explain_error(query, error, dialect))
                    
                    corrected = correct_sql(query, error, dialect)
                    st.code(corrected, language="sql")
                    
                    if st.button("Try Correction"):
                        st.session_state.query_input = corrected
                        st.rerun()
    
    with tab2:
        if schema_manager.get_schema():
            validation_query = st.text_area("Test query against your data", height=200)
            if st.button("Validate"):
                with st.spinner("Validating..."):
                    result, error = execute_query_on_csv(validation_query, dialect)
                    if error:
                        st.error(f"Error: {error}")
                    else:
                        st.success(f"Returned {len(result)} rows")
                        st.dataframe(result.head(10))
        else:
            st.warning("Upload CSV files to enable validation")

if __name__ == "__main__":
    import sqlite3  # Moved here to prevent Streamlit reload issues
    main()