# WebTales/Choose your own Adventure python helper functions
# Maria Cabrera, Annelle Abatoni, Ryan Rowe
from flask import (Flask, render_template, make_response, request,
                   redirect, flash, url_for, session)
app = Flask(__name__)
import cs304dbi as dbi
import pymysql
import bcrypt
from datetime import date

def getStories(conn):
    """
    Connects to the database and gets information
    on all the stories available
    """
    curs = dbi.dict_cursor(conn)
    curs.execute ('''select story_id, story_title, author_username, 
    genre, synopsis, average_rating, content_rating from story''')
    return curs.fetchall()

def getOneStory(conn, storyID):
    """
    Connects to the database and gets information
    on a Story given its ID
    """
    curs = dbi.dict_cursor(conn)
    curs.execute('''select story_id, story_title, author_username,
    genre, synopsis, average_rating, content_rating from story
    where story_id = %s ''', [storyID])
    return curs.fetchall()[0] #curs.fetchall() returns the dictionary inside a list, so we choose the 0 position: the dictionary

def getStoryID(conn, chapterID):
    """
    Connects to the database to get the story_id
    of a story given the chapterID of a chapter not yet written 
    belonging to that story
    """
    curs = dbi.cursor(conn)
    curs.execute('''select host_chapter from choice
    where chapter_redirect = %s''', [chapterID])
    host_chapter_id = curs.fetchall()[0] # the last written chapter
    curs.execute('''select story_id from chapter
    where chapter_id = %s''', [host_chapter_id])
    return curs.fetchall()[0]

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
    with open('/students/cyo/draft/story_texts/'+filepath) as f:
        contents = f.readlines()[0]
    return contents


def getChoices(conn, chapterID):
    """
    Connects to the database to get a dictionary
    of choices relative to a chapter
    """
    curs = dbi.dict_cursor(conn)
    curs.execute(''' select * from choice where host_chapter = %s''', [chapterID])
    choices = curs.fetchall()
    return choices

def getUsername(conn, username):
    """
    Gets usename of one user from the userpass table 
    """
    curs = dbi.dict_cursor(conn)
    curs.execute('''select username from userpass
    where username = %s ''', [username])
    return curs.fetchall()[0]

def addStory(conn, story_title, author_username, genre, synopsis):
    """Adds stories to database 
    given information from the write.html template
    """
    curs = dbi.cursor(conn)
    curs.execute('''insert into story(story_title, author_username, genre, synopsis) 
    values(%s,%s,%s,%s)''', [story_title, author_username, genre, synopsis])
    curs.execute('''select last_insert_id()''')
    last_insert_story_id = curs.fetchone()[0]
    print (last_insert_story_id)
    conn.commit()
    return last_insert_story_id

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
     in /students/cyo/draft/story_texts
    Then, it connects to the database to insert the .txt file name to the chapter table
    """
    currentDate = date.today()
    chapterTitle = chapterInfo['chapter_title'].replace(' ','_') # Gets the current chapter's title and replaces spaces by _
    chapterFileName = chapterTitle + "_" + str(currentDate)
    filePath = "/students/cyo/draft/story_texts/"
    print(filePath+chapterFileName)
    with open(filePath+chapterFileName, 'w') as f:
        f.writelines(chapterText)
    # Now, we insert the name of .txt file in the chapter table
    chapterID = chapterInfo['chapter_id']
    curs = dbi.cursor(conn)
    curs.execute('''update chapter 
    set chapter_content = %s
    where chapter_id = %s''', [chapterFileName, chapterID])
    conn.commit()

if __name__ == '__main__':
    conn = dbi.connect()
    delete_user(conn, 'fred')
    delete_user(conn, 'george')

    for username in ['fred', 'george', 'fred']:
        print(username, insert_user(conn, username, 'secret'))
        print(username, login_user(conn, username, 'secret'))
        