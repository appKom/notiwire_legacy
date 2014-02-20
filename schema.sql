drop table if exists affiliation_keys;
create table affiliation_keys (
  id integer primary key autoincrement,
  affiliation text unique not null,
  key text not null
);
