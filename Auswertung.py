import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import sieger  # Datei mit den richtigen Ergebnissen

# -------------------------------
# Google Sheets Setup
# -------------------------------
creds_dict = st.secrets["gspread"]
scope = ["https://spreadsheets.google.com/feeds",
         "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(creds)
sheet = client.open_by_key(st.secrets["gspread"]["sheet_id"]).sheet1

st.title("🏆 VFV Spandau Tippspiel - Leaderboard / Auswertung")

# -------------------------------
# Daten aus Google Sheet laden (Cache)
# -------------------------------
@st.cache_data(ttl=60)
def load_sheet_data():
    data = sheet.get_all_records()
    return pd.DataFrame(data)

df = load_sheet_data()

if df.empty or "Name" not in df.columns:
    st.write("Noch keine Tipps vorhanden.")
else:
    # Liste aller Disziplinen: (Spaltenprefix, Siegerliste aus sieger.py)
    disziplinen = [
        ("100mM", sieger.ohmm),
        ("m200", sieger.m200),
        ("m1500", sieger.m1500),
        ("Speer", sieger.speer),
        ("Zehnkampf", sieger.zehn),
        ("100mW", sieger.ohmw),
        ("h100W", sieger.h100w),
        ("h400W", sieger.h400w),
        ("Weitsprung", sieger.weitsprung),
        ("Hochsprung", sieger.hoch),
        ("Staffel100mM", sieger.staffel100m),
        ("Staffel100mW", sieger.staffel100w),
        ("Staffel400mM", sieger.staffel400m),
        ("Staffel400mW", sieger.staffel400w),
    ]

# -------------------------------
# Hilfsfunktion zum Vergleich von Namen
# -------------------------------
def normalize_name(name):
    """Normalisiert Namen für robusteren Vergleich"""
    if not isinstance(name, str):
        return ""
    return (
        name.strip()
        .lower()
        .replace("-", "")
        .replace(" ", "")
    )

# -------------------------------
# Punkteberechnung für alle Teilnehmer
# -------------------------------
updates = []  # Liste für Batch-Update
for idx, row in df.iterrows():
    punkte = 0

    for prefix, richtige_reihenfolge in disziplinen:
        tipps = [
            row.get(f"{prefix}1", ""),
            row.get(f"{prefix}2", ""),
            row.get(f"{prefix}3", "")
        ]

        for i, val in enumerate(tipps):
            if normalize_name(val) == normalize_name(richtige_reihenfolge[i]):
                punkte += 3   # exakte Position
            elif normalize_name(val) in [normalize_name(x) for x in richtige_reihenfolge]:
                punkte += 1   # in Top 3, aber falsche Position

    df.at[idx, "Punkte"] = punkte
    updates.append(punkte)

# -------------------------------
# Batch-Update der Punkte-Spalte
# -------------------------------
col_idx = df.columns.get_loc("Punkte") + 1
cell_list = sheet.range(2, col_idx, len(df) + 1, col_idx)
for cell, punkte in zip(cell_list, updates):
    cell.value = punkte
sheet.update_cells(cell_list)

# -------------------------------
# Leaderboard anzeigen
# -------------------------------
leaderboard = df[["Name", "Punkte"]].sort_values(by="Punkte", ascending=False)
st.subheader("🏅 Leaderboard")
st.dataframe(leaderboard)

