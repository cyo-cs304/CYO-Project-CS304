-- <!-- ddl.sql for WebTales/CYO Adventure CS304 Project -->
-- CS304 FA22 Project
-- Annelle Abatoni, Ryan Rowe, Maria Moura

use cyo_db;

drop table if exists user;
create table user(
    userID int not null auto_increment,
    username varchar(20),
    email varchar(50),
    passkey varchar(50), /* password */
    PRIMARY KEY (userID)
);

drop table if exists story;
create table story(
    story_id int not null auto_increment,
    story_title varchar(20),
    author_username varchar(20), /* foreign key username from user table */
    genre varchar(20),
    synopsis varchar(200),
    PRIMARY KEY (story_id)
);

drop table if exists follow;
create table follow(
    username varchar(20), /* foreign key from user table */
    story_id int, /* foreign key from story table */
    saved_progress int, /* foreign key chapter_id from chapter table */
    user_rating enum('1', '2', '3', '4', '5'),
    PRIMARY KEY (username, story_id)
);

drop table if exists chapter;
create table chapter(
    chapter_id int not null auto_increment,
    story_id int, /* foreign key from story table */
    chapter_title varchar(50),  
    chapter_content varchar(50), /* name of a txt file that contains text to the story */
    PRIMARY KEY (chapter_id)
);

drop table if exists choice;
create table choice (
    choice_id int not null auto_increment,
    host_chapter int, /* foreign key chapter_id from chapter table */
    description_text varchar(100),
    chapter_redirect int, /* foreign key chapter_id from chapter table */
    PRIMARY KEY (choice_id)
);

INSERT INTO story(story_id, story_title, author_username, genre, synopsis) 
VALUES (123,'The last night', 'maria_m','drama','A touching story from Maya Angelou'); 

INSERT INTO follow(username,story_id,saved_progress, user_rating) 
VALUES ('follower_1',123,1,'4');

INSERT INTO chapter(chapter_id, story_id, chapter_title, chapter_content) 
VALUES (1,123,'First Chapter', 'samplestory.txt');

INSERT INTO chapter(chapter_id, story_id, chapter_title, chapter_content) 
VALUES (2,123,'Third Chapter', 'freemantrial.txt');

INSERT INTO chapter(chapter_id, story_id, chapter_title, chapter_content) 
VALUES (3,123,'Third Chapter', 'runaway.txt');

INSERT INTO choice(choice_id, host_chapter, description_text, chapter_redirect)
VALUES (1,1, 'Attend Mr. Freeman`s trial', 2);

INSERT INTO choice(choice_id, host_chapter, description_text, chapter_redirect)
VALUES (2,1, 'Run away with Bailey', 3);

INSERT INTO choice(choice_id, host_chapter, description_text, chapter_redirect)
VALUES (3,3, 'Tell Mom to come home', 0);

INSERT INTO choice(choice_id, host_chapter, description_text, chapter_redirect)
VALUES (4,2, 'Run from trial', 0);