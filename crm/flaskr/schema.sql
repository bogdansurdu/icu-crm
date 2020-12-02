DROP TABLE IF EXISTS ticket;
DROP TABLE IF EXISTS comments;
DROP TABLE IF EXISTS messages;
DROP TABLE IF EXISTS conversation;

CREATE TABLE ticket (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  department TEXT,
  author_name TEXT NOT NULL,
  author_email TEXT NOT NULL,
  author_group TEXT,
  claim_number TEXT,
  created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  resolved TIMESTAMP,
  title TEXT NOT NULL,
  body TEXT NOT NULL,
  response TEXT,
  responder TEXT,
  responder_email TEXT,
  response_time TIMESTAMP,
  response_meeting TEXT
);

CREATE TABLE comments (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  ticket_id INTEGER NOT NULL,
  author_name TEXT NOT NULL,
  author_email TEXT NOT NULL,
  comment TEXT NOT NULL,
  created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (ticket_id) REFERENCES ticket (id)
);

CREATE TABLE conversation (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  student_name TEXT NOT NULL,
  student_email TEXT NOT NULL,
  staff_name TEXT NOT NULL,
  staff_email TEXT NOT NULL,
  seen_by_staff INTEGER,
  seen_by_student INTEGER
);

CREATE TABLE messages (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  conversation_id INTEGER NOT NULL,
  message TEXT NOT NULL,
  created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  author TEXT NOT NULL,
  FOREIGN KEY (conversation_id) REFERENCES conversation (id)
);