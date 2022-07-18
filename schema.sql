/* user table: registers students, teachers and db admins */
CREATE TABLE users (
    id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(30) NOT NULL,
    password VARCHAR(255) NOT NULL,
    email VARCHAR(100) NOT NULL,
    fullname VARCHAR(50) NOT NULL,
    role VARCHAR(10) NOT NULL,
    creation_date DATETIME DEFAULT CURRENT_TIMESTAMP
);

/* subjects table: each subject has a teacher and three activities assigned */
CREATE TABLE subjects (
    id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(30) NOT NULL,
    teacher_id INT NOT NULL,
    cycle_1 FLOAT(3,2) NOT NULL DEFAULT 0,35,
    cycle_2 FLOAT(3,2) NOT NULL DEFAULT 0,35,
    cycle_3 FLOAT(3,2) NOT NULL DEFAULT 0,3,
    FOREIGN KEY (teacher_id) REFERENCES users(id)
);

/* activities table: each activity has a subject assigned */
CREATE TABLE activities (
    id INT NOT NULL AUTO_INCREMENT,
    title VARCHAR(100) NOT NULL,
    description VARCHAR(280) NOT NULL,
    due_date DATETIME NOT NULL,
    subject_id INT NOT NULL,
    PRIMARY KEY (id),
    FOREIGN KEY (subject_id) REFERENCES subjects(id)
);

/* each student may have multiple or no subjects assigned */
CREATE TABLE students_subjects (
    student_id INT NOT NULL,
    subject_id INT NOT NULL,
    grade FLOAT(3,2) NOT NULL,
    FOREIGN KEY (student_id) REFERENCES users(id),
    FOREIGN KEY (subject_id) REFERENCES subjects(id)
);

/* activities per subject DROPPED */
CREATE TABLE subject_activities (
    subject_id INT NOT NULL,
    act1_id INT NOT NULL,
    act2_id INT NOT NULL,
    act3_id INT NOT NULL,
    FOREIGN KEY (subject_id) REFERENCES subjects(id),
    FOREIGN KEY (act1_id) REFERENCES activities(id),
    FOREIGN KEY (act2_id) REFERENCES activities(id),
    FOREIGN KEY (act3_id) REFERENCES activities(id)
);

/* each student may have multiple or no activities assigned depending on the subjects assigned */
CREATE TABLE students_activities (
    student_id INT NOT NULL,
    activity_id INT NOT NULL,
    subject_id INT NOT NULL,
    submitted BOOLEAN NOT NULL DEFAULT FALSE,
    grade FLOAT(3,2) NOT NULL,
    FOREIGN KEY (student_id) REFERENCES users(id),
    FOREIGN KEY (activity_id) REFERENCES activities(id),
    FOREIGN KEY (subject_id) REFERENCES subjects(id)
);

/* each teacher may have multiple or no activities assigned depenging on the subjects assigned */
CREATE TABLE teacher_activities (
    teacher_id INTEGER NOT NULL,
    activity_id INTEGER NOT NULL,
    FOREIGN KEY (teacher_id) REFERENCES users(id),
    FOREIGN KEY (activity_id) REFERENCES activities(id)
);

/* loading users */
LOAD DATA INFILE '/home/bernalcodes/Desktop/initial_commit/code/final_project_cs50x/edu-board/user_data.txt'
INTO TABLE users
FIELDS TERMINATED BY ','
LINES TERMINATED BY '\n'
(username, password, email, fullname, role);

/* loading subjects */
LOAD DATA INFILE '/home/bernalcodes/Desktop/initial_commit/code/final_project_cs50x/edu-board/subject_data.txt'
INTO TABLE subjects
FIELDS TERMINATED BY ','
LINES TERMINATED BY '\n'
(name, teacher_id);

/* loading activities */
LOAD DATA INFILE '/home/bernalcodes/Desktop/initial_commit/code/final_project_cs50x/edu-board/activity_data.txt'
INTO TABLE activities
FIELDS TERMINATED BY ','
LINES TERMINATED BY '\n'
(title, description, due_date, subject_id);

/* loading students subjects */
LOAD DATA INFILE '/home/bernalcodes/Desktop/initial_commit/code/final_project_cs50x/edu-board/db_data/students_subjects_data.txt'
INTO TABLE students_subjects
FIELDS TERMINATED BY ','
LINES TERMINATED BY '\n'
(student_id, subject_id);

/* loading students activities */
LOAD DATA INFILE '/home/bernalcodes/Desktop/initial_commit/code/final_project_cs50x/edu-board/db_data/students_activities_data.txt'
INTO TABLE students_activities
FIELDS TERMINATED BY ','
LINES TERMINATED BY '\n'
(student_id, activity_id, subject_id, submitted);

/* loading activities */
LOAD DATA INFILE '/home/bernalcodes/Desktop/initial_commit/code/final_project_cs50x/edu-board/db_data/subjects_activities_data.txt'
INTO TABLE activities
FIELDS TERMINATED BY ','
LINES TERMINATED BY '\n'
(title, description, due_date, subject_id);

/* loading student's activities */
LOAD DATA INFILE '/home/bernalcodes/Desktop/initial_commit/code/final_project_cs50x/edu-board/db_data/students_activities_data.txt'
INTO TABLE students_activities
FIELDS TERMINATED BY ','
LINES TERMINATED BY '\n'
(student_id, activity_id, subject_id);

/* alter column data */
ALTER TABLE foobar_data
MODIFY COLUMN col VARCHAR(255) NOT NULL DEFAULT '{}';

/* retrieves ids, names and teachers for a student's subjects */
SELECT subjects.id, subjects.name, users.fullname
FROM subjects INNER JOIN users
ON subjects.teacher_id=users.id
WHERE subjects.id IN (
    SELECT subject_id
    FROM students_subjects
    WHERE student_id = 6
) ORDER BY subjects.name;

/* same as last query but including grades*/
SELECT subjects.id, subjects.name, users.fullname, students_subjects.grade
FROM subjects
INNER JOIN users
ON subjects.teacher_id=users.id
INNER JOIN students_subjects
ON subjects.id=students_subjects.subject_id
WHERE students_subjects.student_id=6;

/* retrieves student's activities for each subject */
SELECT subjects.id, subjects.name, activities.title, activities.description, activities.due_date
FROM subjects
INNER JOIN activities ON subjects.id=activities.subject_id
INNER JOIN students_subjects ON subjects.id=students_subjects.subject_id
WHERE students_subjects.student_id=23;

/* retrieves subject info */
SELECT subjects.id, subjects.name, students_subjects.grade, users.fullname
FROM subjects
INNER JOIN users ON subjects.teacher_id=users.id
INNER JOIN students_subjects ON subjects.id=students_subjects.subject_id
WHERE subjects.id=4 AND students_subjects.student_id=23;

SELECT *
FROM activities
INNER JOIN students_activities ON activities.id=students_activities.activity_id
WHERE activities.subject_id = 1 AND students_activities.student_id = 23;

/* retrieving student's activity data from a subject */
SELECT
	activities.id,
	activities.title,
	activities.description,
	activities.due_date,
	students_activities.submitted,
	students_activities.grade,
FROM students_activities
INNER JOIN activities
ON students_activities.activity_id=activities.id
WHERE students_activities.student_id = 23
AND students_activities.subject_id = 1;

/* relating activities to students */
INSERT INTO students_activities (student_id, activity_id, subject_id)
SELECT students_subjects.student_id, activities.id, activities.subject_id
FROM activities
INNER JOIN students_subjects ON activities.subject_id=students_subjects.subject_id
WHERE students_subjects.student_id = 23 AND activities.subject_id = 4;

/* updating id on subjects due to wrong user (role) */
UPDATE subjects
SET teacher_id = 24
WHERE teacher_id = 4;

/* retrieve a teacher's subjects and activities */
SELECT subjects.id, subjects.name, activities.id, activities.title, activities.description, activities.due_date
FROM subjects
INNER JOIN activities ON subjects.id=activities.subject_id
WHERE subjects.teacher_id=

/* retrieve a teacher's subject's activities per subject*/
SELECT users.id, users.fullname, subjects.id, subjects.name, activities.id, activities.title, activities.description
FROM users
INNER JOIN subjects ON users.id=subjects.teacher_id
INNER JOIN activities ON subjects.id=activities.subject_id
WHERE subject_id = %s AND teacher_id=%s

/* working on showing all students per subject's activity */
SELECT
    users.id,
    users.fullname
FROM users
INNER JOIN students_subjects ON students_subjects.student_id=users.id
INNER JOIN students_activities ON students_activities.student_id=users.id
WHERE students_subjects.subject_id =


SELECT *
FROM users
INNER JOIN students_subjects ON students_subjects.student_id=users.id
INNER JOIN students_activities ON students_activities.student_id=users.id
WHERE students_subjects.subject_id =

/* retrieves all students from a specific subject*/
SELECT
    users.id,
    users.fullname
FROM users
INNER JOIN students_subjects ON students_subjects.student_id=users.id
WHERE students_subjects.subject_id = %s