from flask import Flask, jsonify, request

# Initialize Flask app
app = Flask(__name__)

# Home route
@app.route('/')
def home():
    return jsonify({"message": "Welcome to the Flask Boilerplate!"})

# Example GET route
@app.route('/hello', methods=['GET'])
def hello():
    return jsonify({"message": "Hello, World!"})

# Example POST route
@app.route('/echo', methods=['POST'])
def echo():
    data = request.json
    return jsonify({"you_sent": data})

# Run the app
if __name__ == '__main__':
    app.run(debug=True)