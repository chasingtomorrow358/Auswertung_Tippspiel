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
    # Punkteberechnung für alle Teilnehmer
    for idx, row in df.iterrows():
        hmm = [row["100mM1"], row["100mM2"], row["100mM3"]]
        hmw = [row["100mW1"], row["100mW2"], row["100mW3"]]
        punkte = 0

        # 100m Männer
        for i, val in enumerate(hmm):
            if val == sieger.ohmm[i]:
                punkte += 2
            elif val in sieger.ohmm:
                punkte += 1

        # 100m Frauen
        for i, val in enumerate(hmw):
            if val == sieger.ohmw[i]:
                punkte += 2
            elif val in sieger.ohmw:
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
