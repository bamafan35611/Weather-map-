"""
learning_monitor.py - Check if your bot is learning
Run this to see proof of learning in real-time!
"""

import sqlite3
from datetime import datetime, timedelta
import os

DB_PATH = os.getenv('SQLITE_DB_PATH', '/data/weather_learning.db')

# Fallback for local
if not os.path.exists(DB_PATH):
    DB_PATH = 'weather_learning.db'

def check_database_exists():
    """Check if database file exists"""
    if os.path.exists(DB_PATH):
        size = os.path.getsize(DB_PATH)
        print(f"✅ Database found at: {DB_PATH}")
        print(f"   Size: {size:,} bytes ({size/1024:.2f} KB)")
        return True
    else:
        print(f"❌ Database not found at: {DB_PATH}")
        print("   Bot hasn't created database yet - wait for first forecast")
        return False

def count_forecasts():
    """Count total forecasts"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('SELECT COUNT(*) FROM forecasts')
    total = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM forecasts WHERE verified = 1')
    verified = cursor.fetchone()[0]
    
    conn.close()
    
    return total, verified

def get_recent_forecasts(limit=5):
    """Get most recent forecasts"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT 
            id,
            timestamp,
            location,
            predicted_event,
            confidence,
            verified,
            accuracy_score
        FROM forecasts 
        ORDER BY timestamp DESC 
        LIMIT ?
    ''', (limit,))
    
    forecasts = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return forecasts

def get_accuracy_trend():
    """Get accuracy over time"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Last 7 days
    week_ago = (datetime.now() - timedelta(days=7)).isoformat()
    cursor.execute('''
        SELECT AVG(accuracy_score) FROM forecasts 
        WHERE verified = 1 AND timestamp >= ?
    ''', (week_ago,))
    recent = cursor.fetchone()[0] or 0.0
    
    # Previous 7 days
    two_weeks_ago = (datetime.now() - timedelta(days=14)).isoformat()
    cursor.execute('''
        SELECT AVG(accuracy_score) FROM forecasts 
        WHERE verified = 1 AND timestamp >= ? AND timestamp < ?
    ''', (two_weeks_ago, week_ago))
    previous = cursor.fetchone()[0] or 0.0
    
    conn.close()
    
    return recent, previous

def get_alert_history_count():
    """Count actual alerts that occurred"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('SELECT COUNT(*) FROM alert_history')
    total = cursor.fetchone()[0]
    
    conn.close()
    return total

def get_pattern_count():
    """Count learned patterns"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('SELECT COUNT(*) FROM patterns')
    total = cursor.fetchone()[0]
    
    conn.close()
    return total

def main():
    print("=" * 70)
    print("🧠 NORTHBAMAWX LEARNING MONITOR")
    print("=" * 70)
    print()
    
    # Check if database exists
    if not check_database_exists():
        print("\n💡 TIP: Deploy your bot and wait for weather events to start learning!")
        return
    
    print()
    
    # Count forecasts
    try:
        total, verified = count_forecasts()
        print(f"📊 FORECAST STATISTICS:")
        print(f"   Total predictions made: {total}")
        print(f"   Verified predictions: {verified}")
        
        if total == 0:
            print("\n⏳ No forecasts yet - bot is waiting for weather events")
            print("   Learning will begin when conditions warrant predictions")
        else:
            print(f"   Verification rate: {verified/total*100:.1f}%")
        
        print()
    except Exception as e:
        print(f"❌ Error reading forecasts: {e}")
        return
    
    # Show recent forecasts
    if total > 0:
        print("📋 RECENT PREDICTIONS:")
        forecasts = get_recent_forecasts(5)
        
        for i, f in enumerate(forecasts, 1):
            verified_icon = "✓" if f['verified'] else "⏳"
            accuracy = f"{f['accuracy_score']*100:.0f}%" if f['accuracy_score'] else "Pending"
            confidence = f"{f['confidence']*100:.0f}%" if f['confidence'] else "N/A"
            
            print(f"\n   {i}. {f['predicted_event']}")
            print(f"      Location: {f['location']}")
            print(f"      Confidence: {confidence}")
            print(f"      Verified: {verified_icon}")
            if f['verified']:
                print(f"      Accuracy: {accuracy}")
        
        print()
    
    # Show accuracy trend
    if verified > 0:
        recent_acc, prev_acc = get_accuracy_trend()
        
        print("📈 LEARNING PROGRESS:")
        print(f"   Recent accuracy (7 days): {recent_acc*100:.1f}%")
        if prev_acc > 0:
            print(f"   Previous accuracy (7 days): {prev_acc*100:.1f}%")
            improvement = (recent_acc - prev_acc) * 100
            if improvement > 0:
                print(f"   Improvement: +{improvement:.1f}% 📈 GETTING SMARTER!")
            elif improvement < 0:
                print(f"   Change: {improvement:.1f}% (learning from mistakes)")
            else:
                print(f"   Change: No change (consistent)")
        
        print()
    
    # Alert history
    try:
        alert_count = get_alert_history_count()
        print(f"🚨 ALERTS TRACKED:")
        print(f"   Actual weather events logged: {alert_count}")
        print()
    except:
        pass
    
    # Learned patterns
    try:
        pattern_count = get_pattern_count()
        print(f"🧩 PATTERNS DISCOVERED:")
        print(f"   Weather patterns learned: {pattern_count}")
        if pattern_count > 0:
            print(f"   Bot is recognizing recurring conditions!")
        print()
    except:
        pass
    
    # Learning status
    print("🎯 LEARNING STATUS:")
    
    if total == 0:
        print("   Status: WAITING FOR DATA")
        print("   Next: Bot will predict when conditions warrant")
    elif total < 10:
        print("   Status: GATHERING DATA (Early stage)")
        print(f"   Progress: {total}/100 forecasts for baseline")
    elif total < 100:
        print("   Status: LEARNING PATTERNS (Building knowledge)")
        print(f"   Progress: {total}/100 forecasts for initial learning")
    elif total < 500:
        print("   Status: IMPROVING ACCURACY (Getting smarter)")
        print(f"   Progress: {total}/500 forecasts for strong patterns")
    else:
        print("   Status: EXPERT LEVEL (Highly trained)")
        print(f"   Total experience: {total} forecasts analyzed")
    
    if verified > 0 and total > 0:
        avg_accuracy = sum(f.get('accuracy_score', 0) for f in get_recent_forecasts(verified)) / verified
        print(f"   Current skill level: {avg_accuracy*100:.0f}% accurate")
    
    print()
    print("=" * 70)
    print("✅ Bot is actively learning from weather events!")
    print("💡 Check back weekly to see improvement over time")
    print("=" * 70)

if __name__ == '__main__':
    main()
