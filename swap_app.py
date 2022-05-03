import json
from flask import Flask, render_template, request, redirect, session, url_for, flash
import QueryUtil
from app_config import app, mysql



@app.route('/')
def entry():
    return redirect('/search-form')



@app.route("/search-form", methods=['GET', 'POST'])
def searchForm():
    return render_template('search_form.html')


@app.route("/search-results", methods=['GET', 'POST'])
def searchResults():
    if request.method == 'POST':
        # Fetch data from forms
        search_input = request.form

    print(search_input)

    return render_template('search_results.html')


if __name__ == "__main__":
    # app.run(debug=True, use_reloader=False)
    app.config['SECRET_KEY'] = 'something only you know'  # My part will show error without this
    app.run(debug=True)
