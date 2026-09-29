#!/usr/bin/env python3
import sqlite3, json, os
from datetime import datetime

DOSSIER = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(DOSSIER, 'la1ere.db')
SORTIE = os.path.join(DOSSIER, 'data.json')

conn = sqlite3.connect(DB)
conn.row_factory = sqlite3.Row
c = conn.cursor()
L = lambda rows: [dict(r) for r in rows]


def extraire_pour_radio(rid=None):
    params = ()
    where = ""
    if rid and rid != '__all__':
        where = "WHERE radio = ?"
        params = (rid,)

    wa = where + (" AND " if where else "WHERE ") + "artistes IS NOT NULL AND artistes != ''"
    wh = where + (" AND " if where else "WHERE ") + "heure IS NOT NULL"
    wd = where + (" AND " if where else "WHERE ") + "date IS NOT NULL"

    d = {}
    d['volume'] = dict(c.execute(
        "SELECT COUNT(*) AS nb_diffusions, COUNT(DISTINCT radio) AS nb_radios, "
        "COUNT(DISTINCT artistes) AS nb_artistes, COUNT(DISTINCT titre) AS nb_titres, "
        "ROUND(SUM(duree)/3600.0, 2) AS heures, ROUND(AVG(duree), 1) AS duree_moy "
        "FROM diffusions " + wa, params).fetchone() or {})

    d['top_artistes'] = L(c.execute(
        "SELECT artistes, COUNT(*) AS nb_diffusions, ROUND(SUM(duree)/60.0, 1) AS minutes "
        "FROM diffusions " + wa + " GROUP BY artistes ORDER BY minutes DESC LIMIT 20",
        params).fetchall())

    d['top_titres'] = L(c.execute(
        "SELECT artistes, titre, COUNT(*) AS nb_diffusions, ROUND(SUM(duree)/60.0, 1) AS minutes "
        "FROM diffusions " + wa + " GROUP BY artistes, titre ORDER BY nb_diffusions DESC LIMIT 20",
        params).fetchall())

    d['heures'] = L(c.execute(
        "SELECT heure, COUNT(*) AS nb FROM diffusions " + wh + " GROUP BY heure ORDER BY heure",
        params).fetchall())

    d['jours'] = L(c.execute(
        "SELECT date, COUNT(*) AS nb FROM diffusions " + wd + " GROUP BY date ORDER BY date",
        params).fetchall())

    d['semaine'] = L(c.execute(
        "SELECT CASE CAST(strftime('%w', date) AS INTEGER) "
        "WHEN 0 THEN 'Dimanche' WHEN 1 THEN 'Lundi' WHEN 2 THEN 'Mardi' "
        "WHEN 3 THEN 'Mercredi' WHEN 4 THEN 'Jeudi' WHEN 5 THEN 'Vendredi' "
        "WHEN 6 THEN 'Samedi' END AS jour, COUNT(*) AS nb "
        "FROM diffusions " + wd + " GROUP BY strftime('%w', date) "
        "ORDER BY CAST(strftime('%w', date) AS INTEGER)", params).fetchall())

    d['recurrents'] = L(c.execute(
        "SELECT artistes, COUNT(DISTINCT date) AS nb_jours, COUNT(*) AS nb_diffusions "
        "FROM diffusions " + wa + " GROUP BY artistes HAVING nb_jours >= 2 "
        "ORDER BY nb_jours DESC LIMIT 20", params).fetchall())

    d['titres_recurrents'] = L(c.execute(
        "SELECT artistes, titre, COUNT(DISTINCT date) AS nb_jours, COUNT(*) AS nb_diffusions "
        "FROM diffusions " + wa + " GROUP BY artistes, titre HAVING nb_jours >= 2 "
        "ORDER BY nb_jours DESC LIMIT 20", params).fetchall())

    d['diversifies'] = L(c.execute(
        "SELECT artistes, COUNT(DISTINCT titre) AS nb_titres, COUNT(*) AS nb "
        "FROM diffusions " + wa + " GROUP BY artistes HAVING nb_titres >= 2 "
        "ORDER BY nb_titres DESC LIMIT 20", params).fetchall())

    d['annees'] = L(c.execute(
        "SELECT annee, COUNT(*) AS nb_diffusions FROM diffusions " + where +
        (" AND " if where else "WHERE ") + "annee IS NOT NULL GROUP BY annee ORDER BY annee DESC",
        params).fetchall())

    d['explicit'] = L(c.execute(
        "SELECT CASE explicit_lyrics WHEN 1 THEN 'Explicit' WHEN 0 THEN 'Clean' "
        "ELSE 'Inconnu' END AS type_contenu, COUNT(*) AS nb FROM diffusions " +
        where + (" AND " if where else "WHERE ") + "explicit_lyrics IS NOT NULL "
        "GROUP BY explicit_lyrics", params).fetchall())

    d['albums'] = L(c.execute(
        "SELECT album, artistes, COUNT(*) AS nb FROM diffusions " + where +
        (" AND " if where else "WHERE ") + "album IS NOT NULL AND album != '' "
        "GROUP BY album ORDER BY nb DESC LIMIT 20", params).fetchall())

    d['derniers_morceaux'] = L(c.execute(
        "SELECT titre, artistes, cover_deezer, cover_uri, preview_mp3, "
        "date, heure, album, annee, start_ts, end_ts, radio, radio_nom "
        "FROM diffusions " + where + " ORDER BY start_ts DESC LIMIT 10",
        params).fetchall())

    return d


data = {
    'genere_le': datetime.now().isoformat(),
    'genere_ts': int(datetime.now().timestamp()),
}

radios = L(c.execute(
    "SELECT radio, radio_nom, COUNT(*) AS nb_diffusions, "
    "COUNT(DISTINCT artistes) AS nb_artistes, COUNT(DISTINCT titre) AS nb_titres "
    "FROM diffusions GROUP BY radio ORDER BY nb_diffusions DESC").fetchall())
data['par_radio'] = radios
data['global'] = extraire_pour_radio('__all__')
data['par_radio_data'] = {}
for r in radios:
    data['par_radio_data'][r['radio']] = extraire_pour_radio(r['radio'])

data['derniers_par_radio'] = {}
for r in c.execute("SELECT DISTINCT radio FROM diffusions").fetchall():
    rid = r['radio']
    d = c.execute(
        "SELECT titre, artistes, cover_deezer, cover_uri, preview_mp3, "
        "start_ts, end_ts, radio_nom FROM diffusions WHERE radio=? "
        "ORDER BY start_ts DESC LIMIT 1", (rid,)).fetchone()
    if d:
        data['derniers_par_radio'][rid] = dict(d)

conn.close()

with open(SORTIE, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("data.json genere : " + str(len(radios)) + " radios")
print("Global : " + str(data['global']['volume'].get('nb_diffusions', 0)) + " diffusions")
for r in radios:
    print("- " + r['radio_nom'] + " : " + str(r['nb_diffusions']) + " diffusions")
