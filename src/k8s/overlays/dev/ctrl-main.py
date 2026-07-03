import time
import requests
import os
from kubernetes import client, config

def run_controller():
    print("Starting predictive scaler controller...")
    
    # Load Kubernetes config
    try:
        config.load_incluster_config()
        v1 = client.AppsV1Api()
    except Exception as e:
        print(f"Warning: Could not load k8s config: {e}")
        v1 = None

    namespace = "knative-predictive-scaler"
    target_deployment = "dev-target-app" # Kustomize adds dev- prefix

    while True:
        try:
            # Query the ML service for predicted concurrency
            ml_url = os.environ.get("ML_SERVICE_URL", "http://dev-ml-forecasting-service/predict")
            resp = requests.get(ml_url, timeout=5)
            if resp.status_code == 200:
                prediction = resp.json().get("predicted_concurrency", 0)
                print(f"Predicted concurrency: {prediction}. Adjusting Kubernetes target deployment...")
                
                # Scale the target deployment
                if v1:
                    # Get current replicas
                    scale = v1.read_namespaced_deployment_scale(name=target_deployment, namespace=namespace)
                    current_replicas = scale.spec.replicas
                    
                    # We map concurrency directly to replicas for this demo
                    desired_replicas = max(1, prediction) # Keep at least 1 for baseline
                    
                    # Smoothing Algorithm (Limit scaling velocity)
                    if desired_replicas > current_replicas:
                        # Scale Up: Max 2 pods added per cycle to prevent overwhelming the cluster
                        target_replicas = min(current_replicas + 2, desired_replicas)
                    elif desired_replicas < current_replicas:
                        # Scale Down: Max 1 pod removed per cycle to prevent premature scale-down (thrashing)
                        target_replicas = max(current_replicas - 1, desired_replicas)
                    else:
                        target_replicas = current_replicas
                        
                    if target_replicas != current_replicas:
                        body = {'spec': {'replicas': target_replicas}}
                        v1.patch_namespaced_deployment_scale(
                            name=target_deployment,
                            namespace=namespace,
                            body=body
                        )
                        print(f"Scaled {target_deployment} from {current_replicas} to {target_replicas} replicas (Desired: {desired_replicas}).")
                    else:
                        print(f"No scaling needed. Current replicas: {current_replicas}.")
        except Exception as e:
            print(f"Error in controller loop: {e}")
        time.sleep(10)

if __name__ == '__main__':
    run_controller()
