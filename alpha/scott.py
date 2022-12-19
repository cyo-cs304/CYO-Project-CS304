# App draft for WebTales/CYO Adventure CS304 Project

from flask import (Flask, render_template, make_response, url_for, request,
                   redirect, flash, session, send_from_directory)
app = Flask(__name__)

import os
import bcrypt
import secrets
import cs304dbi as dbi
import cs304login as auth
import webtales

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
    session['uid'] = uid
    session['username'] = username
    session['logged_in'] = True
    session['visits'] = 1
    return redirect( url_for('user', username=username) )

@app.route('/user/<username>')
def user(username):
    try:
        # don't trust the URL; it's only there for decoration
        if 'username' in session:
            username = session['username']
            uid = session['uid']
            session['visits'] = 1+int(session['visits'])
            return render_template('greet.html',
                                   page_title='Welcome {}, to Choose Your Own Story'.format(username),
                                   name=username,
                                   uid=uid,
                                   visits=session['visits'])
        else:
            flash('you are not logged in. Please login or join')
            return redirect( url_for('index') )
    except Exception as err:
        flash('some kind of error '+str(err))
        return redirect( url_for('index') )
        
@app.route('/greet/', methods=["GET", "POST"])
def greet():
    return render_template('greet.html', page_title='Welcome')

@app.route('/read/', methods=["GET", "POST"])
def read():
    conn = dbi.connect()
    getAllStories = webtales.getStories(conn)
    return render_template('read.html', page_title='Our Stories', stories=getAllStories)

@app.route('/loadstory/<storyID>', methods=["GET","POST"])
def loadstory(storyID):
    conn = dbi.connect()
    getStory = webtales.getOneStory(conn, storyID)
    getChapters = webtales.getChapters(conn, storyID)
    print(getChapters)
    return render_template('story.html', page_title=getStory['story_title'], story=getStory, chapters=getChapters)

@app.route('/loadchapter/<chapterID>', methods=["GET", "POST"])
def loadchapter(chapterID):
    conn = dbi.connect()
    chapterInformation = webtales.getChapter(conn,chapterID)
    print(chapterInformation)
    print("len of chapter info:" + str(len(chapterInformation)))
    # If a choice led to a chapter not written yet, run this:
    if len(chapterInformation)==0:
        flash('You are all caught up with this story. There are no more chapters available as for now!')
        print(chapterID)
        hostStoryID = webtales.getStoryID(conn, chapterID)[0] # gets the story_id from the host story
        print(hostStoryID)
        return redirect(url_for('loadstory', storyID=hostStoryID))

    # else, continue rendering the existing chapter:
    chapterInformation = chapterInformation[0] # curs.fetchall() in webtales.py returned the dictionary inside a tuple
    hostStoryID = chapterInformation['story_id']
    hostStoryInfo = webtales.getOneStory(conn,hostStoryID)
    chapterContent = webtales.getChapterContent(conn, chapterID)
    choicesContent = webtales.getChoices(conn, chapterID)
    return render_template('chapter.html', page_title=chapterInformation['chapter_title'], chapter=chapterInformation, story=hostStoryInfo, text= chapterContent, choices = choicesContent)

@app.route('/write_options/', methods=["GET", "POST"])
def write_options():
    return render_template('write_options.html', page_title='Welcome')

@app.route('/write/', methods=["GET", "POST"])
def write():
    if request.method == 'GET':
        return render_template('write.html', title = 'Write Story')
    else:
        conn = dbi.connect()
        story_title = request.form['story_title']
        genre = request.form['genre']
        synopsis = request.form['synopsis']
        author_username = session.get('username')

        # check if all info is filled out:
        flag = False # initializing a flag as False
        if story_title == '':
            flash('missing input: Title is missing')
            flag = True
        if synopsis == '':
            flash('missing input: Synopsis is missing')
            flag = True
        if genre == '':
            flash('missing input: Genre is missing')
            flag = True
        if flag: # If any of the fields above are missing, rendering the template once will flash all relevant messages
            return render_template('write.html', title = 'Write Story')
        
        submit = request.form['submit']
        if submit == "New Chapter":
            # Adding story to database, which returns the newly added story
            newStory = webtales.addStory(conn, story_title, author_username, genre, synopsis)
            flash('Your story "{}" was saved successfully!'.format(story_title))
            return render_template('newchapterWithID.html', title = 'New Chapter', newStory = newStory)
        else:
            return redirect(url_for('write'))

@app.route('/newchapter/', methods=["GET", "POST"])
def newchapter(storyID=None):
    conn = dbi.connect()
    if request.method == 'GET':
        author_username = session.get('username')
        allStories = webtales.getStories(conn, author_username=author_username) # getting all stories authored by user in the session
        return render_template('newchapter.html', title = 'New Chapter', stories = allStories)
    else:
        if storyID == None:
            storyID = request.form["storyID"] # using the storyID from the newStory dropdown
        chapter_title = request.form['chapter_title']
        chapter_content = request.form['chapter_content']

        # check if all info is filled out
        flag = False
        if chapter_title == '':
            flash('missing input: Title is missing')
            flag = True
        if chapter_content  == '':
            flash('missing input: Story text is missing')
            flag = True
        if flag:
            return render_template('newchapter.html', title = 'New Chapter')
        
       # Adding story to database, which returns the chapter_id of the newly added chapter
        newChapter = webtales.addChapter(conn, storyID, chapter_title)
        chapterInfo = webtales.getChapter(conn, newChapter)[0]
        addingContent = webtales.contentFile(conn, chapterInfo, chapter_content)
        flash('New chapter "{}" was saved successfully!'.format(chapter_title))
        newStory = webtales.getOneStory(conn, storyID) # getting that Story's information
        return render_template('newchapterWithID.html', title = 'New Chapter', newStory = newStory)

@app.route('/choices/')
def choices():
    # for this, we need to learn how to update the page with the choices someone does without them submitting a form
    # for example, they are gonna choose first the story they want to work on,
    # and that choice should bring up all chapters from the story they selected (but they did not pressed a button!!)
    # and then they can click to somehow preview a text from that chapter or something so they know what is each chapter about
    pass

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
    app.run('0.0.0.0',port=8080)
