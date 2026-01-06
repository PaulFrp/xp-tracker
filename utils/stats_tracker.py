from datetime import datetime, date
from utils.db import get_db_connection

def get_daily_stats(user_id):
    """Get today's stats (XP earned, challenges completed)"""
    today = date.today().isoformat()
    
    with get_db_connection() as conn:
        c = conn.cursor()
        
        # Get actual count of completed challenges from daily table
        c.execute("""
            SELECT COUNT(*) FROM daily 
            WHERE user_id = %s AND completed = TRUE
        """, (user_id,))
        actual_completed = c.fetchone()[0]
        
        # Get XP earned today
        c.execute("""
            SELECT xp_earned
            FROM daily_stats
            WHERE user_id = %s AND date = %s
        """, (user_id, today))
        
        row = c.fetchone()
        xp_earned = row[0] if row else 0
        
        return {"xp_earned": xp_earned, "challenges_completed": actual_completed}

def update_daily_stats(user_id, xp_added=0, challenge_completed=False, decrement=False):
    """Update today's stats - only tracks XP, challenges are counted from daily table"""
    today = date.today().isoformat()
    
    with get_db_connection() as conn:
        c = conn.cursor()
        
        # Only track XP earned, ignore challenge_completed parameter
        if xp_added > 0:
            c.execute("""
                INSERT INTO daily_stats (user_id, date, xp_earned, challenges_completed)
                VALUES (%s, %s, %s, 0)
                ON CONFLICT (user_id, date) DO UPDATE SET
                    xp_earned = daily_stats.xp_earned + %s
            """, (user_id, today, xp_added, xp_added))
            conn.commit()

def get_streaks(user_id):
    """Get all skill streaks for a user"""
    with get_db_connection() as conn:
        c = conn.cursor()
        c.execute("""
            SELECT skill, current_streak, best_streak, last_completed
            FROM streaks
            WHERE user_id = %s
            ORDER BY current_streak DESC
        """, (user_id,))
        
        rows = c.fetchall()
        return [{"skill": r[0], "current": r[1], "best": r[2], "last_completed": r[3]} for r in rows]

def update_streak(user_id, skill, increment=1):
    """Update streak for a skill"""
    today = date.today().isoformat()
    
    with get_db_connection() as conn:
        c = conn.cursor()
        
        # Get current streak info
        c.execute("""
            SELECT current_streak, best_streak, last_completed
            FROM streaks
            WHERE user_id = %s AND skill = %s
        """, (user_id, skill))
        
        row = c.fetchone()
        if row:
            current_streak, best_streak, last_completed = row
            
            # Check if streak should continue or reset
            if last_completed and last_completed == today:
                # Already completed today, no change
                return
            
            # Check if streak continues (completed yesterday or today)
            yesterday = (datetime.now().date() - __import__('datetime').timedelta(days=1)).isoformat()
            
            if last_completed == yesterday:
                # Continue streak
                new_streak = current_streak + 1
                new_best = max(best_streak, new_streak)
            else:
                # Streak broken, reset to 1
                new_streak = 1
                new_best = best_streak
            
            c.execute("""
                UPDATE streaks
                SET current_streak = %s, best_streak = %s, last_completed = %s
                WHERE user_id = %s AND skill = %s
            """, (new_streak, new_best, today, user_id, skill))
        else:
            # First time completing this skill
            c.execute("""
                INSERT INTO streaks (user_id, skill, current_streak, best_streak, last_completed)
                VALUES (%s, %s, %s, %s, %s)
            """, (user_id, skill, 1, 1, today))
        
        conn.commit()

def get_next_milestone(user_id, skill):
    """Calculate next level milestone for a skill"""
    with get_db_connection() as conn:
        c = conn.cursor()
        c.execute("""
            SELECT xp, level
            FROM progress
            WHERE user_id = %s AND skill = %s
        """, (user_id, skill))
        
        row = c.fetchone()
        if row:
            current_xp, current_level = row
            xp_for_next = 80 + 12 * (current_level * (current_level + 1)) // 2
            xp_remaining = max(0, xp_for_next - current_xp)
            return {
                "next_level": current_level + 1,
                "xp_needed": xp_for_next,
                "xp_current": current_xp,
                "xp_remaining": xp_remaining
            }
        return None

def get_all_milestones(user_id):
    """Calculate next level milestones for all skills at once - OPTIMIZED"""
    with get_db_connection() as conn:
        c = conn.cursor()
        c.execute("""
            SELECT skill, xp, level
            FROM progress
            WHERE user_id = %s
        """, (user_id,))
        
        rows = c.fetchall()
        milestones = {}
        for skill, current_xp, current_level in rows:
            xp_for_next = 80 + 12 * (current_level * (current_level + 1)) // 2
            xp_remaining = max(0, xp_for_next - current_xp)
            milestones[skill] = {
                "next_level": current_level + 1,
                "xp_needed": xp_for_next,
                "xp_current": current_xp,
                "xp_remaining": xp_remaining
            }
        return milestones
