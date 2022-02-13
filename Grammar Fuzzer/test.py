from fuzzingbook.GrammarFuzzer import GrammarFuzzer
from typing import Dict, Union, Any, Tuple, List
import string

Option = Dict[str, Any]
Expansion = Union[str, Tuple[str, Option]]
Grammar = Dict[str, List[Expansion]]

dbs = {
    'Users_DB': {
        'fields': ['name', 'age', 'email_address', 'phone_number'],
        # TODO: Allow passing of params to specify additional constraints (e.g., numerical ranges, age should be 1 to 100)
        'types': ['<String>', '<Integer>', '<Email>', '<Phone>'],
    }
}

DB = 'Users_DB'

SQL_GRAMMAR: Grammar = {
    '<Query>':
        ['SELECT <SelList> FROM <FromList> WHERE <Condition>',
         'SELECT <SelList> FROM <FromList>',
         'SELECT * FROM <FromList>',
         'INSERT INTO <FromList> VALUES ("' + '", "'.join(dbs[DB]["types"]) + '")'],

    '<SelList>':
        ['<Attribute>', '<SelList>, <Attribute>'],

    '<FromList>':
        ['<Relation>'],

    '<Condition>':
        ['<Comparison>', '<Condition> AND <Comparison>',
            '<Condition> OR <Comparison>'],

    '<Comparison>':
        [f'{f} <Comparator> "{t}"' for f, t in zip(
            dbs[DB]['fields'], dbs[DB]['types'])],

    '<Comparator>':
        ['<', '<=', '=', '>=', '>'],

    '<Relation>': [DB],

    '<Attribute>':
        dbs[DB]['fields'],

    # Types:
    '<String>': ['<Char>', '<String><Char>'],
    '<Char>': list(string.ascii_lowercase),
    '<Integer>': ['<Digit>', '-<Integer>', '<Integer><Digit>'],
    '<Digit>': [str(i) for i in range(10)],
    '<Email>': ['<String>@<String>.com', '<String>@<String>.org', '<String>@<String>.edu'],
    '<Phone>': ['(<Area>) <Exchange>-<Line>'],
    '<Lead-Digit>': [str(i) for i in range(2, 10)],
    '<Area>': ['<Lead-Digit><Digit><Digit>'],
    '<Exchange>': ['<Lead-Digit><Digit><Digit>'],
    '<Line>': ['<Digit><Digit><Digit><Digit>']
}

fuzzer = GrammarFuzzer(grammar=SQL_GRAMMAR,
                       start_symbol='<Query>', max_nonterminals=5)

for i in range(15):
    print(f'#{i}: \t{fuzzer.fuzz()}')
