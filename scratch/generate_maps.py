import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import os

# Create images directory if it doesn't exist
os.makedirs("images/maps", exist_ok=True)

# --- Carte 1 : Abidjan avec communes ---
def carte_abidjan():
    try:
        fig, ax = plt.subplots(figsize=(8, 8), subplot_kw={'projection': ccrs.PlateCarree()})
        ax.set_extent([-4.1, -3.9, 5.25, 5.4], crs=ccrs.PlateCarree())
        
        # Communes (coordonnées pour étiquettes - centres approximatifs)
        communes = {
            "ABOBO": (-3.98, 5.33),
            "ADJAME": (-4.03, 5.33),
            "ANYAMA": (-4.05, 5.30),
            "COCODY": (-3.98, 5.35),
            "KOUMASSI": (-4.06, 5.35),
            "PORT-BOUET": (-4.01, 5.28),
            "YOPOUGON": (-4.07, 5.32)
        }
        
        # Ajouter un fond de carte (optionnel)
        ax.add_feature(cfeature.LAND, facecolor='lightgray')
        ax.add_feature(cfeature.OCEAN, facecolor='lightblue')
        ax.add_feature(cfeature.COASTLINE, linewidth=0.5)
        
        # Tracer un contour d'Abidjan (exemple: un polygone simple)
        from matplotlib.patches import Polygon
        abidjan_contour = [
            (-4.10, 5.25), (-4.08, 5.32), (-4.05, 5.36), (-4.00, 5.38),
            (-3.95, 5.36), (-3.92, 5.33), (-3.94, 5.28), (-3.98, 5.26),
            (-4.05, 5.25), (-4.10, 5.25)
        ]
        poly = Polygon(abidjan_contour, closed=True, edgecolor='black', facecolor='none', linewidth=2)
        ax.add_patch(poly)
        
        # Étiquettes des communes
        for nom, (lon, lat) in communes.items():
            ax.text(lon, lat, nom, fontsize=9, ha='center', va='center',
                    bbox=dict(boxstyle="round,pad=0.2", facecolor="white", alpha=0.7))
        
        ax.set_title("Abidjan - Limites communales", fontsize=14)
        plt.savefig("images/maps/carte_abidjan.png", dpi=150, bbox_inches='tight')
        plt.close()
        print("Carte Abidjan générée.")
    except Exception as e:
        print(f"Erreur carte Abidjan: {e}")

# --- Carte 2 : Côte d'Ivoire avec villes ---
def carte_civ():
    try:
        fig, ax = plt.subplots(figsize=(10, 12), subplot_kw={'projection': ccrs.PlateCarree()})
        ax.set_extent([-8.6, -2.5, 4.0, 10.8], crs=ccrs.PlateCarree())
        
        # Tracer le contour de la Côte d'Ivoire
        ax.add_feature(cfeature.BORDERS, linewidth=1.5, edgecolor='black')
        ax.add_feature(cfeature.COASTLINE, linewidth=1)
        ax.add_feature(cfeature.LAKES, edgecolor='blue', facecolor='none')
        ax.add_feature(cfeature.RIVERS, edgecolor='blue', linewidth=0.5)
        
        # Villes
        villes = {
            "ABENGOUROU": (-3.49, 6.73),
            "ABOISSO": (-3.21, 5.46),
            "AKOUPE": (-3.89, 6.38),
            "BOUAKE": (-5.03, 7.69),
            "DABOU": (-4.36, 5.33),
            "DALOA": (-6.43, 6.88),
            "DUEKOUE": (-7.36, 6.74),
            "KORHOGO": (-5.67, 9.46),
            "MANKONO": (-7.30, 8.06),
            "ODIENNE": (-7.57, 9.51),
            "SAN-PEDRO": (-6.62, 4.75),
            "SOUBRE": (-6.60, 5.78),
            "YAMOUSSOUKRO": (-5.27, 6.82),
            "ZUENOULA": (-6.93, 6.90)
        }
        
        # Ajouter les étiquettes
        for nom, (lon, lat) in villes.items():
            ax.text(lon, lat, nom, fontsize=8, ha='center', va='center',
                    bbox=dict(boxstyle="round,pad=0.2", facecolor="white", alpha=0.6))
            ax.plot(lon, lat, 'ro', markersize=2)
        
        ax.set_title("Côte d'Ivoire - villes principales", fontsize=14)
        plt.savefig("images/maps/cote_ivoire_villes.png", dpi=150, bbox_inches='tight')
        plt.close()
        print("Carte CIV générée.")
    except Exception as e:
        print(f"Erreur carte CIV: {e}")

# Exécution
if __name__ == "__main__":
    carte_abidjan()
    carte_civ()
