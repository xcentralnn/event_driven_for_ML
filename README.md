# Predictive Scheduling for Serverless Cold-Start Optimization

This repository contains the implementation and documentation for optimizing cold-starts in serverless platforms (specifically Knative) using Machine Learning and predictive scheduling.

## Repository Structure

- **`docs/`**: Contains the LaTeX source code for the research report/thesis, including chapters, references, and the compiled `main.pdf`.
- **`src/`**: Contains the source code for the system's microservices and Kubernetes deployment manifests.
  - **`app/ml-service/`**: Python/Flask application serving the Long Short-Term Memory (LSTM) forecasting model.
  - **`app/controller/`**: Python application acting as the Predictive Scaler Controller. It queries the `ml-service` and adjusts Knative scaling policies.
  - **`k8s/`**: Kustomize manifests for deploying the system.
    - **`base/`**: Core deployments, services, and RBAC permissions.
    - **`overlays/`**: Environment-specific overrides (e.g., `dev`, `prod`).

## Deployment Instructions

### Prerequisites
- A running Kubernetes cluster (e.g., Kind, Minikube, or Docker Desktop K8s).
- `kubectl` installed and configured.
- Knative Serving installed on the cluster.

### Build and Deploy

1. **Deploy using Kustomize**:
   The `dev` overlay is configured for fast iteration. It automatically pulls a public Python image and mounts the source code via ConfigMaps, so you don't need to manually build Docker images for local testing.
   ```bash
   kubectl apply -k src/k8s/overlays/dev
   ```

2. **Verify Deployment**:
   Check if the pods are running correctly:
   ```bash
   kubectl get pods
   ```

## Testing the ML Service
Once the pods are running, you can port-forward the ML service to test its forecasting endpoint locally:
```bash
kubectl port-forward svc/dev-ml-forecasting-service 8080:80
```
Then, in a new terminal, send a request:
```bash
curl http://localhost:8080/predict
```
Expected output:
```json
{"predicted_concurrency": 10}
```
