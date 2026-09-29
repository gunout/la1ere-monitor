#!/usr/bin/env python3
"""
Collecteur multi-radios du réseau La 1ère.
Écoute les flux Icecast et stocke les morceaux dans SQLite.
Détection anti-doublons : vérifie en base avant d'insérer.
"""

import urllib.request
import sqlite3
import re
import time
import os
import sys
import signal
import threading
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import RADIOS

DOSSIER = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(DOSSIER, 'la1ere.db')
LOG = os.path.join(DOSSIER, 'collecteur.log')

try:
    from enrichir import enrichir as enrichir_morceaux
except ImportError:
    enrichir_morceaux = None


def init_db():
    conn = sqlite3.connect(DB, check_same_thread=False)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS diffusions (
            uid             INTEGER PRIMARY KEY AUTOINCREMENT,
            radio           TEXT NOT NULL,
            radio_nom       TEXT,
            titre           TEXT NOT NULL,
            artistes        TEXT,
            start_ts        INTEGER NOT NULL,
            end_ts          INTEGER,
            duree           INTEGER,
            date            TEXT,
            heure           INTEGER,
            album           TEXT,
            cover_deezer    TEXT,
            cover_uri       TEXT,
            annee           INTEGER,
            preview_mp3     TEXT,
            deezer_rank     INTEGER,
            explicit_lyrics INTEGER,
            likes           INTEGER DEFAULT 0,
            type            TEXT DEFAULT 'record',
            collecte        INTEGER
        )
    ''')
    c.execute('CREATE INDEX IF NOT EXISTS idx_radio ON diffusions(radio)')
    c.execute('CREATE INDEX IF NOT EXISTS idx_start_ts ON diffusions(start_ts)')
    c.execute('CREATE INDEX IF NOT EXISTS idx_artistes ON diffusions(artistes)')
    c.execute('CREATE INDEX IF NOT EXISTS idx_titre ON diffusions(titre)')
    conn.commit()
    return conn


_log_lock = threading.Lock()


def log(msg):
    h = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    l = f"[{h}] {msg}"
    with _log_lock:
        print(l, flush=True)
        try:
            with open(LOG, 'a', encoding='utf-8') as f:
                f.write(l + '\n')
        except Exception:
            pass


def ecouter_radio(radio, conn, stop_event):
    """Écoute un flux Icecast et stocke les morceaux avec anti-doublons."""
    rid = radio['id']
    nom = radio['nom']
    url = radio['url']

    while not stop_event.is_set():
        try:
            req = urllib.request.Request(url, headers={"Icy-MetaData": "1"})
            response = urllib.request.urlopen(req, timeout=15)
            metaint = int(response.headers.get('icy-metaint', 16000))
            log(f"[{rid}] Connecté (metaint={metaint})")

            dernier_titre_local = None

            while not stop_event.is_set():
                response.read(metaint)
                lb = response.read(1)[0]
                ml = lb * 16
                if ml == 0:
                    continue

                meta = response.read(ml).decode('utf-8', errors='ignore')
                m = re.search(r"StreamTitle='([^']*)';", meta)
                if not m:
                    continue

                st = m.group(1).strip()
                if not st:
                    continue

                # Éviter les répétitions immédiates (même cycle)
                if st == dernier_titre_local:
                    # Mettre à jour end_ts du morceau existant
                    try:
                        c = conn.cursor()
                        now = int(time.time())
                        c.execute('''UPDATE diffusions SET end_ts = ?, duree = ?
                                     WHERE radio = ? AND titre = ?
                                       AND end_ts IS NULL
                                       AND start_ts > ?
                                     ORDER BY start_ts DESC LIMIT 1''',
                                  (now, now - 300, rid, st, now - 600))
                        conn.commit()
                    except sqlite3.Error:
                        pass
                    continue

                # Nouveau titre détecté
                if ' - ' in st:
                    art, tit = [x.strip() for x in st.split(' - ', 1)]
                else:
                    art, tit = None, st

                now = int(time.time())
                dt = datetime.fromtimestamp(now)

                try:
                    c = conn.cursor()

                    # ANTI-DOUBLON : chercher si le même morceau existe déjà
                    # (même radio + même titre + même artiste) récemment
                    row = c.execute("""
                        SELECT uid, start_ts FROM diffusions
                        WHERE radio = ? AND titre = ?
                          AND IFNULL(artistes, '') = IFNULL(?, '')
                        ORDER BY start_ts DESC LIMIT 1
                    """, (rid, tit, art)).fetchone()

                    if row:
                        uid_existant, start_existant = row
                        # Si le morceau a commencé il y a moins de 10 minutes,
                        # on met juste à jour end_ts (pas de nouvel insert)
                        if now - start_existant < 600:
                            c.execute("""UPDATE diffusions
                                         SET end_ts = ?, duree = ?
                                         WHERE uid = ?""",
                                      (now, now - start_existant, uid_existant))
                            conn.commit()
                            dernier_titre_local = st
                            continue

                    # Sinon, on insère un nouveau morceau
                    c.execute('''INSERT INTO diffusions
                        (radio, radio_nom, titre, artistes, start_ts,
                         date, heure, type, collecte)
                        VALUES (?,?,?,?,?,?,?, 'record', ?)''',
                        (rid, nom, tit, art, now,
                         dt.strftime('%Y-%m-%d'), dt.hour, int(time.time())))
                    conn.commit()
                    if c.rowcount > 0:
                        log(f"[{rid}] + {st}")
                        # Enrichir immédiatement ce morceau
                        if enrichir_morceaux:
                            try:
                                enrichir_morceaux(limite=1, verbeux=False)
                            except Exception:
                                pass

                except sqlite3.Error as e:
                    log(f"[{rid}] ! Erreur : {e}")

                dernier_titre_local = st

        except Exception as e:
            log(f"[{rid}] Erreur flux : {e} — reconnexion dans 10s")
            for _ in range(10):
                if stop_event.is_set():
                    break
                time.sleep(1)


arret = False


def gerer_signal(sig, frame):
    global arret
    arret = True
    log("Arrêt demandé...")


signal.signal(signal.SIGINT, gerer_signal)
signal.signal(signal.SIGTERM, gerer_signal)


def boucle():
    conn = init_db()
    log(f"Démarrage — {len(RADIOS)} radios")

    stop_event = threading.Event()
    threads = []
    for r in RADIOS:
        t = threading.Thread(target=ecouter_radio,
                              args=(r, conn, stop_event), daemon=True)
        t.start()
        threads.append(t)
        time.sleep(0.3)

    # Boucle principale
    while not arret:
        time.sleep(30)
        if enrichir_morceaux:
            try:
                enrichir_morceaux(limite=20, verbeux=False)
            except Exception as e:
                log(f"Enrichissement : {e}")

    stop_event.set()
    conn.close()
    log("Arrêt.")


def test():
    """Mode test : écoute rapide de chaque radio."""
    log(f"Mode test — {len(RADIOS)} radios")
    for r in RADIOS:
        log(f"Test {r['nom']}...")
        try:
            req = urllib.request.Request(r['url'],
                                          headers={"Icy-MetaData": "1"})
            response = urllib.request.urlopen(req, timeout=10)
            metaint = int(response.headers.get('icy-metaint', 16000))
            trouve = False
            for _ in range(60):
                response.read(metaint)
                lb = response.read(1)[0]
                ml = lb * 16
                if ml > 0:
                    meta = response.read(ml).decode('utf-8', errors='ignore')
                    m = re.search(r"StreamTitle='([^']*)';", meta)
                    if m and m.group(1).strip():
                        log(f"  ✓ {m.group(1)}")
                        trouve = True
                        break
            if not trouve:
                log(f"  ⚠ Aucune métadonnée")
        except Exception as e:
            log(f"  ❌ {e}")


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'test':
        test()
    else:
        boucle()
