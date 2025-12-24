import matplotlib.pyplot as plt
import io
from datetime import datetime, timedelta
from datetime import datetime, timedelta
# from core.db import db # Removed incorrect import
from backend.database import get_sync_db # Import specifically
from sqlalchemy import text

from sqlalchemy import text

def generate_charts():
    """
    Generate analytics charts (DAU Trend + Retention) and return as In-Memory BytesIO objects.
    Returns: dict {'dau': bytes, 'retention': bytes}
    """
    charts = {}
    
    # with db.get_sync_db() as session: # ERROR: db object has no method get_sync_db
    with get_sync_db() as session:

        # 1. DAU Trend (Last 7 Days)
        dau_sql = """
        SELECT date_trunc('day', created_at) as day, count(distinct user_id) as users
        FROM event_logs
        WHERE created_at >= now() - interval '7 days'
        GROUP BY 1
        ORDER BY 1
        """
        dau_data = session.execute(text(dau_sql)).fetchall()
        
        dates = [r[0].strftime('%d/%m') for r in dau_data]
        counts = [r[1] for r in dau_data]
        
        if not dates:
            dates = [(datetime.now() - timedelta(days=i)).strftime('%d/%m') for i in range(7)]
            counts = [0] * 7
            
        plt.figure(figsize=(6, 4))
        plt.plot(dates, counts, marker='o', linestyle='-', color='#4CAF50')
        plt.title('DAU (Last 7 Days)')
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        
        buf = io.BytesIO()
        plt.savefig(buf, format='png')
        buf.seek(0)
        charts['dau'] = buf
        plt.close()

        # 2. Retention (Simple Bar)
        # We calculated D1/D3/D7 in admin.py logic, let's re-calculate quickly for chart or mock visualization
        # Ideally pass metrics in, but let's query specific for chart
        
        # Mocking for robust visualization if data scarce
        # In prod, this query mirrors admin.py
        ret_sql = """
            WITH cohort AS (
            SELECT user_id, MIN(date_trunc('day', created_at)) AS day0
            FROM event_logs
            WHERE event_type = 'onboarding_completed' AND created_at >= now() - interval '14 days'
            GROUP BY 1
            ),
            activity AS (
            SELECT DISTINCT user_id, date_trunc('day', created_at) AS day
            FROM event_logs
            WHERE created_at >= now() - interval '14 days'
            )
            SELECT
            ROUND(100.0 * SUM(CASE WHEN EXISTS (SELECT 1 FROM activity a WHERE a.user_id=c.user_id AND a.day=c.day0 + interval '1 day') THEN 1 ELSE 0 END) / NULLIF(COUNT(*),0), 1) AS d1,
            ROUND(100.0 * SUM(CASE WHEN EXISTS (SELECT 1 FROM activity a WHERE a.user_id=c.user_id AND a.day=c.day0 + interval '3 day') THEN 1 ELSE 0 END) / NULLIF(COUNT(*),0), 1) AS d3
            FROM cohort c
        """
        res = session.execute(text(ret_sql)).fetchone()
        d1 = res[0] or 0 if res else 0
        d3 = res[1] or 0 if res else 0
        
        labels = ['Day 1', 'Day 3']
        values = [d1, d3]
        
        plt.figure(figsize=(6, 4))
        bars = plt.bar(labels, values, color=['#2196F3', '#FF9800'])
        plt.title('Retention Rate (%)')
        plt.ylim(0, 100)
        plt.grid(axis='y', alpha=0.3)
        
        # Add values on bars
        for bar in bars:
            height = bar.get_height()
            plt.text(bar.get_x() + bar.get_width()/2., height,
                    f'{height}%',
                    ha='center', va='bottom')
                    
        plt.tight_layout()
        buf2 = io.BytesIO()
        plt.savefig(buf2, format='png')
        buf2.seek(0)
        charts['retention'] = buf2
        plt.close()
        
    return charts
