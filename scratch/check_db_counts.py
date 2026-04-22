import db_utils
try:
    conn = db_utils.get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Check clubs in season 5
    cursor.execute("SELECT COUNT(DISTINCT List_club) as count FROM clubs_saison WHERE List_saison = 5")
    clubs = cursor.fetchone()
    print(f"Clubs in season 5: {clubs['count']}")
    
    # Check athletes in season 5
    # Note: I need to check the correct column name for athletes_saison
    # Earlier I used 'list_saison' and 'list_ath'
    cursor.execute("SELECT COUNT(DISTINCT list_ath) as count FROM athletes_saison WHERE list_saison = 5")
    athletes = cursor.fetchone()
    print(f"Athletes in season 5: {athletes['count']}")
    
    cursor.close()
    conn.close()
except Exception as e:
    print(f"Error: {e}")
