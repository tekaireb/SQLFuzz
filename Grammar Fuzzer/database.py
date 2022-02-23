import sqlite3
import apsw

DB_NAME = "persons.db"

class Person(): 
    def __init__(self, ssn, name, age, email_address, phone_number):
        self.ssn = ssn
        self.name = name
        self.age = age
        self.email_address = email_address
        self.phone_number = phone_number
    
    def __eq__(self, rhs):
        return self.ssn == rhs.ssn and self.name == rhs.name and self.age == rhs.age and self.email_address == rhs.email_address and self.phone_number == phone_number

    def toString(self):
        return "ssn: {} name: {} age: {}, email address: {}, phone number: {}".format(self.ssn, self.name, self.age, self.email_address, self.phone_number)

class Query:
    INSERT_PERSON = "INSERT INTO Persons VALUES('{}','{}', {}, '{}', '{}')"
    SELECT_ALL = "SELECT * FROM Persons"
    CREATE_PERSON_TABLE = "CREATE TABLE if not exists Persons (ssn VARCHAR(11) PRIMARY KEY, name VARCHAR(64), age INT, email_address VARCHAR(64), phone_number VARCHAR(64))"

    def __init__(self):
        self.db_name = DB_NAME
        self.conn = apsw.Connection(self.db_name, statementcachesize = 0)
        self.conn.cursor().execute(self.CREATE_PERSON_TABLE)
    
    def startConnection(self):
        self.conn = apsw.Connection(self.db_name, statementcachesize = 0)

    def closeConnection(self):
        self.conn.close()

    def insertPerson(self, person):
        self.conn.cursor().execute(self.INSERT_PERSON.format(person.ssn, person.name, person.age, person.email_address, person.phone_number))

    def getAll(self):
        return [self.objectify(p) for p in self.conn.cursor().execute(self.SELECT_ALL).fetchall()]
        
    def objectify(self, p):
        return Person(p[0], p[1], p[2], p[3], p[4])


p = Person("123-12-1234", "gautam", 21, "gautam@ucsb.edu", "(408) 823-1234")
q = Query()
q.insertPerson(p)
result = q.getAll()
