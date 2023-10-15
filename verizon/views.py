import os
from flask import Blueprint, redirect, render_template, request
from tempfile import mkdtemp

views = Blueprint(__name__,"views")


@views.route("/")
def home():
    
        return render_template("homepage.html")
    

@views.route("/iphone15")
def ha():
    
    return render_template("iphone15.html")



