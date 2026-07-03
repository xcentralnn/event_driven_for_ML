# Predictive Scheduling for Serverless Cold-Start Optimization

This repository contains the implementation and documentation for optimizing cold-starts in serverless platforms (specifically Knative) using Machine Learning and predictive scheduling. 

By proactively scaling Kubernetes Deployments based on Time-Series Forecasting (LSTM), we can significantly reduce the latency overhead caused by "Scale-to-Zero" cold starts, while still maintaining high resource efficiency.

## Key Features

- **ML Forecasting Service:** A Flask-based mock LSTM service that simulates traffic forecasting. It includes an advanced 3-phase spike simulation (Ramp Up -> Hold Peak -> Ramp Down) to realistically emulate flash-sale scenarios.
- **Predictive Scaler Controller:** A custom Kubernetes Python controller that polls the ML Service and preemptively scales the target deployment. Features a built-in **Smoothing Algorithm (Stabilization Window)** that caps scale-up/scale-down velocity to prevent thrashing and cluster exhaustion (Max 10 Pods, +/- 2 Pods per cycle).
- **Executive Dashboard:** A premium, real-time Streamlit dashboard showcasing the system's performance.
  - **Single Window View:** KPIs, Trajectory, and Pod Topology side-by-side with zero scrolling required.
  - **ML Model Insights Tab:** Connects real-time prediction data to a mathematically simulated confidence-interval forecast graph.
  - **Premium AWS-style UI:** Styled with deep slate gradient animations and a sleek dark mode.

## Repository Structure

- **`docs/`**: Contains the LaTeX source code for the research report/thesis, including chapters, references, and the compiled `main.pdf`.
- **`src/`**: Contains the source code for the system's microservices and Kubernetes deployment manifests.
  - **`app/ml-service/`**: Python/Flask application serving the Long Short-Term Memory (LSTM) forecasting model.
  - **`app/controller/`**: Python application acting as the Predictive Scaler Controller.
  - **`app/dashboard/`**: Streamlit application providing real-time data visualization.
  - **`app/target-app/`**: A mock Node.js target application representing a user workload.
  - **`k8s/`**: Kustomize manifests for deploying the system.
    - **`base/`**: Core deployments, services, and RBAC permissions.
    - **`overlays/`**: Environment-specific overrides (e.g., `dev`).

## Deployment Instructions

### Prerequisites
- A running Kubernetes cluster (e.g., Kind, Minikube, or Docker Desktop K8s).
- `kubectl` installed and configured.

### Build and Deploy (Dev Environment)

The `dev` overlay is configured for fast iteration. It automatically pulls a public Python image and mounts the source code (`src/app/*`) via ConfigMaps. No manual Docker builds are required for local testing!

```bash
# Apply the Kustomize manifest
kubectl apply -k src/k8s/overlays/dev

# Verify all components are running
kubectl get pods -n knative-predictive-scaler
```

## How to use the Dashboard

Once all pods are running, port-forward the Streamlit dashboard to your local machine:

```bash
kubectl port-forward -n knative-predictive-scaler svc/dev-dashboard-service 8501:8501
```

Open `http://localhost:8501` in your browser. 
From the dashboard, you can click **"Trigger Traffic Spike"** to simulate an incoming DDoS or flash-sale event. You will instantly see the ML Service's prediction graph ramp up, the Controller proactively scaling the Pods smoothly, and the Topology table dynamically populating with new Nodes!
