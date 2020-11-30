from flask import Flask, render_template

from server_module import Server

app = Flask(__name__)

server = Server()


@app.route('/', methods=['GET'])
def main_page():
    return render_template('test.html')


@app.route('/login', methods=['POST'])
def login():
    return server.login()


@app.route('/new_account', methods=['GET'])
def new_account():
    return server.main_creating_account_page()


@app.route('/create_account', methods=['POST'])
def create_account():
    return server.create_account()


@app.route('/user/<username>', methods=['GET'])
def user(username):
    return server.user_main(username)


@app.route('/user/<username>/upload_essay', methods=['POST'])
def upload_essay(username):
    return server.upload_essay(username)


@app.route('/search/<username>', methods=['POST'])
def search(username):
    return server.search(username)
