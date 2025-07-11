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
    // New fluent operators (preferred)
    Contains '(' hdict ')'
    | From '(' huser ')'
    | MentionsUser '(' huser ')'
    | IsQuestion '(' ')'
    | MentionsDate '(' ')'
    | MentionsTime '(' ')'
    | MentionsPlace '(' ')'
    | MentionsOrg '(' ')'
    | ContainsLink '(' ')'
    
    // Legacy operators (backward compatibility)
    | HasWordOfDict '(' hdict ')'
    | ByUser '(' huser ')'
    | HasUserMentioned '(' huser ')'
    | HasQuestion '(' ')'
    | HasDate '(' ')'
    | HasTime '(' ')'
    | HasLocation '(' ')'
    | HasOrganization '(' ')'
    | HasURL '(' ')'
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

// New fluent condition keywords (preferred)
Contains         : 'CONTAINS'         | 'contains'        ;
From             : 'FROM'             | 'from'            ;
MentionsUser     : 'MENTIONS_USER'    | 'mentions_user'   | 'MENTIONSUSER' | 'mentionsuser' ;
IsQuestion       : 'IS_QUESTION'      | 'is_question'     | 'ISQUESTION'   | 'isquestion'   ;
MentionsDate     : 'MENTIONS_DATE'    | 'mentions_date'   | 'MENTIONSDATE' | 'mentionsdate' ;
MentionsTime     : 'MENTIONS_TIME'    | 'mentions_time'   | 'MENTIONSTIME' | 'mentionstime' ;
MentionsPlace    : 'MENTIONS_PLACE'   | 'mentions_place'  | 'MENTIONSPLACE'| 'mentionsplace';
MentionsOrg      : 'MENTIONS_ORG'     | 'mentions_org'    | 'MENTIONSORG'  | 'mentionsorg'  ;
ContainsLink     : 'CONTAINS_LINK'    | 'contains_link'   | 'CONTAINSLINK' | 'containslink' ;

// Legacy condition keywords (backward compatibility)
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