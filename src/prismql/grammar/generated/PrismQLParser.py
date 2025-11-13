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
        4,1,71,435,2,0,7,0,2,1,7,1,2,2,7,2,2,3,7,3,2,4,7,4,2,5,7,5,2,6,7,
        6,2,7,7,7,2,8,7,8,2,9,7,9,2,10,7,10,2,11,7,11,2,12,7,12,2,13,7,13,
        2,14,7,14,2,15,7,15,2,16,7,16,2,17,7,17,2,18,7,18,2,19,7,19,2,20,
        7,20,2,21,7,21,2,22,7,22,2,23,7,23,2,24,7,24,2,25,7,25,1,0,1,0,1,
        0,1,1,1,1,3,1,58,8,1,1,1,3,1,61,8,1,1,1,1,1,1,1,1,1,1,1,1,1,3,1,
        69,8,1,1,1,3,1,72,8,1,1,1,3,1,75,8,1,1,1,3,1,78,8,1,1,1,3,1,81,8,
        1,1,1,3,1,84,8,1,1,2,1,2,1,2,1,2,5,2,90,8,2,10,2,12,2,93,9,2,1,3,
        1,3,1,3,1,3,1,3,1,3,1,3,1,3,1,3,1,3,1,3,1,3,1,3,1,3,1,3,1,3,1,3,
        1,3,1,3,3,3,114,8,3,1,4,1,4,1,5,1,5,1,5,5,5,121,8,5,10,5,12,5,124,
        9,5,1,5,3,5,127,8,5,1,6,1,6,3,6,131,8,6,1,6,1,6,3,6,135,8,6,1,7,
        1,7,1,7,1,7,1,7,1,7,1,7,1,7,1,7,1,7,1,7,1,7,1,7,1,7,1,7,3,7,152,
        8,7,1,8,1,8,1,8,1,8,1,8,1,8,1,8,1,8,3,8,162,8,8,1,8,1,8,1,8,1,8,
        1,8,1,8,1,8,1,8,1,8,1,8,1,8,1,8,1,8,1,8,1,8,1,8,1,8,1,8,1,8,1,8,
        1,8,1,8,1,8,1,8,1,8,1,8,1,8,1,8,1,8,1,8,1,8,1,8,1,8,1,8,1,8,1,8,
        1,8,1,8,1,8,1,8,1,8,1,8,1,8,1,8,1,8,1,8,1,8,1,8,1,8,1,8,1,8,1,8,
        1,8,1,8,5,8,218,8,8,10,8,12,8,221,9,8,1,9,1,9,1,9,1,9,1,9,1,9,1,
        9,1,9,1,9,1,9,1,9,1,9,1,9,1,9,1,9,1,9,1,9,1,9,1,9,1,9,1,9,1,9,1,
        9,1,9,1,9,1,9,1,9,1,9,1,9,1,9,1,9,1,9,1,9,1,9,1,9,1,9,1,9,1,9,1,
        9,1,9,1,9,1,9,1,9,1,9,1,9,1,9,1,9,1,9,1,9,1,9,1,9,1,9,1,9,1,9,1,
        9,1,9,1,9,1,9,1,9,1,9,1,9,1,9,1,9,1,9,1,9,1,9,1,9,1,9,1,9,1,9,1,
        9,1,9,1,9,1,9,1,9,1,9,1,9,1,9,1,9,1,9,1,9,1,9,1,9,1,9,1,9,3,9,308,
        8,9,1,10,1,10,1,10,1,10,1,10,1,10,1,10,1,10,1,10,1,10,1,10,1,10,
        1,10,1,10,1,10,1,10,1,10,3,10,327,8,10,1,11,1,11,1,11,1,11,3,11,
        333,8,11,1,12,1,12,1,12,1,12,5,12,339,8,12,10,12,12,12,342,9,12,
        1,13,1,13,1,13,1,13,1,13,1,13,3,13,350,8,13,1,14,1,14,1,15,1,15,
        1,15,1,15,5,15,358,8,15,10,15,12,15,361,9,15,1,16,1,16,1,16,1,16,
        1,16,1,16,1,16,1,16,1,16,1,16,1,16,1,16,1,16,1,16,1,16,1,16,1,16,
        1,16,1,16,1,16,1,16,1,16,1,16,1,16,1,16,1,16,1,16,1,16,1,16,1,16,
        1,16,1,16,1,16,1,16,3,16,397,8,16,1,17,1,17,1,17,3,17,402,8,17,1,
        17,1,17,1,17,3,17,407,8,17,5,17,409,8,17,10,17,12,17,412,9,17,1,
        18,1,18,1,18,1,18,3,18,418,8,18,1,19,1,19,1,19,1,20,1,20,1,21,1,
        21,1,22,1,22,1,23,1,23,1,24,1,24,1,25,1,25,1,25,0,1,16,26,0,2,4,
        6,8,10,12,14,16,18,20,22,24,26,28,30,32,34,36,38,40,42,44,46,48,
        50,0,5,1,0,16,19,1,0,39,43,1,0,29,30,1,0,37,41,2,0,67,67,69,70,476,
        0,52,1,0,0,0,2,57,1,0,0,0,4,85,1,0,0,0,6,113,1,0,0,0,8,115,1,0,0,
        0,10,117,1,0,0,0,12,128,1,0,0,0,14,151,1,0,0,0,16,161,1,0,0,0,18,
        307,1,0,0,0,20,326,1,0,0,0,22,332,1,0,0,0,24,334,1,0,0,0,26,349,
        1,0,0,0,28,351,1,0,0,0,30,353,1,0,0,0,32,396,1,0,0,0,34,398,1,0,
        0,0,36,413,1,0,0,0,38,419,1,0,0,0,40,422,1,0,0,0,42,424,1,0,0,0,
        44,426,1,0,0,0,46,428,1,0,0,0,48,430,1,0,0,0,50,432,1,0,0,0,52,53,
        5,7,0,0,53,54,3,2,1,0,54,1,1,0,0,0,55,58,3,4,2,0,56,58,3,10,5,0,
        57,55,1,0,0,0,57,56,1,0,0,0,58,60,1,0,0,0,59,61,5,1,0,0,60,59,1,
        0,0,0,60,61,1,0,0,0,61,68,1,0,0,0,62,63,5,9,0,0,63,69,3,42,21,0,
        64,65,5,10,0,0,65,69,3,42,21,0,66,67,5,11,0,0,67,69,3,38,19,0,68,
        62,1,0,0,0,68,64,1,0,0,0,68,66,1,0,0,0,68,69,1,0,0,0,69,71,1,0,0,
        0,70,72,3,20,10,0,71,70,1,0,0,0,71,72,1,0,0,0,72,74,1,0,0,0,73,75,
        3,24,12,0,74,73,1,0,0,0,74,75,1,0,0,0,75,77,1,0,0,0,76,78,3,30,15,
        0,77,76,1,0,0,0,77,78,1,0,0,0,78,80,1,0,0,0,79,81,3,34,17,0,80,79,
        1,0,0,0,80,81,1,0,0,0,81,83,1,0,0,0,82,84,3,36,18,0,83,82,1,0,0,
        0,83,84,1,0,0,0,84,3,1,0,0,0,85,86,5,2,0,0,86,87,3,0,0,0,87,91,5,
        3,0,0,88,90,3,6,3,0,89,88,1,0,0,0,90,93,1,0,0,0,91,89,1,0,0,0,91,
        92,1,0,0,0,92,5,1,0,0,0,93,91,1,0,0,0,94,95,5,1,0,0,95,96,5,2,0,
        0,96,97,3,0,0,0,97,98,5,3,0,0,98,114,1,0,0,0,99,100,3,8,4,0,100,
        101,5,2,0,0,101,102,3,0,0,0,102,103,5,3,0,0,103,104,5,9,0,0,104,
        105,3,42,21,0,105,114,1,0,0,0,106,107,3,8,4,0,107,108,5,2,0,0,108,
        109,3,0,0,0,109,110,5,3,0,0,110,111,5,11,0,0,111,112,3,42,21,0,112,
        114,1,0,0,0,113,94,1,0,0,0,113,99,1,0,0,0,113,106,1,0,0,0,114,7,
        1,0,0,0,115,116,7,0,0,0,116,9,1,0,0,0,117,122,3,12,6,0,118,119,5,
        4,0,0,119,121,3,12,6,0,120,118,1,0,0,0,121,124,1,0,0,0,122,120,1,
        0,0,0,122,123,1,0,0,0,123,126,1,0,0,0,124,122,1,0,0,0,125,127,5,
        12,0,0,126,125,1,0,0,0,126,127,1,0,0,0,127,11,1,0,0,0,128,130,3,
        16,8,0,129,131,3,14,7,0,130,129,1,0,0,0,130,131,1,0,0,0,131,134,
        1,0,0,0,132,133,5,8,0,0,133,135,5,68,0,0,134,132,1,0,0,0,134,135,
        1,0,0,0,135,13,1,0,0,0,136,137,5,5,0,0,137,138,3,42,21,0,138,139,
        5,6,0,0,139,152,1,0,0,0,140,141,5,5,0,0,141,142,3,42,21,0,142,143,
        5,4,0,0,143,144,5,6,0,0,144,152,1,0,0,0,145,146,5,5,0,0,146,147,
        3,42,21,0,147,148,5,4,0,0,148,149,3,42,21,0,149,150,5,6,0,0,150,
        152,1,0,0,0,151,136,1,0,0,0,151,140,1,0,0,0,151,145,1,0,0,0,152,
        15,1,0,0,0,153,154,6,8,-1,0,154,155,5,2,0,0,155,156,3,16,8,0,156,
        157,5,3,0,0,157,162,1,0,0,0,158,159,5,13,0,0,159,162,3,16,8,2,160,
        162,3,18,9,0,161,153,1,0,0,0,161,158,1,0,0,0,161,160,1,0,0,0,162,
        219,1,0,0,0,163,164,10,13,0,0,164,165,5,14,0,0,165,218,3,16,8,14,
        166,167,10,12,0,0,167,168,5,15,0,0,168,218,3,16,8,13,169,170,10,
        11,0,0,170,171,5,16,0,0,171,172,3,16,8,0,172,173,5,9,0,0,173,174,
        3,42,21,0,174,218,1,0,0,0,175,176,10,10,0,0,176,177,5,17,0,0,177,
        178,3,16,8,0,178,179,5,9,0,0,179,180,3,42,21,0,180,218,1,0,0,0,181,
        182,10,9,0,0,182,183,5,18,0,0,183,184,3,16,8,0,184,185,5,9,0,0,185,
        186,3,42,21,0,186,218,1,0,0,0,187,188,10,8,0,0,188,189,5,19,0,0,
        189,190,3,16,8,0,190,191,5,9,0,0,191,192,3,42,21,0,192,218,1,0,0,
        0,193,194,10,7,0,0,194,195,5,16,0,0,195,196,3,16,8,0,196,197,5,11,
        0,0,197,198,3,42,21,0,198,218,1,0,0,0,199,200,10,6,0,0,200,201,5,
        17,0,0,201,202,3,16,8,0,202,203,5,11,0,0,203,204,3,42,21,0,204,218,
        1,0,0,0,205,206,10,5,0,0,206,207,5,18,0,0,207,208,3,16,8,0,208,209,
        5,11,0,0,209,210,3,42,21,0,210,218,1,0,0,0,211,212,10,4,0,0,212,
        213,5,19,0,0,213,214,3,16,8,0,214,215,5,11,0,0,215,216,3,42,21,0,
        216,218,1,0,0,0,217,163,1,0,0,0,217,166,1,0,0,0,217,169,1,0,0,0,
        217,175,1,0,0,0,217,181,1,0,0,0,217,187,1,0,0,0,217,193,1,0,0,0,
        217,199,1,0,0,0,217,205,1,0,0,0,217,211,1,0,0,0,218,221,1,0,0,0,
        219,217,1,0,0,0,219,220,1,0,0,0,220,17,1,0,0,0,221,219,1,0,0,0,222,
        223,5,44,0,0,223,224,5,2,0,0,224,225,3,44,22,0,225,226,5,3,0,0,226,
        308,1,0,0,0,227,228,5,45,0,0,228,229,5,2,0,0,229,230,3,44,22,0,230,
        231,5,3,0,0,231,308,1,0,0,0,232,233,5,46,0,0,233,234,5,2,0,0,234,
        235,5,68,0,0,235,308,5,3,0,0,236,237,5,47,0,0,237,238,5,2,0,0,238,
        239,3,46,23,0,239,240,5,3,0,0,240,308,1,0,0,0,241,242,5,48,0,0,242,
        243,5,2,0,0,243,244,3,46,23,0,244,245,5,3,0,0,245,308,1,0,0,0,246,
        247,5,49,0,0,247,248,5,2,0,0,248,308,5,3,0,0,249,250,5,50,0,0,250,
        251,5,2,0,0,251,308,5,3,0,0,252,253,5,51,0,0,253,254,5,2,0,0,254,
        308,5,3,0,0,255,256,5,52,0,0,256,257,5,2,0,0,257,308,5,3,0,0,258,
        259,5,53,0,0,259,260,5,2,0,0,260,308,5,3,0,0,261,262,5,54,0,0,262,
        263,5,2,0,0,263,308,5,3,0,0,264,265,5,55,0,0,265,266,5,2,0,0,266,
        267,3,48,24,0,267,268,5,3,0,0,268,308,1,0,0,0,269,270,5,56,0,0,270,
        271,5,2,0,0,271,272,3,48,24,0,272,273,5,3,0,0,273,308,1,0,0,0,274,
        275,5,57,0,0,275,276,5,2,0,0,276,277,3,44,22,0,277,278,5,3,0,0,278,
        308,1,0,0,0,279,280,5,65,0,0,280,281,5,2,0,0,281,282,3,46,23,0,282,
        283,5,3,0,0,283,308,1,0,0,0,284,285,5,64,0,0,285,286,5,2,0,0,286,
        287,3,46,23,0,287,288,5,3,0,0,288,308,1,0,0,0,289,290,5,63,0,0,290,
        291,5,2,0,0,291,308,5,3,0,0,292,293,5,62,0,0,293,294,5,2,0,0,294,
        308,5,3,0,0,295,296,5,58,0,0,296,297,5,2,0,0,297,308,5,3,0,0,298,
        299,5,59,0,0,299,300,5,2,0,0,300,308,5,3,0,0,301,302,5,60,0,0,302,
        303,5,2,0,0,303,308,5,3,0,0,304,305,5,61,0,0,305,306,5,2,0,0,306,
        308,5,3,0,0,307,222,1,0,0,0,307,227,1,0,0,0,307,232,1,0,0,0,307,
        236,1,0,0,0,307,241,1,0,0,0,307,246,1,0,0,0,307,249,1,0,0,0,307,
        252,1,0,0,0,307,255,1,0,0,0,307,258,1,0,0,0,307,261,1,0,0,0,307,
        264,1,0,0,0,307,269,1,0,0,0,307,274,1,0,0,0,307,279,1,0,0,0,307,
        284,1,0,0,0,307,289,1,0,0,0,307,292,1,0,0,0,307,295,1,0,0,0,307,
        298,1,0,0,0,307,301,1,0,0,0,307,304,1,0,0,0,308,19,1,0,0,0,309,310,
        5,33,0,0,310,311,5,2,0,0,311,312,3,22,11,0,312,313,5,3,0,0,313,327,
        1,0,0,0,314,315,5,34,0,0,315,316,5,2,0,0,316,317,3,22,11,0,317,318,
        5,3,0,0,318,327,1,0,0,0,319,320,5,35,0,0,320,321,5,2,0,0,321,322,
        3,22,11,0,322,323,5,4,0,0,323,324,3,22,11,0,324,325,5,3,0,0,325,
        327,1,0,0,0,326,309,1,0,0,0,326,314,1,0,0,0,326,319,1,0,0,0,327,
        21,1,0,0,0,328,333,5,68,0,0,329,330,3,38,19,0,330,331,5,36,0,0,331,
        333,1,0,0,0,332,328,1,0,0,0,332,329,1,0,0,0,333,23,1,0,0,0,334,335,
        5,21,0,0,335,340,3,26,13,0,336,337,5,4,0,0,337,339,3,26,13,0,338,
        336,1,0,0,0,339,342,1,0,0,0,340,338,1,0,0,0,340,341,1,0,0,0,341,
        25,1,0,0,0,342,340,1,0,0,0,343,350,3,50,25,0,344,345,3,28,14,0,345,
        346,5,2,0,0,346,347,3,50,25,0,347,348,5,3,0,0,348,350,1,0,0,0,349,
        343,1,0,0,0,349,344,1,0,0,0,350,27,1,0,0,0,351,352,7,1,0,0,352,29,
        1,0,0,0,353,354,5,20,0,0,354,359,3,32,16,0,355,356,5,4,0,0,356,358,
        3,32,16,0,357,355,1,0,0,0,358,361,1,0,0,0,359,357,1,0,0,0,359,360,
        1,0,0,0,360,31,1,0,0,0,361,359,1,0,0,0,362,363,5,22,0,0,363,364,
        5,2,0,0,364,397,5,3,0,0,365,366,5,22,0,0,366,367,5,2,0,0,367,368,
        5,23,0,0,368,369,3,50,25,0,369,370,5,3,0,0,370,397,1,0,0,0,371,372,
        5,23,0,0,372,373,5,2,0,0,373,374,3,50,25,0,374,375,5,3,0,0,375,397,
        1,0,0,0,376,377,5,24,0,0,377,378,5,2,0,0,378,379,3,50,25,0,379,380,
        5,3,0,0,380,397,1,0,0,0,381,382,5,25,0,0,382,383,5,2,0,0,383,384,
        3,50,25,0,384,385,5,3,0,0,385,397,1,0,0,0,386,387,5,26,0,0,387,388,
        5,2,0,0,388,389,3,50,25,0,389,390,5,3,0,0,390,397,1,0,0,0,391,392,
        5,27,0,0,392,393,5,2,0,0,393,394,3,50,25,0,394,395,5,3,0,0,395,397,
        1,0,0,0,396,362,1,0,0,0,396,365,1,0,0,0,396,371,1,0,0,0,396,376,
        1,0,0,0,396,381,1,0,0,0,396,386,1,0,0,0,396,391,1,0,0,0,397,33,1,
        0,0,0,398,399,5,28,0,0,399,401,3,50,25,0,400,402,7,2,0,0,401,400,
        1,0,0,0,401,402,1,0,0,0,402,410,1,0,0,0,403,404,5,4,0,0,404,406,
        3,50,25,0,405,407,7,2,0,0,406,405,1,0,0,0,406,407,1,0,0,0,407,409,
        1,0,0,0,408,403,1,0,0,0,409,412,1,0,0,0,410,408,1,0,0,0,410,411,
        1,0,0,0,411,35,1,0,0,0,412,410,1,0,0,0,413,414,5,31,0,0,414,417,
        3,42,21,0,415,416,5,32,0,0,416,418,3,42,21,0,417,415,1,0,0,0,417,
        418,1,0,0,0,418,37,1,0,0,0,419,420,3,42,21,0,420,421,3,40,20,0,421,
        39,1,0,0,0,422,423,7,3,0,0,423,41,1,0,0,0,424,425,5,66,0,0,425,43,
        1,0,0,0,426,427,7,4,0,0,427,45,1,0,0,0,428,429,7,4,0,0,429,47,1,
        0,0,0,430,431,5,67,0,0,431,49,1,0,0,0,432,433,5,67,0,0,433,51,1,
        0,0,0,29,57,60,68,71,74,77,80,83,91,113,122,126,130,134,151,161,
        217,219,307,326,332,340,349,359,396,401,406,410,417
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
                     "<INVALID>", "<INVALID>", "<INVALID>", "<INVALID>", 
                     "<INVALID>", "<INVALID>", "<INVALID>", "'*'" ]

    symbolicNames = [ "<INVALID>", "<INVALID>", "<INVALID>", "<INVALID>", 
                      "<INVALID>", "<INVALID>", "<INVALID>", "Select", "As", 
                      "InWindow", "InWin", "Within", "Unr", "Not", "And", 
                      "Or", "FollowedBy", "PrecededBy", "NotFollowedBy", 
                      "NotPrecededBy", "Aggregate", "GroupBy", "Count", 
                      "Distinct", "Sum", "Avg", "Min", "Max", "OrderBy", 
                      "Asc", "Desc", "Limit", "Offset", "Before", "After", 
                      "Between", "Ago", "Seconds", "Minutes", "Hours", "Days", 
                      "Weeks", "Months", "Years", "Contains", "ContainsTokens", 
                      "ContainsPhrase", "From", "MentionsUser", "IsQuestion", 
                      "MentionsDate", "MentionsTime", "MentionsPlace", "MentionsOrg", 
                      "ContainsLink", "HasFeature", "LabeledAs", "HasWordOfDict", 
                      "HasTime", "HasLocation", "HasOrganization", "HasURL", 
                      "HasDate", "HasQuestion", "HasUserMentioned", "ByUser", 
                      "INTEGER", "STRING", "QUOTED_STRING", "VARIABLE", 
                      "WILDCARD", "WS" ]

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
    InWindow=9
    InWin=10
    Within=11
    Unr=12
    Not=13
    And=14
    Or=15
    FollowedBy=16
    PrecededBy=17
    NotFollowedBy=18
    NotPrecededBy=19
    Aggregate=20
    GroupBy=21
    Count=22
    Distinct=23
    Sum=24
    Avg=25
    Min=26
    Max=27
    OrderBy=28
    Asc=29
    Desc=30
    Limit=31
    Offset=32
    Before=33
    After=34
    Between=35
    Ago=36
    Seconds=37
    Minutes=38
    Hours=39
    Days=40
    Weeks=41
    Months=42
    Years=43
    Contains=44
    ContainsTokens=45
    ContainsPhrase=46
    From=47
    MentionsUser=48
    IsQuestion=49
    MentionsDate=50
    MentionsTime=51
    MentionsPlace=52
    MentionsOrg=53
    ContainsLink=54
    HasFeature=55
    LabeledAs=56
    HasWordOfDict=57
    HasTime=58
    HasLocation=59
    HasOrganization=60
    HasURL=61
    HasDate=62
    HasQuestion=63
    HasUserMentioned=64
    ByUser=65
    INTEGER=66
    STRING=67
    QUOTED_STRING=68
    VARIABLE=69
    WILDCARD=70
    WS=71

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


        def InWindow(self):
            return self.getToken(PrismQLParser.InWindow, 0)

        def number(self):
            return self.getTypedRuleContext(PrismQLParser.NumberContext,0)


        def InWin(self):
            return self.getToken(PrismQLParser.InWin, 0)

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


            self.state = 68
            self._errHandler.sync(self)
            token = self._input.LA(1)
            if token in [9]:
                self.state = 62
                self.match(PrismQLParser.InWindow)
                self.state = 63
                self.number()
                pass
            elif token in [10]:
                self.state = 64
                self.match(PrismQLParser.InWin)
                self.state = 65
                self.number()
                pass
            elif token in [11]:
                self.state = 66
                self.match(PrismQLParser.Within)
                self.state = 67
                self.time_value()
                pass
            elif token in [3, 20, 21, 28, 31, 33, 34, 35]:
                pass
            else:
                pass
            self.state = 71
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if (((_la) & ~0x3f) == 0 and ((1 << _la) & 60129542144) != 0):
                self.state = 70
                self.temporal_filter()


            self.state = 74
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if _la==21:
                self.state = 73
                self.groupby_clause()


            self.state = 77
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if _la==20:
                self.state = 76
                self.aggregate_clause()


            self.state = 80
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if _la==28:
                self.state = 79
                self.orderby_clause()


            self.state = 83
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if _la==31:
                self.state = 82
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
            self.state = 85
            self.match(PrismQLParser.T__1)
            self.state = 86
            self.query()
            self.state = 87
            self.match(PrismQLParser.T__2)
            self.state = 91
            self._errHandler.sync(self)
            _alt = self._interp.adaptivePredict(self._input,8,self._ctx)
            while _alt!=2 and _alt!=ATN.INVALID_ALT_NUMBER:
                if _alt==1:
                    self.state = 88
                    self.query_seq_continuation() 
                self.state = 93
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



    class PositionalSubqueryDeprecatedContext(Query_seq_continuationContext):

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
            if hasattr( visitor, "visitPositionalSubqueryDeprecated" ):
                return visitor.visitPositionalSubqueryDeprecated(self)
            else:
                return visitor.visitChildren(self)


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

        def InWindow(self):
            return self.getToken(PrismQLParser.InWindow, 0)
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
            self.state = 113
            self._errHandler.sync(self)
            la_ = self._interp.adaptivePredict(self._input,9,self._ctx)
            if la_ == 1:
                localctx = PrismQLParser.UnorderedSubqueryContext(self, localctx)
                self.enterOuterAlt(localctx, 1)
                self.state = 94
                self.match(PrismQLParser.T__0)
                self.state = 95
                self.match(PrismQLParser.T__1)
                self.state = 96
                self.query()
                self.state = 97
                self.match(PrismQLParser.T__2)
                pass

            elif la_ == 2:
                localctx = PrismQLParser.PositionalSubqueryContext(self, localctx)
                self.enterOuterAlt(localctx, 2)
                self.state = 99
                self.positional_op()
                self.state = 100
                self.match(PrismQLParser.T__1)
                self.state = 101
                self.query()
                self.state = 102
                self.match(PrismQLParser.T__2)
                self.state = 103
                self.match(PrismQLParser.InWindow)
                self.state = 104
                self.number()
                pass

            elif la_ == 3:
                localctx = PrismQLParser.PositionalSubqueryDeprecatedContext(self, localctx)
                self.enterOuterAlt(localctx, 3)
                self.state = 106
                self.positional_op()
                self.state = 107
                self.match(PrismQLParser.T__1)
                self.state = 108
                self.query()
                self.state = 109
                self.match(PrismQLParser.T__2)
                self.state = 110
                self.match(PrismQLParser.Within)
                self.state = 111
                self.number()
                pass


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
            self.state = 115
            _la = self._input.LA(1)
            if not((((_la) & ~0x3f) == 0 and ((1 << _la) & 983040) != 0)):
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
            self.state = 117
            self.named_restriction()
            self.state = 122
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            while _la==4:
                self.state = 118
                self.match(PrismQLParser.T__3)
                self.state = 119
                self.named_restriction()
                self.state = 124
                self._errHandler.sync(self)
                _la = self._input.LA(1)

            self.state = 126
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if _la==12:
                self.state = 125
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
            self.state = 128
            self.restriction(0)
            self.state = 130
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if _la==5:
                self.state = 129
                self.quantifier()


            self.state = 134
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if _la==8:
                self.state = 132
                self.match(PrismQLParser.As)
                self.state = 133
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
            self.state = 151
            self._errHandler.sync(self)
            la_ = self._interp.adaptivePredict(self._input,14,self._ctx)
            if la_ == 1:
                localctx = PrismQLParser.ExactQuantifierContext(self, localctx)
                self.enterOuterAlt(localctx, 1)
                self.state = 136
                self.match(PrismQLParser.T__4)
                self.state = 137
                self.number()
                self.state = 138
                self.match(PrismQLParser.T__5)
                pass

            elif la_ == 2:
                localctx = PrismQLParser.AtLeastQuantifierContext(self, localctx)
                self.enterOuterAlt(localctx, 2)
                self.state = 140
                self.match(PrismQLParser.T__4)
                self.state = 141
                self.number()
                self.state = 142
                self.match(PrismQLParser.T__3)
                self.state = 143
                self.match(PrismQLParser.T__5)
                pass

            elif la_ == 3:
                localctx = PrismQLParser.RangeQuantifierContext(self, localctx)
                self.enterOuterAlt(localctx, 3)
                self.state = 145
                self.match(PrismQLParser.T__4)
                self.state = 146
                self.number()
                self.state = 147
                self.match(PrismQLParser.T__3)
                self.state = 148
                self.number()
                self.state = 149
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

        def InWindow(self):
            return self.getToken(PrismQLParser.InWindow, 0)

        def number(self):
            return self.getTypedRuleContext(PrismQLParser.NumberContext,0)


        def PrecededBy(self):
            return self.getToken(PrismQLParser.PrecededBy, 0)

        def NotFollowedBy(self):
            return self.getToken(PrismQLParser.NotFollowedBy, 0)

        def NotPrecededBy(self):
            return self.getToken(PrismQLParser.NotPrecededBy, 0)

        def Within(self):
            return self.getToken(PrismQLParser.Within, 0)

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
            self.state = 161
            self._errHandler.sync(self)
            token = self._input.LA(1)
            if token in [2]:
                self.state = 154
                self.match(PrismQLParser.T__1)
                self.state = 155
                self.restriction(0)
                self.state = 156
                self.match(PrismQLParser.T__2)
                pass
            elif token in [13]:
                self.state = 158
                self.match(PrismQLParser.Not)
                self.state = 159
                self.restriction(2)
                pass
            elif token in [44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65]:
                self.state = 160
                self.condition()
                pass
            else:
                raise NoViableAltException(self)

            self._ctx.stop = self._input.LT(-1)
            self.state = 219
            self._errHandler.sync(self)
            _alt = self._interp.adaptivePredict(self._input,17,self._ctx)
            while _alt!=2 and _alt!=ATN.INVALID_ALT_NUMBER:
                if _alt==1:
                    if self._parseListeners is not None:
                        self.triggerExitRuleEvent()
                    _prevctx = localctx
                    self.state = 217
                    self._errHandler.sync(self)
                    la_ = self._interp.adaptivePredict(self._input,16,self._ctx)
                    if la_ == 1:
                        localctx = PrismQLParser.RestrictionContext(self, _parentctx, _parentState)
                        self.pushNewRecursionContext(localctx, _startState, self.RULE_restriction)
                        self.state = 163
                        if not self.precpred(self._ctx, 13):
                            from antlr4.error.Errors import FailedPredicateException
                            raise FailedPredicateException(self, "self.precpred(self._ctx, 13)")
                        self.state = 164
                        self.match(PrismQLParser.And)
                        self.state = 165
                        self.restriction(14)
                        pass

                    elif la_ == 2:
                        localctx = PrismQLParser.RestrictionContext(self, _parentctx, _parentState)
                        self.pushNewRecursionContext(localctx, _startState, self.RULE_restriction)
                        self.state = 166
                        if not self.precpred(self._ctx, 12):
                            from antlr4.error.Errors import FailedPredicateException
                            raise FailedPredicateException(self, "self.precpred(self._ctx, 12)")
                        self.state = 167
                        self.match(PrismQLParser.Or)
                        self.state = 168
                        self.restriction(13)
                        pass

                    elif la_ == 3:
                        localctx = PrismQLParser.RestrictionContext(self, _parentctx, _parentState)
                        self.pushNewRecursionContext(localctx, _startState, self.RULE_restriction)
                        self.state = 169
                        if not self.precpred(self._ctx, 11):
                            from antlr4.error.Errors import FailedPredicateException
                            raise FailedPredicateException(self, "self.precpred(self._ctx, 11)")
                        self.state = 170
                        self.match(PrismQLParser.FollowedBy)
                        self.state = 171
                        self.restriction(0)
                        self.state = 172
                        self.match(PrismQLParser.InWindow)
                        self.state = 173
                        self.number()
                        pass

                    elif la_ == 4:
                        localctx = PrismQLParser.RestrictionContext(self, _parentctx, _parentState)
                        self.pushNewRecursionContext(localctx, _startState, self.RULE_restriction)
                        self.state = 175
                        if not self.precpred(self._ctx, 10):
                            from antlr4.error.Errors import FailedPredicateException
                            raise FailedPredicateException(self, "self.precpred(self._ctx, 10)")
                        self.state = 176
                        self.match(PrismQLParser.PrecededBy)
                        self.state = 177
                        self.restriction(0)
                        self.state = 178
                        self.match(PrismQLParser.InWindow)
                        self.state = 179
                        self.number()
                        pass

                    elif la_ == 5:
                        localctx = PrismQLParser.RestrictionContext(self, _parentctx, _parentState)
                        self.pushNewRecursionContext(localctx, _startState, self.RULE_restriction)
                        self.state = 181
                        if not self.precpred(self._ctx, 9):
                            from antlr4.error.Errors import FailedPredicateException
                            raise FailedPredicateException(self, "self.precpred(self._ctx, 9)")
                        self.state = 182
                        self.match(PrismQLParser.NotFollowedBy)
                        self.state = 183
                        self.restriction(0)
                        self.state = 184
                        self.match(PrismQLParser.InWindow)
                        self.state = 185
                        self.number()
                        pass

                    elif la_ == 6:
                        localctx = PrismQLParser.RestrictionContext(self, _parentctx, _parentState)
                        self.pushNewRecursionContext(localctx, _startState, self.RULE_restriction)
                        self.state = 187
                        if not self.precpred(self._ctx, 8):
                            from antlr4.error.Errors import FailedPredicateException
                            raise FailedPredicateException(self, "self.precpred(self._ctx, 8)")
                        self.state = 188
                        self.match(PrismQLParser.NotPrecededBy)
                        self.state = 189
                        self.restriction(0)
                        self.state = 190
                        self.match(PrismQLParser.InWindow)
                        self.state = 191
                        self.number()
                        pass

                    elif la_ == 7:
                        localctx = PrismQLParser.RestrictionContext(self, _parentctx, _parentState)
                        self.pushNewRecursionContext(localctx, _startState, self.RULE_restriction)
                        self.state = 193
                        if not self.precpred(self._ctx, 7):
                            from antlr4.error.Errors import FailedPredicateException
                            raise FailedPredicateException(self, "self.precpred(self._ctx, 7)")
                        self.state = 194
                        self.match(PrismQLParser.FollowedBy)
                        self.state = 195
                        self.restriction(0)
                        self.state = 196
                        self.match(PrismQLParser.Within)
                        self.state = 197
                        self.number()
                        pass

                    elif la_ == 8:
                        localctx = PrismQLParser.RestrictionContext(self, _parentctx, _parentState)
                        self.pushNewRecursionContext(localctx, _startState, self.RULE_restriction)
                        self.state = 199
                        if not self.precpred(self._ctx, 6):
                            from antlr4.error.Errors import FailedPredicateException
                            raise FailedPredicateException(self, "self.precpred(self._ctx, 6)")
                        self.state = 200
                        self.match(PrismQLParser.PrecededBy)
                        self.state = 201
                        self.restriction(0)
                        self.state = 202
                        self.match(PrismQLParser.Within)
                        self.state = 203
                        self.number()
                        pass

                    elif la_ == 9:
                        localctx = PrismQLParser.RestrictionContext(self, _parentctx, _parentState)
                        self.pushNewRecursionContext(localctx, _startState, self.RULE_restriction)
                        self.state = 205
                        if not self.precpred(self._ctx, 5):
                            from antlr4.error.Errors import FailedPredicateException
                            raise FailedPredicateException(self, "self.precpred(self._ctx, 5)")
                        self.state = 206
                        self.match(PrismQLParser.NotFollowedBy)
                        self.state = 207
                        self.restriction(0)
                        self.state = 208
                        self.match(PrismQLParser.Within)
                        self.state = 209
                        self.number()
                        pass

                    elif la_ == 10:
                        localctx = PrismQLParser.RestrictionContext(self, _parentctx, _parentState)
                        self.pushNewRecursionContext(localctx, _startState, self.RULE_restriction)
                        self.state = 211
                        if not self.precpred(self._ctx, 4):
                            from antlr4.error.Errors import FailedPredicateException
                            raise FailedPredicateException(self, "self.precpred(self._ctx, 4)")
                        self.state = 212
                        self.match(PrismQLParser.NotPrecededBy)
                        self.state = 213
                        self.restriction(0)
                        self.state = 214
                        self.match(PrismQLParser.Within)
                        self.state = 215
                        self.number()
                        pass

             
                self.state = 221
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


        def ContainsTokens(self):
            return self.getToken(PrismQLParser.ContainsTokens, 0)

        def ContainsPhrase(self):
            return self.getToken(PrismQLParser.ContainsPhrase, 0)

        def QUOTED_STRING(self):
            return self.getToken(PrismQLParser.QUOTED_STRING, 0)

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


        def LabeledAs(self):
            return self.getToken(PrismQLParser.LabeledAs, 0)

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
            self.state = 307
            self._errHandler.sync(self)
            token = self._input.LA(1)
            if token in [44]:
                self.enterOuterAlt(localctx, 1)
                self.state = 222
                self.match(PrismQLParser.Contains)
                self.state = 223
                self.match(PrismQLParser.T__1)
                self.state = 224
                self.hdict()
                self.state = 225
                self.match(PrismQLParser.T__2)
                pass
            elif token in [45]:
                self.enterOuterAlt(localctx, 2)
                self.state = 227
                self.match(PrismQLParser.ContainsTokens)
                self.state = 228
                self.match(PrismQLParser.T__1)
                self.state = 229
                self.hdict()
                self.state = 230
                self.match(PrismQLParser.T__2)
                pass
            elif token in [46]:
                self.enterOuterAlt(localctx, 3)
                self.state = 232
                self.match(PrismQLParser.ContainsPhrase)
                self.state = 233
                self.match(PrismQLParser.T__1)
                self.state = 234
                self.match(PrismQLParser.QUOTED_STRING)
                self.state = 235
                self.match(PrismQLParser.T__2)
                pass
            elif token in [47]:
                self.enterOuterAlt(localctx, 4)
                self.state = 236
                self.match(PrismQLParser.From)
                self.state = 237
                self.match(PrismQLParser.T__1)
                self.state = 238
                self.huser()
                self.state = 239
                self.match(PrismQLParser.T__2)
                pass
            elif token in [48]:
                self.enterOuterAlt(localctx, 5)
                self.state = 241
                self.match(PrismQLParser.MentionsUser)
                self.state = 242
                self.match(PrismQLParser.T__1)
                self.state = 243
                self.huser()
                self.state = 244
                self.match(PrismQLParser.T__2)
                pass
            elif token in [49]:
                self.enterOuterAlt(localctx, 6)
                self.state = 246
                self.match(PrismQLParser.IsQuestion)
                self.state = 247
                self.match(PrismQLParser.T__1)
                self.state = 248
                self.match(PrismQLParser.T__2)
                pass
            elif token in [50]:
                self.enterOuterAlt(localctx, 7)
                self.state = 249
                self.match(PrismQLParser.MentionsDate)
                self.state = 250
                self.match(PrismQLParser.T__1)
                self.state = 251
                self.match(PrismQLParser.T__2)
                pass
            elif token in [51]:
                self.enterOuterAlt(localctx, 8)
                self.state = 252
                self.match(PrismQLParser.MentionsTime)
                self.state = 253
                self.match(PrismQLParser.T__1)
                self.state = 254
                self.match(PrismQLParser.T__2)
                pass
            elif token in [52]:
                self.enterOuterAlt(localctx, 9)
                self.state = 255
                self.match(PrismQLParser.MentionsPlace)
                self.state = 256
                self.match(PrismQLParser.T__1)
                self.state = 257
                self.match(PrismQLParser.T__2)
                pass
            elif token in [53]:
                self.enterOuterAlt(localctx, 10)
                self.state = 258
                self.match(PrismQLParser.MentionsOrg)
                self.state = 259
                self.match(PrismQLParser.T__1)
                self.state = 260
                self.match(PrismQLParser.T__2)
                pass
            elif token in [54]:
                self.enterOuterAlt(localctx, 11)
                self.state = 261
                self.match(PrismQLParser.ContainsLink)
                self.state = 262
                self.match(PrismQLParser.T__1)
                self.state = 263
                self.match(PrismQLParser.T__2)
                pass
            elif token in [55]:
                self.enterOuterAlt(localctx, 12)
                self.state = 264
                self.match(PrismQLParser.HasFeature)
                self.state = 265
                self.match(PrismQLParser.T__1)
                self.state = 266
                self.feature_name()
                self.state = 267
                self.match(PrismQLParser.T__2)
                pass
            elif token in [56]:
                self.enterOuterAlt(localctx, 13)
                self.state = 269
                self.match(PrismQLParser.LabeledAs)
                self.state = 270
                self.match(PrismQLParser.T__1)
                self.state = 271
                self.feature_name()
                self.state = 272
                self.match(PrismQLParser.T__2)
                pass
            elif token in [57]:
                self.enterOuterAlt(localctx, 14)
                self.state = 274
                self.match(PrismQLParser.HasWordOfDict)
                self.state = 275
                self.match(PrismQLParser.T__1)
                self.state = 276
                self.hdict()
                self.state = 277
                self.match(PrismQLParser.T__2)
                pass
            elif token in [65]:
                self.enterOuterAlt(localctx, 15)
                self.state = 279
                self.match(PrismQLParser.ByUser)
                self.state = 280
                self.match(PrismQLParser.T__1)
                self.state = 281
                self.huser()
                self.state = 282
                self.match(PrismQLParser.T__2)
                pass
            elif token in [64]:
                self.enterOuterAlt(localctx, 16)
                self.state = 284
                self.match(PrismQLParser.HasUserMentioned)
                self.state = 285
                self.match(PrismQLParser.T__1)
                self.state = 286
                self.huser()
                self.state = 287
                self.match(PrismQLParser.T__2)
                pass
            elif token in [63]:
                self.enterOuterAlt(localctx, 17)
                self.state = 289
                self.match(PrismQLParser.HasQuestion)
                self.state = 290
                self.match(PrismQLParser.T__1)
                self.state = 291
                self.match(PrismQLParser.T__2)
                pass
            elif token in [62]:
                self.enterOuterAlt(localctx, 18)
                self.state = 292
                self.match(PrismQLParser.HasDate)
                self.state = 293
                self.match(PrismQLParser.T__1)
                self.state = 294
                self.match(PrismQLParser.T__2)
                pass
            elif token in [58]:
                self.enterOuterAlt(localctx, 19)
                self.state = 295
                self.match(PrismQLParser.HasTime)
                self.state = 296
                self.match(PrismQLParser.T__1)
                self.state = 297
                self.match(PrismQLParser.T__2)
                pass
            elif token in [59]:
                self.enterOuterAlt(localctx, 20)
                self.state = 298
                self.match(PrismQLParser.HasLocation)
                self.state = 299
                self.match(PrismQLParser.T__1)
                self.state = 300
                self.match(PrismQLParser.T__2)
                pass
            elif token in [60]:
                self.enterOuterAlt(localctx, 21)
                self.state = 301
                self.match(PrismQLParser.HasOrganization)
                self.state = 302
                self.match(PrismQLParser.T__1)
                self.state = 303
                self.match(PrismQLParser.T__2)
                pass
            elif token in [61]:
                self.enterOuterAlt(localctx, 22)
                self.state = 304
                self.match(PrismQLParser.HasURL)
                self.state = 305
                self.match(PrismQLParser.T__1)
                self.state = 306
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
            self.state = 326
            self._errHandler.sync(self)
            token = self._input.LA(1)
            if token in [33]:
                self.enterOuterAlt(localctx, 1)
                self.state = 309
                self.match(PrismQLParser.Before)
                self.state = 310
                self.match(PrismQLParser.T__1)
                self.state = 311
                self.timestamp()
                self.state = 312
                self.match(PrismQLParser.T__2)
                pass
            elif token in [34]:
                self.enterOuterAlt(localctx, 2)
                self.state = 314
                self.match(PrismQLParser.After)
                self.state = 315
                self.match(PrismQLParser.T__1)
                self.state = 316
                self.timestamp()
                self.state = 317
                self.match(PrismQLParser.T__2)
                pass
            elif token in [35]:
                self.enterOuterAlt(localctx, 3)
                self.state = 319
                self.match(PrismQLParser.Between)
                self.state = 320
                self.match(PrismQLParser.T__1)
                self.state = 321
                self.timestamp()
                self.state = 322
                self.match(PrismQLParser.T__3)
                self.state = 323
                self.timestamp()
                self.state = 324
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
            self.state = 332
            self._errHandler.sync(self)
            token = self._input.LA(1)
            if token in [68]:
                localctx = PrismQLParser.AbsoluteTimestampContext(self, localctx)
                self.enterOuterAlt(localctx, 1)
                self.state = 328
                self.match(PrismQLParser.QUOTED_STRING)
                pass
            elif token in [66]:
                localctx = PrismQLParser.RelativeTimestampContext(self, localctx)
                self.enterOuterAlt(localctx, 2)
                self.state = 329
                self.time_value()
                self.state = 330
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
            self.state = 334
            self.match(PrismQLParser.GroupBy)
            self.state = 335
            self.groupby_field()
            self.state = 340
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            while _la==4:
                self.state = 336
                self.match(PrismQLParser.T__3)
                self.state = 337
                self.groupby_field()
                self.state = 342
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
            self.state = 349
            self._errHandler.sync(self)
            token = self._input.LA(1)
            if token in [67]:
                localctx = PrismQLParser.SimpleGroupByContext(self, localctx)
                self.enterOuterAlt(localctx, 1)
                self.state = 343
                self.field_name()
                pass
            elif token in [39, 40, 41, 42, 43]:
                localctx = PrismQLParser.TemporalGroupByContext(self, localctx)
                self.enterOuterAlt(localctx, 2)
                self.state = 344
                self.temporal_group_func()
                self.state = 345
                self.match(PrismQLParser.T__1)
                self.state = 346
                self.field_name()
                self.state = 347
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
            self.state = 351
            _la = self._input.LA(1)
            if not((((_la) & ~0x3f) == 0 and ((1 << _la) & 17042430230528) != 0)):
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
            self.state = 353
            self.match(PrismQLParser.Aggregate)
            self.state = 354
            self.aggregation_func()
            self.state = 359
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            while _la==4:
                self.state = 355
                self.match(PrismQLParser.T__3)
                self.state = 356
                self.aggregation_func()
                self.state = 361
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
            self.state = 396
            self._errHandler.sync(self)
            la_ = self._interp.adaptivePredict(self._input,24,self._ctx)
            if la_ == 1:
                localctx = PrismQLParser.CountAllContext(self, localctx)
                self.enterOuterAlt(localctx, 1)
                self.state = 362
                self.match(PrismQLParser.Count)
                self.state = 363
                self.match(PrismQLParser.T__1)
                self.state = 364
                self.match(PrismQLParser.T__2)
                pass

            elif la_ == 2:
                localctx = PrismQLParser.CountDistinctContext(self, localctx)
                self.enterOuterAlt(localctx, 2)
                self.state = 365
                self.match(PrismQLParser.Count)
                self.state = 366
                self.match(PrismQLParser.T__1)
                self.state = 367
                self.match(PrismQLParser.Distinct)
                self.state = 368
                self.field_name()
                self.state = 369
                self.match(PrismQLParser.T__2)
                pass

            elif la_ == 3:
                localctx = PrismQLParser.DistinctValuesContext(self, localctx)
                self.enterOuterAlt(localctx, 3)
                self.state = 371
                self.match(PrismQLParser.Distinct)
                self.state = 372
                self.match(PrismQLParser.T__1)
                self.state = 373
                self.field_name()
                self.state = 374
                self.match(PrismQLParser.T__2)
                pass

            elif la_ == 4:
                localctx = PrismQLParser.SumFuncContext(self, localctx)
                self.enterOuterAlt(localctx, 4)
                self.state = 376
                self.match(PrismQLParser.Sum)
                self.state = 377
                self.match(PrismQLParser.T__1)
                self.state = 378
                self.field_name()
                self.state = 379
                self.match(PrismQLParser.T__2)
                pass

            elif la_ == 5:
                localctx = PrismQLParser.AvgFuncContext(self, localctx)
                self.enterOuterAlt(localctx, 5)
                self.state = 381
                self.match(PrismQLParser.Avg)
                self.state = 382
                self.match(PrismQLParser.T__1)
                self.state = 383
                self.field_name()
                self.state = 384
                self.match(PrismQLParser.T__2)
                pass

            elif la_ == 6:
                localctx = PrismQLParser.MinFuncContext(self, localctx)
                self.enterOuterAlt(localctx, 6)
                self.state = 386
                self.match(PrismQLParser.Min)
                self.state = 387
                self.match(PrismQLParser.T__1)
                self.state = 388
                self.field_name()
                self.state = 389
                self.match(PrismQLParser.T__2)
                pass

            elif la_ == 7:
                localctx = PrismQLParser.MaxFuncContext(self, localctx)
                self.enterOuterAlt(localctx, 7)
                self.state = 391
                self.match(PrismQLParser.Max)
                self.state = 392
                self.match(PrismQLParser.T__1)
                self.state = 393
                self.field_name()
                self.state = 394
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
            self.state = 398
            self.match(PrismQLParser.OrderBy)
            self.state = 399
            self.field_name()
            self.state = 401
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if _la==29 or _la==30:
                self.state = 400
                _la = self._input.LA(1)
                if not(_la==29 or _la==30):
                    self._errHandler.recoverInline(self)
                else:
                    self._errHandler.reportMatch(self)
                    self.consume()


            self.state = 410
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            while _la==4:
                self.state = 403
                self.match(PrismQLParser.T__3)
                self.state = 404
                self.field_name()
                self.state = 406
                self._errHandler.sync(self)
                _la = self._input.LA(1)
                if _la==29 or _la==30:
                    self.state = 405
                    _la = self._input.LA(1)
                    if not(_la==29 or _la==30):
                        self._errHandler.recoverInline(self)
                    else:
                        self._errHandler.reportMatch(self)
                        self.consume()


                self.state = 412
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
            self.state = 413
            self.match(PrismQLParser.Limit)
            self.state = 414
            self.number()
            self.state = 417
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if _la==32:
                self.state = 415
                self.match(PrismQLParser.Offset)
                self.state = 416
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
            self.state = 419
            self.number()
            self.state = 420
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
            self.state = 422
            _la = self._input.LA(1)
            if not((((_la) & ~0x3f) == 0 and ((1 << _la) & 4260607557632) != 0)):
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
            self.state = 424
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
            self.state = 426
            _la = self._input.LA(1)
            if not(((((_la - 67)) & ~0x3f) == 0 and ((1 << (_la - 67)) & 13) != 0)):
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
            self.state = 428
            _la = self._input.LA(1)
            if not(((((_la - 67)) & ~0x3f) == 0 and ((1 << (_la - 67)) & 13) != 0)):
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
            self.state = 430
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
            self.state = 432
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
                return self.precpred(self._ctx, 13)
         

            if predIndex == 1:
                return self.precpred(self._ctx, 12)
         

            if predIndex == 2:
                return self.precpred(self._ctx, 11)
         

            if predIndex == 3:
                return self.precpred(self._ctx, 10)
         

            if predIndex == 4:
                return self.precpred(self._ctx, 9)
         

            if predIndex == 5:
                return self.precpred(self._ctx, 8)
         

            if predIndex == 6:
                return self.precpred(self._ctx, 7)
         

            if predIndex == 7:
                return self.precpred(self._ctx, 6)
         

            if predIndex == 8:
                return self.precpred(self._ctx, 5)
         

            if predIndex == 9:
                return self.precpred(self._ctx, 4)
         




