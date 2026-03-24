"""seed.py — Peuple la base avec des produits informatiques de démonstration."""

from app import create_app
from models import db, Product

PRODUITS = [
    # Processeurs
    {"nom": "Intel Core i9-14900K", "description": "Processeur 24 cœurs (8P+16E), 6.0 GHz boost, socket LGA1700", "categorie": "Processeurs", "prix": 589.99, "quantite_stock": 15},
    {"nom": "AMD Ryzen 9 7950X", "description": "Processeur 16 cœurs 32 threads, 5.7 GHz boost, socket AM5", "categorie": "Processeurs", "prix": 549.99, "quantite_stock": 12},
    {"nom": "Intel Core i5-13600K", "description": "Processeur 14 cœurs (6P+8E), 5.1 GHz boost, socket LGA1700", "categorie": "Processeurs", "prix": 289.99, "quantite_stock": 30},
    # Cartes graphiques
    {"nom": "NVIDIA GeForce RTX 4090", "description": "GPU 24 Go GDDR6X, 16384 CUDA cores, PCIe 4.0", "categorie": "Cartes graphiques", "prix": 1799.99, "quantite_stock": 8},
    {"nom": "AMD Radeon RX 7900 XTX", "description": "GPU 24 Go GDDR6, 6144 stream processors, PCIe 4.0", "categorie": "Cartes graphiques", "prix": 999.99, "quantite_stock": 10},
    {"nom": "NVIDIA GeForce RTX 4070", "description": "GPU 12 Go GDDR6X, 5888 CUDA cores, idéal 1440p", "categorie": "Cartes graphiques", "prix": 649.99, "quantite_stock": 20},
    # Mémoire RAM
    {"nom": "Corsair Vengeance DDR5 32 Go", "description": "Kit 2x16 Go DDR5-6000 CL36, RGB, compatible XMP 3.0", "categorie": "Mémoire RAM", "prix": 129.99, "quantite_stock": 50},
    {"nom": "Kingston Fury Beast DDR4 16 Go", "description": "Kit 2x8 Go DDR4-3200 CL16, faible profil", "categorie": "Mémoire RAM", "prix": 44.99, "quantite_stock": 80},
    # Stockage
    {"nom": "Samsung 990 Pro 2 To", "description": "SSD NVMe PCIe 4.0 M.2, 7450 Mo/s lecture, 6900 Mo/s écriture", "categorie": "Stockage", "prix": 179.99, "quantite_stock": 35},
    {"nom": "WD Black SN850X 1 To", "description": "SSD NVMe PCIe 4.0 M.2, 7300 Mo/s lecture, optimisé gaming", "categorie": "Stockage", "prix": 109.99, "quantite_stock": 40},
    {"nom": "Seagate Barracuda 4 To", "description": "Disque dur 3.5 pouces 7200 RPM SATA III, cache 256 Mo", "categorie": "Stockage", "prix": 79.99, "quantite_stock": 25},
    # Cartes mères
    {"nom": "ASUS ROG Maximus Z790 Hero", "description": "Carte mère ATX LGA1700, DDR5, PCIe 5.0, WiFi 6E, 4x M.2", "categorie": "Cartes mères", "prix": 549.99, "quantite_stock": 10},
    {"nom": "MSI MAG B650 Tomahawk", "description": "Carte mère ATX AM5, DDR5, PCIe 5.0, 2.5G LAN, 3x M.2", "categorie": "Cartes mères", "prix": 229.99, "quantite_stock": 18},
    # Alimentation
    {"nom": "Corsair RM1000x 1000W", "description": "Alimentation modulaire 80+ Gold, ventilateur 135mm semi-passif", "categorie": "Alimentation", "prix": 189.99, "quantite_stock": 22},
    {"nom": "be quiet! Straight Power 750W", "description": "Alimentation modulaire 80+ Platinum, ultra silencieuse", "categorie": "Alimentation", "prix": 139.99, "quantite_stock": 28},
    # Refroidissement
    {"nom": "Noctua NH-D15", "description": "Ventirad double tour 140mm, compatible AM5/LGA1700, TDP 250W", "categorie": "Refroidissement", "prix": 99.99, "quantite_stock": 30},
    {"nom": "Corsair iCUE H150i Elite LCD", "description": "Watercooling AIO 360mm, écran LCD intégré, RGB", "categorie": "Refroidissement", "prix": 269.99, "quantite_stock": 14},
    # Périphériques
    {"nom": "Logitech MX Keys S", "description": "Clavier sans fil rétroéclairé, profil bas, multi-appareils Bluetooth", "categorie": "Périphériques", "prix": 119.99, "quantite_stock": 45},
    {"nom": "Razer DeathAdder V3 Pro", "description": "Souris gaming sans fil 63g, capteur Focus Pro 30K DPI", "categorie": "Périphériques", "prix": 149.99, "quantite_stock": 38},
    {"nom": "Samsung Odyssey G7 27\"", "description": "Écran gaming QHD 240Hz 1ms, IPS, G-Sync Compatible, HDR600", "categorie": "Écrans", "prix": 499.99, "quantite_stock": 16},
]


def seed():
    app = create_app()
    with app.app_context():
        existing = Product.query.count()
        if existing > 0:
            print(f"{existing} produit(s) déjà présent(s) en base, seed annulé.")
            return

        for data in PRODUITS:
            db.session.add(Product(**data))

        db.session.commit()
        print(f"{len(PRODUITS)} produits ajoutés.")


if __name__ == '__main__':
    seed()
