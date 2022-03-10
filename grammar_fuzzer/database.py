import sqlite3
import apsw

DB_NAME = "persons.db"

generatedSSNs = set()

# class Person():
#     def __init__(self, ssn, name, age, email_address, phone_number):
#         self.ssn = ssn
#         self.name = name
#         self.age = age
#         self.email_address = email_address
#         self.phone_number = phone_number

#     def __eq__(self, rhs):
#         return self.ssn == rhs.ssn and self.name == rhs.name and self.age == rhs.age and self.email_address == rhs.email_address and self.phone_number == phone_number

#     def toString(self):
#         return "ssn: {} name: {} age: {}, email address: {}, phone number: {}".format(self.ssn, self.name, self.age, self.email_address, self.phone_number)


class Query:
    INSERT_PERSON = "INSERT INTO Users_DB (name, age, email_address, phone_number, ssn) VALUES('{}', '{}', '{}', '{}', '{}')"
    SELECT_ALL = "SELECT * FROM Users_DB"
    CREATE_USERDB_TABLE = "CREATE TABLE if not exists Users_DB (name VARCHAR(64), age INT, email_address VARCHAR(128), phone_number VARCHAR(64), ssn VARCHAR(11))"
    DROP_USERDB_TABLE = "DROP TABLE IF EXISTS Users_DB"

    def __init__(self):
        self.db_name = DB_NAME
        self.conn = apsw.Connection(self.db_name, statementcachesize=0)
        self.conn.cursor().execute(self.DROP_USERDB_TABLE)

        # Clear saved successes failures between runs
        with open('./output/insert/failures.txt', 'w') as f:
            pass
        with open('./output/insert/successes.txt', 'w') as f:
            pass
        with open('./output/delete/failures.txt', 'w') as f:
            pass
        with open('./output/delete/successes.txt', 'w') as f:
            pass

        self.conn.cursor().execute(self.CREATE_USERDB_TABLE)

    def startConnection(self):
        self.conn = apsw.Connection(self.db_name, statementcachesize=0)

    def closeConnection(self):
        self.conn.close()

    def executeSelectStatement(self, sqlSelect):
        result = self.conn.cursor().execute(sqlSelect).fetchall()
        return result

    def executeSqlStatement(self, sqlStatement):
        print(f'STATEMENT: {sqlStatement}')
        self.conn.cursor().execute(sqlStatement)

    def failure_executeInsertStatementTwice(self, sqlInsert):
        self.executeSqlStatement(sqlInsert)
        self.executeSqlStatement(sqlInsert)

    def getAll(self):
        return self.conn.cursor().execute(self.SELECT_ALL).fetchall()

    # def objectify(self, p):
    #     print(p)
    #     return Person(p[0], p[1], p[2], p[3], p[4])

# p = Person("123-12-1234", "gautam", 21, "gautam@ucsb.edu", "(408) 823-1234")
# q = Query()
# q.insertPerson(p)
# result = q.getAll()
