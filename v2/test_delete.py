import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), 'instance', 'digimarket.db')

EMAILS_TEST = ['jean@example.com', 'admin@example.com']
NOMS_PRODUITS_TEST = [
    'Clavier mécanique',
    'Souris sans fil',
    'Casque audio',
    'Tapis de souris XL',
    'Hack',
]


def delete_test_data():
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()

    # Récupération des IDs utilisateurs de test
    placeholders = ','.join('?' for _ in EMAILS_TEST)
    cur.execute(f'SELECT id FROM user WHERE email IN ({placeholders})', EMAILS_TEST)
    user_ids = [row[0] for row in cur.fetchall()]

    # Récupération des IDs produits de test
    placeholders = ','.join('?' for _ in NOMS_PRODUITS_TEST)
    cur.execute(f'SELECT id FROM product WHERE nom IN ({placeholders})', NOMS_PRODUITS_TEST)
    product_ids = [row[0] for row in cur.fetchall()]

    # Récupération des IDs commandes de test
    if user_ids:
        placeholders = ','.join('?' for _ in user_ids)
        cur.execute(f'SELECT id FROM "order" WHERE utilisateur_id IN ({placeholders})', user_ids)
        order_ids = [row[0] for row in cur.fetchall()]
    else:
        order_ids = []

    # Suppression dans l'ordre (clés étrangères)

    # 1. Lignes de commande
    if order_ids:
        placeholders = ','.join('?' for _ in order_ids)
        cur.execute(f'DELETE FROM order_item WHERE commande_id IN ({placeholders})', order_ids)
        print(f"  order_item supprimés  : {cur.rowcount}")

    # 2. Commandes
    if order_ids:
        placeholders = ','.join('?' for _ in order_ids)
        cur.execute(f'DELETE FROM "order" WHERE id IN ({placeholders})', order_ids)
        print(f"  order supprimés       : {cur.rowcount}")

    # 3. Produits de test
    if product_ids:
        placeholders = ','.join('?' for _ in product_ids)
        cur.execute(f'DELETE FROM product WHERE id IN ({placeholders})', product_ids)
        print(f"  product supprimés     : {cur.rowcount}")

    # 4. Utilisateurs de test
    if user_ids:
        placeholders = ','.join('?' for _ in user_ids)
        cur.execute(f'DELETE FROM user WHERE id IN ({placeholders})', user_ids)
        print(f"  user supprimés        : {cur.rowcount}")

    con.commit()
    con.close()
    print("\nNettoyage terminé.")


if __name__ == '__main__':
    delete_test_data()
