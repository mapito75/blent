Ce que j'ai fait
1. Le fichier de tests test_auth.py
J'ai écrit 14 tests unitaires pour les deux routes de auth.py :

POST /api/auth/register
POST /api/auth/login
2. La structure générale (inspirée de ton exemple)
Comme dans ton exemple avec test_data, j'utilise un fixture pytest :


@pytest.fixture
def client():
    app = create_app(...)
    with app.app_context():
        yield app.test_client()
Le client est l'équivalent de test_data — c'est une ressource partagée injectée automatiquement dans chaque test qui en a besoin.

3. Pourquoi des mocks ?
Sans mocks, chaque test écrirait/lirait dans une vraie base de données. C'est lent, fragile, et les tests deviennent dépendants les uns des autres.

Avec unittest.mock.patch, on remplace temporairement les appels DB par des faux objets contrôlés :


with patch('blueprints.auth.db.session') as mock_session:
    mock_session.execute.return_value = _db_result(None)  # "pas d'utilisateur en base"
    r = client.post('/api/auth/register', json={...})
La route tourne normalement, mais au lieu de vraiment interroger SQLite, elle reçoit ce qu'on lui a préparé.

4. Les trois problèmes rencontrés (et leurs solutions)
Problème 1 — date_creation est None après un commit mocké

→ SQLAlchemy n'assigne jamais la valeur par défaut puisqu'il n'y a pas de vrai flush. user.to_dict() plante sur .isoformat().

→ Solution : patcher User.to_dict avec une version qui tolère None.

Problème 2 — db.select(User) valide que User est un vrai modèle SQLAlchemy

→ Si on patchait User avec un MagicMock, SQLAlchemy rejetait l'appel.

→ Solution : patcher aussi db.select pour court-circuiter cette validation.

Problème 3 — Comment vérifier que l'email est bien mis en minuscules ou que le rôle invalide est corrigé, sans inspecter la DB ?

→ Solution : inspecter l'objet User passé à session.add() via mock_session.add.call_args.args[0]. C'est l'objet que la route aurait persisté — on vérifie ses attributs directement.

14/14 passent. Voici ce qui a été fait :

test_auth.py déplacé vers unit_tests/test_auth.py
unit_tests/__init__.py créé (fichier vide) pour que Python reconnaisse le dossier comme un package et que les imports fonctionnent correctement
Pour lancer les tests :


cd v2
python -m pytest unit_tests/ -v