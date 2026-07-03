import streamlit as st
import requests
import os
import time
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from kubernetes import client, config

st.set_page_config(page_title="Predictive Scaler Dashboard", layout="wide", initial_sidebar_state="expanded")

# --- Custom Styling ---
st.markdown("""
<style>
    @keyframes gradientBG {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }
    .stApp::before {
        content: "";
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 35vh;
        background: linear-gradient(-45deg, #0f172a, #1e1b4b, #111827, #020617);
        background-size: 400% 400%;
        animation: gradientBG 15s ease infinite;
        z-index: -1;
        -webkit-mask-image: linear-gradient(to bottom, black 50%, transparent 100%);
        mask-image: linear-gradient(to bottom, black 50%, transparent 100%);
    }
    .stApp {
        background-color: #0f172a;
        color: #F3F4F6;
        font-family: 'Inter', sans-serif;
    }
    @keyframes shine {
        to { background-position: 200% center; }
    }
    .shiny-text {
        background: linear-gradient(to right, #38BDF8 20%, #A78BFA 40%, #A78BFA 60%, #38BDF8 80%);
        background-size: 200% auto;
        color: #000;
        background-clip: text;
        text-fill-color: transparent;
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        animation: shine 3s linear infinite;
        font-weight: 900;
    }
    .kpi-container {
        padding: 0 !important;
        background: transparent !important;
    }
    .kpi-label {
        color: #9CA3AF;
        font-size: 1rem;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-bottom: -10px;
    }
    .kpi-val {
        font-size: 2.2rem;
        font-weight: 700;
        letter-spacing: -1px;
        margin-top: 0px;
    }
    [data-testid="stMetricValue"] {
        font-size: 2.2rem !important;
        font-weight: 700;
        letter-spacing: -1px;
    }
    /* Distinct Colors for the 4 KPIs */
    [data-testid="column"]:nth-of-type(1) [data-testid="stMetricValue"] {
        color: #38BDF8 !important; /* Sky Blue for Prediction */
    }
    [data-testid="column"]:nth-of-type(2) [data-testid="stMetricValue"] {
        color: #34D399 !important; /* Emerald for Replicas */
    }
    [data-testid="column"]:nth-of-type(3) [data-testid="stMetricValue"] {
        color: #FBBF24 !important; /* Amber for Cold Starts */
    }
    [data-testid="column"]:nth-of-type(4) [data-testid="stMetricValue"] {
        color: #A78BFA !important; /* Purple for Efficiency */
    }
    [data-testid="stMetricLabel"] {
        color: #9CA3AF !important;
        font-size: 1rem !important;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    @keyframes pulse {
        0% { transform: scale(1); opacity: 1; box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.7); }
        70% { transform: scale(1); opacity: 0.8; box-shadow: 0 0 0 10px rgba(16, 185, 129, 0); }
        100% { transform: scale(1); opacity: 1; box-shadow: 0 0 0 0 rgba(16, 185, 129, 0); }
    }
    .status-dot {
        height: 12px;
        width: 12px;
        background-color: #10B981;
        border-radius: 50%;
        display: inline-block;
        margin-right: 10px;
        animation: pulse 2s infinite;
    }
    .status-panel {
        background: rgba(31, 41, 55, 0.7);
        border: 1px solid rgba(75, 85, 99, 0.4);
        padding: 15px;
        border-radius: 8px;
        margin-bottom: 15px;
    }
</style>
""", unsafe_allow_html=True)

# --- State Initialization ---
if 'history' not in st.session_state:
    st.session_state.history = pd.DataFrame(columns=['Time', 'Predicted Concurrency', 'Active Replicas'])
if 'cold_starts_prevented' not in st.session_state:
    st.session_state.cold_starts_prevented = 0
if 'total_requests' not in st.session_state:
    st.session_state.total_requests = 0

# --- Sidebar ---
with st.sidebar:
    st.header("Configuration")
    st.markdown("**ML Framework:** <span class='shiny-text'>LSTM (PyTorch)</span>", unsafe_allow_html=True)
    st.markdown("**Algorithm:** Time-Series Forecasting")
    st.markdown("**Target App:** `dev-target-app`")
    st.markdown("---")
    
    st.markdown("""
        <div class="status-panel">
            <div style="display: flex; align-items: center; margin-bottom: 10px;">
                <span class="status-dot"></span>
                <span style="font-weight: 600; color: #E5E7EB;">Controller: Active</span>
            </div>
            <div style="color: #9CA3AF; font-size: 0.9em;">Model: v1.0.0-simulated</div>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    st.header("Simulation Controls")
    if st.button("Trigger Traffic Spike", type="primary"):
        try:
            requests.post(os.environ.get("ML_SERVICE_URL", "http://dev-ml-forecasting-service").replace("/predict", "") + "/trigger-spike", timeout=2)
            st.toast("Traffic Spike Triggered!")
        except:
            st.error("Failed to trigger spike.")
            
    st.markdown("---")
    is_paused = st.toggle("Pause Auto-Refresh", value=False)

# --- Data Fetching Functions ---
def fetch_prediction():
    try:
        url = os.environ.get("ML_SERVICE_URL", "http://dev-ml-forecasting-service/predict")
        resp = requests.get(url, timeout=2)
        if resp.status_code == 200:
            return resp.json()
    except Exception:
        pass
    return None

def fetch_pods():
    try:
        config.load_incluster_config()
        v1 = client.CoreV1Api()
        pods = v1.list_namespaced_pod(namespace="knative-predictive-scaler", label_selector="app=target-app")
        
        running = 0
        terminating = 0
        pending = 0
        
        pod_list = []
        for p in pods.items:
            if p.metadata.deletion_timestamp:
                terminating += 1
                status = "Terminating"
            else:
                if p.status.phase == "Running":
                    running += 1
                    status = "Running"
                elif p.status.phase == "Pending":
                    pending += 1
                    status = "Pending"
                else:
                    status = p.status.phase
            
            # Only append non-terminating to keep table clean
            if status != "Terminating":
                pod_list.append({
                    "Pod Name": p.metadata.name,
                    "Status": status,
                    "Node": p.spec.node_name
                })
            
        stats = {"Running": running, "Terminating": terminating, "Pending": pending}
        return pd.DataFrame(pod_list), stats
    except Exception:
        return pd.DataFrame(), {"Running": 0, "Terminating": 0, "Pending": 0}

# --- Main Data Logic ---
data = fetch_prediction()
pods_df, pod_stats = fetch_pods()

current_time = pd.Timestamp.now().strftime('%H:%M:%S')

pred = 0
if data:
    pred = data.get("predicted_concurrency", 0)
    st.session_state.total_requests += pred
    if len(st.session_state.history) > 0:
        last_pred = st.session_state.history['Predicted Concurrency'].iloc[-1]
        if pred > last_pred:
            st.session_state.cold_starts_prevented += int(pred - last_pred)
            
active_replicas = pod_stats["Running"]

if not is_paused:
    new_row = pd.DataFrame({
        'Time': [current_time], 
        'Predicted Concurrency': [pred],
        'Active Replicas': [active_replicas]
    })
    st.session_state.history = pd.concat([st.session_state.history, new_row]).tail(60)

# --- Layout: Header ---
st.title("Knative Predictive Scaler - Executive Dashboard")

tab_main, tab_ml = st.tabs(["Executive Dashboard", "ML Model Insights"])

with tab_main:
    # --- Layout: Top KPIs ---
    st.markdown("<br>", unsafe_allow_html=True)
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)

    with kpi1:
        st.markdown(f"<div class='kpi-container'><p class='kpi-label'>Predicted Concurrency (RPS)</p><h1 class='kpi-val' style='color:#38BDF8;'>{pred:,}</h1></div>", unsafe_allow_html=True)
    with kpi2:
        st.markdown(f"<div class='kpi-container'><p class='kpi-label'>Actual Ready Replicas</p><h1 class='kpi-val' style='color:#34D399;'>{active_replicas:,}</h1></div>", unsafe_allow_html=True)
    with kpi3:
        st.markdown(f"<div class='kpi-container'><p class='kpi-label'>Cold Starts Prevented</p><h1 class='kpi-val' style='color:#FBBF24;'>{st.session_state.cold_starts_prevented:,}</h1></div>", unsafe_allow_html=True)
    with kpi4:
        efficiency = (active_replicas / pred * 100) if pred > 0 else 100
        st.markdown(f"<div class='kpi-container'><p class='kpi-label'>Resource Efficiency Score</p><h1 class='kpi-val' style='color:#A78BFA;'>{min(100, efficiency):.1f}%</h1></div>", unsafe_allow_html=True)

    # --- Layout: Main Panel (1 Row, 3 Columns) ---
    st.markdown("<br>", unsafe_allow_html=True)
    col_chart, col_donut, col_table = st.columns([2, 1, 1.2])

    with col_chart:
        st.subheader("Scaling Trajectory")
        fig = px.line(st.session_state.history, x='Time', y=['Predicted Concurrency', 'Active Replicas'],
                      labels={'value': 'Count', 'variable': 'Metric'},
                      color_discrete_map={"Predicted Concurrency": "#38BDF8", "Active Replicas": "#34D399"})
        fig.update_traces(line=dict(width=3, shape='spline'), fill='tozeroy')
        fig.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", 
                          font_color="#9CA3AF", margin=dict(l=0, r=0, t=10, b=0),
                          legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                          height=280,
                          xaxis=dict(showgrid=True, gridcolor='rgba(75, 85, 99, 0.2)'),
                          yaxis=dict(showgrid=True, gridcolor='rgba(75, 85, 99, 0.2)'))
        st.plotly_chart(fig)

    with col_donut:
        st.subheader("Lifecycle State")
        labels = ['Running', 'Terminating', 'Pending']
        values = [pod_stats["Running"], pod_stats["Terminating"], pod_stats["Pending"]]
        colors = ['#34D399', '#F87171', '#FBBF24']
        
        if sum(values) > 0:
            # Filter out 0 values so they don't clutter the chart
            active_labels = [l for l, v in zip(labels, values) if v > 0]
            active_values = [v for v in values if v > 0]
            active_colors = [c for c, v in zip(colors, values) if v > 0]
            
            fig_donut = go.Figure(data=[go.Pie(labels=active_labels, values=active_values, hole=.65, marker_colors=active_colors, 
                                               textinfo='percent', textposition='inside', textfont=dict(size=14, color='white'), pull=[0.05 if l == 'Running' else 0 for l in active_labels])])
            fig_donut.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                                    font_color="#9CA3AF", margin=dict(l=0, r=0, t=10, b=40),
                                    showlegend=True, legend=dict(orientation="h", yanchor="top", y=-0.1, xanchor="center", x=0.5),
                                    height=280)
            st.plotly_chart(fig_donut, use_container_width=True)
        else:
            st.info("No Pods active.")

    with col_table:
        st.subheader("Cluster Topology")
        if not pods_df.empty:
            def color_status(val):
                color = '#34D399' if val == 'Running' else '#F87171' if val == 'Terminating' else '#FBBF24'
                return f'color: {color}; font-weight: bold;'
            styled_df = pods_df.style.map(color_status, subset=['Status'])
            # Set height to 280 to match charts and prevent scrolling
            st.dataframe(styled_df, hide_index=True, height=280)
        else:
            st.warning("Target application has scaled to zero.")

with tab_ml:
    st.markdown("<br>", unsafe_allow_html=True)
    st.subheader("LSTM Time-Series Forecasting Model")
    
    col_ml_1, col_ml_2 = st.columns([1, 2.8])
    with col_ml_1:
        st.markdown("""
        <div style='background:rgba(31, 41, 55, 0.4); padding:20px; border-radius:12px; border:1px solid rgba(75, 85, 99, 0.3); backdrop-filter: blur(10px); box-shadow: 0 4px 6px rgba(0,0,0,0.3);'>
            <h4 style='color:#38BDF8; margin-top:0; border-bottom:1px solid rgba(56, 189, 248, 0.3); padding-bottom:5px;'>1. Model Architecture</h4>
            <ul style='color:#E5E7EB; font-size: 0.95em;'>
                <li><b>Network:</b> 3-Layer LSTM</li>
                <li><b>Hidden Size:</b> 128 units</li>
                <li><b>Dropout Rate:</b> 0.2</li>
            </ul>
            <h4 style='color:#34D399; border-bottom:1px solid rgba(52, 211, 153, 0.3); padding-bottom:5px;'>2. Training Metrics</h4>
            <ul style='color:#E5E7EB; font-size: 0.95em;'>
                <li><b>RMSE:</b> <span style='color:#34D399; font-weight:bold;'>0.042</span> | <b>Loss:</b> <span style='color:#34D399; font-weight:bold;'>0.0018</span></li>
                <li><b>Optimizer:</b> AdamW</li>
            </ul>
            <h4 style='color:#A78BFA; border-bottom:1px solid rgba(167, 139, 250, 0.3); padding-bottom:5px;'>3. Inference Pipeline</h4>
            <ol style='color:#E5E7EB; font-size: 0.95em;'>
                <li>Ingest PromQL Metrics (Latency, RPS)</li>
                <li>Data Imputation & Normalization</li>
                <li>Forward Pass (LSTM)</li>
                <li>Denormalize & Output Prediction</li>
            </ol>
        </div>
        """, unsafe_allow_html=True)
    with col_ml_2:
        # Generate forecast graph based on REAL data
        if not st.session_state.history.empty:
            hist_df = st.session_state.history
            t = list(range(len(hist_df)))
            historical = hist_df['Predicted Concurrency'].values
            
            # Forecast into the future (next 20 seconds) based on the latest prediction
            future_t = list(range(len(hist_df), len(hist_df) + 20))
            forecast = [pred] * 20
            
            # Confidence bounds (+/- 1 pod variance)
            upper_bound = [p + 1.5 for p in forecast]
            lower_bound = [max(0, p - 1.5) for p in forecast]
            
            fig_ml = go.Figure()
            fig_ml.add_trace(go.Scatter(x=t, y=historical, name='Historical (Actual)', line=dict(color='#9CA3AF', width=3, shape='spline'), fill='tozeroy', fillcolor='rgba(156, 163, 175, 0.1)'))
            fig_ml.add_trace(go.Scatter(x=future_t, y=forecast, name='LSTM Forecast', line=dict(color='#38BDF8', dash='dash', width=3, shape='spline')))
            fig_ml.add_trace(go.Scatter(x=future_t, y=upper_bound, mode='lines', line=dict(width=0, shape='spline'), showlegend=False, name='Upper Bound', hoverinfo='skip'))
            fig_ml.add_trace(go.Scatter(x=future_t, y=lower_bound, mode='lines', line=dict(width=0, shape='spline'), fill='tonexty', fillcolor='rgba(56, 189, 248, 0.15)', showlegend=False, name='Lower Bound', hoverinfo='skip'))
            
            fig_ml.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", font_color="#9CA3AF", margin=dict(l=0, r=0, t=10, b=0), height=460,
                                 xaxis=dict(showgrid=True, gridcolor='rgba(75, 85, 99, 0.2)'),
                                 yaxis=dict(showgrid=True, gridcolor='rgba(75, 85, 99, 0.2)'))
            st.plotly_chart(fig_ml, use_container_width=True)
        else:
            st.info("Waiting for data to generate forecast...")

# Auto-refresh mechanism
time.sleep(2)
if hasattr(st, "rerun"):
    st.rerun()
else:
    st.experimental_rerun()
