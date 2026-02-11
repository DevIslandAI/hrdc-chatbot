import os
from flask import Flask, render_template, request, jsonify
from chatbot import HRDCChatbot
from config import config

app = Flask(__name__)
app.secret_key = config.SECRET_KEY

# Initialize chatbot
chatbot = HRDCChatbot()

@app.route('/')
def index():
    """Render the chatbot UI"""
    return render_template('index.html')

@app.route('/ask', methods=['POST'])
def ask():
    """Handle chatbot queries"""
    data = request.json
    query = data.get('query', '')
    
    if not query:
        return jsonify({'error': 'Empty query'}), 400
    
    try:
        # Connect to DB for each request or keep persistent?
        # For simplicity in this demo, we'll connect/disconnect
        chatbot.connect_db()
        result = chatbot.ask(query)
        chatbot.disconnect_db()
        
        return jsonify(result)
    except Exception as e:
        print(f"Error handling query: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({'status': 'healthy'})

if __name__ == '__main__':
    # Ensure templates directory exists
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static', exist_ok=True)
    
    app.run(host='0.0.0.0', port=5002, debug=True)
