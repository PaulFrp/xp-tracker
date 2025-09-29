from datetime import datetime
import random
from utils.db import get_db_connection
from utils.challenge_bank import CHALLENGE_BANK  # your challenge bank dict

def reset_daily_challenges_if_needed():
    try:
        with get_db_connection() as conn:
            c = conn.cursor()

            # Ensure last_reset_date exists
            c.execute("""
                INSERT INTO config (key, value)
                VALUES (%s, %s)
                ON CONFLICT (key) DO NOTHING
            """, ("last_reset_date", "1970-01-01"))

            # Fetch last reset date
            c.execute("SELECT value FROM config WHERE key = %s", ("last_reset_date",))
            row = c.fetchone()
            last_reset_date = row[0] if row else "1970-01-01"

            current_date = datetime.now().strftime("%Y-%m-%d")
            print("Current date:", current_date, "Last reset:", last_reset_date)

            if current_date != last_reset_date:
                print(f"Resetting daily challenges: {last_reset_date} -> {current_date}")

                # Pick 4 random challenges from the bank
                daily_choices = random.sample(list(CHALLENGE_BANK.keys()), 4)

                # Clear old challenges
                c.execute("DELETE FROM daily")

                # Assign 4 challenges to every user
                c.execute("SELECT id FROM users")
                users = c.fetchall()
                for (user_id,) in users:
                    for challenge in daily_choices:
                        c.execute(
                            "INSERT INTO daily (user_id, challenge, completed) VALUES (%s, %s, %s)",
                            (user_id, challenge, False)
                        )

                # Update last reset date
                c.execute("UPDATE config SET value = %s WHERE key = %s", (current_date, "last_reset_date"))
                conn.commit()

    except Exception as e:
        print("Error in daily reset:", e)
