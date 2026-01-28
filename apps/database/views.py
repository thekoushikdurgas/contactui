"""Database views."""
from django.shortcuts import render
from django.contrib.auth.decorators import login_required


@login_required
def database_view(request):
    """Database schema viewer."""
    from django.db import connection
    
    try:
        with connection.cursor() as cursor:
            # Get table list
            if connection.vendor == 'postgresql':
                cursor.execute("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public'
                    ORDER BY table_name
                """)
                tables = [row[0] for row in cursor.fetchall()]
            else:
                # SQLite fallback
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = [row[0] for row in cursor.fetchall()]
    except Exception:
        tables = []
    
    context = {
        'tables': tables,
        'schema_sql': '-- Database schema will be displayed here'
    }
    return render(request, 'database/schema.html', context)
