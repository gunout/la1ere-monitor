#!/usr/bin/env python3
import sqlite3, os, pandas as pd
DOSSIER = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(DOSSIER, 'la1ere.db')
RES = os.path.join(DOSSIER, 'resultats')
os.makedirs(RES, exist_ok=True)
if not os.path.exists(DB):
    print(f"❌ Base introuvable"); raise SystemExit(1)
conn = sqlite3.connect(DB)
try:
    total = conn.execute("SELECT COUNT(*) FROM diffusions").fetchone()[0]
except sqlite3.OperationalError:
    print("❌ Table introuvable"); raise SystemExit(1)
print(f"Base : {total} diffusions")

def export(nom, req):
    try:
        df = pd.read_sql_query(req, conn)
    except Exception as e:
        print(f"❌ {nom} : {e}"); return
    df.to_csv(os.path.join(RES, f'{nom}.csv'), index=False, encoding='utf-8-sig')
    print(f"\n=== {nom.upper()} ===")
    print(df.head(8).to_string(index=False))

export('00_volume_global', """SELECT COUNT(*) AS nb_diffusions,
    COUNT(DISTINCT radio) AS nb_radios,
    COUNT(DISTINCT artistes) AS nb_artistes,
    COUNT(DISTINCT titre) AS nb_titres,
    ROUND(SUM(duree)/3600.0, 2) AS heures
    FROM diffusions WHERE artistes IS NOT NULL AND artistes != ''""")

export('01_top_artistes', """SELECT artistes, COUNT(*) AS nb_diffusions,
    ROUND(SUM(duree)/60.0, 1) AS minutes
    FROM diffusions WHERE artistes IS NOT NULL AND artistes != ''
    GROUP BY artistes ORDER BY minutes DESC LIMIT 30""")

export('02_top_titres', """SELECT artistes, titre, COUNT(*) AS nb_diffusions,
    ROUND(SUM(duree)/60.0, 1) AS minutes
    FROM diffusions WHERE artistes IS NOT NULL AND artistes != ''
    GROUP BY artistes, titre ORDER BY nb_diffusions DESC LIMIT 30""")

export('03_repartition_horaire', """SELECT heure, COUNT(*) AS nb
    FROM diffusions WHERE heure IS NOT NULL GROUP BY heure ORDER BY heure""")

export('04_repartition_journaliere', """SELECT date, COUNT(*) AS nb,
    COUNT(DISTINCT titre) AS titres FROM diffusions
    WHERE date IS NOT NULL GROUP BY date ORDER BY date""")

export('06_artistes_recurrents', """SELECT artistes,
    COUNT(DISTINCT date) AS nb_jours, COUNT(*) AS nb_diffusions
    FROM diffusions WHERE artistes IS NOT NULL AND artistes != ''
    GROUP BY artistes HAVING nb_jours >= 2
    ORDER BY nb_jours DESC LIMIT 30""")

export('07_titres_recurrents', """SELECT artistes, titre,
    COUNT(DISTINCT date) AS nb_jours, COUNT(*) AS nb
    FROM diffusions WHERE artistes IS NOT NULL AND artistes != ''
    GROUP BY artistes, titre HAVING nb_jours >= 2
    ORDER BY nb_jours DESC LIMIT 30""")

export('09_jour_semaine', """SELECT CASE CAST(strftime('%w', date) AS INTEGER)
    WHEN 0 THEN 'Dimanche' WHEN 1 THEN 'Lundi' WHEN 2 THEN 'Mardi'
    WHEN 3 THEN 'Mercredi' WHEN 4 THEN 'Jeudi' WHEN 5 THEN 'Vendredi'
    WHEN 6 THEN 'Samedi' END AS jour, COUNT(*) AS nb
    FROM diffusions WHERE date IS NOT NULL
    GROUP BY strftime('%w', date)
    ORDER BY CAST(strftime('%w', date) AS INTEGER)""")

export('10_par_radio', """SELECT radio, radio_nom,
    COUNT(*) AS nb_diffusions, COUNT(DISTINCT artistes) AS nb_artistes,
    COUNT(DISTINCT titre) AS nb_titres
    FROM diffusions GROUP BY radio ORDER BY nb_diffusions DESC""")

export('13_artistes_diversifies', """SELECT artistes,
    COUNT(DISTINCT titre) AS nb_titres, COUNT(*) AS nb
    FROM diffusions WHERE artistes IS NOT NULL AND artistes != ''
    GROUP BY artistes HAVING nb_titres >= 2
    ORDER BY nb_titres DESC LIMIT 30""")

export('17_top_albums', """SELECT album, artistes, COUNT(*) AS nb
    FROM diffusions WHERE album IS NOT NULL AND album != ''
    GROUP BY album ORDER BY nb DESC LIMIT 30""")

export('18_dernier_morceau', """SELECT titre, artistes, cover_deezer,
    preview_mp3, date, heure, album, annee, start_ts, end_ts, radio, radio_nom
    FROM diffusions ORDER BY start_ts DESC LIMIT 1""")

conn.close()
print(f"\n✅ Terminé → {RES}")
