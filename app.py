from flask import Flask, request, redirect, render_template, session
from spotify_requests import spotify
import musictaste
import os
import spotipy
from helpers import apology
import base64
from werkzeug.exceptions import HTTPException


app = Flask(__name__)
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
app.config['TEMPLATES_AUTO_RELOAD'] = True

app.secret_key = os.urandom(24)

# ----------------------- AUTH API PROCEDURE -------------------------
@app.route("/auth")
def auth():
    return redirect(spotify.AUTH_URL)


@app.route("/callback/")
def callback():

    auth_token = request.args['code']
    auth_header = spotify.authorize(auth_token)
    session['auth_header'] = auth_header

    return visualize()

def valid_token(resp):
    return resp is not None and not 'error' in resp

# prevent cached responses
@app.after_request
def add_header(response):
    response.headers['Pragma'] = 'no-cache'
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Expires'] = '0'
    return response

@app.errorhandler(HTTPException)
def handle_exception(e):
    return apology("error", 404)

# -------------------------- API REQUESTS ----------------------------
@app.route("/")
def home():
    return render_template('home.html')

@app.route('/visualize')
def visualize():
    if 'auth_header' in session:
        auth_header = session['auth_header']
        sp = spotipy.Spotify(auth=auth_header)

        # get user's recently played tracks and collect the artist(s)'s data
        results = sp.current_user_recently_played(limit=50, after=None, before=None)
        list = []
        list.append(results)
        session['recently_played_json'] = list

        # get user's top short-term artists
        results = sp.current_user_top_artists(limit=50,offset=0,time_range='short_term')
        list = []
        list.append(results)
        session['short_artists_json'] = list

        # get user's top medium-term artists
        results = sp.current_user_top_artists(limit=50,offset=0,time_range='medium_term')
        list = []
        list.append(results)
        session['med_artists_json'] = list

        # get user's top long-term artists
        results = sp.current_user_top_artists(limit=50,offset=0,time_range='long_term')
        list = []
        list.append(results)
        session['long_artists_json'] = list

        # test token
        recently_played = spotify.get_users_recently_played(auth_header)
        
        # if the token is valid, continue to next step: plotting data
        if valid_token(recently_played):
            try:
                # create buffer with image of music map
                buffer = musictaste.main(sp, session['recently_played_json'], session['short_artists_json'], session['med_artists_json'], session['long_artists_json'])
                buffer.seek(0)
                # encode buffer
                image_memory = base64.b64encode(buffer.getvalue())
                # render index.html and pass decoded buffer
                return render_template("index.html", img_data=image_memory.decode('utf-8'))
            except BaseException:
                return apology("error", 403)

    return render_template('visualize.html')

if __name__ == "__main__":
    app.run()
