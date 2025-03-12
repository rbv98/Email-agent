from mistralai import Mistral
from sqlalchemy import create_engine, text
import os
import re
from datetime import datetime, timedelta

class QueryProcessor:
    def __init__(self):
        self.engine = create_engine('sqlite:///emails.db')
        self.client = Mistral(api_key=os.getenv("MISTRAL_API_KEY"))
        self.model = "mistral-large-latest"
    
    def process_query(self, query):
        try:
            # Generate SQL using the LLM
            sql_query = self._generate_sql(query)
            
            # Apply SQLite compatibility fixes
            sql_query = self._fix_sqlite_compatibility(sql_query)
            
            print(f"Generated SQL query: {sql_query}")
            
            with self.engine.connect() as connection:
                result = connection.execute(text(sql_query))
                results = result.fetchall()
            return results, sql_query
        except Exception as e:
            return f"Error executing query: {str(e)}", None
    
    def _generate_sql(self, query):
        # Create a context with today's date to help with relative time references
        today = datetime.now()
        date_context = f"""Today's date is {today.strftime('%Y-%m-%d')}.
        - "Last week" means from {(today - timedelta(days=7)).strftime('%Y-%m-%d')} to {today.strftime('%Y-%m-%d')}
        - "Yesterday" means {(today - timedelta(days=1)).strftime('%Y-%m-%d')}
        - "Last month" means from {(today - timedelta(days=30)).strftime('%Y-%m-%d')} to {today.strftime('%Y-%m-%d')}
        """
        
        chat_response = self.client.chat.complete(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": f"""You are a SQL expert. Convert natural language queries to SQL for a SQLite database.
                    Return ONLY the raw SQL query without ANY markdown formatting, code blocks, backticks, or explanations.
                    
                    {date_context}
                    
                    The database has a table 'emails' with columns: 
                    - id (TEXT)
                    - sender (TEXT) - Contains both name and email address like "John Doe <john@example.com>"
                    - recipient (TEXT)
                    - date (DATETIME) - Stored in format YYYY-MM-DD HH:MM:SS
                    - subject (TEXT)
                    - content (TEXT)
                    
                    IMPORTANT RULES:
                    1. Use SQLite syntax:
                       - Instead of CURDATE(), use DATE('now')
                       - Instead of NOW(), use DATETIME('now')
                       - For date operations, use DATE() and DATETIME() functions
                       
                    2. For searching people:
                       - Always use LIKE '%name%' instead of equality to enable partial matching
                       - If query mentions a name without an email, search in the sender field with LIKE
                       
                    3. For string searches:
                       - Use the LIKE operator with % wildcards
                       - Make searches case-insensitive when possible
                       
                    4. Sort by date in descending order (newest first) unless specified otherwise
                    
                    5. For time-based queries, convert relative time references to absolute dates:
                       - "last week" means emails from the past 7 days
                       - "last month" means emails from the past 30 days
                       - "today" means emails from today's date
                       - "yesterday" means emails from yesterday's date
                       - "this week" means emails since the start of the current week
                       - "last year" means emails from the past 365 days
                       
                    6. For combined queries like "show emails from last week sent by John":
                       - Combine time conditions AND sender conditions
                       - For example: "WHERE date >= '2025-02-21' AND date <= '2025-02-28' AND sender LIKE '%John%'"
                       
                    Remember, return ONLY the raw SQL query. Do not include any backticks, markdown formatting, or explanations.
                    """
                },
                {
                    "role": "user",
                    "content": f"Write SQL query for: {query}"
                }
            ]
        )
        
        response_text = chat_response.choices[0].message.content
        
        # Remove any markdown formatting
        # First, remove code block markers like ```sql and ```
        response_text = re.sub(r'```\w*', '', response_text)
        response_text = response_text.replace('```', '')
        
        # Remove any inline backticks
        response_text = response_text.replace('`', '')
        
        # Strip whitespace
        response_text = response_text.strip()
        
        # Check if we actually got a SQL query back
        if "SELECT" in response_text.upper():
            # Ensure it ends with a semicolon
            if not response_text.strip().endswith(';'):
                response_text = response_text.strip() + ';'
                
            return response_text
        else:
            raise ValueError("No valid SQL query found in the response")
    
    def _fix_sqlite_compatibility(self, query):
        """Apply fixes to ensure SQL is compatible with SQLite"""
        # Handle basic SQLite compatibility issues
        
        # Ensure we have ORDER BY date DESC if not already present
        if 'ORDER BY' not in query.upper():
            query = query.rstrip(';') + ' ORDER BY date DESC;'
            
        return query