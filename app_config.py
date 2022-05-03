from flask import Flask, render_template, request, redirect
from flask_mysqldb import MySQL
import logging

app = Flask(__name__)
app.secret_key = 'super secret key'

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


# Required
app.config["MYSQL_HOST"] = "34.86.39.76"
app.config["MYSQL_USER"] = "user"
app.config["MYSQL_PASSWORD"] = "password"
app.config["MYSQL_DB"] = "dev-demo"

mysql = MySQL(app)