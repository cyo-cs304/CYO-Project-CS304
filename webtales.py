# <!-- webtales.py for WebTales/CYO Adventure CS304 Project -->

# WebTales/Choose your own Adventure python helper functions
# Maria Cabrera, Annelle Abatoni, Ryan Rowe

from flask import (Flask, render_template, make_response, request,
                   redirect, flash, url_for, session)
app = Flask(__name__)
import cs304dbi as dbi
import pymysql
import bcrypt
from datetime import date

def getStories(conn, author_username=None):
    """
    Connects to the database and gets information
    on all the stories available
    """
    curs = dbi.dict_cursor(conn)
    if author_username == None:
        curs.execute ('''select story_id, story_title, author_username, 
        genre, synopsis from story''')
    else:
        curs.execute('''select story_id, story_title, author_username,
        genre, synopsis from story
        where author_username = %s''', [author_username])    
    return curs.fetchall()

def getOneStory(conn, storyID):
    """
    Connects to the database and gets information
    on a Story given its ID
    """
    curs = dbi.dict_cursor(conn)
    curs.execute('''select story_id, story_title, author_username,
    genre, synopsis from story
    where story_id = %s ''', [storyID])
    return curs.fetchall()[0] #curs.fetchall() returns the dictionary inside a list, so we choose the 0 position: the dictionary

def addStory(conn, story_title, author_username, genre, synopsis):
    """Adds stories to database 
    given information from the write.html template
    """
    curs = dbi.cursor(conn)
    curs.execute('''insert into story(story_title, author_username, genre, synopsis) 
    values(%s,%s,%s,%s)''', [story_title, author_username, genre, synopsis])
    conn.commit()
    curs.execute('''select last_insert_id()''')
    last_insert_story_id = curs.fetchone()[0]
    return getOneStory(conn, last_insert_story_id) # addStory returns information from the story just added
    
def getChapters(conn, storyID):
    """
    Connects to the database and gets information
    on the chapters of a Story given the storyID
    """
    curs = dbi.dict_cursor(conn)
    curs.execute('''select chapter_id, story_id, chapter_title from chapter
    where story_id = %s''', [storyID])
    return curs.fetchall()

def getChapter(conn, chapterID):
    """
    Connects to the database and gets information
    on a specific chapter given its ID
    """
    curs = dbi.dict_cursor(conn)
    curs.execute('''select chapter_id, story_id, chapter_title from chapter
    where chapter_id = %s''', [chapterID])
    return curs.fetchall()

def getChapterContent(conn, chapterID):
    """
    Connects to the database to get the name of .txt file
    and extracts its text content
    """
    curs = dbi.cursor(conn)
    curs.execute(''' select chapter_content from chapter where chapter_id = %s''', [chapterID])
    filepath = curs.fetchone()[0]
    with open('/students/cyo/beta/story_texts/'+filepath) as f:
        contents = f.readlines()[0]
    return contents

def updateProgress(conn, chapterID, author_username):
    """
    Connects to the database to update a user's progress
    in a specific story
    """
    curs = dbi.cursor(conn)
    storyID = getChapter(conn, chapterID)[0]['story_id']
    curs.execute(''' INSERT INTO follow (username, story_id, saved_progress)
    VALUES (%s, %s, %s) ON DUPLICATE KEY UPDATE
    saved_progress = %s''', [author_username, storyID, chapterID, chapterID])
    conn.commit()

def getProgressByStory(conn, author_username):
    """
    Connects to the database to get the current user's 
    progress and story information from all stories they started playing,
    grouped by each storyID
    """
    curs = dbi.dict_cursor(conn)
    curs.execute('''select follow.story_id, chapter_title, author_username, synopsis, genre, saved_progress from story
    INNER JOIN follow on story.story_id = follow.story_id
    INNER JOIN chapter on chapter.chapter_id = follow.saved_progress
    where username = %s''', [author_username])
    return curs.fetchall()
    
def addChapter(conn, storyID, chapter_title):
    """Adds new chapter to database 
    given information from the newchapter.html template
    """
    curs = dbi.cursor(conn)
    if storyID == 0:
        curs.execute('''select last_insert_id()''')
        storyID = curs.fetchone()
    curs.execute('''insert into chapter(story_id, chapter_title) 
    values(%s,%s)''', [storyID, chapter_title])
    conn.commit()

    curs.execute('''select last_insert_id()''')
    last_insert_chapter_id = curs.fetchone()
    return last_insert_chapter_id # Getting the chapter_id of the newly inserted chapter

def contentFile(conn, chapterInfo, chapterText):
    """Gets the chapter content typed by user and dumps it in a .txt file located in
     in /students/cyo/beta/story_texts
    Then, it connects to the database to insert the .txt file name to the chapter table
    """
    currentDate = date.today()
    chapterTitle = chapterInfo['chapter_title'].replace(' ','_') # Gets the current chapter's title and replaces spaces by _
    chapterFileName = chapterTitle + "_" + str(currentDate)
    filePath = "/students/cyo/beta/story_texts/"
    with open(filePath+chapterFileName, 'w') as f:
        f.writelines(chapterText)
    # Now, we insert the name of .txt file in the chapter table
    chapterID = chapterInfo['chapter_id']
    curs = dbi.cursor(conn)
    curs.execute('''update chapter 
    set chapter_content = %s
    where chapter_id = %s''', [chapterFileName, chapterID])
    conn.commit()

def getChoices(conn, chapterID):
    """
    Connects to the database to get a dictionary
    of choices relative to a chapter
    """
    curs = dbi.dict_cursor(conn)
    curs.execute(''' select * from choice where host_chapter = %s''', [chapterID])
    choices = curs.fetchall()
    return choices
    
def getChoice(conn, choiceID):
    """
    Connects to the database and gets information
    on a specific choice given its ID
    """
    curs = dbi.dict_cursor(conn)
    curs.execute('''select choice_id, host_chapter, description_text from choice
    where choice_id = %s''', [choiceID])
    return curs.fetchall()

def addChoice(conn, chapterID, choice_title, chapter_redirect=0):
    """Adds new choice to database 
    given information from the newchoice.html template
    """
    curs = dbi.cursor(conn)
    curs.execute('''insert into choice(host_chapter, description_text, chapter_redirect) 
    values(%s,%s,%s)''', [chapterID, choice_title, chapter_redirect])
    conn.commit()

    curs.execute('''select last_insert_id()''')
    last_insert_choice_id = curs.fetchone()
    return last_insert_choice_id 

if __name__ == '__main__':
    conn = dbi.connect()
    delete_user(conn, 'fred')
    delete_user(conn, 'george')

    for username in ['fred', 'george', 'fred']:
        print(username, insert_user(conn, username, 'secret'))
        print(username, login_user(conn, username, 'secret'))
        
