grammar PrismQL;

// Entry point
query
    :
    Select body
    ;

body
    :
    (query_seq | restrictions) ';'? (InWindow number | InWin number | During time_value | Within time_value)? temporal_filter? groupby_clause? aggregate_clause? orderby_clause? limit_clause?
    ;

query_seq
    :
    '(' query ')' query_seq_continuation*
    ;

query_seq_continuation
    :
    ';' '(' query ')'                                      # UnorderedSubquery
    | positional_op '(' query ')' InWindow number          # PositionalSubquery
    | positional_op '(' query ')' Within number            # PositionalSubqueryDeprecated
    ;

positional_op
    :
    FollowedBy | PrecededBy | NotFollowedBy | NotPrecededBy
    ;

restrictions
    :
    named_restriction (',' named_restriction)* Unr?
    ;

named_restriction
    :
    restriction quantifier? (As QUOTED_STRING)?
    ;

quantifier
    :
    '{' number '}'                  # ExactQuantifier
    | '{' number ',' '}'            # AtLeastQuantifier
    | '{' number ',' number '}'     # RangeQuantifier
    ;

restriction
    :
    restriction And restriction
    | restriction Or restriction
    | restriction FollowedBy restriction InWindow number
    | restriction PrecededBy restriction InWindow number
    | restriction NotFollowedBy restriction InWindow number
    | restriction NotPrecededBy restriction InWindow number
    | restriction FollowedBy restriction Within number
    | restriction PrecededBy restriction Within number
    | restriction NotFollowedBy restriction Within number
    | restriction NotPrecededBy restriction Within number
    | '(' restriction ')'
    | Not restriction
    | condition
    ;

condition
    :
    // New fluent operators (preferred)
    Contains '(' hdict ')'
    | ContainsTokens '(' hdict ')'
    | ContainsPhrase '(' QUOTED_STRING ')'
    | From '(' huser ')'
    | MentionsUser '(' huser ')'
    | IsQuestion '(' ')'
    | MentionsDate '(' ')'
    | MentionsTime '(' ')'
    | MentionsPlace '(' ')'
    | MentionsOrg '(' ')'
    | ContainsLink '(' ')'
    | HasFeature '(' feature_name ')'
    | LabeledAs '(' feature_name ')'

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

// Temporal filtering
temporal_filter
    :
    Before '(' timestamp ')'
    | After '(' timestamp ')'
    | Between '(' timestamp ',' timestamp ')'
    ;

timestamp
    :
    QUOTED_STRING       # AbsoluteTimestamp
    | time_value Ago    # RelativeTimestamp
    ;

// Aggregation and grouping
groupby_clause
    :
    GroupBy groupby_field (',' groupby_field)*
    ;

groupby_field
    :
    field_name                          # SimpleGroupBy
    | temporal_group_func '(' field_name ')'  # TemporalGroupBy
    ;

temporal_group_func
    :
    Hours | Days | Weeks | Months | Years
    ;

aggregate_clause
    :
    Aggregate aggregation_func (',' aggregation_func)*
    ;

aggregation_func
    :
    Count '(' ')'                          # CountAll
    | Count '(' Distinct field_name ')'    # CountDistinct
    | Distinct '(' field_name ')'          # DistinctValues
    | Sum '(' field_name ')'               # SumFunc
    | Avg '(' field_name ')'               # AvgFunc
    | Min '(' field_name ')'               # MinFunc
    | Max '(' field_name ')'               # MaxFunc
    ;

orderby_clause
    :
    OrderBy field_name (Asc | Desc)? (',' field_name (Asc | Desc)?)*
    ;

limit_clause
    :
    Limit number (Offset number)?
    ;

// Temporal support
time_value
    :
    number time_unit
    ;

time_unit
    :
    Seconds | Minutes | Hours | Days | Weeks
    ;

// Rule references
number : INTEGER;
hdict : STRING | VARIABLE | WILDCARD;
huser : STRING | VARIABLE | WILDCARD;
feature_name : STRING;
field_name : STRING;

// Keywords (case-insensitive)
Select   : 'SELECT'   | 'select'  ;
As       : 'AS'       | 'as'      ;
InWindow : 'INWINDOW' | 'inwindow' | 'IN_WINDOW' | 'in_window' ;  // Unified positional operator
InWin    : 'INWIN'    | 'inwin'   ;  // Deprecated: use INWINDOW instead
During   : 'DURING'   | 'during'  ;  // Temporal window operator (time-based filtering)
Within   : 'WITHIN'   | 'within'  ;  // Deprecated: use DURING for temporal, INWINDOW for positional
Unr      : 'UNR'      | 'unr'     ;
Not      : 'NOT'      | 'not'     ;
And      : 'AND'      | 'and'     ;
Or       : 'OR'       | 'or'      ;

// Positional operators for lookahead/lookbehind
FollowedBy     : 'FOLLOWED_BY'     | 'followed_by'     | 'FOLLOWEDBY'    | 'followedby'    ;
PrecededBy     : 'PRECEDED_BY'     | 'preceded_by'     | 'PRECEDEDBY'    | 'precededby'    ;
NotFollowedBy  : 'NOT_FOLLOWED_BY' | 'not_followed_by' | 'NOTFOLLOWEDBY' | 'notfollowedby' ;
NotPrecededBy  : 'NOT_PRECEDED_BY' | 'not_preceded_by' | 'NOTPRECEDEDBY' | 'notprecededby' ;

// Aggregation keywords
Aggregate : 'AGGREGATE' | 'aggregate' ;
GroupBy   : 'GROUP BY'  | 'group by' | 'GROUPBY' | 'groupby' ;
Count     : 'COUNT'     | 'count'    ;
Distinct  : 'DISTINCT'  | 'distinct' ;
Sum       : 'SUM'       | 'sum'      ;
Avg       : 'AVG'       | 'avg'      ;
Min       : 'MIN'       | 'min'      ;
Max       : 'MAX'       | 'max'      ;

// Ordering and limiting
OrderBy   : 'ORDER BY'  | 'order by' | 'ORDERBY' | 'orderby' ;
Asc       : 'ASC'       | 'asc'      ;
Desc      : 'DESC'      | 'desc'     ;
Limit     : 'LIMIT'     | 'limit'    ;
Offset    : 'OFFSET'    | 'offset'   ;

// Temporal filtering keywords
Before    : 'BEFORE'    | 'before'   ;
After     : 'AFTER'     | 'after'    ;
Between   : 'BETWEEN'   | 'between'  ;
Ago       : 'AGO'       | 'ago'      ;

// Time units (also used for temporal grouping)
Seconds   : 'SECONDS' | 'seconds' | 'SECOND' | 'second' | 's' ;
Minutes   : 'MINUTES' | 'minutes' | 'MINUTE' | 'minute' | 'm' ;
Hours     : 'HOURS'   | 'hours'   | 'HOUR'   | 'hour'   | 'h' ;
Days      : 'DAYS'    | 'days'    | 'DAY'    | 'day'    | 'd' ;
Weeks     : 'WEEKS'   | 'weeks'   | 'WEEK'   | 'week'   | 'w' ;
Months    : 'MONTHS'  | 'months'  | 'MONTH'  | 'month'  ;
Years     : 'YEARS'   | 'years'   | 'YEAR'   | 'year'   ;

// New fluent condition keywords (preferred)
Contains         : 'CONTAINS'         | 'contains'        ;
ContainsTokens   : 'CONTAINS_TOKENS'  | 'contains_tokens' | 'CONTAINSTOKENS' | 'containstokens' ;
ContainsPhrase   : 'CONTAINS_PHRASE'  | 'contains_phrase' | 'CONTAINSPHRASE' | 'containsphrase' ;
From             : 'FROM'             | 'from'            ;
MentionsUser     : 'MENTIONS_USER'    | 'mentions_user'   | 'MENTIONSUSER' | 'mentionsuser' ;
IsQuestion       : 'IS_QUESTION'      | 'is_question'     | 'ISQUESTION'   | 'isquestion'   ;
MentionsDate     : 'MENTIONS_DATE'    | 'mentions_date'   | 'MENTIONSDATE' | 'mentionsdate' ;
MentionsTime     : 'MENTIONS_TIME'    | 'mentions_time'   | 'MENTIONSTIME' | 'mentionstime' ;
MentionsPlace    : 'MENTIONS_PLACE'   | 'mentions_place'  | 'MENTIONSPLACE'| 'mentionsplace';
MentionsOrg      : 'MENTIONS_ORG'     | 'mentions_org'    | 'MENTIONSORG'  | 'mentionsorg'  ;
ContainsLink     : 'CONTAINS_LINK'    | 'contains_link'   | 'CONTAINSLINK' | 'containslink' ;
HasFeature       : 'HAS_FEATURE'      | 'has_feature'     | 'HASFEATURE'   | 'hasfeature'   ;
LabeledAs        : 'LABELED_AS'       | 'labeled_as'      | 'LABELEDAS'    | 'labeledas'    ;

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
QUOTED_STRING : '"' (~["])* '"' | '\'' (~['])* '\'';
VARIABLE : '$' (LETTER | DIGIT)+;
WILDCARD : '*';

// Whitespace (skip)
WS: [ \n\r\t] -> skip;

// Fragments
fragment DIGIT : [0-9];
fragment LETTER : [a-zA-Z_];
