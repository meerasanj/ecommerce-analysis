import sqlglot
from sqlglot import parse_one, exp, dialects
from typing import Tuple, Optional

# method to validate SQL syntax and return (is_valid, error_message).
def validate_sql(query: str, dialect: str = None) -> Tuple[bool, Optional[str]]:
    try:
        parse_one(query, read=dialect)
        return True, None
    except Exception as e:
        return False, str(e)

# Method to extract components from SQL query
def extract_query_components(query: str, dialect: str):
    try:
        parsed = parse_one(query, read=dialect)
        components = {
            'tables': [],
            'columns': [],
            'joins': [],
            'conditions': []
        }
        
        for table in parsed.find_all(exp.Table):
            components['tables'].append(table.name)
            
        for column in parsed.find_all(exp.Column):
            components['columns'].append(column.name)
            
        for join in parsed.find_all(exp.Join):
            components['joins'].append(join.sql())
            
        for condition in parsed.find_all(exp.Condition):
            components['conditions'].append(condition.sql())
            
        return components
    except:
        return None