from watch.fetch import diff, find_list_file, key_of


def test_diff_detects_add_remove_change():
    old = {"1": {"siren": "1", "statut": "candidate"}, "2": {"siren": "2", "statut": "agréée"}}
    new = {"1": {"siren": "1", "statut": "agréée"}, "3": {"siren": "3", "statut": "agréée"}}
    out = "\n".join(diff(old, new))
    assert "Ajout" in out and "Retrait" in out and "candidate → agréée" in out


def test_find_list_file_prefers_spreadsheet():
    html = ('<a href="/sites/a.pdf">Liste des plateformes agréées (PDF)</a>'
            '<a href="/sites/liste_pa.xlsx">Liste des plateformes agréées</a>')
    assert find_list_file("https://x.fr/p", html) == "https://x.fr/sites/liste_pa.xlsx"


def test_key_uses_siren_column():
    assert key_of({"Nom": "A", "SIREN": "123 456 789"}) == "123456789"
