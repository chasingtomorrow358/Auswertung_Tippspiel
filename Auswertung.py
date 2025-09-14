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
        ("200mM", sieger.m200),
        ("1500mM", sieger.m1500),
        ("Speer", sieger.speer),
        ("Zehnkampf", sieger.zehn),
        ("100mW", sieger.ohmw),
        ("100mHürdenW", sieger.h100w),
        ("400mHürdenW", sieger.h400w),
        ("Weitsprung", sieger.weitsprung),
        ("Hochsprung", sieger.hoch),
        ("Staffel100mM", sieger.staffel100m),
        ("Staffel100mW", sieger.staffel100w),
        ("Staffel400mM", sieger.staffel400m),
        ("Staffel400mW", sieger.staffel400w),
    ]

    # Punkteberechnung für alle Teilnehmer
    updates = []  # Liste für Batch-Update
    for idx, row in df.iterrows():
        punkte = 0

        for prefix, richtige_reihenfolge in disziplinen:
            tipps = [row.get(f"{prefix}1", ""), row.get(f"{prefix}2", ""), row.get(f"{prefix}3", "")]
            for i, val in enumerate(tipps):
                if val == richtige_reihenfolge[i]:
                    punkte += 3
                elif val in richtige_reihenfolge:
                    punkte += 1

        df.at[idx, "Punkte"] = punkte
        updates.append(punkte)

    # Batch-Update der Punkte-Spalte
    col_idx = df.columns.get_loc("Punkte") + 1
    cell_list = sheet.range(2, col_idx, len(df) + 1, col_idx)
    for cell, punkte in zip(cell_list, updates):
        cell.value = punkte
    sheet.update_cells(cell_list)

    # Leaderboard anzeigen
    leaderboard = df[["Name", "Punkte"]].sort_values(by="Punkte", ascending=False)
    st.subheader("🏅 Leaderboard")
    st.dataframe(leaderboard)
