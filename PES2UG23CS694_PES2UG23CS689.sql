CREATE DATABASE IF NOT EXISTS College_database;
USE College_database;
CREATE TABLE College (
    Clg_ID INT PRIMARY KEY,
    Clg_Name VARCHAR(255) NOT NULL UNIQUE,
    Address VARCHAR(255) NOT NULL
);

-- Create the Department table
CREATE TABLE Department (
    Dept_ID INT PRIMARY KEY,
    Dept_Name VARCHAR(255) NOT NULL UNIQUE,
    HOD VARCHAR(255)
);

-- Create the Professor table with a foreign key to Department
CREATE TABLE Professor (
    Prof_ID INT PRIMARY KEY,
    Name VARCHAR(255) NOT NULL,
    Phone_No VARCHAR(20) UNIQUE,
    Email VARCHAR(255) NOT NULL UNIQUE,
    Address VARCHAR(255),
    Dept_ID INT,
    FOREIGN KEY (Dept_ID) REFERENCES Department(Dept_ID)
        ON DELETE SET NULL
        ON UPDATE CASCADE
);

-- Create the Student table with a foreign key to College
CREATE TABLE Student (
    Stu_ID INT PRIMARY KEY,
    Name VARCHAR(255) NOT NULL,
    Phone_No VARCHAR(20) UNIQUE,
    Email VARCHAR(255) NOT NULL UNIQUE,
    DOB DATE,
    Gender VARCHAR(10),
    Clg_ID INT,
    FOREIGN KEY (Clg_ID) REFERENCES College(Clg_ID)
        ON DELETE SET NULL
        ON UPDATE CASCADE
);

-- Create the Course table with a foreign key to Department
CREATE TABLE Course (
    Course_ID INT PRIMARY KEY,
    Course_Name VARCHAR(255) NOT NULL,
    Credits INT NOT NULL,
    Dept_ID INT,
    FOREIGN KEY (Dept_ID) REFERENCES Department(Dept_ID)
        ON DELETE SET NULL
        ON UPDATE CASCADE
);

-- Create the Enrollment junction table with a composite primary key
-- to link Students and Courses, and a foreign key to Professor
CREATE TABLE Enrollment (
    Stu_ID INT,
    Course_ID INT,
    Grade VARCHAR(2),
    PRIMARY KEY (Stu_ID, Course_ID),
    FOREIGN KEY (Stu_ID) REFERENCES Student(Stu_ID)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    FOREIGN KEY (Course_ID) REFERENCES Course(Course_ID)
        ON DELETE CASCADE
        ON UPDATE CASCADE
);
-- DML: Insert data into the tables

-- 1. Insert data into independent tables
INSERT INTO College (Clg_ID, Clg_Name, Address) VALUES
(101, 'National University of Technology', '123 Tech Park, Silicon Valley'),
(102, 'State College of Arts & Sciences', '456 Main Street, Capital City'),
(103, 'City Community College', '789 Oak Avenue, Metropolis'),
(104, 'Global Institute of Management', '101 Pine Lane, Business District'),
(105, 'St. Mary’s College', '202 Church Road, Suburbia');

INSERT INTO Department (Dept_ID, Dept_Name, HOD) VALUES
(1, 'Computer Science', 'Dr. Albus Dumbledore'),
(2, 'Electrical Engineering', 'Prof. Minerva McGonagall'),
(3, 'Business Administration', 'Dr. Severus Snape'),
(4, 'Applied Sciences', 'Prof. Filius Flitwick'),
(5, 'Humanities', 'Dr. Rubeus Hagrid');

-- 2. Insert data into tables that depend on the above (Student, Professor, Course)
INSERT INTO Student (Stu_ID, Name, Phone_No, Email, DOB, Gender, Clg_ID) VALUES
(1, 'John Smith', '9876543210', 'john.smith@email.com', '2005-03-15', 'Male', 101),
(2, 'Jane Doe', '9988776655', 'jane.doe@email.com', '2004-10-22', 'Female', 102),
(3, 'Peter Jones', '9123456789', 'peter.jones@email.com', '2006-01-30', 'Male', 101),
(4, 'Emily White', '9567891234', 'emily.white@email.com', '2005-07-05', 'Female', 103),
(5, 'Chris Green', '9678901234', 'chris.green@email.com', '2004-11-18', 'Male', 104),
(6, 'Samantha Brown', '9789012345', 'samantha.brown@email.com', '2006-04-25', 'Female', 102);

INSERT INTO Professor (Prof_ID, Name, Phone_No, Email, Address, Dept_ID) VALUES
(1, 'Dr. Smith', '1234567890', 'smith@nu.edu', '123 Main St', 1),
(2, 'Prof. Johnson', '1234567891', 'johnson@nu.edu', '456 Oak St', 2),
(3, 'Dr. Williams', '1234567892', 'williams@nu.edu', '789 Pine St', 3),
(4, 'Prof. Davis', '1234567893', 'davis@nu.edu', '101 Maple Ave', 1),
(5, 'Dr. Miller', '1234567894', 'miller@nu.edu', '202 Birch Rd', 4);

INSERT INTO Course (Course_ID, Course_Name, Credits, Dept_ID) VALUES
(1, 'Introduction to Databases', 4, 1),
(2, 'Circuits and Electronics', 5, 2),
(3, 'Financial Accounting', 3, 3),
(4, 'Data Structures', 4, 1),
(5, 'Organic Chemistry', 5, 4),
(6, 'Principles of Management', 3, 3);

-- 3. Insert data into the final dependent table (Enrollment)
INSERT INTO Enrollment (Stu_ID, Course_ID, Grade) VALUES
(1, 10, 'A'),
(1, 13, 'B+'),
(2, 11, 'A-'),
(3, 10, 'B'),
(4, 14, 'A'),
(5, 12, 'B'),
(6, 11, 'C+');

DELIMITER $$  
CREATE TRIGGER trg_student_Insert_Lowercase_Email  
BEFORE INSERT ON Professor  
FOR EACH ROW BEGIN SET NEW.Email = LOWER(NEW.Email);  
END$$  

DELIMITER $$  
CREATE TRIGGER trg_Before_Student_Insert_Validate_DOB  
BEFORE INSERT ON Student  
FOR EACH ROW  
BEGIN  
    IF NEW.DOB > CURDATE() OR NEW.DOB > DATE_SUB(CURDATE(), INTERVAL 18 YEAR) THEN  
        SIGNAL SQLSTATE '45000'   
        SET MESSAGE_TEXT = 'Invalid Date of Birth. Student must be at least 18 years old.';      END IF;  
END$$  

DELIMITER $$  
CREATE PROCEDURE sp_AddNewStudent(  
    IN p_Stu_ID INT,  
    IN p_Name VARCHAR(255),  
    IN p_Phone VARCHAR(20),  
    IN p_Email VARCHAR(255),  
    IN p_DOB DATE,  
    IN p_Gender VARCHAR(10),   
    IN p_Clg_ID INT  
)  
BEGIN  
    INSERT INTO Student (Stu_ID, Name, Phone_No, Email, DOB, Gender,  
Clg_ID)  
    VALUES (p_Stu_ID, p_Name, p_Phone, p_Email, p_DOB, p_Gender, p_Clg_ID);   
END$$  

DELIMITER $$  
CREATE PROCEDURE sp_GetStudentsByDepartment(  
    IN p_Dept_Name VARCHAR(255)  
)  
BEGIN  
      
    SELECT DISTINCT         s.Name,  
        s.Email  
    FROM Student s  
    JOIN Enrollment e ON s.Stu_ID = e.Stu_ID  
    JOIN Course c ON e.Course_ID = c.Course_ID  
    JOIN Department d ON c.Dept_ID = d.Dept_ID  
    WHERE d.Dept_Name = p_Dept_Name;  
END$$  

DELIMITER $$  
CREATE FUNCTION fn_GetDepartmenttHOD(     p_Dept_Name VARCHAR(255)  
)  
RETURNS VARCHAR(255)  
READS SQL DATA  
BEGIN  
    DECLARE v_HOD_Name VARCHAR(255);  
  
      
    SELECT HOD   
    INTO v_HOD_Name   
    FROM Department   
    WHERE Dept_Name = p_Dept_Name;  
  
    RETURN v_HOD_Name;  
END$$  

DELIMITER $$  
CREATE FUNCTION fn_GetStudentCountByCollege_(  
    p_Clg_ID INT  
)  
RETURNS INT  
READS SQL DATA  
BEGIN  
    DECLARE v_Student_Count INT;  
  
    SELECT COUNT(*)  
    INTO v_Student_Count  
    FROM Student  
    WHERE Clg_ID = p_Clg_ID;  
  
    RETURN v_Student_Count;  
END$$  

