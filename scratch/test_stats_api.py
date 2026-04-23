
import urllib.request
import json

BASE_URL = "http://localhost:5000/api/admin"

def test_stats():
    try:
        # Test saisons first
        with urllib.request.urlopen(f"{BASE_URL}/saisons") as response:
            saisons = json.loads(response.read().decode())
        print("Saisons:", saisons)
        
        if saisons['success'] and saisons['saisons']:
            saison_id = saisons['saisons'][0]['id_saison']
            print(f"Testing stats for saison_id={saison_id}")
            with urllib.request.urlopen(f"{BASE_URL}/stats/sectorielles?saison_id={saison_id}") as response:
                stats = json.loads(response.read().decode())
            print("Stats:", json.dumps(stats, indent=2))
        else:
            print("No seasons found to test stats.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_stats()
