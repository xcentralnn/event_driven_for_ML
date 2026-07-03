import os

def write_file(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content.strip() + "\n")

write_file('src/k8s/base/namespace.yaml', """
apiVersion: v1
kind: Namespace
metadata:
  name: knative-predictive-scaler
""")

write_file('src/k8s/base/kustomization.yaml', """
namespace: knative-predictive-scaler

resources:
- namespace.yaml
- ml-service
- controller
- dashboard
""")

write_file('src/k8s/base/controller/rbac.yaml', """
apiVersion: v1
kind: ServiceAccount
metadata:
  name: predictive-scaler-sa
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: predictive-scaler-role
rules:
- apiGroups: ["serving.knative.dev"]
  resources: ["services", "revisions"]
  verbs: ["get", "list", "watch", "update", "patch"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: predictive-scaler-binding
subjects:
- kind: ServiceAccount
  name: predictive-scaler-sa
  namespace: knative-predictive-scaler
roleRef:
  kind: ClusterRole
  name: predictive-scaler-role
  apiGroup: rbac.authorization.k8s.io
""")

write_file('src/app/dashboard/main.py', """
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
""")

write_file('src/app/dashboard/requirements.txt', """
streamlit==1.28.2
requests==2.31.0
pandas==2.1.3
""")

write_file('src/app/dashboard/Dockerfile', """
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8501
CMD ["streamlit", "run", "main.py", "--server.port=8501", "--server.address=0.0.0.0"]
""")

write_file('src/k8s/base/dashboard/deployment.yaml', """
apiVersion: apps/v1
kind: Deployment
metadata:
  name: dashboard-service
spec:
  replicas: 1
  selector:
    matchLabels:
      app: dashboard
  template:
    metadata:
      labels:
        app: dashboard
    spec:
      containers:
      - name: dashboard
        image: dashboard-service:latest
        ports:
        - containerPort: 8501
""")

write_file('src/k8s/base/dashboard/service.yaml', """
apiVersion: v1
kind: Service
metadata:
  name: dashboard-service
spec:
  selector:
    app: dashboard
  ports:
  - port: 8501
    targetPort: 8501
""")

write_file('src/k8s/base/dashboard/kustomization.yaml', """
resources:
- deployment.yaml
- service.yaml
""")
