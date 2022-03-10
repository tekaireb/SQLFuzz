from typing import Dict, Union, Any, Tuple, List
import string

from config import Config

# Specify SQL Grammar for grammar-based fuzzer to generate SQL queries

Option = Dict[str, Any]
Expansion = Union[str, Tuple[str, Option]]
Grammar = Dict[str, List[Expansion]]


def sql_grammar(config: Config):
    db = config.db

    fields = config.fields
    comparators = config.comparators
    types = config.types

    SQL_GRAMMAR: Grammar = {
        '<Query>':
            ['SELECT <SelList> FROM <FromList> WHERE <Condition>'],
        #  'SELECT <SelList> FROM <FromList>',
        #  'SELECT * FROM <FromList>',

        '<SelList>':
            ['<Attribute>', '<SelList>, <Attribute>'],

        '<FromList>':
            ['<Relation>'],

        '<Condition>':
            ['<Comparison>', '<Condition> AND <Comparison>',
                '<Condition> OR <Comparison>'],

        '<Comparison>':
            [f'{f} {c} "{t}"' for f, c, t in zip(fields, comparators, types)],

        '<Comparator>':
            ['<', '<=', '=', '<LAngle><RAngle>', '>=', '>'],

        '<StringComparator>':
            ['=', '<LAngle><RAngle>'],

        '<LAngle>': ['<'],

        '<RAngle>': ['>'],

        '<Relation>': [db],

        '<Attribute>':
            fields,

        # Types:
        '<Name>': ['<String>'],
        '<String>': ['<Char>', '<String><Char>'],
        '<Char>': list(string.ascii_lowercase),
        '<Age>': [str(i) for i in range(2, 100)],
        # '<Integer>': ['<Digit>', '-<Integer>', '<Integer><Digit>'],
        # '<Integer>': ['<Digit>', '<Integer><Digit>'],  # Only positive numbers
        '<Digit>': [str(i) for i in range(10)],
        '<Email>': ['<String>@<String>.com', '<String>@<String>.org', '<String>@<String>.edu'],
        '<Phone>': ['(<Area>)<Exchange>-<Line>'],
        '<Lead-Digit>': [str(i) for i in range(2, 10)],
        '<Area>': ['<Lead-Digit><Digit><Digit>'],
        '<Exchange>': ['<Lead-Digit><Digit><Digit>'],
        '<Line>': ['<Digit><Digit><Digit><Digit>'],
        '<SSN>': ['<Digit><Digit><Digit>-<Digit><Digit>-<Digit><Digit><Digit><Digit>']
    }

    return SQL_GRAMMAR
