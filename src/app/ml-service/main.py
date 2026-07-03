from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/predict', methods=['GET'])
def predict():
    # Placeholder for LSTM inference
    return jsonify({"predicted_concurrency": 10})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
