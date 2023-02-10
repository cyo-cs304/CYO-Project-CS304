-- <!-- userpass-recreate.sql for WebTales/CYO Adventure CS304 Project -->

drop table if exists userpass;

create table userpass(
       uid int auto_increment,
       username varchar(50) not null,
       hashed char(60),
       unique(username),
       index(username),
       primary key (uid)
);
