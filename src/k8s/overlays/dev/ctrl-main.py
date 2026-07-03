import time
import requests

def run_controller():
    print("Starting predictive scaler controller...")
    while True:
        try:
            # Query the ML service for predicted concurrency
            resp = requests.get("http://ml-forecasting-service/predict")
            if resp.status_code == 200:
                prediction = resp.json().get("predicted_concurrency", 0)
                print(f"Predicted concurrency: {prediction}. Adjusting Knative settings...")
                # Placeholder for Kubernetes API calls to update Knative service minScale
        except Exception as e:
            print(f"Error checking prediction: {e}")
        time.sleep(10)

if __name__ == '__main__':
    run_controller()
