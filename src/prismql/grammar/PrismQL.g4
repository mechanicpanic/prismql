grammar PrismQL;

// Entry point
query
    :
    Select body
    ;

body
    :
    (query_seq | restrictions) ';'? (InWin number)?
    ;

query_seq
    :
    '(' query ')' ( ';' '(' query ')' )* 
    ;

restrictions
    :
    restriction (',' restriction)* Unr?
    ;

restriction
    :
    restriction And restriction
    | restriction Or restriction
    | '(' restriction ')'
    | Not restriction
    | condition
    ;

condition
    :
    HasWordOfDict '(' hdict ')'
    | HasTime '(' ')'
    | HasLocation '(' ')'
    | HasOrganization '(' ')'
    | HasURL '(' ')'
    | HasDate '(' ')'
    | HasQuestion '(' ')'
    | HasUserMentioned '(' huser ')'
    | ByUser '(' huser ')'
    ;

// Rule references
number : INTEGER;
hdict : STRING;
huser : STRING;

// Keywords (case-insensitive)
Select : 'SELECT' | 'select';
InWin  : 'INWIN'  | 'inwin' ;
Unr    : 'UNR'    | 'unr'   ;
Not    : 'NOT'    | 'not'   ;
And    : 'AND'    | 'and'   ;
Or     : 'OR'     | 'or'    ;

// Condition keywords
HasWordOfDict    : 'HASWORDOFDICT'    | 'haswordofdict'   ;
HasTime          : 'HASTIME'          | 'hastime'         ;
HasLocation      : 'HASLOCATION'      | 'haslocation'     ;
HasOrganization  : 'HASORGANIZATION'  | 'hasorganization' ;
HasURL           : 'HASURL'           | 'hasurl'          ;
HasDate          : 'HASDATE'          | 'hasdate'         ;
HasQuestion      : 'HASQUESTION'      | 'hasquestion'     ;
HasUserMentioned : 'HASUSERMENTIONED' | 'hasusermentioned';
ByUser           : 'BYUSER'           | 'byuser'          ;

// Tokens
INTEGER : DIGIT+;
STRING  : (LETTER | DIGIT)+;

// Whitespace (skip)
WS: [ \n\r\t] -> skip;

// Fragments
fragment DIGIT : [0-9];
fragment LETTER : [a-zA-Z_];