"""
data_loader.py
--------------
Loads flights_clean.csv, filters to LAX departures on 7 Nov 2025
between 05:00 and 12:00 with emissions available.
Finds the busiest 15-minute window (14 departures).
Picks the first 6 flights from that window as DECISION flights.
The remaining 8 are kept as fixed background.
"""

import pandas as pd
import json
import os

CSV_PATH = os.path.join(os.path.dirname(__file__), "..", "flights_clean.csv")
BASELINE_JSON = os.path.join(os.path.dirname(__file__), "..", "results", "baseline_piece.json")


def load_lax_nov7(csv_path: str = CSV_PATH) -> pd.DataFrame:
    """Return full filtered dataframe: LAX origin, Nov 7 2025, 05:00-12:00, emissions available."""
    df = pd.read_csv(csv_path, low_memory=False)

    # Filter: LAX origin
    df = df[df["ORIGIN_AIRPORT"] == "LAX"].copy()

    # Parse actual departure
    df["ACTUAL_DEP_DT"] = pd.to_datetime(df["ACTUAL_DEP_LOCAL"], errors="coerce")

    # Filter: Nov 7 2025
    df = df[df["ACTUAL_DEP_DT"].dt.date == pd.Timestamp("2025-11-07").date()].copy()

    # Filter: 05:00 - 12:00
    start = pd.Timestamp("2025-11-07 05:00")
    end   = pd.Timestamp("2025-11-07 12:00")
    df = df[(df["ACTUAL_DEP_DT"] >= start) & (df["ACTUAL_DEP_DT"] < end)].copy()

    # Filter: emissions available
    df = df[df["EMISSIONS_AVAILABLE"] == True].copy()

    df = df.sort_values("ACTUAL_DEP_DT").reset_index(drop=True)
    print(f"[data_loader] LAX Nov-7 05:00-12:00 with emissions: {len(df)} flights")
    return df


def find_busiest_window(df: pd.DataFrame, window_minutes: int = 15):
    """
    Slide a 15-minute window over sorted departure times.
    Return (window_start, window_flights_df).
    """
    best_start = None
    best_count = 0

    for i, t in enumerate(df["ACTUAL_DEP_DT"]):
        window_end = t + pd.Timedelta(minutes=window_minutes)
        mask = (df["ACTUAL_DEP_DT"] >= t) & (df["ACTUAL_DEP_DT"] < window_end)
        count = mask.sum()
        if count > best_count:
            best_count = count
            best_start = t

    window_end = best_start + pd.Timedelta(minutes=window_minutes)
    window_df = df[(df["ACTUAL_DEP_DT"] >= best_start) & (df["ACTUAL_DEP_DT"] < window_end)].copy()

    print(f"[data_loader] Busiest window: {best_start} -> {window_end}  ({len(window_df)} flights)")
    return best_start, window_df


def select_decision_flights(window_df: pd.DataFrame, n_decision: int = 6):
    """
    Pick first n_decision flights from the busiest window as decision flights.
    The rest are fixed background within that window.
    Returns (decision_df, background_window_df).
    """
    decision_df = window_df.iloc[:n_decision].copy().reset_index(drop=True)
    background_df = window_df.iloc[n_decision:].copy().reset_index(drop=True)
    print(f"[data_loader] Decision flights: {len(decision_df)}  |  Background window flights: {len(background_df)}")
    return decision_df, background_df


def write_baseline(decision_df: pd.DataFrame, window_df: pd.DataFrame, out_path: str = BASELINE_JSON):
    """Write baseline_piece.json with before CO2 and busiest-window departure count."""
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    before_co2_kg = float(decision_df["CO2_LTO_KG"].sum())
    busiest_window_departures = len(window_df)

    baseline = {
        "before_co2_kg": round(before_co2_kg, 4),
        "busiest_window_departures": busiest_window_departures,
        "decision_flight_ids": decision_df["FLIGHT_ID"].tolist(),
    }
    with open(out_path, "w") as f:
        json.dump(baseline, f, indent=2)

    print(f"\n[baseline] Before CO2 (6 flights): {before_co2_kg:.2f} kg")
    print(f"[baseline] Busiest window departures: {busiest_window_departures}")
    print(f"[baseline] Written to: {out_path}\n")
    return baseline


if __name__ == "__main__":
    df = load_lax_nov7()
    _, window_df = find_busiest_window(df)
    decision_df, bg_df = select_decision_flights(window_df)
    write_baseline(decision_df, window_df)
    print(decision_df[["FLIGHT_ID", "FLIGHT_NUMBER", "CARRIER", "ACTUAL_DEP_DT", "CO2_LTO_KG", "FUEL_LTO_KG"]].to_string())
