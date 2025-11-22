# Prototype.py
# AUMVION Prototype — Self-Healing Cyber Defense (demo-friendly)
# Run: streamlit run Prototype.py
# Requirements: streamlit, pandas, numpy, scikit-learn

import streamlit as st
import pandas as pd
import numpy as np
import random
import time
import hashlib
import os
from datetime import datetime
from sklearn.ensemble import IsolationForest

# -------------------------
# Config
# -------------------------
LEDGER_CSV = "prototype_ledger.csv"
MAX_LEDGER_MEM = 300
ANOMALY_CONTAMINATION = 0.04
RANDOM_SEED = 42

random.seed(RANDOM_SEED)
np.random.seed(RANDOM_SEED)

# -------------------------
# Minimal CSS
# -------------------------
st.set_page_config(page_title="Prototype · AUMVION", layout="wide")
st.markdown(
    """
    <style>
    .stApp { background-color: #0c0d12; color: #e0e0e0; font-family: 'Consolas', monospace; }
    .big-title { font-size: 28px; font-weight: 800; color: #00ffea; text-shadow: 0px 0px 8px #00ffea; }
    .metric-box { padding:10px; border-radius:8px; background:#121318; }
    </style>
    """,
    unsafe_allow_html=True,
)

# -------------------------
# Threats & Locations
# -------------------------
THREATS = {
    "SQL Injection": ("Web Attack", "Attacker tried to manipulate a database query."),
    "DDoS": ("Network Attack", "Massive traffic flood to overwhelm the server."),
    "Zero-Day": ("Advanced Attack", "Previously unknown vulnerability exploited."),
    "Phishing": ("Social Engineering", "Deceptive message that tricks users."),
    "Insider Threat": ("Internal Threat", "Malicious or negligent internal actor."),
    "Ransomware": ("Malware", "Files encrypted demanding ransom."),
}

LOCATIONS = {
    "Mumbai": (19.0760, 72.8777),
    "Delhi": (28.7041, 77.1025),
    "Bangalore": (12.9716, 77.5946),
    "Hyderabad": (17.3850, 78.4867),
    "Chennai": (13.0827, 80.2707),
    "Kolkata": (22.5726, 88.3639),
}

# -------------------------
# Helpers
# -------------------------
def now_str():
    return datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

def short_hash(s=None):
    s_in = s if s is not None else now_str()
    return hashlib.sha256(str(s_in).encode()).hexdigest()[:12]

def sha256(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()

def compute_chain_hash(prev_hash: str, ts: str, event: str, data: str) -> str:
    payload = f"{prev_hash}|{ts}|{event}|{data}"
    return sha256(payload)

def load_ledger_file():
    if os.path.exists(LEDGER_CSV):
        try:
            return pd.read_csv(LEDGER_CSV)
        except Exception:
            return pd.DataFrame(columns=["ts","event","data","hash","prev_hash"])
    return pd.DataFrame(columns=["ts","event","data","hash","prev_hash"])

def append_ledger_row(event_name: str, data_obj):
    df_file = load_ledger_file()
    prev_hash = df_file.iloc[-1]["hash"] if len(df_file) > 0 else "0"*64
    ts = now_str()
    data_str = str(data_obj)
    new_hash = compute_chain_hash(prev_hash, ts, event_name, data_str)
    row = {"ts": ts, "event": event_name, "data": data_str, "hash": new_hash, "prev_hash": prev_hash}
    header = not os.path.exists(LEDGER_CSV)
    pd.DataFrame([row]).to_csv(LEDGER_CSV, index=False, mode="w" if header else "a", header=header)
    # update session memory copy
    if "ledger_mem" not in st.session_state:
        st.session_state.ledger_mem = []
    st.session_state.ledger_mem.append(row)
    if len(st.session_state.ledger_mem) > MAX_LEDGER_MEM:
        st.session_state.ledger_mem = st.session_state.ledger_mem[-MAX_LEDGER_MEM:]

def verify_ledger(df: pd.DataFrame):
    prev_hash = "0"*64
    for i, r in df.reset_index(drop=True).iterrows():
        recomputed = compute_chain_hash(prev_hash, r["ts"], r["event"], str(r["data"]))
        if recomputed != r["hash"]:
            return False, i
        prev_hash = r["hash"]
    return True, -1

def ai_defense_text(threat_type, threat_desc):
    if threat_type == "Advanced Attack":
        return "Heuristic diversification + memory rollback deployed; critical patch autopushed."
    if threat_type == "Network Attack":
        return "Traffic shaping + geo-block + clean instance redeploy initiated."
    return f"Playbook executed: {threat_desc.split('.')[0]}. Sandboxed and rollback applied."

# -------------------------
# IsolationForest model
# -------------------------
def init_if_model():
    if "if_model" in st.session_state:
        return
    n_nodes = len(LOCATIONS)
    X = np.random.normal(loc=50, scale=3, size=(350, n_nodes))
    model = IsolationForest(contamination=ANOMALY_CONTAMINATION, random_state=RANDOM_SEED)
    model.fit(X)
    st.session_state.if_model = model
    st.session_state.if_node_names = list(LOCATIONS.keys())

def metrics_vector(intensity=1):
    n = len(LOCATIONS)
    base = np.random.normal(50, 3, size=n)
    # bump 1-2 nodes
    k = min(n, max(1, int(round(intensity))))
    idxs = random.sample(range(n), k=k)
    for i in idxs:
        base[i] += random.uniform(6.0 * intensity, 12.0 * intensity)
    return np.round(base,3)

def is_anomaly(vec):
    model = st.session_state.if_model
    pred = model.predict([vec])[0]
    return pred == -1

# -------------------------
# Session-state initialization
# -------------------------
init_if_model()
if "ledger_mem" not in st.session_state:
    st.session_state.ledger_mem = load_ledger_file().to_dict("records")[-MAX_LEDGER_MEM:]
if "attack_counts" not in st.session_state:
    st.session_state.attack_counts = []
if "attack_level" not in st.session_state:
    st.session_state.attack_level = 0.0
if "status" not in st.session_state:
    st.session_state.status = "Stable"

# -------------------------
# UI Layout
# -------------------------
st.markdown("<div class='big-title'>🛡️ AUMVION · Prototype — Live Demo</div>", unsafe_allow_html=True)
st.markdown("---")
left, right = st.columns([1.4, 2])

with left:
    st.markdown("#### Controls")
    col1, col2 = st.columns(2)
    with col1:
        manual_attack = st.button("🚀 Manual Attack (1 cycle)")
    with col2:
        auto_cycles = st.number_input("Auto cycles", min_value=1, max_value=50, value=6, step=1)
        auto_delay = st.slider("Delay between cycles (s)", min_value=0.2, max_value=3.0, value=1.0, step=0.2)
        start_auto = st.button("▶ Start Auto Run")
    st.markdown("---")
    st.markdown("#### Auto Settings (demo safe)")
    contamination = st.slider("Anomaly sensitivity (contamination)", 0.01, 0.2, float(ANOMALY_CONTAMINATION), 0.01)
    st.markdown("---")
    st.markdown("#### Ledger & Quick actions")
    if st.button("Run 5 Quick Cycles (fast)"):
        run_cycles(5, 0.3, intensity=2)  # helper defined later
    if st.button("Verify ledger integrity"):
        dfv = load_ledger_file()
        if dfv.empty:
            st.warning("Ledger empty.")
        else:
            ok, idx = verify_ledger(dfv)
            if ok:
                st.success("Ledger OK — no tampering detected.")
            else:
                st.error(f"Tamper detected at row {idx}.")
                st.write(dfv.iloc[max(0, idx-2):idx+3])
    if st.button("Export ledger CSV"):
        df_e = load_ledger_file()
        if df_e.empty:
            st.info("Ledger empty.")
        else:
            csv = df_e.to_csv(index=False).encode("utf-8")
            st.download_button("Download prototype_ledger.csv", csv, file_name="prototype_ledger.csv", mime="text/csv")

with right:
    map_placeholder = st.empty()
    chart_placeholder = st.empty()
    status_placeholder = st.empty()
    log_placeholder = st.empty()

st.markdown("---")
st.markdown("### Short Pitch")
st.info("AUMVION autonomously detects anomalies, quarantines affected nodes, rotates keys and redeploys clean instances — all while recording tamper-evident events.")

# -------------------------
# Core functions (placed after UI so buttons render before running heavy logic)
# -------------------------
def spawn_event(intensity=1):
    loc = random.choice(list(LOCATIONS.keys()))
    lat, lon = LOCATIONS[loc]
    threat = random.choice(list(THREATS.keys()))
    ttype, tdesc = THREATS[threat]
    evt = {
        "id": short_hash(now_str() + threat + str(random.random())),
        "time": now_str(),
        "threat": threat,
        "type": ttype,
        "desc": tdesc,
        "location": loc,
        "lat": lat + random.uniform(-0.25, 0.25),
        "lon": lon + random.uniform(-0.25, 0.25),
        "healing_time_s": 0.0,
        "defense": "",
        "hash": ""
    }
    return evt

def heal_event_visual(evt):
    """Visual staged healing (blocking, but short). Returns healed evt."""
    status_placeholder.markdown("**Status:** <span style='color:#fb7185'>UNDER ATTACK</span>", unsafe_allow_html=True)
    # Stage 1 - detect/isolate
    prog = st.progress(0)
    st.write(f"Detected: **{evt['threat']}** at **{evt['location']}**")
    for p in range(0, 35):
        prog.progress(p/100)
        time.sleep(0.02)
    # Stage 2 - defend
    status_placeholder.markdown("**Status:** <span style='color:#f59e0b'>HEALING</span>", unsafe_allow_html=True)
    defense_text = ai_defense_text(evt["type"], evt["desc"])
    st.write(f"Applying defense: *{defense_text}*")
    for p in range(35, 80):
        prog.progress(p/100)
        time.sleep(0.02)
    # Stage 3 - reinforce
    st.write("Reinforcing: key rotation, sandbox, redeploy.")
    for p in range(80, 101):
        prog.progress(p/100)
        time.sleep(0.01)
    prog.empty()
    heal_time = round(random.uniform(0.6, 2.6), 2)
    evt["healing_time_s"] = heal_time
    evt["defense"] = defense_text
    evt["hash"] = short_hash(evt["id"] + evt["time"])
    status_placeholder.markdown("**Status:** <span style='color:#4ade80'>STABLE</span>", unsafe_allow_html=True)
    return evt

# define run_cycles now (used by left controls)
def run_cycles(n_cycles, delay_s, intensity=1):
    # update model contamination if user changed slider
    global ANOMALY_CONTAMINATION
    ANOMALY_CONTAMINATION = contamination  # slider above
    # retrain small model quickly
    X = np.random.normal(loc=50, scale=3, size=(300, len(LOCATIONS)))
    model = IsolationForest(contamination=ANOMALY_CONTAMINATION, random_state=RANDOM_SEED)
    model.fit(X)
    st.session_state.if_model = model

    for i in range(n_cycles):
        # spawn
        evt = spawn_event(intensity=intensity)
        vec = metrics_vector(intensity)
        anomalous = is_anomaly(vec)
        # bump chart level
        st.session_state.attack_level += random.uniform(0.6 * intensity, 1.4 * intensity)
        st.session_state.attack_counts.append({"time": pd.Timestamp.now(), "count": st.session_state.attack_level})
        # update chart
        try:
            df_chart = pd.DataFrame(st.session_state.attack_counts).set_index("time")
            chart_placeholder.line_chart(df_chart)
        except Exception:
            pass
        # update map to this event
        map_placeholder.map(pd.DataFrame({"lat":[evt["lat"]],"lon":[evt["lon"]]}), zoom=6)
        # log
        if anomalous:
            log_placeholder.info(f"[{evt['time']}] Anomaly detected: {evt['threat']} @ {evt['location']}")
            # run visual healing
            healed = heal_event_visual(evt)
            # append to session memory and ledger file
            if "session_healed" not in st.session_state:
                st.session_state.session_healed = []
            st.session_state.session_healed.append(healed)
            append_ledger_row("detected_heal", {"evt": healed, "vec": vec.tolist(), "anomaly": True})
        else:
            log_placeholder.info(f"[{evt['time']}] Event: {evt['threat']} @ {evt['location']} (no anomaly)")
            append_ledger_row("cycle_no_detect", {"evt": evt, "vec": vec.tolist(), "anomaly": False})
        time.sleep(delay_s)
    st.success(f"Completed {n_cycles} cycles.")

# -------------------------
# Button handlers: manual & auto
# -------------------------
if manual_attack:
    run_cycles(1, 0.1, intensity=2)

if start_auto:
    # run selected number of cycles (blocking for demo) — update UI each cycle
    run_cycles(int(auto_cycles), float(auto_delay), intensity=2)

# -------------------------
# Render ledger view & small stats
# -------------------------
# show recent ledger entries from file
df_file = load_ledger_file()
if not df_file.empty:
    # try to parse 'data' field (safe-ish)
    parsed = []
    for r in df_file.tail(30).itertuples():
        try:
            d = eval(r.data) if isinstance(r.data, str) else r.data
            evt = d.get("evt", {})
            parsed.append({
                "Time": r.ts,
                "Threat": evt.get("threat", "") or d.get("evt", {}).get("threat",""),
                "Location": evt.get("location", "") or d.get("evt", {}).get("location",""),
                "Healing Time (s)": evt.get("healing_time_s", ""),
                "Defense": evt.get("defense", ""),
                "Hash": r.hash
            })
        except Exception:
            parsed.append({"Time": r.ts, "Threat": r.event, "Location":"", "Healing Time (s)":"", "Defense":"", "Hash": r.hash})
    st.markdown("### Ledger — recent")
    st.dataframe(pd.DataFrame(parsed), use_container_width=True)
else:
    st.info("Ledger is empty. Trigger cycles to populate ledger entries.")

# small stats
st.sidebar.markdown("### Demo stats")
st.sidebar.write(f"Ledger rows: {len(load_ledger_file())}")
st.sidebar.write(f"Attack chart points: {len(st.session_state.attack_counts)}")
st.sidebar.write(f"Model contamination: {ANOMALY_CONTAMINATION:.3f}")

# EOF
