import requests
base_url = "http://localhost:5000/api/admin"
try:
    r = requests.get(f"{base_url}/clubs/count?saison=5")
    print("Clubs count (Saison 5):", r.json())
    
    r = requests.get(f"{base_url}/licencies/count?saison=5")
    print("Licenciés count (Saison 5):", r.json())
except Exception as e:
    print(f"Error: {e}")
