from flask import Flask, jsonify, request
import math
import time
import random

app = Flask(__name__)

# Global state to track spike
spike_start = 0

@app.route('/predict', methods=['GET'])
def predict():
    current_time = time.time()
    elapsed = current_time - spike_start
    
    if elapsed < 20:
        # Phase 1: Ramp Up (0 to 20s) -> from 1 to 10 pods
        predicted_load = int(1 + (elapsed / 20.0) * 9)
    elif elapsed < 40:
        # Phase 2: Peak / Delay (20 to 40s) -> Hold at 10 pods
        predicted_load = 10
    elif elapsed < 60:
        # Phase 3: Ramp Down (40 to 60s) -> from 10 to 1 pod
        ramp_down_elapsed = elapsed - 40
        predicted_load = int(10 - (ramp_down_elapsed / 20.0) * 9)
    else:
        # Normal baseline is 1 pod
        predicted_load = 1
        
    # Cap at 10 max
    predicted_load = max(1, min(10, predicted_load))
        
    return jsonify({
        'predicted_concurrency': predicted_load,
        'model_used': 'LSTM (Long Short-Term Memory)',
        'model_version': 'v1.0.0-simulated',
        'timestamp': current_time
    })

@app.route('/trigger-spike', methods=['POST'])
def trigger_spike():
    global spike_start
    # Start the 60s spike event
    spike_start = time.time()
    return jsonify({'status': 'Spike triggered', 'duration': 60})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
