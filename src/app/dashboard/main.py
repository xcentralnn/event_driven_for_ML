import streamlit as st
import requests
import time
import pandas as pd

st.set_page_config(page_title="Predictive Scaler Dashboard", layout="wide")
st.title("Knative Predictive Scaler Dashboard")

st.markdown("Monitoring the ML Forecasting Service and Predictive Scaler.")

if 'history' not in st.session_state:
    st.session_state.history = pd.DataFrame(columns=['Time', 'Predicted Concurrency'])

col1, col2 = st.columns(2)

with col1:
    st.subheader("Current Prediction")
    pred_placeholder = st.empty()

with col2:
    st.subheader("System Status")
    status_placeholder = st.empty()

st.subheader("Concurrency Trend")
chart_placeholder = st.empty()

def fetch_prediction():
    try:
        resp = requests.get("http://ml-forecasting-service/predict")
        if resp.status_code == 200:
            return resp.json().get("predicted_concurrency", 0)
    except Exception as e:
        return None
    return None

while True:
    pred = fetch_prediction()
    current_time = pd.Timestamp.now().strftime('%H:%M:%S')
    
    if pred is not None:
        pred_placeholder.metric(label="Predicted Concurrency", value=pred)
        status_placeholder.success("ML Service is Online")
        
        new_row = pd.DataFrame({'Time': [current_time], 'Predicted Concurrency': [pred]})
        st.session_state.history = pd.concat([st.session_state.history, new_row]).tail(50)
        
    else:
        pred_placeholder.metric(label="Predicted Concurrency", value="N/A")
        status_placeholder.error("ML Service is Offline")
    
    if not st.session_state.history.empty:
        chart_placeholder.line_chart(st.session_state.history.set_index('Time'))
        
    time.sleep(2)
