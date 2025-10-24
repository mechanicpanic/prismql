# Generated from /home/aleph/projects/prismql/src/prismql/grammar/PrismQL.g4 by ANTLR 4.13.1
# encoding: utf-8
from antlr4 import *
from io import StringIO
import sys
if sys.version_info[1] > 5:
	from typing import TextIO
else:
	from typing.io import TextIO

def serializedATN():
    return [
        4,1,67,388,2,0,7,0,2,1,7,1,2,2,7,2,2,3,7,3,2,4,7,4,2,5,7,5,2,6,7,
        6,2,7,7,7,2,8,7,8,2,9,7,9,2,10,7,10,2,11,7,11,2,12,7,12,2,13,7,13,
        2,14,7,14,2,15,7,15,2,16,7,16,2,17,7,17,2,18,7,18,2,19,7,19,2,20,
        7,20,2,21,7,21,2,22,7,22,2,23,7,23,2,24,7,24,2,25,7,25,1,0,1,0,1,
        0,1,1,1,1,3,1,58,8,1,1,1,3,1,61,8,1,1,1,1,1,1,1,1,1,3,1,67,8,1,1,
        1,3,1,70,8,1,1,1,3,1,73,8,1,1,1,3,1,76,8,1,1,1,3,1,79,8,1,1,1,3,
        1,82,8,1,1,2,1,2,1,2,1,2,5,2,88,8,2,10,2,12,2,91,9,2,1,3,1,3,1,3,
        1,3,1,3,1,3,1,3,1,3,1,3,1,3,1,3,1,3,3,3,105,8,3,1,4,1,4,1,5,1,5,
        1,5,5,5,112,8,5,10,5,12,5,115,9,5,1,5,3,5,118,8,5,1,6,1,6,3,6,122,
        8,6,1,6,1,6,3,6,126,8,6,1,7,1,7,1,7,1,7,1,7,1,7,1,7,1,7,1,7,1,7,
        1,7,1,7,1,7,1,7,1,7,3,7,143,8,7,1,8,1,8,1,8,1,8,1,8,1,8,1,8,1,8,
        3,8,153,8,8,1,8,1,8,1,8,1,8,1,8,1,8,1,8,1,8,1,8,1,8,1,8,1,8,1,8,
        1,8,1,8,1,8,1,8,1,8,1,8,1,8,1,8,1,8,1,8,1,8,1,8,1,8,1,8,1,8,1,8,
        1,8,5,8,185,8,8,10,8,12,8,188,9,8,1,9,1,9,1,9,1,9,1,9,1,9,1,9,1,
        9,1,9,1,9,1,9,1,9,1,9,1,9,1,9,1,9,1,9,1,9,1,9,1,9,1,9,1,9,1,9,1,
        9,1,9,1,9,1,9,1,9,1,9,1,9,1,9,1,9,1,9,1,9,1,9,1,9,1,9,1,9,1,9,1,
        9,1,9,1,9,1,9,1,9,1,9,1,9,1,9,1,9,1,9,1,9,1,9,1,9,1,9,1,9,1,9,1,
        9,1,9,1,9,1,9,1,9,1,9,1,9,1,9,1,9,1,9,1,9,1,9,1,9,1,9,1,9,1,9,3,
        9,261,8,9,1,10,1,10,1,10,1,10,1,10,1,10,1,10,1,10,1,10,1,10,1,10,
        1,10,1,10,1,10,1,10,1,10,1,10,3,10,280,8,10,1,11,1,11,1,11,1,11,
        3,11,286,8,11,1,12,1,12,1,12,1,12,5,12,292,8,12,10,12,12,12,295,
        9,12,1,13,1,13,1,13,1,13,1,13,1,13,3,13,303,8,13,1,14,1,14,1,15,
        1,15,1,15,1,15,5,15,311,8,15,10,15,12,15,314,9,15,1,16,1,16,1,16,
        1,16,1,16,1,16,1,16,1,16,1,16,1,16,1,16,1,16,1,16,1,16,1,16,1,16,
        1,16,1,16,1,16,1,16,1,16,1,16,1,16,1,16,1,16,1,16,1,16,1,16,1,16,
        1,16,1,16,1,16,1,16,1,16,3,16,350,8,16,1,17,1,17,1,17,3,17,355,8,
        17,1,17,1,17,1,17,3,17,360,8,17,5,17,362,8,17,10,17,12,17,365,9,
        17,1,18,1,18,1,18,1,18,3,18,371,8,18,1,19,1,19,1,19,1,20,1,20,1,
        21,1,21,1,22,1,22,1,23,1,23,1,24,1,24,1,25,1,25,1,25,0,1,16,26,0,
        2,4,6,8,10,12,14,16,18,20,22,24,26,28,30,32,34,36,38,40,42,44,46,
        48,50,0,5,1,0,15,18,1,0,38,42,1,0,28,29,1,0,36,40,2,0,63,63,65,66,
        420,0,52,1,0,0,0,2,57,1,0,0,0,4,83,1,0,0,0,6,104,1,0,0,0,8,106,1,
        0,0,0,10,108,1,0,0,0,12,119,1,0,0,0,14,142,1,0,0,0,16,152,1,0,0,
        0,18,260,1,0,0,0,20,279,1,0,0,0,22,285,1,0,0,0,24,287,1,0,0,0,26,
        302,1,0,0,0,28,304,1,0,0,0,30,306,1,0,0,0,32,349,1,0,0,0,34,351,
        1,0,0,0,36,366,1,0,0,0,38,372,1,0,0,0,40,375,1,0,0,0,42,377,1,0,
        0,0,44,379,1,0,0,0,46,381,1,0,0,0,48,383,1,0,0,0,50,385,1,0,0,0,
        52,53,5,7,0,0,53,54,3,2,1,0,54,1,1,0,0,0,55,58,3,4,2,0,56,58,3,10,
        5,0,57,55,1,0,0,0,57,56,1,0,0,0,58,60,1,0,0,0,59,61,5,1,0,0,60,59,
        1,0,0,0,60,61,1,0,0,0,61,66,1,0,0,0,62,63,5,9,0,0,63,67,3,42,21,
        0,64,65,5,10,0,0,65,67,3,38,19,0,66,62,1,0,0,0,66,64,1,0,0,0,66,
        67,1,0,0,0,67,69,1,0,0,0,68,70,3,20,10,0,69,68,1,0,0,0,69,70,1,0,
        0,0,70,72,1,0,0,0,71,73,3,24,12,0,72,71,1,0,0,0,72,73,1,0,0,0,73,
        75,1,0,0,0,74,76,3,30,15,0,75,74,1,0,0,0,75,76,1,0,0,0,76,78,1,0,
        0,0,77,79,3,34,17,0,78,77,1,0,0,0,78,79,1,0,0,0,79,81,1,0,0,0,80,
        82,3,36,18,0,81,80,1,0,0,0,81,82,1,0,0,0,82,3,1,0,0,0,83,84,5,2,
        0,0,84,85,3,0,0,0,85,89,5,3,0,0,86,88,3,6,3,0,87,86,1,0,0,0,88,91,
        1,0,0,0,89,87,1,0,0,0,89,90,1,0,0,0,90,5,1,0,0,0,91,89,1,0,0,0,92,
        93,5,1,0,0,93,94,5,2,0,0,94,95,3,0,0,0,95,96,5,3,0,0,96,105,1,0,
        0,0,97,98,3,8,4,0,98,99,5,2,0,0,99,100,3,0,0,0,100,101,5,3,0,0,101,
        102,5,10,0,0,102,103,3,42,21,0,103,105,1,0,0,0,104,92,1,0,0,0,104,
        97,1,0,0,0,105,7,1,0,0,0,106,107,7,0,0,0,107,9,1,0,0,0,108,113,3,
        12,6,0,109,110,5,4,0,0,110,112,3,12,6,0,111,109,1,0,0,0,112,115,
        1,0,0,0,113,111,1,0,0,0,113,114,1,0,0,0,114,117,1,0,0,0,115,113,
        1,0,0,0,116,118,5,11,0,0,117,116,1,0,0,0,117,118,1,0,0,0,118,11,
        1,0,0,0,119,121,3,16,8,0,120,122,3,14,7,0,121,120,1,0,0,0,121,122,
        1,0,0,0,122,125,1,0,0,0,123,124,5,8,0,0,124,126,5,64,0,0,125,123,
        1,0,0,0,125,126,1,0,0,0,126,13,1,0,0,0,127,128,5,5,0,0,128,129,3,
        42,21,0,129,130,5,6,0,0,130,143,1,0,0,0,131,132,5,5,0,0,132,133,
        3,42,21,0,133,134,5,4,0,0,134,135,5,6,0,0,135,143,1,0,0,0,136,137,
        5,5,0,0,137,138,3,42,21,0,138,139,5,4,0,0,139,140,3,42,21,0,140,
        141,5,6,0,0,141,143,1,0,0,0,142,127,1,0,0,0,142,131,1,0,0,0,142,
        136,1,0,0,0,143,15,1,0,0,0,144,145,6,8,-1,0,145,146,5,2,0,0,146,
        147,3,16,8,0,147,148,5,3,0,0,148,153,1,0,0,0,149,150,5,12,0,0,150,
        153,3,16,8,2,151,153,3,18,9,0,152,144,1,0,0,0,152,149,1,0,0,0,152,
        151,1,0,0,0,153,186,1,0,0,0,154,155,10,9,0,0,155,156,5,13,0,0,156,
        185,3,16,8,10,157,158,10,8,0,0,158,159,5,14,0,0,159,185,3,16,8,9,
        160,161,10,7,0,0,161,162,5,15,0,0,162,163,3,16,8,0,163,164,5,10,
        0,0,164,165,3,42,21,0,165,185,1,0,0,0,166,167,10,6,0,0,167,168,5,
        16,0,0,168,169,3,16,8,0,169,170,5,10,0,0,170,171,3,42,21,0,171,185,
        1,0,0,0,172,173,10,5,0,0,173,174,5,17,0,0,174,175,3,16,8,0,175,176,
        5,10,0,0,176,177,3,42,21,0,177,185,1,0,0,0,178,179,10,4,0,0,179,
        180,5,18,0,0,180,181,3,16,8,0,181,182,5,10,0,0,182,183,3,42,21,0,
        183,185,1,0,0,0,184,154,1,0,0,0,184,157,1,0,0,0,184,160,1,0,0,0,
        184,166,1,0,0,0,184,172,1,0,0,0,184,178,1,0,0,0,185,188,1,0,0,0,
        186,184,1,0,0,0,186,187,1,0,0,0,187,17,1,0,0,0,188,186,1,0,0,0,189,
        190,5,43,0,0,190,191,5,2,0,0,191,192,3,44,22,0,192,193,5,3,0,0,193,
        261,1,0,0,0,194,195,5,44,0,0,195,196,5,2,0,0,196,197,3,46,23,0,197,
        198,5,3,0,0,198,261,1,0,0,0,199,200,5,45,0,0,200,201,5,2,0,0,201,
        202,3,46,23,0,202,203,5,3,0,0,203,261,1,0,0,0,204,205,5,46,0,0,205,
        206,5,2,0,0,206,261,5,3,0,0,207,208,5,47,0,0,208,209,5,2,0,0,209,
        261,5,3,0,0,210,211,5,48,0,0,211,212,5,2,0,0,212,261,5,3,0,0,213,
        214,5,49,0,0,214,215,5,2,0,0,215,261,5,3,0,0,216,217,5,50,0,0,217,
        218,5,2,0,0,218,261,5,3,0,0,219,220,5,51,0,0,220,221,5,2,0,0,221,
        261,5,3,0,0,222,223,5,52,0,0,223,224,5,2,0,0,224,225,3,48,24,0,225,
        226,5,3,0,0,226,261,1,0,0,0,227,228,5,53,0,0,228,229,5,2,0,0,229,
        230,3,44,22,0,230,231,5,3,0,0,231,261,1,0,0,0,232,233,5,61,0,0,233,
        234,5,2,0,0,234,235,3,46,23,0,235,236,5,3,0,0,236,261,1,0,0,0,237,
        238,5,60,0,0,238,239,5,2,0,0,239,240,3,46,23,0,240,241,5,3,0,0,241,
        261,1,0,0,0,242,243,5,59,0,0,243,244,5,2,0,0,244,261,5,3,0,0,245,
        246,5,58,0,0,246,247,5,2,0,0,247,261,5,3,0,0,248,249,5,54,0,0,249,
        250,5,2,0,0,250,261,5,3,0,0,251,252,5,55,0,0,252,253,5,2,0,0,253,
        261,5,3,0,0,254,255,5,56,0,0,255,256,5,2,0,0,256,261,5,3,0,0,257,
        258,5,57,0,0,258,259,5,2,0,0,259,261,5,3,0,0,260,189,1,0,0,0,260,
        194,1,0,0,0,260,199,1,0,0,0,260,204,1,0,0,0,260,207,1,0,0,0,260,
        210,1,0,0,0,260,213,1,0,0,0,260,216,1,0,0,0,260,219,1,0,0,0,260,
        222,1,0,0,0,260,227,1,0,0,0,260,232,1,0,0,0,260,237,1,0,0,0,260,
        242,1,0,0,0,260,245,1,0,0,0,260,248,1,0,0,0,260,251,1,0,0,0,260,
        254,1,0,0,0,260,257,1,0,0,0,261,19,1,0,0,0,262,263,5,32,0,0,263,
        264,5,2,0,0,264,265,3,22,11,0,265,266,5,3,0,0,266,280,1,0,0,0,267,
        268,5,33,0,0,268,269,5,2,0,0,269,270,3,22,11,0,270,271,5,3,0,0,271,
        280,1,0,0,0,272,273,5,34,0,0,273,274,5,2,0,0,274,275,3,22,11,0,275,
        276,5,4,0,0,276,277,3,22,11,0,277,278,5,3,0,0,278,280,1,0,0,0,279,
        262,1,0,0,0,279,267,1,0,0,0,279,272,1,0,0,0,280,21,1,0,0,0,281,286,
        5,64,0,0,282,283,3,38,19,0,283,284,5,35,0,0,284,286,1,0,0,0,285,
        281,1,0,0,0,285,282,1,0,0,0,286,23,1,0,0,0,287,288,5,20,0,0,288,
        293,3,26,13,0,289,290,5,4,0,0,290,292,3,26,13,0,291,289,1,0,0,0,
        292,295,1,0,0,0,293,291,1,0,0,0,293,294,1,0,0,0,294,25,1,0,0,0,295,
        293,1,0,0,0,296,303,3,50,25,0,297,298,3,28,14,0,298,299,5,2,0,0,
        299,300,3,50,25,0,300,301,5,3,0,0,301,303,1,0,0,0,302,296,1,0,0,
        0,302,297,1,0,0,0,303,27,1,0,0,0,304,305,7,1,0,0,305,29,1,0,0,0,
        306,307,5,19,0,0,307,312,3,32,16,0,308,309,5,4,0,0,309,311,3,32,
        16,0,310,308,1,0,0,0,311,314,1,0,0,0,312,310,1,0,0,0,312,313,1,0,
        0,0,313,31,1,0,0,0,314,312,1,0,0,0,315,316,5,21,0,0,316,317,5,2,
        0,0,317,350,5,3,0,0,318,319,5,21,0,0,319,320,5,2,0,0,320,321,5,22,
        0,0,321,322,3,50,25,0,322,323,5,3,0,0,323,350,1,0,0,0,324,325,5,
        22,0,0,325,326,5,2,0,0,326,327,3,50,25,0,327,328,5,3,0,0,328,350,
        1,0,0,0,329,330,5,23,0,0,330,331,5,2,0,0,331,332,3,50,25,0,332,333,
        5,3,0,0,333,350,1,0,0,0,334,335,5,24,0,0,335,336,5,2,0,0,336,337,
        3,50,25,0,337,338,5,3,0,0,338,350,1,0,0,0,339,340,5,25,0,0,340,341,
        5,2,0,0,341,342,3,50,25,0,342,343,5,3,0,0,343,350,1,0,0,0,344,345,
        5,26,0,0,345,346,5,2,0,0,346,347,3,50,25,0,347,348,5,3,0,0,348,350,
        1,0,0,0,349,315,1,0,0,0,349,318,1,0,0,0,349,324,1,0,0,0,349,329,
        1,0,0,0,349,334,1,0,0,0,349,339,1,0,0,0,349,344,1,0,0,0,350,33,1,
        0,0,0,351,352,5,27,0,0,352,354,3,50,25,0,353,355,7,2,0,0,354,353,
        1,0,0,0,354,355,1,0,0,0,355,363,1,0,0,0,356,357,5,4,0,0,357,359,
        3,50,25,0,358,360,7,2,0,0,359,358,1,0,0,0,359,360,1,0,0,0,360,362,
        1,0,0,0,361,356,1,0,0,0,362,365,1,0,0,0,363,361,1,0,0,0,363,364,
        1,0,0,0,364,35,1,0,0,0,365,363,1,0,0,0,366,367,5,30,0,0,367,370,
        3,42,21,0,368,369,5,31,0,0,369,371,3,42,21,0,370,368,1,0,0,0,370,
        371,1,0,0,0,371,37,1,0,0,0,372,373,3,42,21,0,373,374,3,40,20,0,374,
        39,1,0,0,0,375,376,7,3,0,0,376,41,1,0,0,0,377,378,5,62,0,0,378,43,
        1,0,0,0,379,380,7,4,0,0,380,45,1,0,0,0,381,382,7,4,0,0,382,47,1,
        0,0,0,383,384,5,63,0,0,384,49,1,0,0,0,385,386,5,63,0,0,386,51,1,
        0,0,0,29,57,60,66,69,72,75,78,81,89,104,113,117,121,125,142,152,
        184,186,260,279,285,293,302,312,349,354,359,363,370
    ]

class PrismQLParser ( Parser ):

    grammarFileName = "PrismQL.g4"

    atn = ATNDeserializer().deserialize(serializedATN())

    decisionsToDFA = [ DFA(ds, i) for i, ds in enumerate(atn.decisionToState) ]

    sharedContextCache = PredictionContextCache()

    literalNames = [ "<INVALID>", "';'", "'('", "')'", "','", "'{'", "'}'", 
                     "<INVALID>", "<INVALID>", "<INVALID>", "<INVALID>", 
                     "<INVALID>", "<INVALID>", "<INVALID>", "<INVALID>", 
                     "<INVALID>", "<INVALID>", "<INVALID>", "<INVALID>", 
                     "<INVALID>", "<INVALID>", "<INVALID>", "<INVALID>", 
                     "<INVALID>", "<INVALID>", "<INVALID>", "<INVALID>", 
                     "<INVALID>", "<INVALID>", "<INVALID>", "<INVALID>", 
                     "<INVALID>", "<INVALID>", "<INVALID>", "<INVALID>", 
                     "<INVALID>", "<INVALID>", "<INVALID>", "<INVALID>", 
                     "<INVALID>", "<INVALID>", "<INVALID>", "<INVALID>", 
                     "<INVALID>", "<INVALID>", "<INVALID>", "<INVALID>", 
                     "<INVALID>", "<INVALID>", "<INVALID>", "<INVALID>", 
                     "<INVALID>", "<INVALID>", "<INVALID>", "<INVALID>", 
                     "<INVALID>", "<INVALID>", "<INVALID>", "<INVALID>", 
                     "<INVALID>", "<INVALID>", "<INVALID>", "<INVALID>", 
                     "<INVALID>", "<INVALID>", "<INVALID>", "'*'" ]

    symbolicNames = [ "<INVALID>", "<INVALID>", "<INVALID>", "<INVALID>", 
                      "<INVALID>", "<INVALID>", "<INVALID>", "Select", "As", 
                      "InWin", "Within", "Unr", "Not", "And", "Or", "FollowedBy", 
                      "PrecededBy", "NotFollowedBy", "NotPrecededBy", "Aggregate", 
                      "GroupBy", "Count", "Distinct", "Sum", "Avg", "Min", 
                      "Max", "OrderBy", "Asc", "Desc", "Limit", "Offset", 
                      "Before", "After", "Between", "Ago", "Seconds", "Minutes", 
                      "Hours", "Days", "Weeks", "Months", "Years", "Contains", 
                      "From", "MentionsUser", "IsQuestion", "MentionsDate", 
                      "MentionsTime", "MentionsPlace", "MentionsOrg", "ContainsLink", 
                      "HasFeature", "HasWordOfDict", "HasTime", "HasLocation", 
                      "HasOrganization", "HasURL", "HasDate", "HasQuestion", 
                      "HasUserMentioned", "ByUser", "INTEGER", "STRING", 
                      "QUOTED_STRING", "VARIABLE", "WILDCARD", "WS" ]

    RULE_query = 0
    RULE_body = 1
    RULE_query_seq = 2
    RULE_query_seq_continuation = 3
    RULE_positional_op = 4
    RULE_restrictions = 5
    RULE_named_restriction = 6
    RULE_quantifier = 7
    RULE_restriction = 8
    RULE_condition = 9
    RULE_temporal_filter = 10
    RULE_timestamp = 11
    RULE_groupby_clause = 12
    RULE_groupby_field = 13
    RULE_temporal_group_func = 14
    RULE_aggregate_clause = 15
    RULE_aggregation_func = 16
    RULE_orderby_clause = 17
    RULE_limit_clause = 18
    RULE_time_value = 19
    RULE_time_unit = 20
    RULE_number = 21
    RULE_hdict = 22
    RULE_huser = 23
    RULE_feature_name = 24
    RULE_field_name = 25

    ruleNames =  [ "query", "body", "query_seq", "query_seq_continuation", 
                   "positional_op", "restrictions", "named_restriction", 
                   "quantifier", "restriction", "condition", "temporal_filter", 
                   "timestamp", "groupby_clause", "groupby_field", "temporal_group_func", 
                   "aggregate_clause", "aggregation_func", "orderby_clause", 
                   "limit_clause", "time_value", "time_unit", "number", 
                   "hdict", "huser", "feature_name", "field_name" ]

    EOF = Token.EOF
    T__0=1
    T__1=2
    T__2=3
    T__3=4
    T__4=5
    T__5=6
    Select=7
    As=8
    InWin=9
    Within=10
    Unr=11
    Not=12
    And=13
    Or=14
    FollowedBy=15
    PrecededBy=16
    NotFollowedBy=17
    NotPrecededBy=18
    Aggregate=19
    GroupBy=20
    Count=21
    Distinct=22
    Sum=23
    Avg=24
    Min=25
    Max=26
    OrderBy=27
    Asc=28
    Desc=29
    Limit=30
    Offset=31
    Before=32
    After=33
    Between=34
    Ago=35
    Seconds=36
    Minutes=37
    Hours=38
    Days=39
    Weeks=40
    Months=41
    Years=42
    Contains=43
    From=44
    MentionsUser=45
    IsQuestion=46
    MentionsDate=47
    MentionsTime=48
    MentionsPlace=49
    MentionsOrg=50
    ContainsLink=51
    HasFeature=52
    HasWordOfDict=53
    HasTime=54
    HasLocation=55
    HasOrganization=56
    HasURL=57
    HasDate=58
    HasQuestion=59
    HasUserMentioned=60
    ByUser=61
    INTEGER=62
    STRING=63
    QUOTED_STRING=64
    VARIABLE=65
    WILDCARD=66
    WS=67

    def __init__(self, input:TokenStream, output:TextIO = sys.stdout):
        super().__init__(input, output)
        self.checkVersion("4.13.1")
        self._interp = ParserATNSimulator(self, self.atn, self.decisionsToDFA, self.sharedContextCache)
        self._predicates = None




    class QueryContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def Select(self):
            return self.getToken(PrismQLParser.Select, 0)

        def body(self):
            return self.getTypedRuleContext(PrismQLParser.BodyContext,0)


        def getRuleIndex(self):
            return PrismQLParser.RULE_query

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitQuery" ):
                return visitor.visitQuery(self)
            else:
                return visitor.visitChildren(self)




    def query(self):

        localctx = PrismQLParser.QueryContext(self, self._ctx, self.state)
        self.enterRule(localctx, 0, self.RULE_query)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 52
            self.match(PrismQLParser.Select)
            self.state = 53
            self.body()
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class BodyContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def query_seq(self):
            return self.getTypedRuleContext(PrismQLParser.Query_seqContext,0)


        def restrictions(self):
            return self.getTypedRuleContext(PrismQLParser.RestrictionsContext,0)


        def InWin(self):
            return self.getToken(PrismQLParser.InWin, 0)

        def number(self):
            return self.getTypedRuleContext(PrismQLParser.NumberContext,0)


        def Within(self):
            return self.getToken(PrismQLParser.Within, 0)

        def time_value(self):
            return self.getTypedRuleContext(PrismQLParser.Time_valueContext,0)


        def temporal_filter(self):
            return self.getTypedRuleContext(PrismQLParser.Temporal_filterContext,0)


        def groupby_clause(self):
            return self.getTypedRuleContext(PrismQLParser.Groupby_clauseContext,0)


        def aggregate_clause(self):
            return self.getTypedRuleContext(PrismQLParser.Aggregate_clauseContext,0)


        def orderby_clause(self):
            return self.getTypedRuleContext(PrismQLParser.Orderby_clauseContext,0)


        def limit_clause(self):
            return self.getTypedRuleContext(PrismQLParser.Limit_clauseContext,0)


        def getRuleIndex(self):
            return PrismQLParser.RULE_body

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitBody" ):
                return visitor.visitBody(self)
            else:
                return visitor.visitChildren(self)




    def body(self):

        localctx = PrismQLParser.BodyContext(self, self._ctx, self.state)
        self.enterRule(localctx, 2, self.RULE_body)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 57
            self._errHandler.sync(self)
            la_ = self._interp.adaptivePredict(self._input,0,self._ctx)
            if la_ == 1:
                self.state = 55
                self.query_seq()
                pass

            elif la_ == 2:
                self.state = 56
                self.restrictions()
                pass


            self.state = 60
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if _la==1:
                self.state = 59
                self.match(PrismQLParser.T__0)


            self.state = 66
            self._errHandler.sync(self)
            token = self._input.LA(1)
            if token in [9]:
                self.state = 62
                self.match(PrismQLParser.InWin)
                self.state = 63
                self.number()
                pass
            elif token in [10]:
                self.state = 64
                self.match(PrismQLParser.Within)
                self.state = 65
                self.time_value()
                pass
            elif token in [3, 19, 20, 27, 30, 32, 33, 34]:
                pass
            else:
                pass
            self.state = 69
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if (((_la) & ~0x3f) == 0 and ((1 << _la) & 30064771072) != 0):
                self.state = 68
                self.temporal_filter()


            self.state = 72
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if _la==20:
                self.state = 71
                self.groupby_clause()


            self.state = 75
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if _la==19:
                self.state = 74
                self.aggregate_clause()


            self.state = 78
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if _la==27:
                self.state = 77
                self.orderby_clause()


            self.state = 81
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if _la==30:
                self.state = 80
                self.limit_clause()


        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class Query_seqContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def query(self):
            return self.getTypedRuleContext(PrismQLParser.QueryContext,0)


        def query_seq_continuation(self, i:int=None):
            if i is None:
                return self.getTypedRuleContexts(PrismQLParser.Query_seq_continuationContext)
            else:
                return self.getTypedRuleContext(PrismQLParser.Query_seq_continuationContext,i)


        def getRuleIndex(self):
            return PrismQLParser.RULE_query_seq

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitQuery_seq" ):
                return visitor.visitQuery_seq(self)
            else:
                return visitor.visitChildren(self)




    def query_seq(self):

        localctx = PrismQLParser.Query_seqContext(self, self._ctx, self.state)
        self.enterRule(localctx, 4, self.RULE_query_seq)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 83
            self.match(PrismQLParser.T__1)
            self.state = 84
            self.query()
            self.state = 85
            self.match(PrismQLParser.T__2)
            self.state = 89
            self._errHandler.sync(self)
            _alt = self._interp.adaptivePredict(self._input,8,self._ctx)
            while _alt!=2 and _alt!=ATN.INVALID_ALT_NUMBER:
                if _alt==1:
                    self.state = 86
                    self.query_seq_continuation() 
                self.state = 91
                self._errHandler.sync(self)
                _alt = self._interp.adaptivePredict(self._input,8,self._ctx)

        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class Query_seq_continuationContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser


        def getRuleIndex(self):
            return PrismQLParser.RULE_query_seq_continuation

     
        def copyFrom(self, ctx:ParserRuleContext):
            super().copyFrom(ctx)



    class UnorderedSubqueryContext(Query_seq_continuationContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a PrismQLParser.Query_seq_continuationContext
            super().__init__(parser)
            self.copyFrom(ctx)

        def query(self):
            return self.getTypedRuleContext(PrismQLParser.QueryContext,0)


        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitUnorderedSubquery" ):
                return visitor.visitUnorderedSubquery(self)
            else:
                return visitor.visitChildren(self)


    class PositionalSubqueryContext(Query_seq_continuationContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a PrismQLParser.Query_seq_continuationContext
            super().__init__(parser)
            self.copyFrom(ctx)

        def positional_op(self):
            return self.getTypedRuleContext(PrismQLParser.Positional_opContext,0)

        def query(self):
            return self.getTypedRuleContext(PrismQLParser.QueryContext,0)

        def Within(self):
            return self.getToken(PrismQLParser.Within, 0)
        def number(self):
            return self.getTypedRuleContext(PrismQLParser.NumberContext,0)


        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitPositionalSubquery" ):
                return visitor.visitPositionalSubquery(self)
            else:
                return visitor.visitChildren(self)



    def query_seq_continuation(self):

        localctx = PrismQLParser.Query_seq_continuationContext(self, self._ctx, self.state)
        self.enterRule(localctx, 6, self.RULE_query_seq_continuation)
        try:
            self.state = 104
            self._errHandler.sync(self)
            token = self._input.LA(1)
            if token in [1]:
                localctx = PrismQLParser.UnorderedSubqueryContext(self, localctx)
                self.enterOuterAlt(localctx, 1)
                self.state = 92
                self.match(PrismQLParser.T__0)
                self.state = 93
                self.match(PrismQLParser.T__1)
                self.state = 94
                self.query()
                self.state = 95
                self.match(PrismQLParser.T__2)
                pass
            elif token in [15, 16, 17, 18]:
                localctx = PrismQLParser.PositionalSubqueryContext(self, localctx)
                self.enterOuterAlt(localctx, 2)
                self.state = 97
                self.positional_op()
                self.state = 98
                self.match(PrismQLParser.T__1)
                self.state = 99
                self.query()
                self.state = 100
                self.match(PrismQLParser.T__2)
                self.state = 101
                self.match(PrismQLParser.Within)
                self.state = 102
                self.number()
                pass
            else:
                raise NoViableAltException(self)

        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class Positional_opContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def FollowedBy(self):
            return self.getToken(PrismQLParser.FollowedBy, 0)

        def PrecededBy(self):
            return self.getToken(PrismQLParser.PrecededBy, 0)

        def NotFollowedBy(self):
            return self.getToken(PrismQLParser.NotFollowedBy, 0)

        def NotPrecededBy(self):
            return self.getToken(PrismQLParser.NotPrecededBy, 0)

        def getRuleIndex(self):
            return PrismQLParser.RULE_positional_op

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitPositional_op" ):
                return visitor.visitPositional_op(self)
            else:
                return visitor.visitChildren(self)




    def positional_op(self):

        localctx = PrismQLParser.Positional_opContext(self, self._ctx, self.state)
        self.enterRule(localctx, 8, self.RULE_positional_op)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 106
            _la = self._input.LA(1)
            if not((((_la) & ~0x3f) == 0 and ((1 << _la) & 491520) != 0)):
                self._errHandler.recoverInline(self)
            else:
                self._errHandler.reportMatch(self)
                self.consume()
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class RestrictionsContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def named_restriction(self, i:int=None):
            if i is None:
                return self.getTypedRuleContexts(PrismQLParser.Named_restrictionContext)
            else:
                return self.getTypedRuleContext(PrismQLParser.Named_restrictionContext,i)


        def Unr(self):
            return self.getToken(PrismQLParser.Unr, 0)

        def getRuleIndex(self):
            return PrismQLParser.RULE_restrictions

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitRestrictions" ):
                return visitor.visitRestrictions(self)
            else:
                return visitor.visitChildren(self)




    def restrictions(self):

        localctx = PrismQLParser.RestrictionsContext(self, self._ctx, self.state)
        self.enterRule(localctx, 10, self.RULE_restrictions)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 108
            self.named_restriction()
            self.state = 113
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            while _la==4:
                self.state = 109
                self.match(PrismQLParser.T__3)
                self.state = 110
                self.named_restriction()
                self.state = 115
                self._errHandler.sync(self)
                _la = self._input.LA(1)

            self.state = 117
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if _la==11:
                self.state = 116
                self.match(PrismQLParser.Unr)


        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class Named_restrictionContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def restriction(self):
            return self.getTypedRuleContext(PrismQLParser.RestrictionContext,0)


        def quantifier(self):
            return self.getTypedRuleContext(PrismQLParser.QuantifierContext,0)


        def As(self):
            return self.getToken(PrismQLParser.As, 0)

        def QUOTED_STRING(self):
            return self.getToken(PrismQLParser.QUOTED_STRING, 0)

        def getRuleIndex(self):
            return PrismQLParser.RULE_named_restriction

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitNamed_restriction" ):
                return visitor.visitNamed_restriction(self)
            else:
                return visitor.visitChildren(self)




    def named_restriction(self):

        localctx = PrismQLParser.Named_restrictionContext(self, self._ctx, self.state)
        self.enterRule(localctx, 12, self.RULE_named_restriction)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 119
            self.restriction(0)
            self.state = 121
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if _la==5:
                self.state = 120
                self.quantifier()


            self.state = 125
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if _la==8:
                self.state = 123
                self.match(PrismQLParser.As)
                self.state = 124
                self.match(PrismQLParser.QUOTED_STRING)


        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class QuantifierContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser


        def getRuleIndex(self):
            return PrismQLParser.RULE_quantifier

     
        def copyFrom(self, ctx:ParserRuleContext):
            super().copyFrom(ctx)



    class AtLeastQuantifierContext(QuantifierContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a PrismQLParser.QuantifierContext
            super().__init__(parser)
            self.copyFrom(ctx)

        def number(self):
            return self.getTypedRuleContext(PrismQLParser.NumberContext,0)


        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitAtLeastQuantifier" ):
                return visitor.visitAtLeastQuantifier(self)
            else:
                return visitor.visitChildren(self)


    class ExactQuantifierContext(QuantifierContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a PrismQLParser.QuantifierContext
            super().__init__(parser)
            self.copyFrom(ctx)

        def number(self):
            return self.getTypedRuleContext(PrismQLParser.NumberContext,0)


        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitExactQuantifier" ):
                return visitor.visitExactQuantifier(self)
            else:
                return visitor.visitChildren(self)


    class RangeQuantifierContext(QuantifierContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a PrismQLParser.QuantifierContext
            super().__init__(parser)
            self.copyFrom(ctx)

        def number(self, i:int=None):
            if i is None:
                return self.getTypedRuleContexts(PrismQLParser.NumberContext)
            else:
                return self.getTypedRuleContext(PrismQLParser.NumberContext,i)


        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitRangeQuantifier" ):
                return visitor.visitRangeQuantifier(self)
            else:
                return visitor.visitChildren(self)



    def quantifier(self):

        localctx = PrismQLParser.QuantifierContext(self, self._ctx, self.state)
        self.enterRule(localctx, 14, self.RULE_quantifier)
        try:
            self.state = 142
            self._errHandler.sync(self)
            la_ = self._interp.adaptivePredict(self._input,14,self._ctx)
            if la_ == 1:
                localctx = PrismQLParser.ExactQuantifierContext(self, localctx)
                self.enterOuterAlt(localctx, 1)
                self.state = 127
                self.match(PrismQLParser.T__4)
                self.state = 128
                self.number()
                self.state = 129
                self.match(PrismQLParser.T__5)
                pass

            elif la_ == 2:
                localctx = PrismQLParser.AtLeastQuantifierContext(self, localctx)
                self.enterOuterAlt(localctx, 2)
                self.state = 131
                self.match(PrismQLParser.T__4)
                self.state = 132
                self.number()
                self.state = 133
                self.match(PrismQLParser.T__3)
                self.state = 134
                self.match(PrismQLParser.T__5)
                pass

            elif la_ == 3:
                localctx = PrismQLParser.RangeQuantifierContext(self, localctx)
                self.enterOuterAlt(localctx, 3)
                self.state = 136
                self.match(PrismQLParser.T__4)
                self.state = 137
                self.number()
                self.state = 138
                self.match(PrismQLParser.T__3)
                self.state = 139
                self.number()
                self.state = 140
                self.match(PrismQLParser.T__5)
                pass


        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class RestrictionContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def restriction(self, i:int=None):
            if i is None:
                return self.getTypedRuleContexts(PrismQLParser.RestrictionContext)
            else:
                return self.getTypedRuleContext(PrismQLParser.RestrictionContext,i)


        def Not(self):
            return self.getToken(PrismQLParser.Not, 0)

        def condition(self):
            return self.getTypedRuleContext(PrismQLParser.ConditionContext,0)


        def And(self):
            return self.getToken(PrismQLParser.And, 0)

        def Or(self):
            return self.getToken(PrismQLParser.Or, 0)

        def FollowedBy(self):
            return self.getToken(PrismQLParser.FollowedBy, 0)

        def Within(self):
            return self.getToken(PrismQLParser.Within, 0)

        def number(self):
            return self.getTypedRuleContext(PrismQLParser.NumberContext,0)


        def PrecededBy(self):
            return self.getToken(PrismQLParser.PrecededBy, 0)

        def NotFollowedBy(self):
            return self.getToken(PrismQLParser.NotFollowedBy, 0)

        def NotPrecededBy(self):
            return self.getToken(PrismQLParser.NotPrecededBy, 0)

        def getRuleIndex(self):
            return PrismQLParser.RULE_restriction

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitRestriction" ):
                return visitor.visitRestriction(self)
            else:
                return visitor.visitChildren(self)



    def restriction(self, _p:int=0):
        _parentctx = self._ctx
        _parentState = self.state
        localctx = PrismQLParser.RestrictionContext(self, self._ctx, _parentState)
        _prevctx = localctx
        _startState = 16
        self.enterRecursionRule(localctx, 16, self.RULE_restriction, _p)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 152
            self._errHandler.sync(self)
            token = self._input.LA(1)
            if token in [2]:
                self.state = 145
                self.match(PrismQLParser.T__1)
                self.state = 146
                self.restriction(0)
                self.state = 147
                self.match(PrismQLParser.T__2)
                pass
            elif token in [12]:
                self.state = 149
                self.match(PrismQLParser.Not)
                self.state = 150
                self.restriction(2)
                pass
            elif token in [43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61]:
                self.state = 151
                self.condition()
                pass
            else:
                raise NoViableAltException(self)

            self._ctx.stop = self._input.LT(-1)
            self.state = 186
            self._errHandler.sync(self)
            _alt = self._interp.adaptivePredict(self._input,17,self._ctx)
            while _alt!=2 and _alt!=ATN.INVALID_ALT_NUMBER:
                if _alt==1:
                    if self._parseListeners is not None:
                        self.triggerExitRuleEvent()
                    _prevctx = localctx
                    self.state = 184
                    self._errHandler.sync(self)
                    la_ = self._interp.adaptivePredict(self._input,16,self._ctx)
                    if la_ == 1:
                        localctx = PrismQLParser.RestrictionContext(self, _parentctx, _parentState)
                        self.pushNewRecursionContext(localctx, _startState, self.RULE_restriction)
                        self.state = 154
                        if not self.precpred(self._ctx, 9):
                            from antlr4.error.Errors import FailedPredicateException
                            raise FailedPredicateException(self, "self.precpred(self._ctx, 9)")
                        self.state = 155
                        self.match(PrismQLParser.And)
                        self.state = 156
                        self.restriction(10)
                        pass

                    elif la_ == 2:
                        localctx = PrismQLParser.RestrictionContext(self, _parentctx, _parentState)
                        self.pushNewRecursionContext(localctx, _startState, self.RULE_restriction)
                        self.state = 157
                        if not self.precpred(self._ctx, 8):
                            from antlr4.error.Errors import FailedPredicateException
                            raise FailedPredicateException(self, "self.precpred(self._ctx, 8)")
                        self.state = 158
                        self.match(PrismQLParser.Or)
                        self.state = 159
                        self.restriction(9)
                        pass

                    elif la_ == 3:
                        localctx = PrismQLParser.RestrictionContext(self, _parentctx, _parentState)
                        self.pushNewRecursionContext(localctx, _startState, self.RULE_restriction)
                        self.state = 160
                        if not self.precpred(self._ctx, 7):
                            from antlr4.error.Errors import FailedPredicateException
                            raise FailedPredicateException(self, "self.precpred(self._ctx, 7)")
                        self.state = 161
                        self.match(PrismQLParser.FollowedBy)
                        self.state = 162
                        self.restriction(0)
                        self.state = 163
                        self.match(PrismQLParser.Within)
                        self.state = 164
                        self.number()
                        pass

                    elif la_ == 4:
                        localctx = PrismQLParser.RestrictionContext(self, _parentctx, _parentState)
                        self.pushNewRecursionContext(localctx, _startState, self.RULE_restriction)
                        self.state = 166
                        if not self.precpred(self._ctx, 6):
                            from antlr4.error.Errors import FailedPredicateException
                            raise FailedPredicateException(self, "self.precpred(self._ctx, 6)")
                        self.state = 167
                        self.match(PrismQLParser.PrecededBy)
                        self.state = 168
                        self.restriction(0)
                        self.state = 169
                        self.match(PrismQLParser.Within)
                        self.state = 170
                        self.number()
                        pass

                    elif la_ == 5:
                        localctx = PrismQLParser.RestrictionContext(self, _parentctx, _parentState)
                        self.pushNewRecursionContext(localctx, _startState, self.RULE_restriction)
                        self.state = 172
                        if not self.precpred(self._ctx, 5):
                            from antlr4.error.Errors import FailedPredicateException
                            raise FailedPredicateException(self, "self.precpred(self._ctx, 5)")
                        self.state = 173
                        self.match(PrismQLParser.NotFollowedBy)
                        self.state = 174
                        self.restriction(0)
                        self.state = 175
                        self.match(PrismQLParser.Within)
                        self.state = 176
                        self.number()
                        pass

                    elif la_ == 6:
                        localctx = PrismQLParser.RestrictionContext(self, _parentctx, _parentState)
                        self.pushNewRecursionContext(localctx, _startState, self.RULE_restriction)
                        self.state = 178
                        if not self.precpred(self._ctx, 4):
                            from antlr4.error.Errors import FailedPredicateException
                            raise FailedPredicateException(self, "self.precpred(self._ctx, 4)")
                        self.state = 179
                        self.match(PrismQLParser.NotPrecededBy)
                        self.state = 180
                        self.restriction(0)
                        self.state = 181
                        self.match(PrismQLParser.Within)
                        self.state = 182
                        self.number()
                        pass

             
                self.state = 188
                self._errHandler.sync(self)
                _alt = self._interp.adaptivePredict(self._input,17,self._ctx)

        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.unrollRecursionContexts(_parentctx)
        return localctx


    class ConditionContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def Contains(self):
            return self.getToken(PrismQLParser.Contains, 0)

        def hdict(self):
            return self.getTypedRuleContext(PrismQLParser.HdictContext,0)


        def From(self):
            return self.getToken(PrismQLParser.From, 0)

        def huser(self):
            return self.getTypedRuleContext(PrismQLParser.HuserContext,0)


        def MentionsUser(self):
            return self.getToken(PrismQLParser.MentionsUser, 0)

        def IsQuestion(self):
            return self.getToken(PrismQLParser.IsQuestion, 0)

        def MentionsDate(self):
            return self.getToken(PrismQLParser.MentionsDate, 0)

        def MentionsTime(self):
            return self.getToken(PrismQLParser.MentionsTime, 0)

        def MentionsPlace(self):
            return self.getToken(PrismQLParser.MentionsPlace, 0)

        def MentionsOrg(self):
            return self.getToken(PrismQLParser.MentionsOrg, 0)

        def ContainsLink(self):
            return self.getToken(PrismQLParser.ContainsLink, 0)

        def HasFeature(self):
            return self.getToken(PrismQLParser.HasFeature, 0)

        def feature_name(self):
            return self.getTypedRuleContext(PrismQLParser.Feature_nameContext,0)


        def HasWordOfDict(self):
            return self.getToken(PrismQLParser.HasWordOfDict, 0)

        def ByUser(self):
            return self.getToken(PrismQLParser.ByUser, 0)

        def HasUserMentioned(self):
            return self.getToken(PrismQLParser.HasUserMentioned, 0)

        def HasQuestion(self):
            return self.getToken(PrismQLParser.HasQuestion, 0)

        def HasDate(self):
            return self.getToken(PrismQLParser.HasDate, 0)

        def HasTime(self):
            return self.getToken(PrismQLParser.HasTime, 0)

        def HasLocation(self):
            return self.getToken(PrismQLParser.HasLocation, 0)

        def HasOrganization(self):
            return self.getToken(PrismQLParser.HasOrganization, 0)

        def HasURL(self):
            return self.getToken(PrismQLParser.HasURL, 0)

        def getRuleIndex(self):
            return PrismQLParser.RULE_condition

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitCondition" ):
                return visitor.visitCondition(self)
            else:
                return visitor.visitChildren(self)




    def condition(self):

        localctx = PrismQLParser.ConditionContext(self, self._ctx, self.state)
        self.enterRule(localctx, 18, self.RULE_condition)
        try:
            self.state = 260
            self._errHandler.sync(self)
            token = self._input.LA(1)
            if token in [43]:
                self.enterOuterAlt(localctx, 1)
                self.state = 189
                self.match(PrismQLParser.Contains)
                self.state = 190
                self.match(PrismQLParser.T__1)
                self.state = 191
                self.hdict()
                self.state = 192
                self.match(PrismQLParser.T__2)
                pass
            elif token in [44]:
                self.enterOuterAlt(localctx, 2)
                self.state = 194
                self.match(PrismQLParser.From)
                self.state = 195
                self.match(PrismQLParser.T__1)
                self.state = 196
                self.huser()
                self.state = 197
                self.match(PrismQLParser.T__2)
                pass
            elif token in [45]:
                self.enterOuterAlt(localctx, 3)
                self.state = 199
                self.match(PrismQLParser.MentionsUser)
                self.state = 200
                self.match(PrismQLParser.T__1)
                self.state = 201
                self.huser()
                self.state = 202
                self.match(PrismQLParser.T__2)
                pass
            elif token in [46]:
                self.enterOuterAlt(localctx, 4)
                self.state = 204
                self.match(PrismQLParser.IsQuestion)
                self.state = 205
                self.match(PrismQLParser.T__1)
                self.state = 206
                self.match(PrismQLParser.T__2)
                pass
            elif token in [47]:
                self.enterOuterAlt(localctx, 5)
                self.state = 207
                self.match(PrismQLParser.MentionsDate)
                self.state = 208
                self.match(PrismQLParser.T__1)
                self.state = 209
                self.match(PrismQLParser.T__2)
                pass
            elif token in [48]:
                self.enterOuterAlt(localctx, 6)
                self.state = 210
                self.match(PrismQLParser.MentionsTime)
                self.state = 211
                self.match(PrismQLParser.T__1)
                self.state = 212
                self.match(PrismQLParser.T__2)
                pass
            elif token in [49]:
                self.enterOuterAlt(localctx, 7)
                self.state = 213
                self.match(PrismQLParser.MentionsPlace)
                self.state = 214
                self.match(PrismQLParser.T__1)
                self.state = 215
                self.match(PrismQLParser.T__2)
                pass
            elif token in [50]:
                self.enterOuterAlt(localctx, 8)
                self.state = 216
                self.match(PrismQLParser.MentionsOrg)
                self.state = 217
                self.match(PrismQLParser.T__1)
                self.state = 218
                self.match(PrismQLParser.T__2)
                pass
            elif token in [51]:
                self.enterOuterAlt(localctx, 9)
                self.state = 219
                self.match(PrismQLParser.ContainsLink)
                self.state = 220
                self.match(PrismQLParser.T__1)
                self.state = 221
                self.match(PrismQLParser.T__2)
                pass
            elif token in [52]:
                self.enterOuterAlt(localctx, 10)
                self.state = 222
                self.match(PrismQLParser.HasFeature)
                self.state = 223
                self.match(PrismQLParser.T__1)
                self.state = 224
                self.feature_name()
                self.state = 225
                self.match(PrismQLParser.T__2)
                pass
            elif token in [53]:
                self.enterOuterAlt(localctx, 11)
                self.state = 227
                self.match(PrismQLParser.HasWordOfDict)
                self.state = 228
                self.match(PrismQLParser.T__1)
                self.state = 229
                self.hdict()
                self.state = 230
                self.match(PrismQLParser.T__2)
                pass
            elif token in [61]:
                self.enterOuterAlt(localctx, 12)
                self.state = 232
                self.match(PrismQLParser.ByUser)
                self.state = 233
                self.match(PrismQLParser.T__1)
                self.state = 234
                self.huser()
                self.state = 235
                self.match(PrismQLParser.T__2)
                pass
            elif token in [60]:
                self.enterOuterAlt(localctx, 13)
                self.state = 237
                self.match(PrismQLParser.HasUserMentioned)
                self.state = 238
                self.match(PrismQLParser.T__1)
                self.state = 239
                self.huser()
                self.state = 240
                self.match(PrismQLParser.T__2)
                pass
            elif token in [59]:
                self.enterOuterAlt(localctx, 14)
                self.state = 242
                self.match(PrismQLParser.HasQuestion)
                self.state = 243
                self.match(PrismQLParser.T__1)
                self.state = 244
                self.match(PrismQLParser.T__2)
                pass
            elif token in [58]:
                self.enterOuterAlt(localctx, 15)
                self.state = 245
                self.match(PrismQLParser.HasDate)
                self.state = 246
                self.match(PrismQLParser.T__1)
                self.state = 247
                self.match(PrismQLParser.T__2)
                pass
            elif token in [54]:
                self.enterOuterAlt(localctx, 16)
                self.state = 248
                self.match(PrismQLParser.HasTime)
                self.state = 249
                self.match(PrismQLParser.T__1)
                self.state = 250
                self.match(PrismQLParser.T__2)
                pass
            elif token in [55]:
                self.enterOuterAlt(localctx, 17)
                self.state = 251
                self.match(PrismQLParser.HasLocation)
                self.state = 252
                self.match(PrismQLParser.T__1)
                self.state = 253
                self.match(PrismQLParser.T__2)
                pass
            elif token in [56]:
                self.enterOuterAlt(localctx, 18)
                self.state = 254
                self.match(PrismQLParser.HasOrganization)
                self.state = 255
                self.match(PrismQLParser.T__1)
                self.state = 256
                self.match(PrismQLParser.T__2)
                pass
            elif token in [57]:
                self.enterOuterAlt(localctx, 19)
                self.state = 257
                self.match(PrismQLParser.HasURL)
                self.state = 258
                self.match(PrismQLParser.T__1)
                self.state = 259
                self.match(PrismQLParser.T__2)
                pass
            else:
                raise NoViableAltException(self)

        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class Temporal_filterContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def Before(self):
            return self.getToken(PrismQLParser.Before, 0)

        def timestamp(self, i:int=None):
            if i is None:
                return self.getTypedRuleContexts(PrismQLParser.TimestampContext)
            else:
                return self.getTypedRuleContext(PrismQLParser.TimestampContext,i)


        def After(self):
            return self.getToken(PrismQLParser.After, 0)

        def Between(self):
            return self.getToken(PrismQLParser.Between, 0)

        def getRuleIndex(self):
            return PrismQLParser.RULE_temporal_filter

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitTemporal_filter" ):
                return visitor.visitTemporal_filter(self)
            else:
                return visitor.visitChildren(self)




    def temporal_filter(self):

        localctx = PrismQLParser.Temporal_filterContext(self, self._ctx, self.state)
        self.enterRule(localctx, 20, self.RULE_temporal_filter)
        try:
            self.state = 279
            self._errHandler.sync(self)
            token = self._input.LA(1)
            if token in [32]:
                self.enterOuterAlt(localctx, 1)
                self.state = 262
                self.match(PrismQLParser.Before)
                self.state = 263
                self.match(PrismQLParser.T__1)
                self.state = 264
                self.timestamp()
                self.state = 265
                self.match(PrismQLParser.T__2)
                pass
            elif token in [33]:
                self.enterOuterAlt(localctx, 2)
                self.state = 267
                self.match(PrismQLParser.After)
                self.state = 268
                self.match(PrismQLParser.T__1)
                self.state = 269
                self.timestamp()
                self.state = 270
                self.match(PrismQLParser.T__2)
                pass
            elif token in [34]:
                self.enterOuterAlt(localctx, 3)
                self.state = 272
                self.match(PrismQLParser.Between)
                self.state = 273
                self.match(PrismQLParser.T__1)
                self.state = 274
                self.timestamp()
                self.state = 275
                self.match(PrismQLParser.T__3)
                self.state = 276
                self.timestamp()
                self.state = 277
                self.match(PrismQLParser.T__2)
                pass
            else:
                raise NoViableAltException(self)

        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class TimestampContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser


        def getRuleIndex(self):
            return PrismQLParser.RULE_timestamp

     
        def copyFrom(self, ctx:ParserRuleContext):
            super().copyFrom(ctx)



    class RelativeTimestampContext(TimestampContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a PrismQLParser.TimestampContext
            super().__init__(parser)
            self.copyFrom(ctx)

        def time_value(self):
            return self.getTypedRuleContext(PrismQLParser.Time_valueContext,0)

        def Ago(self):
            return self.getToken(PrismQLParser.Ago, 0)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitRelativeTimestamp" ):
                return visitor.visitRelativeTimestamp(self)
            else:
                return visitor.visitChildren(self)


    class AbsoluteTimestampContext(TimestampContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a PrismQLParser.TimestampContext
            super().__init__(parser)
            self.copyFrom(ctx)

        def QUOTED_STRING(self):
            return self.getToken(PrismQLParser.QUOTED_STRING, 0)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitAbsoluteTimestamp" ):
                return visitor.visitAbsoluteTimestamp(self)
            else:
                return visitor.visitChildren(self)



    def timestamp(self):

        localctx = PrismQLParser.TimestampContext(self, self._ctx, self.state)
        self.enterRule(localctx, 22, self.RULE_timestamp)
        try:
            self.state = 285
            self._errHandler.sync(self)
            token = self._input.LA(1)
            if token in [64]:
                localctx = PrismQLParser.AbsoluteTimestampContext(self, localctx)
                self.enterOuterAlt(localctx, 1)
                self.state = 281
                self.match(PrismQLParser.QUOTED_STRING)
                pass
            elif token in [62]:
                localctx = PrismQLParser.RelativeTimestampContext(self, localctx)
                self.enterOuterAlt(localctx, 2)
                self.state = 282
                self.time_value()
                self.state = 283
                self.match(PrismQLParser.Ago)
                pass
            else:
                raise NoViableAltException(self)

        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class Groupby_clauseContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def GroupBy(self):
            return self.getToken(PrismQLParser.GroupBy, 0)

        def groupby_field(self, i:int=None):
            if i is None:
                return self.getTypedRuleContexts(PrismQLParser.Groupby_fieldContext)
            else:
                return self.getTypedRuleContext(PrismQLParser.Groupby_fieldContext,i)


        def getRuleIndex(self):
            return PrismQLParser.RULE_groupby_clause

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitGroupby_clause" ):
                return visitor.visitGroupby_clause(self)
            else:
                return visitor.visitChildren(self)




    def groupby_clause(self):

        localctx = PrismQLParser.Groupby_clauseContext(self, self._ctx, self.state)
        self.enterRule(localctx, 24, self.RULE_groupby_clause)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 287
            self.match(PrismQLParser.GroupBy)
            self.state = 288
            self.groupby_field()
            self.state = 293
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            while _la==4:
                self.state = 289
                self.match(PrismQLParser.T__3)
                self.state = 290
                self.groupby_field()
                self.state = 295
                self._errHandler.sync(self)
                _la = self._input.LA(1)

        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class Groupby_fieldContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser


        def getRuleIndex(self):
            return PrismQLParser.RULE_groupby_field

     
        def copyFrom(self, ctx:ParserRuleContext):
            super().copyFrom(ctx)



    class SimpleGroupByContext(Groupby_fieldContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a PrismQLParser.Groupby_fieldContext
            super().__init__(parser)
            self.copyFrom(ctx)

        def field_name(self):
            return self.getTypedRuleContext(PrismQLParser.Field_nameContext,0)


        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitSimpleGroupBy" ):
                return visitor.visitSimpleGroupBy(self)
            else:
                return visitor.visitChildren(self)


    class TemporalGroupByContext(Groupby_fieldContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a PrismQLParser.Groupby_fieldContext
            super().__init__(parser)
            self.copyFrom(ctx)

        def temporal_group_func(self):
            return self.getTypedRuleContext(PrismQLParser.Temporal_group_funcContext,0)

        def field_name(self):
            return self.getTypedRuleContext(PrismQLParser.Field_nameContext,0)


        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitTemporalGroupBy" ):
                return visitor.visitTemporalGroupBy(self)
            else:
                return visitor.visitChildren(self)



    def groupby_field(self):

        localctx = PrismQLParser.Groupby_fieldContext(self, self._ctx, self.state)
        self.enterRule(localctx, 26, self.RULE_groupby_field)
        try:
            self.state = 302
            self._errHandler.sync(self)
            token = self._input.LA(1)
            if token in [63]:
                localctx = PrismQLParser.SimpleGroupByContext(self, localctx)
                self.enterOuterAlt(localctx, 1)
                self.state = 296
                self.field_name()
                pass
            elif token in [38, 39, 40, 41, 42]:
                localctx = PrismQLParser.TemporalGroupByContext(self, localctx)
                self.enterOuterAlt(localctx, 2)
                self.state = 297
                self.temporal_group_func()
                self.state = 298
                self.match(PrismQLParser.T__1)
                self.state = 299
                self.field_name()
                self.state = 300
                self.match(PrismQLParser.T__2)
                pass
            else:
                raise NoViableAltException(self)

        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class Temporal_group_funcContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def Hours(self):
            return self.getToken(PrismQLParser.Hours, 0)

        def Days(self):
            return self.getToken(PrismQLParser.Days, 0)

        def Weeks(self):
            return self.getToken(PrismQLParser.Weeks, 0)

        def Months(self):
            return self.getToken(PrismQLParser.Months, 0)

        def Years(self):
            return self.getToken(PrismQLParser.Years, 0)

        def getRuleIndex(self):
            return PrismQLParser.RULE_temporal_group_func

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitTemporal_group_func" ):
                return visitor.visitTemporal_group_func(self)
            else:
                return visitor.visitChildren(self)




    def temporal_group_func(self):

        localctx = PrismQLParser.Temporal_group_funcContext(self, self._ctx, self.state)
        self.enterRule(localctx, 28, self.RULE_temporal_group_func)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 304
            _la = self._input.LA(1)
            if not((((_la) & ~0x3f) == 0 and ((1 << _la) & 8521215115264) != 0)):
                self._errHandler.recoverInline(self)
            else:
                self._errHandler.reportMatch(self)
                self.consume()
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class Aggregate_clauseContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def Aggregate(self):
            return self.getToken(PrismQLParser.Aggregate, 0)

        def aggregation_func(self, i:int=None):
            if i is None:
                return self.getTypedRuleContexts(PrismQLParser.Aggregation_funcContext)
            else:
                return self.getTypedRuleContext(PrismQLParser.Aggregation_funcContext,i)


        def getRuleIndex(self):
            return PrismQLParser.RULE_aggregate_clause

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitAggregate_clause" ):
                return visitor.visitAggregate_clause(self)
            else:
                return visitor.visitChildren(self)




    def aggregate_clause(self):

        localctx = PrismQLParser.Aggregate_clauseContext(self, self._ctx, self.state)
        self.enterRule(localctx, 30, self.RULE_aggregate_clause)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 306
            self.match(PrismQLParser.Aggregate)
            self.state = 307
            self.aggregation_func()
            self.state = 312
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            while _la==4:
                self.state = 308
                self.match(PrismQLParser.T__3)
                self.state = 309
                self.aggregation_func()
                self.state = 314
                self._errHandler.sync(self)
                _la = self._input.LA(1)

        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class Aggregation_funcContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser


        def getRuleIndex(self):
            return PrismQLParser.RULE_aggregation_func

     
        def copyFrom(self, ctx:ParserRuleContext):
            super().copyFrom(ctx)



    class DistinctValuesContext(Aggregation_funcContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a PrismQLParser.Aggregation_funcContext
            super().__init__(parser)
            self.copyFrom(ctx)

        def Distinct(self):
            return self.getToken(PrismQLParser.Distinct, 0)
        def field_name(self):
            return self.getTypedRuleContext(PrismQLParser.Field_nameContext,0)


        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitDistinctValues" ):
                return visitor.visitDistinctValues(self)
            else:
                return visitor.visitChildren(self)


    class SumFuncContext(Aggregation_funcContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a PrismQLParser.Aggregation_funcContext
            super().__init__(parser)
            self.copyFrom(ctx)

        def Sum(self):
            return self.getToken(PrismQLParser.Sum, 0)
        def field_name(self):
            return self.getTypedRuleContext(PrismQLParser.Field_nameContext,0)


        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitSumFunc" ):
                return visitor.visitSumFunc(self)
            else:
                return visitor.visitChildren(self)


    class MinFuncContext(Aggregation_funcContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a PrismQLParser.Aggregation_funcContext
            super().__init__(parser)
            self.copyFrom(ctx)

        def Min(self):
            return self.getToken(PrismQLParser.Min, 0)
        def field_name(self):
            return self.getTypedRuleContext(PrismQLParser.Field_nameContext,0)


        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitMinFunc" ):
                return visitor.visitMinFunc(self)
            else:
                return visitor.visitChildren(self)


    class MaxFuncContext(Aggregation_funcContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a PrismQLParser.Aggregation_funcContext
            super().__init__(parser)
            self.copyFrom(ctx)

        def Max(self):
            return self.getToken(PrismQLParser.Max, 0)
        def field_name(self):
            return self.getTypedRuleContext(PrismQLParser.Field_nameContext,0)


        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitMaxFunc" ):
                return visitor.visitMaxFunc(self)
            else:
                return visitor.visitChildren(self)


    class AvgFuncContext(Aggregation_funcContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a PrismQLParser.Aggregation_funcContext
            super().__init__(parser)
            self.copyFrom(ctx)

        def Avg(self):
            return self.getToken(PrismQLParser.Avg, 0)
        def field_name(self):
            return self.getTypedRuleContext(PrismQLParser.Field_nameContext,0)


        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitAvgFunc" ):
                return visitor.visitAvgFunc(self)
            else:
                return visitor.visitChildren(self)


    class CountDistinctContext(Aggregation_funcContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a PrismQLParser.Aggregation_funcContext
            super().__init__(parser)
            self.copyFrom(ctx)

        def Count(self):
            return self.getToken(PrismQLParser.Count, 0)
        def Distinct(self):
            return self.getToken(PrismQLParser.Distinct, 0)
        def field_name(self):
            return self.getTypedRuleContext(PrismQLParser.Field_nameContext,0)


        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitCountDistinct" ):
                return visitor.visitCountDistinct(self)
            else:
                return visitor.visitChildren(self)


    class CountAllContext(Aggregation_funcContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a PrismQLParser.Aggregation_funcContext
            super().__init__(parser)
            self.copyFrom(ctx)

        def Count(self):
            return self.getToken(PrismQLParser.Count, 0)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitCountAll" ):
                return visitor.visitCountAll(self)
            else:
                return visitor.visitChildren(self)



    def aggregation_func(self):

        localctx = PrismQLParser.Aggregation_funcContext(self, self._ctx, self.state)
        self.enterRule(localctx, 32, self.RULE_aggregation_func)
        try:
            self.state = 349
            self._errHandler.sync(self)
            la_ = self._interp.adaptivePredict(self._input,24,self._ctx)
            if la_ == 1:
                localctx = PrismQLParser.CountAllContext(self, localctx)
                self.enterOuterAlt(localctx, 1)
                self.state = 315
                self.match(PrismQLParser.Count)
                self.state = 316
                self.match(PrismQLParser.T__1)
                self.state = 317
                self.match(PrismQLParser.T__2)
                pass

            elif la_ == 2:
                localctx = PrismQLParser.CountDistinctContext(self, localctx)
                self.enterOuterAlt(localctx, 2)
                self.state = 318
                self.match(PrismQLParser.Count)
                self.state = 319
                self.match(PrismQLParser.T__1)
                self.state = 320
                self.match(PrismQLParser.Distinct)
                self.state = 321
                self.field_name()
                self.state = 322
                self.match(PrismQLParser.T__2)
                pass

            elif la_ == 3:
                localctx = PrismQLParser.DistinctValuesContext(self, localctx)
                self.enterOuterAlt(localctx, 3)
                self.state = 324
                self.match(PrismQLParser.Distinct)
                self.state = 325
                self.match(PrismQLParser.T__1)
                self.state = 326
                self.field_name()
                self.state = 327
                self.match(PrismQLParser.T__2)
                pass

            elif la_ == 4:
                localctx = PrismQLParser.SumFuncContext(self, localctx)
                self.enterOuterAlt(localctx, 4)
                self.state = 329
                self.match(PrismQLParser.Sum)
                self.state = 330
                self.match(PrismQLParser.T__1)
                self.state = 331
                self.field_name()
                self.state = 332
                self.match(PrismQLParser.T__2)
                pass

            elif la_ == 5:
                localctx = PrismQLParser.AvgFuncContext(self, localctx)
                self.enterOuterAlt(localctx, 5)
                self.state = 334
                self.match(PrismQLParser.Avg)
                self.state = 335
                self.match(PrismQLParser.T__1)
                self.state = 336
                self.field_name()
                self.state = 337
                self.match(PrismQLParser.T__2)
                pass

            elif la_ == 6:
                localctx = PrismQLParser.MinFuncContext(self, localctx)
                self.enterOuterAlt(localctx, 6)
                self.state = 339
                self.match(PrismQLParser.Min)
                self.state = 340
                self.match(PrismQLParser.T__1)
                self.state = 341
                self.field_name()
                self.state = 342
                self.match(PrismQLParser.T__2)
                pass

            elif la_ == 7:
                localctx = PrismQLParser.MaxFuncContext(self, localctx)
                self.enterOuterAlt(localctx, 7)
                self.state = 344
                self.match(PrismQLParser.Max)
                self.state = 345
                self.match(PrismQLParser.T__1)
                self.state = 346
                self.field_name()
                self.state = 347
                self.match(PrismQLParser.T__2)
                pass


        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class Orderby_clauseContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def OrderBy(self):
            return self.getToken(PrismQLParser.OrderBy, 0)

        def field_name(self, i:int=None):
            if i is None:
                return self.getTypedRuleContexts(PrismQLParser.Field_nameContext)
            else:
                return self.getTypedRuleContext(PrismQLParser.Field_nameContext,i)


        def Asc(self, i:int=None):
            if i is None:
                return self.getTokens(PrismQLParser.Asc)
            else:
                return self.getToken(PrismQLParser.Asc, i)

        def Desc(self, i:int=None):
            if i is None:
                return self.getTokens(PrismQLParser.Desc)
            else:
                return self.getToken(PrismQLParser.Desc, i)

        def getRuleIndex(self):
            return PrismQLParser.RULE_orderby_clause

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitOrderby_clause" ):
                return visitor.visitOrderby_clause(self)
            else:
                return visitor.visitChildren(self)




    def orderby_clause(self):

        localctx = PrismQLParser.Orderby_clauseContext(self, self._ctx, self.state)
        self.enterRule(localctx, 34, self.RULE_orderby_clause)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 351
            self.match(PrismQLParser.OrderBy)
            self.state = 352
            self.field_name()
            self.state = 354
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if _la==28 or _la==29:
                self.state = 353
                _la = self._input.LA(1)
                if not(_la==28 or _la==29):
                    self._errHandler.recoverInline(self)
                else:
                    self._errHandler.reportMatch(self)
                    self.consume()


            self.state = 363
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            while _la==4:
                self.state = 356
                self.match(PrismQLParser.T__3)
                self.state = 357
                self.field_name()
                self.state = 359
                self._errHandler.sync(self)
                _la = self._input.LA(1)
                if _la==28 or _la==29:
                    self.state = 358
                    _la = self._input.LA(1)
                    if not(_la==28 or _la==29):
                        self._errHandler.recoverInline(self)
                    else:
                        self._errHandler.reportMatch(self)
                        self.consume()


                self.state = 365
                self._errHandler.sync(self)
                _la = self._input.LA(1)

        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class Limit_clauseContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def Limit(self):
            return self.getToken(PrismQLParser.Limit, 0)

        def number(self, i:int=None):
            if i is None:
                return self.getTypedRuleContexts(PrismQLParser.NumberContext)
            else:
                return self.getTypedRuleContext(PrismQLParser.NumberContext,i)


        def Offset(self):
            return self.getToken(PrismQLParser.Offset, 0)

        def getRuleIndex(self):
            return PrismQLParser.RULE_limit_clause

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitLimit_clause" ):
                return visitor.visitLimit_clause(self)
            else:
                return visitor.visitChildren(self)




    def limit_clause(self):

        localctx = PrismQLParser.Limit_clauseContext(self, self._ctx, self.state)
        self.enterRule(localctx, 36, self.RULE_limit_clause)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 366
            self.match(PrismQLParser.Limit)
            self.state = 367
            self.number()
            self.state = 370
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if _la==31:
                self.state = 368
                self.match(PrismQLParser.Offset)
                self.state = 369
                self.number()


        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class Time_valueContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def number(self):
            return self.getTypedRuleContext(PrismQLParser.NumberContext,0)


        def time_unit(self):
            return self.getTypedRuleContext(PrismQLParser.Time_unitContext,0)


        def getRuleIndex(self):
            return PrismQLParser.RULE_time_value

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitTime_value" ):
                return visitor.visitTime_value(self)
            else:
                return visitor.visitChildren(self)




    def time_value(self):

        localctx = PrismQLParser.Time_valueContext(self, self._ctx, self.state)
        self.enterRule(localctx, 38, self.RULE_time_value)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 372
            self.number()
            self.state = 373
            self.time_unit()
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class Time_unitContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def Seconds(self):
            return self.getToken(PrismQLParser.Seconds, 0)

        def Minutes(self):
            return self.getToken(PrismQLParser.Minutes, 0)

        def Hours(self):
            return self.getToken(PrismQLParser.Hours, 0)

        def Days(self):
            return self.getToken(PrismQLParser.Days, 0)

        def Weeks(self):
            return self.getToken(PrismQLParser.Weeks, 0)

        def getRuleIndex(self):
            return PrismQLParser.RULE_time_unit

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitTime_unit" ):
                return visitor.visitTime_unit(self)
            else:
                return visitor.visitChildren(self)




    def time_unit(self):

        localctx = PrismQLParser.Time_unitContext(self, self._ctx, self.state)
        self.enterRule(localctx, 40, self.RULE_time_unit)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 375
            _la = self._input.LA(1)
            if not((((_la) & ~0x3f) == 0 and ((1 << _la) & 2130303778816) != 0)):
                self._errHandler.recoverInline(self)
            else:
                self._errHandler.reportMatch(self)
                self.consume()
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class NumberContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def INTEGER(self):
            return self.getToken(PrismQLParser.INTEGER, 0)

        def getRuleIndex(self):
            return PrismQLParser.RULE_number

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitNumber" ):
                return visitor.visitNumber(self)
            else:
                return visitor.visitChildren(self)




    def number(self):

        localctx = PrismQLParser.NumberContext(self, self._ctx, self.state)
        self.enterRule(localctx, 42, self.RULE_number)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 377
            self.match(PrismQLParser.INTEGER)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class HdictContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def STRING(self):
            return self.getToken(PrismQLParser.STRING, 0)

        def VARIABLE(self):
            return self.getToken(PrismQLParser.VARIABLE, 0)

        def WILDCARD(self):
            return self.getToken(PrismQLParser.WILDCARD, 0)

        def getRuleIndex(self):
            return PrismQLParser.RULE_hdict

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitHdict" ):
                return visitor.visitHdict(self)
            else:
                return visitor.visitChildren(self)




    def hdict(self):

        localctx = PrismQLParser.HdictContext(self, self._ctx, self.state)
        self.enterRule(localctx, 44, self.RULE_hdict)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 379
            _la = self._input.LA(1)
            if not(((((_la - 63)) & ~0x3f) == 0 and ((1 << (_la - 63)) & 13) != 0)):
                self._errHandler.recoverInline(self)
            else:
                self._errHandler.reportMatch(self)
                self.consume()
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class HuserContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def STRING(self):
            return self.getToken(PrismQLParser.STRING, 0)

        def VARIABLE(self):
            return self.getToken(PrismQLParser.VARIABLE, 0)

        def WILDCARD(self):
            return self.getToken(PrismQLParser.WILDCARD, 0)

        def getRuleIndex(self):
            return PrismQLParser.RULE_huser

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitHuser" ):
                return visitor.visitHuser(self)
            else:
                return visitor.visitChildren(self)




    def huser(self):

        localctx = PrismQLParser.HuserContext(self, self._ctx, self.state)
        self.enterRule(localctx, 46, self.RULE_huser)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 381
            _la = self._input.LA(1)
            if not(((((_la - 63)) & ~0x3f) == 0 and ((1 << (_la - 63)) & 13) != 0)):
                self._errHandler.recoverInline(self)
            else:
                self._errHandler.reportMatch(self)
                self.consume()
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class Feature_nameContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def STRING(self):
            return self.getToken(PrismQLParser.STRING, 0)

        def getRuleIndex(self):
            return PrismQLParser.RULE_feature_name

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitFeature_name" ):
                return visitor.visitFeature_name(self)
            else:
                return visitor.visitChildren(self)




    def feature_name(self):

        localctx = PrismQLParser.Feature_nameContext(self, self._ctx, self.state)
        self.enterRule(localctx, 48, self.RULE_feature_name)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 383
            self.match(PrismQLParser.STRING)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class Field_nameContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def STRING(self):
            return self.getToken(PrismQLParser.STRING, 0)

        def getRuleIndex(self):
            return PrismQLParser.RULE_field_name

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitField_name" ):
                return visitor.visitField_name(self)
            else:
                return visitor.visitChildren(self)




    def field_name(self):

        localctx = PrismQLParser.Field_nameContext(self, self._ctx, self.state)
        self.enterRule(localctx, 50, self.RULE_field_name)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 385
            self.match(PrismQLParser.STRING)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx



    def sempred(self, localctx:RuleContext, ruleIndex:int, predIndex:int):
        if self._predicates == None:
            self._predicates = dict()
        self._predicates[8] = self.restriction_sempred
        pred = self._predicates.get(ruleIndex, None)
        if pred is None:
            raise Exception("No predicate with index:" + str(ruleIndex))
        else:
            return pred(localctx, predIndex)

    def restriction_sempred(self, localctx:RestrictionContext, predIndex:int):
            if predIndex == 0:
                return self.precpred(self._ctx, 9)
         

            if predIndex == 1:
                return self.precpred(self._ctx, 8)
         

            if predIndex == 2:
                return self.precpred(self._ctx, 7)
         

            if predIndex == 3:
                return self.precpred(self._ctx, 6)
         

            if predIndex == 4:
                return self.precpred(self._ctx, 5)
         

            if predIndex == 5:
                return self.precpred(self._ctx, 4)
         




