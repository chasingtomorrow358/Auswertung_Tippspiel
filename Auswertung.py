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
# Daten aus Google Sheet
# -------------------------------
data = sheet.get_all_records()
df = pd.DataFrame(data)

if df.empty or "Name" not in df.columns:
    st.write("Noch keine Tipps vorhanden.")
else:
    # Liste aller Disziplinen: (Spaltenprefix, Siegerliste aus sieger.py)
    disziplinen = [
        ("100mM", sieger.ohmm),
        ("100mW", sieger.ohmw),
        ("200mM", sieger.m200),
        ("1500mM", sieger.m1500),
        ("HindernisM", sieger.hind),
        ("Diskus", sieger.diskus),
        ("Stab", sieger.stab),
        ("Speer", sieger.speer),
        ("Zehnkampf", sieger.zehn),
        ("100mHürdenW", sieger.h100w),
        ("400mHürdenW", sieger.h400w),
        ("800mW", sieger.f800),
        ("Weitsprung", sieger.weitsprung),
        ("Hochsprung", sieger.hoch),
        ("Kugel", sieger.kugel),
        ("Staffel100mM", sieger.staffel100m),
        ("Staffel100mW", sieger.staffel100w),
        ("Staffel400mM", sieger.staffel400m),
        ("Staffel400mW", sieger.staffel400w),
    ]

    # Punkteberechnung für alle Teilnehmer
    for idx, row in df.iterrows():
        punkte = 0

        for prefix, richtige_reihenfolge in disziplinen:
            tipps = [row.get(f"{prefix}1", ""), row.get(f"{prefix}2", ""), row.get(f"{prefix}3", "")]
            for i, val in enumerate(tipps):
                if val == richtige_reihenfolge[i]:
                    punkte += 2
                elif val in richtige_reihenfolge:
                    punkte += 1

        # Punkte in Sheet aktualisieren
        row_idx = idx + 2
        col_idx = df.columns.get_loc("Punkte") + 1
        sheet.update_cell(row_idx, col_idx, punkte)

    # Leaderboard anzeigen
    df["Punkte"] = pd.to_numeric(df["Punkte"], errors="coerce")
    leaderboard = df[["Name", "Punkte"]].sort_values(by="Punkte", ascending=False)
    st.subheader("🏅 Leaderboard")
    st.dataframe(leaderboard)
