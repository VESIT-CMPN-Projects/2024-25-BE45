from flask import Flask
from flask_cors import CORS

from routes.auth_routes import auth_bp
from routes.chat_routes import chat_bp
from routes.session_routes import session_bp
from routes.query_routes import query_bp
from routes.batch_routes import batch_bp
from routes.home_routes import home_bp
from flask import Flask


app = Flask(__name__)
CORS(app)

app.static_folder = 'static'

app.register_blueprint(auth_bp, url_prefix="/auth")
app.register_blueprint(session_bp, url_prefix="/session")
app.register_blueprint(chat_bp, url_prefix="/chat")
app.register_blueprint(query_bp, url_prefix="/query")
app.register_blueprint(batch_bp, url_prefix="/batch_tool")
app.register_blueprint(home_bp)

if __name__ == '__main__':
    port = 5000
    app.run(port=port, debug=True)
