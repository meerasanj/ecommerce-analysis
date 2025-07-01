import pandas as pd
import streamlit as st
import os
import hashlib
from typing import Dict, Optional

class SchemaManager:
    def __init__(self):
        self.schema_cache_dir = "schema_cache"
        os.makedirs(self.schema_cache_dir, exist_ok=True)
        
    # Method to generate a clean table from file name 
    def _get_table_name(self, file_name: str) -> str:
        name = os.path.splitext(file_name)[0]
        name = re.sub(r'[^a-zA-Z0-9_]', '_', name)
        return name.lower()
    
    # Method to get path for cached table data
    def _get_cache_path(self, table_name: str) -> str:
        return os.path.join(self.schema_cache_dir, f"{table_name}.parquet")
    
    # Method to add a table from uploaded CSV
    def add_table(self, uploaded_file) -> None:
        table_name = self._get_table_name(uploaded_file.name)
        
        try:
            df = pd.read_csv(uploaded_file)
            cache_path = self._get_cache_path(table_name)
            df.to_parquet(cache_path)
            
            # Store in session state
            if 'tables' not in st.session_state:
                st.session_state.tables = {}
            st.session_state.tables[table_name] = df
        except Exception as e:
            st.error(f"Error loading {uploaded_file.name}: {str(e)}")
    
    # Method to get current schema with tables + data
    def get_schema(self) -> Dict[str, pd.DataFrame]:
        if 'tables' in st.session_state:
            return st.session_state.tables
        return {}
    
    # Method to clear all uploaded data
    def clear_all(self) -> None:
        if 'tables' in st.session_state:
            del st.session_state.tables
        
        # Clear cache files
        for file in os.listdir(self.schema_cache_dir):
            if file.endswith('.parquet'):
                os.remove(os.path.join(self.schema_cache_dir, file))