
from flask import Flask, flash, redirect, render_template, request, session
#from flask_session import Session
from tempfile import mkdtemp
from views import views
#from werkzeug.security import check_password_hash, generate_password_hash


app = Flask(__name__)
app.register_blueprint(views, url_prefix="/")






if __name__ == '__main__':
    app.run(debug=True, port=8000)
    



