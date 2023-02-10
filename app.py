# <!-- app.py for WebTales/CYO Adventure CS304 Project -->

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
    return render_template('main.html', page_title='Welcome to WebTales')

# I should probably call this "register" instead. Or some other synonym of "join"

@app.route('/join/', methods=["POST"])
def join():
    """Adds the user's username and password to the userpass table based on their input in the form."""
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
    """Logs the user in based on their input in the form. This route checks if the input is already in the userpass table."""
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

@app.route('/user/<username>')
def user(username):
    """A route that gets the current username from the userpass table and displays it on the webpage"""
    try:
        # don't trust the URL; it's only there for decoration
        username = session['username']
        if 'username' in session:
            username = session['username']
            uid = session['uid']
            session['visits'] = 1+int(session['visits'])
            return render_template('greet.html',
                                   page_title='Welcome {}, to WebTales'.format(username),
                                   name=username,
                                   uid=uid,
                                   visits=session['visits'])
        # else:
        #     flash('you are not logged in. Please login or join')
        #     return redirect( url_for('index') )
    except Exception as err:
        flash('some kind of error '+str(err))
        return redirect( url_for('index') )  

@app.route('/read/', methods=["GET", "POST"])
def read():
    if session.get('logged_in'):
        conn = dbi.connect()
        getAllStories = webtales.getStories(conn)
        user = session.get('username')
        progressByStory = webtales.getProgressByStory(conn, user)
        return render_template('read.html', page_title='Our Stories', stories=getAllStories, progressByStory=progressByStory)
    else:
        flash('Please log in')
        return redirect(url_for('index'))

@app.route('/loadstory/<storyID>', methods=["GET","POST"])
def loadstory(storyID):
    if session.get('logged_in'):
        conn = dbi.connect()
        getStory = webtales.getOneStory(conn, storyID)
        getChapters = webtales.getChapters(conn, storyID)
        return render_template('story.html', page_title=getStory['story_title'], story=getStory, chapters=getChapters)
    else:
        flash('Please log in')
        return redirect(url_for('index'))

@app.route('/loadchapter/<chapterID>', methods=["GET", "POST"])
def loadchapter(chapterID):
    conn = dbi.connect()
    user = session.get('username')
    if session.get('logged_in'):
        chapterInformation = webtales.getChapter(conn,chapterID)
        # If a choice led to a chapter not written yet, run this:
        if len(chapterInformation)==0:
            flash('You are all caught up with this story. There are no more chapters available as for now!')
            # hostStoryID = chapterInformation['story_id'] # gets the story_id from the host story
            return redirect(url_for('read'))

        # else, continue rendering the existing chapter:
        webtales.updateProgress(conn, chapterID, user) # updates this user's progress in this story
        chapterInformation = chapterInformation[0] # curs.fetchall() in webtales.py returned the dictionary inside a tuple
        hostStoryID = chapterInformation['story_id']
        hostStoryInfo = webtales.getOneStory(conn,hostStoryID)
        chapterContent = webtales.getChapterContent(conn, chapterID)
        choicesContent = webtales.getChoices(conn, chapterID)
        return render_template('chapter.html', page_title=chapterInformation['chapter_title'], chapter=chapterInformation, story=hostStoryInfo, text= chapterContent, choices = choicesContent)
    else:
        flash('Please log in')
        return redirect(url_for('index'))

@app.route('/write_options/', methods=["GET", "POST"])
def write_options():
    if session.get('logged_in'):
        return render_template('write_options.html', page_title='Choose what to write')
    else:
        flash('Please log in')
        return redirect(url_for('index'))

@app.route('/write/', methods=["GET", "POST"])
def write():
    if session.get('logged_in'):
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
            if submit == "Create Story":
                # Adding story to database, which returns the story_id of the newly added story
                newStory = webtales.addStory(conn, story_title, author_username, genre, synopsis)
                flash('Your story "{}" was saved successfully!'.format(story_title))
                return render_template('newchapterWithID.html', newStory = newStory)
            else:
                return redirect(url_for('write'))
    else:
        flash('Please log in')
        return redirect(url_for('index'))

@app.route('/newchapter/', methods=["GET", "POST"])
def newchapter():
    if session.get('logged_in'):
        conn = dbi.connect()
        author_username = session.get('username')
        allStories = webtales.getStories(conn, author_username= author_username)

        if request.method == 'GET':
            return render_template('newchapter.html', title = 'New Chapter', stories = allStories)
        else:
            storyID = request.form['storyID']
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
            if storyID == '':
                flash('missing input: Please select a story')
                flag = True
            if flag:
                return render_template('newchapter.html', title = 'New Chapter', stories = allStories)
            
        # Adding story to database, which returns the choice_id of the newly added choice
            newChapter = webtales.addChapter(conn, storyID, chapter_title)
            chapterInfo = webtales.getChapter(conn, newChapter)[0]
            addingContent = webtales.contentFile(conn, chapterInfo, chapter_content)
            flash('New chapter "{}" was saved successfully!'.format(chapter_title))
            return render_template('newchapter.html', title = 'New Chapter', stories = allStories)
    else:
        flash('Please log in')
        return redirect(url_for('index'))
        
@app.route('/newchapter/<storyID>', methods=["POST"])
def newchapterWithID(storyID):
    """
    Renders a template to add a new chapter
    to a just added story (does not use
    a dropdown menu to select a story)
    """
    if session.get('logged_in'):
        conn = dbi.connect()
        author_username = session.get('username')
        allStories = webtales.getStories(conn, author_username= author_username)
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
        if storyID == '':
            flash('missing input: Please select a story')
            flag = True
        if flag:
            return render_template('newchapter.html', title = 'New Chapter', stories = allStories)
        
        # Adding story to database, which returns the choice_id of the newly added choice
        newChapter = webtales.addChapter(conn, storyID, chapter_title)
        chapterInfo = webtales.getChapter(conn, newChapter)[0]
        addingContent = webtales.contentFile(conn, chapterInfo, chapter_content)
        flash('New chapter "{}" was saved successfully!'.format(chapter_title))
        story = webtales.getOneStory(conn,storyID)
        return render_template('newchapterWithID.html', title = 'New Chapter', newStory = story)
    else:
        flash('Please log in')
        return redirect(url_for('index'))

@app.route('/newchoiceStory/', methods=["GET","POST"])
def newchoiceStory():
    """
    This function enables users to choose which story of their
    authorship they want to add choices to
    """
    conn = dbi.connect()
    author_username = session.get('username')
    allStories = webtales.getStories(conn, author_username= author_username)
    if session.get('logged_in'):
        if request.method == 'GET':
            return render_template('newchoice.html', title = 'New Chapter', stories = allStories)
        else: # If method is POST:
            storyID = request.form['storyID']
            if request.form["submit"] == "Choose this story":
                return redirect(url_for('newchoice', storyID=storyID))
            else:
                flash('Please select a story')
                return render_template('newchoice.html', title = 'New Chapter', stories = allStories)

    else:
        flash('Please log in')
        return redirect(url_for('index'))

@app.route('/newchoice/<storyID>', methods=["GET","POST"])
def newchoice(storyID):
    """
    This function allows users to connect 
    two chapters through a choice
    """
    if session.get('logged_in'):
        conn = dbi.connect()
        author_username = session.get('username')
        allStories = webtales.getStories(conn, author_username= author_username)

        if request.method == 'GET':
            allChapters= webtales.getChapters(conn, storyID)
            return render_template('newchoicechapter.html', title = 'New Chapter', chapters=allChapters)
        else: # If method is POST:
            choice_title = request.form['choice_title']
            hostChapterID = request.form['hostChapterID']
            redirectChapterID = request.form['redirectChapterID']

            # check if all info is filled out
            flag = False
            if choice_title == '':
                flash('missing input: Choice description is missing')
                flag = True
            if hostChapterID == '':
                flash('missing input: Please select a chapter that will host your choice')
                flag = True
            if redirectChapterID == '':
                flash('missing input: Please select a chapter your choice will lead to')
                flag = True
            if flag:
                return render_template('newchoiceStory.html', title = 'Select a story', stories=allStories)
            
        # Adding choice to database, which returns the chapter_id of the newly added chapter
            newchoice = webtales.addChoice(conn, hostChapterID, choice_title, redirectChapterID)
            # choiceInfo = webtales.getChoice(conn, newchoice)[0]
            flash('New choice "{}" was saved successfully!'.format(choice_title))
            return redirect(url_for('newchoiceStory'))
    else:
        flash('Please log in')
        return redirect(url_for('index'))

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