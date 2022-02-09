from simple_fuzzer import *

 # https://stackoverflow.com/questions/3538225/how-does-select-from-two-tables-separated-by-a-comma-work-select-from-t1-t2/3538232
 # "<Relation> , <FromList>"],

# http://www.mathcs.emory.edu/~cheung/Courses/554/Syllabus/5-query-opt/SQL-grammar.html
EXPR_GRAMMAR: Grammar = {
    "<Query>":
        ["SELECT <SelList> FROM <FromList> WHERE <Condition>",
        "SELECT <SelList> FROM <FromList>"],

    "<SelList>":
        ["<Attribute>", "<Attribute>, <SelList>", "*"],

    "<FromList>":
        ["<Relation>"],

    # add seperate values for each attribute
    "<Condition>":
        ["<Int_Attribute> = <Int_Value>",
        "<String_Attribute> = <String_Value>"],

    "<Relation>": ["Users_DB"],

    "<Attribute>":
        ["ssn", "name", "age", "email", "address", "phone_number"]

    "Int_Value":
        ["0", "1", "... TODO ..."]
}

for i in range(10):
    print("input number: {}".format(i))
    print(simple_grammar_fuzzer(grammar=EXPR_GRAMMAR, max_nonterminals=5))
    print("\n")