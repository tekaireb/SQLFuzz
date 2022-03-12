# SQLFuzz

While necessary for the development of robust software, the creation of unit tests is typically an expensive and arduous process. In an effort to reduce the requisite human labor, software engineers have attempted to automate the process. One small class project, a simple program for generating text inputs, evolved into a family of techniques for automatically testing all manner of software.

In this project, we propose SQLFuzz, a novel grammar-based fuzzer which is specially designed for testing SQL databases. It uses knowledge of tables and fields within the database and a simple constraint solver in order to generate SQL statements that are both syntactically and semantically valid. It also maintains a brief history of the database’s responses and a set of properties to check in order to determine consistency across multiple queries.

# Overview

SQLFuzz executes multiple related SQL statements on a database and checks for consistency. It first generates a valid query based on a formal grammar specification of SQL coupled with information about table attributes and their types. The query is executed and the results are stored. SQLFuzz then generates mutational statements, such as a DELETE statement based on the results of the previous query, or an INSERT statement based on the conditions in the query’s WHERE clause. The query is then executed again, and its output is compared with the previously saved results. While SQLFuzz has no way of knowing whether or not the output is entirely correct, it is able to make assumptions about the change in the output based on known properties of the database. 

# Required Packages

> Packages from thefuzzingbook: https://www.fuzzingbook.org/html/Importing.html
> 
> tqdm progress bar: https://pypi.org/project/tqdm/
> 
> apsw: https://pypi.org/project/apsw/


# How to Run SQLFuzz

```python3 fuzzer.py config.json```

config.json contains configurable parameters that allows you to craft SQLFuzz to test a variety of database configurations. 

# Sample output

If you wish to see additional data regarding the failure or success of any test, output from SQLFuzz is stored within the output directory. The figure below is an example of a successful INSERT statement, written to the file ./ouptut/insert/sucesses.txt. The output contains the generated SELECT statement from SQLFuzz’s grammar, the INSERT statement from the constraint solver, and a confirmation message that the consistency checker found no errors in the insert. 


Similarly, data about any of the failing tests will be written to a file. The output contains the results from the initial SELECT query, the results from the final SELECT query, the failing DELETE statement, and the actual vs expect difference that SQLFuzz’s consistency checker flagged. 


# Thank you 

Our goal is to make SQLFuzz an open source, easily extensible property-based fuzzer that serves as an intuitive platform to maintain a high standard for both new and legacy SQL database systems. 






