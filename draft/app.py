from flask import (Flask, render_template, make_response, url_for, request,
                   redirect, flash, session, send_from_directory)
app = Flask(__name__)

import os
import bcrypt
import secrets
import cs304dbi as dbi
import cs304login as auth

app.secret_key = 'your secret here'
app.secret_key = secrets.token_hex() # replace that with a random key


@app.route('/')
def index():
    return render_template('main.html', page_title='Welcome to Choose Your Own Story')

# I should probably call this "register" instead. Or some other synonym of "join"

@app.route('/join/', methods=["POST"])
def join():
    username = request.form.get('username')
    passwd1 = request.form.get('password1')
    passwd2 = request.form.get('password2')
    if passwd1 != passwd2:
        flash('passwords do not match')
        return redirect( url_for('index'))
    conn = dbi.connect()
    (uid, is_dup, other_err) = auth.insert_user(conn, username, passwd1)
    if other_err:
        raise other_err
    if is_dup:
        flash('Sorry; that username is taken')
        return redirect(url_for('index'))
    ## success
    flash('FYI, you were issued UID {}'.format(uid))
    session['username'] = username
    session['uid'] = uid
    session['logged_in'] = True
    session['visits'] = 1
    return redirect( url_for('user', username=username) )
        
@app.route('/login/', methods=["POST"])
def login():
    username = request.form.get('username')
    passwd = request.form.get('password')
    conn = dbi.connect()
    (ok, uid) = auth.login_user(conn, username, passwd)
    if not ok:
        flash('login incorrect, please try again or join')
        return redirect(url_for('index'))
    ## success
    print('LOGIN', username)
    flash('successfully logged in as '+username)
    session['username'] = username
    session['uid'] = uid
    session['logged_in'] = True
    session['visits'] = 1
    return redirect( url_for('user', username=username) )

@app.route('/greet/', methods=["GET", "POST"])
def greet():
    return render_template('greet.html', page_title='Welcome')

@app.route('/read/', methods=["GET", "POST"])
def read():
    return render_template('read.html', page_title='Story')

@app.route('/firstchapter/', methods=["GET", "POST"])
def firstchapter():
    return render_template('firstchapter.html', page_title='First Chapter')

@app.route('/user/<username>')
def user(username):
    try:
        # don't trust the URL; it's only there for decoration
        if 'username' in session:
            username = session['username']
            uid = session['uid']
            session['visits'] = 1+int(session['visits'])
            return render_template('greet.html',
                                   page_title='Welcome to Choose Your Own Story {}'.format(username),
                                   name=username,
                                   uid=uid,
                                   visits=session['visits'])
        else:
            flash('you are not logged in. Please login or join')
            return redirect( url_for('index') )
    except Exception as err:
        flash('some kind of error '+str(err))
        return redirect( url_for('index') )

@app.route('/logout/')
def logout():
    if 'username' in session:
        username = session['username']
        session.pop('username')
        session.pop('uid')
        session.pop('logged_in')
        flash('You are logged out')
        return redirect(url_for('index'))
    else:
        flash('you are not logged in. Please login or join')
        return redirect( url_for('index') )

if __name__ == '__main__':
    import sys,os
    if len(sys.argv) > 1:
        # arg, if any, is the desired port number
        port = int(sys.argv[1])
        assert(port>1024)
    else:
        port = os.getuid()
    dbi.cache_cnf()             # use my personal database
    conn = dbi.connect()
    curs = dbi.dict_cursor(conn)
    curs.execute('select database() as db')
    row = curs.fetchone()
    print('Connected to {}'.format(row['db']))
    curs.execute('select uid, username, hashed from userpass')
    print('You have the following users already')
    for row in curs.fetchall():
        print('{uid}\t{username}\t{hashed}'
              .format(uid=row['uid'],
                      username=row['username'],
                      hashed=row['hashed']))
    app.debug = True
    app.run('0.0.0.0',port)
