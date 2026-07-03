import os

def write_file(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content.strip() + "\n")

write_file('src/k8s/overlays/dev/kustomization.yaml', """
namespace: knative-predictive-scaler
namePrefix: dev-

resources:
- ../../base

patchesStrategicMerge:
- patch.yaml

generatorOptions:
  disableNameSuffixHash: true

configMapGenerator:
- name: ml-code
  files:
  - main.py=ml-main.py
- name: controller-code
  files:
  - main.py=ctrl-main.py
- name: dashboard-code
  files:
  - main.py=dash-main.py
""")

write_file('src/k8s/overlays/dev/patch.yaml', """
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ml-forecasting-service
spec:
  replicas: 1
  template:
    spec:
      containers:
      - name: ml-service
        image: python:3.9-slim
        imagePullPolicy: IfNotPresent
        command: ["/bin/sh", "-c"]
        args: ["pip install Flask && python /app/main.py"]
        volumeMounts:
        - name: app-code
          mountPath: /app
      volumes:
      - name: app-code
        configMap:
          name: dev-ml-code
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: predictive-scaler-controller
spec:
  replicas: 1
  template:
    spec:
      containers:
      - name: controller
        image: python:3.9-slim
        imagePullPolicy: IfNotPresent
        command: ["/bin/sh", "-c"]
        args: ["pip install requests kubernetes && python /app/main.py"]
        volumeMounts:
        - name: app-code
          mountPath: /app
      volumes:
      - name: app-code
        configMap:
          name: dev-controller-code
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: dashboard-service
spec:
  replicas: 1
  template:
    spec:
      containers:
      - name: dashboard
        image: python:3.9-slim
        imagePullPolicy: IfNotPresent
        command: ["/bin/sh", "-c"]
        args: ["pip install streamlit requests pandas && streamlit run /app/main.py --server.port=8501 --server.address=0.0.0.0"]
        volumeMounts:
        - name: app-code
          mountPath: /app
      volumes:
      - name: app-code
        configMap:
          name: dev-dashboard-code
""")
