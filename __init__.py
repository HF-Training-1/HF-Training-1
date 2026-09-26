import os
from pathlib import Path
from flask import Flask, abort, jsonify, request
from werkzeug.exceptions import HTTPException
from werkzeug.security import generate_password_hash
from .db import init_db
from .auth import install_auth
from . import auth, admin, portfolio, learning

def create_app(test_config=None):
    root=Path(__file__).resolve().parent.parent
    data=Path(os.environ.get('HF_DATA_DIR',str(root/'instance'))).resolve()
    app=Flask(__name__,static_folder=str(root/'static'),static_url_path='/static')
    app.config.update(DATABASE=str(data/'hf.sqlite3'),UPLOADS=str(data/'uploads'),
        MAX_CONTENT_LENGTH=11*1024*1024,SECURE_COOKIES=os.environ.get('HF_LOCAL_HTTP')!='1',
        DUMMY_HASH=generate_password_hash('not-a-real-account-password',method='scrypt'))
    if test_config:
        app.config.update(test_config)
    Path(app.config['DATABASE']).parent.mkdir(parents=True,exist_ok=True)
    Path(app.config['UPLOADS']).mkdir(parents=True,exist_ok=True)
    init_db(app)
    install_auth(app)
    for module in (auth,admin,portfolio,learning):
        app.register_blueprint(module.bp)

    @app.before_request
    def require_object():
        if request.path.startswith('/api/') and request.method=='POST' and not request.path.endswith('/files'):
            if not request.is_json or not isinstance(request.get_json(silent=True),dict):
                abort(400,'Send a JSON object.')

    @app.get('/')
    def index():
        return app.send_static_file('index.html')

    @app.get('/api/health')
    def health():
        return jsonify(ok=True)

    @app.errorhandler(HTTPException)
    def http_error(error):
        return jsonify(error=error.description),error.code

    @app.after_request
    def headers(response):
        response.headers['X-Content-Type-Options']='nosniff'
        response.headers['X-Frame-Options']='DENY'
        response.headers['Referrer-Policy']='no-referrer'
        response.headers['Content-Security-Policy']="default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self'; connect-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'; object-src 'none'"
        response.headers['Cache-Control']='no-store'
        if app.config['SECURE_COOKIES']:
            response.headers['Strict-Transport-Security']='max-age=31536000'
        return response
    return app
