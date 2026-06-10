# Generated from /Users/aleph/Projects/vibes/prismql/src/prismql/grammar/PrismQL.g4 by ANTLR 4.13.1
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
        4,1,72,443,2,0,7,0,2,1,7,1,2,2,7,2,2,3,7,3,2,4,7,4,2,5,7,5,2,6,7,
        6,2,7,7,7,2,8,7,8,2,9,7,9,2,10,7,10,2,11,7,11,2,12,7,12,2,13,7,13,
        2,14,7,14,2,15,7,15,2,16,7,16,2,17,7,17,2,18,7,18,2,19,7,19,2,20,
        7,20,2,21,7,21,2,22,7,22,2,23,7,23,2,24,7,24,2,25,7,25,2,26,7,26,
        1,0,1,0,1,0,1,1,1,1,3,1,60,8,1,1,1,3,1,63,8,1,1,1,1,1,1,1,1,1,1,
        1,1,1,1,1,1,1,3,1,73,8,1,1,1,3,1,76,8,1,1,1,3,1,79,8,1,1,1,3,1,82,
        8,1,1,1,3,1,85,8,1,1,1,3,1,88,8,1,1,2,1,2,1,2,1,2,5,2,94,8,2,10,
        2,12,2,97,9,2,1,3,1,3,1,3,1,3,1,3,1,3,1,3,1,3,1,3,1,3,1,3,1,3,1,
        3,1,3,1,3,1,3,1,3,1,3,1,3,3,3,118,8,3,1,4,1,4,1,5,1,5,1,5,5,5,125,
        8,5,10,5,12,5,128,9,5,1,5,3,5,131,8,5,1,6,1,6,3,6,135,8,6,1,6,1,
        6,3,6,139,8,6,1,7,1,7,1,7,1,7,1,7,1,7,1,7,1,7,1,7,1,7,1,7,1,7,1,
        7,1,7,1,7,3,7,156,8,7,1,8,1,8,1,8,1,8,1,8,1,8,1,8,1,8,1,8,1,8,1,
        8,1,8,3,8,170,8,8,1,8,1,8,1,8,1,8,1,8,1,8,1,8,1,8,1,8,3,8,181,8,
        8,1,8,1,8,1,8,1,8,1,8,1,8,1,8,1,8,1,8,3,8,192,8,8,1,8,1,8,1,8,1,
        8,1,8,1,8,1,8,1,8,1,8,3,8,203,8,8,5,8,205,8,8,10,8,12,8,208,9,8,
        1,9,1,9,1,9,1,9,1,9,1,9,1,9,1,9,3,9,218,8,9,1,9,1,9,1,9,1,9,1,9,
        1,9,5,9,226,8,9,10,9,12,9,229,9,9,1,10,1,10,1,10,1,10,1,10,1,10,
        1,10,1,10,1,10,1,10,1,10,1,10,1,10,1,10,1,10,1,10,1,10,1,10,1,10,
        1,10,1,10,1,10,1,10,1,10,1,10,1,10,1,10,1,10,1,10,1,10,1,10,1,10,
        1,10,1,10,1,10,1,10,1,10,1,10,1,10,1,10,1,10,1,10,1,10,1,10,1,10,
        1,10,1,10,1,10,1,10,1,10,1,10,1,10,1,10,1,10,1,10,1,10,1,10,1,10,
        1,10,1,10,1,10,1,10,1,10,1,10,1,10,1,10,1,10,1,10,1,10,1,10,1,10,
        1,10,1,10,1,10,1,10,1,10,1,10,1,10,1,10,1,10,1,10,1,10,1,10,1,10,
        1,10,3,10,316,8,10,1,11,1,11,1,11,1,11,1,11,1,11,1,11,1,11,1,11,
        1,11,1,11,1,11,1,11,1,11,1,11,1,11,1,11,3,11,335,8,11,1,12,1,12,
        1,12,1,12,3,12,341,8,12,1,13,1,13,1,13,1,13,5,13,347,8,13,10,13,
        12,13,350,9,13,1,14,1,14,1,14,1,14,1,14,1,14,3,14,358,8,14,1,15,
        1,15,1,16,1,16,1,16,1,16,5,16,366,8,16,10,16,12,16,369,9,16,1,17,
        1,17,1,17,1,17,1,17,1,17,1,17,1,17,1,17,1,17,1,17,1,17,1,17,1,17,
        1,17,1,17,1,17,1,17,1,17,1,17,1,17,1,17,1,17,1,17,1,17,1,17,1,17,
        1,17,1,17,1,17,1,17,1,17,1,17,1,17,3,17,405,8,17,1,18,1,18,1,18,
        3,18,410,8,18,1,18,1,18,1,18,3,18,415,8,18,5,18,417,8,18,10,18,12,
        18,420,9,18,1,19,1,19,1,19,1,19,3,19,426,8,19,1,20,1,20,1,20,1,21,
        1,21,1,22,1,22,1,23,1,23,1,24,1,24,1,25,1,25,1,26,1,26,1,26,0,2,
        16,18,27,0,2,4,6,8,10,12,14,16,18,20,22,24,26,28,30,32,34,36,38,
        40,42,44,46,48,50,52,0,5,1,0,17,20,1,0,40,44,1,0,30,31,1,0,38,42,
        2,0,68,68,70,71,492,0,54,1,0,0,0,2,59,1,0,0,0,4,89,1,0,0,0,6,117,
        1,0,0,0,8,119,1,0,0,0,10,121,1,0,0,0,12,132,1,0,0,0,14,155,1,0,0,
        0,16,157,1,0,0,0,18,217,1,0,0,0,20,315,1,0,0,0,22,334,1,0,0,0,24,
        340,1,0,0,0,26,342,1,0,0,0,28,357,1,0,0,0,30,359,1,0,0,0,32,361,
        1,0,0,0,34,404,1,0,0,0,36,406,1,0,0,0,38,421,1,0,0,0,40,427,1,0,
        0,0,42,430,1,0,0,0,44,432,1,0,0,0,46,434,1,0,0,0,48,436,1,0,0,0,
        50,438,1,0,0,0,52,440,1,0,0,0,54,55,5,7,0,0,55,56,3,2,1,0,56,1,1,
        0,0,0,57,60,3,4,2,0,58,60,3,10,5,0,59,57,1,0,0,0,59,58,1,0,0,0,60,
        62,1,0,0,0,61,63,5,1,0,0,62,61,1,0,0,0,62,63,1,0,0,0,63,72,1,0,0,
        0,64,65,5,9,0,0,65,73,3,44,22,0,66,67,5,10,0,0,67,73,3,44,22,0,68,
        69,5,11,0,0,69,73,3,40,20,0,70,71,5,12,0,0,71,73,3,40,20,0,72,64,
        1,0,0,0,72,66,1,0,0,0,72,68,1,0,0,0,72,70,1,0,0,0,72,73,1,0,0,0,
        73,75,1,0,0,0,74,76,3,22,11,0,75,74,1,0,0,0,75,76,1,0,0,0,76,78,
        1,0,0,0,77,79,3,26,13,0,78,77,1,0,0,0,78,79,1,0,0,0,79,81,1,0,0,
        0,80,82,3,32,16,0,81,80,1,0,0,0,81,82,1,0,0,0,82,84,1,0,0,0,83,85,
        3,36,18,0,84,83,1,0,0,0,84,85,1,0,0,0,85,87,1,0,0,0,86,88,3,38,19,
        0,87,86,1,0,0,0,87,88,1,0,0,0,88,3,1,0,0,0,89,90,5,2,0,0,90,91,3,
        0,0,0,91,95,5,3,0,0,92,94,3,6,3,0,93,92,1,0,0,0,94,97,1,0,0,0,95,
        93,1,0,0,0,95,96,1,0,0,0,96,5,1,0,0,0,97,95,1,0,0,0,98,99,5,1,0,
        0,99,100,5,2,0,0,100,101,3,0,0,0,101,102,5,3,0,0,102,118,1,0,0,0,
        103,104,3,8,4,0,104,105,5,2,0,0,105,106,3,0,0,0,106,107,5,3,0,0,
        107,108,5,9,0,0,108,109,3,44,22,0,109,118,1,0,0,0,110,111,3,8,4,
        0,111,112,5,2,0,0,112,113,3,0,0,0,113,114,5,3,0,0,114,115,5,12,0,
        0,115,116,3,44,22,0,116,118,1,0,0,0,117,98,1,0,0,0,117,103,1,0,0,
        0,117,110,1,0,0,0,118,7,1,0,0,0,119,120,7,0,0,0,120,9,1,0,0,0,121,
        126,3,12,6,0,122,123,5,4,0,0,123,125,3,12,6,0,124,122,1,0,0,0,125,
        128,1,0,0,0,126,124,1,0,0,0,126,127,1,0,0,0,127,130,1,0,0,0,128,
        126,1,0,0,0,129,131,5,13,0,0,130,129,1,0,0,0,130,131,1,0,0,0,131,
        11,1,0,0,0,132,134,3,16,8,0,133,135,3,14,7,0,134,133,1,0,0,0,134,
        135,1,0,0,0,135,138,1,0,0,0,136,137,5,8,0,0,137,139,5,69,0,0,138,
        136,1,0,0,0,138,139,1,0,0,0,139,13,1,0,0,0,140,141,5,5,0,0,141,142,
        3,44,22,0,142,143,5,6,0,0,143,156,1,0,0,0,144,145,5,5,0,0,145,146,
        3,44,22,0,146,147,5,4,0,0,147,148,5,6,0,0,148,156,1,0,0,0,149,150,
        5,5,0,0,150,151,3,44,22,0,151,152,5,4,0,0,152,153,3,44,22,0,153,
        154,5,6,0,0,154,156,1,0,0,0,155,140,1,0,0,0,155,144,1,0,0,0,155,
        149,1,0,0,0,156,15,1,0,0,0,157,158,6,8,-1,0,158,159,3,18,9,0,159,
        206,1,0,0,0,160,161,10,5,0,0,161,162,5,17,0,0,162,169,3,18,9,0,163,
        164,5,9,0,0,164,170,3,44,22,0,165,166,5,11,0,0,166,170,3,40,20,0,
        167,168,5,12,0,0,168,170,3,44,22,0,169,163,1,0,0,0,169,165,1,0,0,
        0,169,167,1,0,0,0,169,170,1,0,0,0,170,205,1,0,0,0,171,172,10,4,0,
        0,172,173,5,18,0,0,173,180,3,18,9,0,174,175,5,9,0,0,175,181,3,44,
        22,0,176,177,5,11,0,0,177,181,3,40,20,0,178,179,5,12,0,0,179,181,
        3,44,22,0,180,174,1,0,0,0,180,176,1,0,0,0,180,178,1,0,0,0,180,181,
        1,0,0,0,181,205,1,0,0,0,182,183,10,3,0,0,183,184,5,19,0,0,184,191,
        3,18,9,0,185,186,5,9,0,0,186,192,3,44,22,0,187,188,5,11,0,0,188,
        192,3,40,20,0,189,190,5,12,0,0,190,192,3,44,22,0,191,185,1,0,0,0,
        191,187,1,0,0,0,191,189,1,0,0,0,191,192,1,0,0,0,192,205,1,0,0,0,
        193,194,10,2,0,0,194,195,5,20,0,0,195,202,3,18,9,0,196,197,5,9,0,
        0,197,203,3,44,22,0,198,199,5,11,0,0,199,203,3,40,20,0,200,201,5,
        12,0,0,201,203,3,44,22,0,202,196,1,0,0,0,202,198,1,0,0,0,202,200,
        1,0,0,0,202,203,1,0,0,0,203,205,1,0,0,0,204,160,1,0,0,0,204,171,
        1,0,0,0,204,182,1,0,0,0,204,193,1,0,0,0,205,208,1,0,0,0,206,204,
        1,0,0,0,206,207,1,0,0,0,207,17,1,0,0,0,208,206,1,0,0,0,209,210,6,
        9,-1,0,210,211,5,14,0,0,211,218,3,18,9,5,212,213,5,2,0,0,213,214,
        3,16,8,0,214,215,5,3,0,0,215,218,1,0,0,0,216,218,3,20,10,0,217,209,
        1,0,0,0,217,212,1,0,0,0,217,216,1,0,0,0,218,227,1,0,0,0,219,220,
        10,4,0,0,220,221,5,15,0,0,221,226,3,18,9,5,222,223,10,3,0,0,223,
        224,5,16,0,0,224,226,3,18,9,4,225,219,1,0,0,0,225,222,1,0,0,0,226,
        229,1,0,0,0,227,225,1,0,0,0,227,228,1,0,0,0,228,19,1,0,0,0,229,227,
        1,0,0,0,230,231,5,45,0,0,231,232,5,2,0,0,232,233,3,46,23,0,233,234,
        5,3,0,0,234,316,1,0,0,0,235,236,5,46,0,0,236,237,5,2,0,0,237,238,
        3,46,23,0,238,239,5,3,0,0,239,316,1,0,0,0,240,241,5,47,0,0,241,242,
        5,2,0,0,242,243,5,69,0,0,243,316,5,3,0,0,244,245,5,48,0,0,245,246,
        5,2,0,0,246,247,3,48,24,0,247,248,5,3,0,0,248,316,1,0,0,0,249,250,
        5,49,0,0,250,251,5,2,0,0,251,252,3,48,24,0,252,253,5,3,0,0,253,316,
        1,0,0,0,254,255,5,50,0,0,255,256,5,2,0,0,256,316,5,3,0,0,257,258,
        5,51,0,0,258,259,5,2,0,0,259,316,5,3,0,0,260,261,5,52,0,0,261,262,
        5,2,0,0,262,316,5,3,0,0,263,264,5,53,0,0,264,265,5,2,0,0,265,316,
        5,3,0,0,266,267,5,54,0,0,267,268,5,2,0,0,268,316,5,3,0,0,269,270,
        5,55,0,0,270,271,5,2,0,0,271,316,5,3,0,0,272,273,5,56,0,0,273,274,
        5,2,0,0,274,275,3,50,25,0,275,276,5,3,0,0,276,316,1,0,0,0,277,278,
        5,57,0,0,278,279,5,2,0,0,279,280,3,50,25,0,280,281,5,3,0,0,281,316,
        1,0,0,0,282,283,5,58,0,0,283,284,5,2,0,0,284,285,3,46,23,0,285,286,
        5,3,0,0,286,316,1,0,0,0,287,288,5,66,0,0,288,289,5,2,0,0,289,290,
        3,48,24,0,290,291,5,3,0,0,291,316,1,0,0,0,292,293,5,65,0,0,293,294,
        5,2,0,0,294,295,3,48,24,0,295,296,5,3,0,0,296,316,1,0,0,0,297,298,
        5,64,0,0,298,299,5,2,0,0,299,316,5,3,0,0,300,301,5,63,0,0,301,302,
        5,2,0,0,302,316,5,3,0,0,303,304,5,59,0,0,304,305,5,2,0,0,305,316,
        5,3,0,0,306,307,5,60,0,0,307,308,5,2,0,0,308,316,5,3,0,0,309,310,
        5,61,0,0,310,311,5,2,0,0,311,316,5,3,0,0,312,313,5,62,0,0,313,314,
        5,2,0,0,314,316,5,3,0,0,315,230,1,0,0,0,315,235,1,0,0,0,315,240,
        1,0,0,0,315,244,1,0,0,0,315,249,1,0,0,0,315,254,1,0,0,0,315,257,
        1,0,0,0,315,260,1,0,0,0,315,263,1,0,0,0,315,266,1,0,0,0,315,269,
        1,0,0,0,315,272,1,0,0,0,315,277,1,0,0,0,315,282,1,0,0,0,315,287,
        1,0,0,0,315,292,1,0,0,0,315,297,1,0,0,0,315,300,1,0,0,0,315,303,
        1,0,0,0,315,306,1,0,0,0,315,309,1,0,0,0,315,312,1,0,0,0,316,21,1,
        0,0,0,317,318,5,34,0,0,318,319,5,2,0,0,319,320,3,24,12,0,320,321,
        5,3,0,0,321,335,1,0,0,0,322,323,5,35,0,0,323,324,5,2,0,0,324,325,
        3,24,12,0,325,326,5,3,0,0,326,335,1,0,0,0,327,328,5,36,0,0,328,329,
        5,2,0,0,329,330,3,24,12,0,330,331,5,4,0,0,331,332,3,24,12,0,332,
        333,5,3,0,0,333,335,1,0,0,0,334,317,1,0,0,0,334,322,1,0,0,0,334,
        327,1,0,0,0,335,23,1,0,0,0,336,341,5,69,0,0,337,338,3,40,20,0,338,
        339,5,37,0,0,339,341,1,0,0,0,340,336,1,0,0,0,340,337,1,0,0,0,341,
        25,1,0,0,0,342,343,5,22,0,0,343,348,3,28,14,0,344,345,5,4,0,0,345,
        347,3,28,14,0,346,344,1,0,0,0,347,350,1,0,0,0,348,346,1,0,0,0,348,
        349,1,0,0,0,349,27,1,0,0,0,350,348,1,0,0,0,351,358,3,52,26,0,352,
        353,3,30,15,0,353,354,5,2,0,0,354,355,3,52,26,0,355,356,5,3,0,0,
        356,358,1,0,0,0,357,351,1,0,0,0,357,352,1,0,0,0,358,29,1,0,0,0,359,
        360,7,1,0,0,360,31,1,0,0,0,361,362,5,21,0,0,362,367,3,34,17,0,363,
        364,5,4,0,0,364,366,3,34,17,0,365,363,1,0,0,0,366,369,1,0,0,0,367,
        365,1,0,0,0,367,368,1,0,0,0,368,33,1,0,0,0,369,367,1,0,0,0,370,371,
        5,23,0,0,371,372,5,2,0,0,372,405,5,3,0,0,373,374,5,23,0,0,374,375,
        5,2,0,0,375,376,5,24,0,0,376,377,3,52,26,0,377,378,5,3,0,0,378,405,
        1,0,0,0,379,380,5,24,0,0,380,381,5,2,0,0,381,382,3,52,26,0,382,383,
        5,3,0,0,383,405,1,0,0,0,384,385,5,25,0,0,385,386,5,2,0,0,386,387,
        3,52,26,0,387,388,5,3,0,0,388,405,1,0,0,0,389,390,5,26,0,0,390,391,
        5,2,0,0,391,392,3,52,26,0,392,393,5,3,0,0,393,405,1,0,0,0,394,395,
        5,27,0,0,395,396,5,2,0,0,396,397,3,52,26,0,397,398,5,3,0,0,398,405,
        1,0,0,0,399,400,5,28,0,0,400,401,5,2,0,0,401,402,3,52,26,0,402,403,
        5,3,0,0,403,405,1,0,0,0,404,370,1,0,0,0,404,373,1,0,0,0,404,379,
        1,0,0,0,404,384,1,0,0,0,404,389,1,0,0,0,404,394,1,0,0,0,404,399,
        1,0,0,0,405,35,1,0,0,0,406,407,5,29,0,0,407,409,3,52,26,0,408,410,
        7,2,0,0,409,408,1,0,0,0,409,410,1,0,0,0,410,418,1,0,0,0,411,412,
        5,4,0,0,412,414,3,52,26,0,413,415,7,2,0,0,414,413,1,0,0,0,414,415,
        1,0,0,0,415,417,1,0,0,0,416,411,1,0,0,0,417,420,1,0,0,0,418,416,
        1,0,0,0,418,419,1,0,0,0,419,37,1,0,0,0,420,418,1,0,0,0,421,422,5,
        32,0,0,422,425,3,44,22,0,423,424,5,33,0,0,424,426,3,44,22,0,425,
        423,1,0,0,0,425,426,1,0,0,0,426,39,1,0,0,0,427,428,3,44,22,0,428,
        429,3,42,21,0,429,41,1,0,0,0,430,431,7,3,0,0,431,43,1,0,0,0,432,
        433,5,67,0,0,433,45,1,0,0,0,434,435,7,4,0,0,435,47,1,0,0,0,436,437,
        7,4,0,0,437,49,1,0,0,0,438,439,5,68,0,0,439,51,1,0,0,0,440,441,5,
        68,0,0,441,53,1,0,0,0,35,59,62,72,75,78,81,84,87,95,117,126,130,
        134,138,155,169,180,191,202,204,206,217,225,227,315,334,340,348,
        357,367,404,409,414,418,425
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
                     "<INVALID>", "<INVALID>", "<INVALID>", "<INVALID>", 
                     "'*'" ]

    symbolicNames = [ "<INVALID>", "<INVALID>", "<INVALID>", "<INVALID>", 
                      "<INVALID>", "<INVALID>", "<INVALID>", "Select", "As", 
                      "InWindow", "InWin", "During", "Within", "Unr", "Not", 
                      "And", "Or", "FollowedBy", "PrecededBy", "NotFollowedBy", 
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
    RULE_bool_restriction = 9
    RULE_condition = 10
    RULE_temporal_filter = 11
    RULE_timestamp = 12
    RULE_groupby_clause = 13
    RULE_groupby_field = 14
    RULE_temporal_group_func = 15
    RULE_aggregate_clause = 16
    RULE_aggregation_func = 17
    RULE_orderby_clause = 18
    RULE_limit_clause = 19
    RULE_time_value = 20
    RULE_time_unit = 21
    RULE_number = 22
    RULE_hdict = 23
    RULE_huser = 24
    RULE_feature_name = 25
    RULE_field_name = 26

    ruleNames =  [ "query", "body", "query_seq", "query_seq_continuation", 
                   "positional_op", "restrictions", "named_restriction", 
                   "quantifier", "restriction", "bool_restriction", "condition", 
                   "temporal_filter", "timestamp", "groupby_clause", "groupby_field", 
                   "temporal_group_func", "aggregate_clause", "aggregation_func", 
                   "orderby_clause", "limit_clause", "time_value", "time_unit", 
                   "number", "hdict", "huser", "feature_name", "field_name" ]

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
    During=11
    Within=12
    Unr=13
    Not=14
    And=15
    Or=16
    FollowedBy=17
    PrecededBy=18
    NotFollowedBy=19
    NotPrecededBy=20
    Aggregate=21
    GroupBy=22
    Count=23
    Distinct=24
    Sum=25
    Avg=26
    Min=27
    Max=28
    OrderBy=29
    Asc=30
    Desc=31
    Limit=32
    Offset=33
    Before=34
    After=35
    Between=36
    Ago=37
    Seconds=38
    Minutes=39
    Hours=40
    Days=41
    Weeks=42
    Months=43
    Years=44
    Contains=45
    ContainsTokens=46
    ContainsPhrase=47
    From=48
    MentionsUser=49
    IsQuestion=50
    MentionsDate=51
    MentionsTime=52
    MentionsPlace=53
    MentionsOrg=54
    ContainsLink=55
    HasFeature=56
    LabeledAs=57
    HasWordOfDict=58
    HasTime=59
    HasLocation=60
    HasOrganization=61
    HasURL=62
    HasDate=63
    HasQuestion=64
    HasUserMentioned=65
    ByUser=66
    INTEGER=67
    STRING=68
    QUOTED_STRING=69
    VARIABLE=70
    WILDCARD=71
    WS=72

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
            self.state = 54
            self.match(PrismQLParser.Select)
            self.state = 55
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

        def During(self):
            return self.getToken(PrismQLParser.During, 0)

        def time_value(self):
            return self.getTypedRuleContext(PrismQLParser.Time_valueContext,0)


        def Within(self):
            return self.getToken(PrismQLParser.Within, 0)

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
            self.state = 59
            self._errHandler.sync(self)
            la_ = self._interp.adaptivePredict(self._input,0,self._ctx)
            if la_ == 1:
                self.state = 57
                self.query_seq()
                pass

            elif la_ == 2:
                self.state = 58
                self.restrictions()
                pass


            self.state = 62
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if _la==1:
                self.state = 61
                self.match(PrismQLParser.T__0)


            self.state = 72
            self._errHandler.sync(self)
            token = self._input.LA(1)
            if token in [9]:
                self.state = 64
                self.match(PrismQLParser.InWindow)
                self.state = 65
                self.number()
                pass
            elif token in [10]:
                self.state = 66
                self.match(PrismQLParser.InWin)
                self.state = 67
                self.number()
                pass
            elif token in [11]:
                self.state = 68
                self.match(PrismQLParser.During)
                self.state = 69
                self.time_value()
                pass
            elif token in [12]:
                self.state = 70
                self.match(PrismQLParser.Within)
                self.state = 71
                self.time_value()
                pass
            elif token in [3, 21, 22, 29, 32, 34, 35, 36]:
                pass
            else:
                pass
            self.state = 75
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if (((_la) & ~0x3f) == 0 and ((1 << _la) & 120259084288) != 0):
                self.state = 74
                self.temporal_filter()


            self.state = 78
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if _la==22:
                self.state = 77
                self.groupby_clause()


            self.state = 81
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if _la==21:
                self.state = 80
                self.aggregate_clause()


            self.state = 84
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if _la==29:
                self.state = 83
                self.orderby_clause()


            self.state = 87
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if _la==32:
                self.state = 86
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
            self.state = 89
            self.match(PrismQLParser.T__1)
            self.state = 90
            self.query()
            self.state = 91
            self.match(PrismQLParser.T__2)
            self.state = 95
            self._errHandler.sync(self)
            _alt = self._interp.adaptivePredict(self._input,8,self._ctx)
            while _alt!=2 and _alt!=ATN.INVALID_ALT_NUMBER:
                if _alt==1:
                    self.state = 92
                    self.query_seq_continuation() 
                self.state = 97
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
            self.state = 117
            self._errHandler.sync(self)
            la_ = self._interp.adaptivePredict(self._input,9,self._ctx)
            if la_ == 1:
                localctx = PrismQLParser.UnorderedSubqueryContext(self, localctx)
                self.enterOuterAlt(localctx, 1)
                self.state = 98
                self.match(PrismQLParser.T__0)
                self.state = 99
                self.match(PrismQLParser.T__1)
                self.state = 100
                self.query()
                self.state = 101
                self.match(PrismQLParser.T__2)
                pass

            elif la_ == 2:
                localctx = PrismQLParser.PositionalSubqueryContext(self, localctx)
                self.enterOuterAlt(localctx, 2)
                self.state = 103
                self.positional_op()
                self.state = 104
                self.match(PrismQLParser.T__1)
                self.state = 105
                self.query()
                self.state = 106
                self.match(PrismQLParser.T__2)
                self.state = 107
                self.match(PrismQLParser.InWindow)
                self.state = 108
                self.number()
                pass

            elif la_ == 3:
                localctx = PrismQLParser.PositionalSubqueryDeprecatedContext(self, localctx)
                self.enterOuterAlt(localctx, 3)
                self.state = 110
                self.positional_op()
                self.state = 111
                self.match(PrismQLParser.T__1)
                self.state = 112
                self.query()
                self.state = 113
                self.match(PrismQLParser.T__2)
                self.state = 114
                self.match(PrismQLParser.Within)
                self.state = 115
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
            self.state = 119
            _la = self._input.LA(1)
            if not((((_la) & ~0x3f) == 0 and ((1 << _la) & 1966080) != 0)):
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
            self.state = 121
            self.named_restriction()
            self.state = 126
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            while _la==4:
                self.state = 122
                self.match(PrismQLParser.T__3)
                self.state = 123
                self.named_restriction()
                self.state = 128
                self._errHandler.sync(self)
                _la = self._input.LA(1)

            self.state = 130
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if _la==13:
                self.state = 129
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
            self.state = 132
            self.restriction(0)
            self.state = 134
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if _la==5:
                self.state = 133
                self.quantifier()


            self.state = 138
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if _la==8:
                self.state = 136
                self.match(PrismQLParser.As)
                self.state = 137
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
            self.state = 155
            self._errHandler.sync(self)
            la_ = self._interp.adaptivePredict(self._input,14,self._ctx)
            if la_ == 1:
                localctx = PrismQLParser.ExactQuantifierContext(self, localctx)
                self.enterOuterAlt(localctx, 1)
                self.state = 140
                self.match(PrismQLParser.T__4)
                self.state = 141
                self.number()
                self.state = 142
                self.match(PrismQLParser.T__5)
                pass

            elif la_ == 2:
                localctx = PrismQLParser.AtLeastQuantifierContext(self, localctx)
                self.enterOuterAlt(localctx, 2)
                self.state = 144
                self.match(PrismQLParser.T__4)
                self.state = 145
                self.number()
                self.state = 146
                self.match(PrismQLParser.T__3)
                self.state = 147
                self.match(PrismQLParser.T__5)
                pass

            elif la_ == 3:
                localctx = PrismQLParser.RangeQuantifierContext(self, localctx)
                self.enterOuterAlt(localctx, 3)
                self.state = 149
                self.match(PrismQLParser.T__4)
                self.state = 150
                self.number()
                self.state = 151
                self.match(PrismQLParser.T__3)
                self.state = 152
                self.number()
                self.state = 153
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

        def bool_restriction(self):
            return self.getTypedRuleContext(PrismQLParser.Bool_restrictionContext,0)


        def restriction(self):
            return self.getTypedRuleContext(PrismQLParser.RestrictionContext,0)


        def FollowedBy(self):
            return self.getToken(PrismQLParser.FollowedBy, 0)

        def InWindow(self):
            return self.getToken(PrismQLParser.InWindow, 0)

        def number(self):
            return self.getTypedRuleContext(PrismQLParser.NumberContext,0)


        def During(self):
            return self.getToken(PrismQLParser.During, 0)

        def time_value(self):
            return self.getTypedRuleContext(PrismQLParser.Time_valueContext,0)


        def Within(self):
            return self.getToken(PrismQLParser.Within, 0)

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
            self.state = 158
            self.bool_restriction(0)
            self._ctx.stop = self._input.LT(-1)
            self.state = 206
            self._errHandler.sync(self)
            _alt = self._interp.adaptivePredict(self._input,20,self._ctx)
            while _alt!=2 and _alt!=ATN.INVALID_ALT_NUMBER:
                if _alt==1:
                    if self._parseListeners is not None:
                        self.triggerExitRuleEvent()
                    _prevctx = localctx
                    self.state = 204
                    self._errHandler.sync(self)
                    la_ = self._interp.adaptivePredict(self._input,19,self._ctx)
                    if la_ == 1:
                        localctx = PrismQLParser.RestrictionContext(self, _parentctx, _parentState)
                        self.pushNewRecursionContext(localctx, _startState, self.RULE_restriction)
                        self.state = 160
                        if not self.precpred(self._ctx, 5):
                            from antlr4.error.Errors import FailedPredicateException
                            raise FailedPredicateException(self, "self.precpred(self._ctx, 5)")
                        self.state = 161
                        self.match(PrismQLParser.FollowedBy)
                        self.state = 162
                        self.bool_restriction(0)
                        self.state = 169
                        self._errHandler.sync(self)
                        la_ = self._interp.adaptivePredict(self._input,15,self._ctx)
                        if la_ == 1:
                            self.state = 163
                            self.match(PrismQLParser.InWindow)
                            self.state = 164
                            self.number()

                        elif la_ == 2:
                            self.state = 165
                            self.match(PrismQLParser.During)
                            self.state = 166
                            self.time_value()

                        elif la_ == 3:
                            self.state = 167
                            self.match(PrismQLParser.Within)
                            self.state = 168
                            self.number()


                        pass

                    elif la_ == 2:
                        localctx = PrismQLParser.RestrictionContext(self, _parentctx, _parentState)
                        self.pushNewRecursionContext(localctx, _startState, self.RULE_restriction)
                        self.state = 171
                        if not self.precpred(self._ctx, 4):
                            from antlr4.error.Errors import FailedPredicateException
                            raise FailedPredicateException(self, "self.precpred(self._ctx, 4)")
                        self.state = 172
                        self.match(PrismQLParser.PrecededBy)
                        self.state = 173
                        self.bool_restriction(0)
                        self.state = 180
                        self._errHandler.sync(self)
                        la_ = self._interp.adaptivePredict(self._input,16,self._ctx)
                        if la_ == 1:
                            self.state = 174
                            self.match(PrismQLParser.InWindow)
                            self.state = 175
                            self.number()

                        elif la_ == 2:
                            self.state = 176
                            self.match(PrismQLParser.During)
                            self.state = 177
                            self.time_value()

                        elif la_ == 3:
                            self.state = 178
                            self.match(PrismQLParser.Within)
                            self.state = 179
                            self.number()


                        pass

                    elif la_ == 3:
                        localctx = PrismQLParser.RestrictionContext(self, _parentctx, _parentState)
                        self.pushNewRecursionContext(localctx, _startState, self.RULE_restriction)
                        self.state = 182
                        if not self.precpred(self._ctx, 3):
                            from antlr4.error.Errors import FailedPredicateException
                            raise FailedPredicateException(self, "self.precpred(self._ctx, 3)")
                        self.state = 183
                        self.match(PrismQLParser.NotFollowedBy)
                        self.state = 184
                        self.bool_restriction(0)
                        self.state = 191
                        self._errHandler.sync(self)
                        la_ = self._interp.adaptivePredict(self._input,17,self._ctx)
                        if la_ == 1:
                            self.state = 185
                            self.match(PrismQLParser.InWindow)
                            self.state = 186
                            self.number()

                        elif la_ == 2:
                            self.state = 187
                            self.match(PrismQLParser.During)
                            self.state = 188
                            self.time_value()

                        elif la_ == 3:
                            self.state = 189
                            self.match(PrismQLParser.Within)
                            self.state = 190
                            self.number()


                        pass

                    elif la_ == 4:
                        localctx = PrismQLParser.RestrictionContext(self, _parentctx, _parentState)
                        self.pushNewRecursionContext(localctx, _startState, self.RULE_restriction)
                        self.state = 193
                        if not self.precpred(self._ctx, 2):
                            from antlr4.error.Errors import FailedPredicateException
                            raise FailedPredicateException(self, "self.precpred(self._ctx, 2)")
                        self.state = 194
                        self.match(PrismQLParser.NotPrecededBy)
                        self.state = 195
                        self.bool_restriction(0)
                        self.state = 202
                        self._errHandler.sync(self)
                        la_ = self._interp.adaptivePredict(self._input,18,self._ctx)
                        if la_ == 1:
                            self.state = 196
                            self.match(PrismQLParser.InWindow)
                            self.state = 197
                            self.number()

                        elif la_ == 2:
                            self.state = 198
                            self.match(PrismQLParser.During)
                            self.state = 199
                            self.time_value()

                        elif la_ == 3:
                            self.state = 200
                            self.match(PrismQLParser.Within)
                            self.state = 201
                            self.number()


                        pass

             
                self.state = 208
                self._errHandler.sync(self)
                _alt = self._interp.adaptivePredict(self._input,20,self._ctx)

        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.unrollRecursionContexts(_parentctx)
        return localctx


    class Bool_restrictionContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def Not(self):
            return self.getToken(PrismQLParser.Not, 0)

        def bool_restriction(self, i:int=None):
            if i is None:
                return self.getTypedRuleContexts(PrismQLParser.Bool_restrictionContext)
            else:
                return self.getTypedRuleContext(PrismQLParser.Bool_restrictionContext,i)


        def restriction(self):
            return self.getTypedRuleContext(PrismQLParser.RestrictionContext,0)


        def condition(self):
            return self.getTypedRuleContext(PrismQLParser.ConditionContext,0)


        def And(self):
            return self.getToken(PrismQLParser.And, 0)

        def Or(self):
            return self.getToken(PrismQLParser.Or, 0)

        def getRuleIndex(self):
            return PrismQLParser.RULE_bool_restriction

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitBool_restriction" ):
                return visitor.visitBool_restriction(self)
            else:
                return visitor.visitChildren(self)



    def bool_restriction(self, _p:int=0):
        _parentctx = self._ctx
        _parentState = self.state
        localctx = PrismQLParser.Bool_restrictionContext(self, self._ctx, _parentState)
        _prevctx = localctx
        _startState = 18
        self.enterRecursionRule(localctx, 18, self.RULE_bool_restriction, _p)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 217
            self._errHandler.sync(self)
            token = self._input.LA(1)
            if token in [14]:
                self.state = 210
                self.match(PrismQLParser.Not)
                self.state = 211
                self.bool_restriction(5)
                pass
            elif token in [2]:
                self.state = 212
                self.match(PrismQLParser.T__1)
                self.state = 213
                self.restriction(0)
                self.state = 214
                self.match(PrismQLParser.T__2)
                pass
            elif token in [45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66]:
                self.state = 216
                self.condition()
                pass
            else:
                raise NoViableAltException(self)

            self._ctx.stop = self._input.LT(-1)
            self.state = 227
            self._errHandler.sync(self)
            _alt = self._interp.adaptivePredict(self._input,23,self._ctx)
            while _alt!=2 and _alt!=ATN.INVALID_ALT_NUMBER:
                if _alt==1:
                    if self._parseListeners is not None:
                        self.triggerExitRuleEvent()
                    _prevctx = localctx
                    self.state = 225
                    self._errHandler.sync(self)
                    la_ = self._interp.adaptivePredict(self._input,22,self._ctx)
                    if la_ == 1:
                        localctx = PrismQLParser.Bool_restrictionContext(self, _parentctx, _parentState)
                        self.pushNewRecursionContext(localctx, _startState, self.RULE_bool_restriction)
                        self.state = 219
                        if not self.precpred(self._ctx, 4):
                            from antlr4.error.Errors import FailedPredicateException
                            raise FailedPredicateException(self, "self.precpred(self._ctx, 4)")
                        self.state = 220
                        self.match(PrismQLParser.And)
                        self.state = 221
                        self.bool_restriction(5)
                        pass

                    elif la_ == 2:
                        localctx = PrismQLParser.Bool_restrictionContext(self, _parentctx, _parentState)
                        self.pushNewRecursionContext(localctx, _startState, self.RULE_bool_restriction)
                        self.state = 222
                        if not self.precpred(self._ctx, 3):
                            from antlr4.error.Errors import FailedPredicateException
                            raise FailedPredicateException(self, "self.precpred(self._ctx, 3)")
                        self.state = 223
                        self.match(PrismQLParser.Or)
                        self.state = 224
                        self.bool_restriction(4)
                        pass

             
                self.state = 229
                self._errHandler.sync(self)
                _alt = self._interp.adaptivePredict(self._input,23,self._ctx)

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
        self.enterRule(localctx, 20, self.RULE_condition)
        try:
            self.state = 315
            self._errHandler.sync(self)
            token = self._input.LA(1)
            if token in [45]:
                self.enterOuterAlt(localctx, 1)
                self.state = 230
                self.match(PrismQLParser.Contains)
                self.state = 231
                self.match(PrismQLParser.T__1)
                self.state = 232
                self.hdict()
                self.state = 233
                self.match(PrismQLParser.T__2)
                pass
            elif token in [46]:
                self.enterOuterAlt(localctx, 2)
                self.state = 235
                self.match(PrismQLParser.ContainsTokens)
                self.state = 236
                self.match(PrismQLParser.T__1)
                self.state = 237
                self.hdict()
                self.state = 238
                self.match(PrismQLParser.T__2)
                pass
            elif token in [47]:
                self.enterOuterAlt(localctx, 3)
                self.state = 240
                self.match(PrismQLParser.ContainsPhrase)
                self.state = 241
                self.match(PrismQLParser.T__1)
                self.state = 242
                self.match(PrismQLParser.QUOTED_STRING)
                self.state = 243
                self.match(PrismQLParser.T__2)
                pass
            elif token in [48]:
                self.enterOuterAlt(localctx, 4)
                self.state = 244
                self.match(PrismQLParser.From)
                self.state = 245
                self.match(PrismQLParser.T__1)
                self.state = 246
                self.huser()
                self.state = 247
                self.match(PrismQLParser.T__2)
                pass
            elif token in [49]:
                self.enterOuterAlt(localctx, 5)
                self.state = 249
                self.match(PrismQLParser.MentionsUser)
                self.state = 250
                self.match(PrismQLParser.T__1)
                self.state = 251
                self.huser()
                self.state = 252
                self.match(PrismQLParser.T__2)
                pass
            elif token in [50]:
                self.enterOuterAlt(localctx, 6)
                self.state = 254
                self.match(PrismQLParser.IsQuestion)
                self.state = 255
                self.match(PrismQLParser.T__1)
                self.state = 256
                self.match(PrismQLParser.T__2)
                pass
            elif token in [51]:
                self.enterOuterAlt(localctx, 7)
                self.state = 257
                self.match(PrismQLParser.MentionsDate)
                self.state = 258
                self.match(PrismQLParser.T__1)
                self.state = 259
                self.match(PrismQLParser.T__2)
                pass
            elif token in [52]:
                self.enterOuterAlt(localctx, 8)
                self.state = 260
                self.match(PrismQLParser.MentionsTime)
                self.state = 261
                self.match(PrismQLParser.T__1)
                self.state = 262
                self.match(PrismQLParser.T__2)
                pass
            elif token in [53]:
                self.enterOuterAlt(localctx, 9)
                self.state = 263
                self.match(PrismQLParser.MentionsPlace)
                self.state = 264
                self.match(PrismQLParser.T__1)
                self.state = 265
                self.match(PrismQLParser.T__2)
                pass
            elif token in [54]:
                self.enterOuterAlt(localctx, 10)
                self.state = 266
                self.match(PrismQLParser.MentionsOrg)
                self.state = 267
                self.match(PrismQLParser.T__1)
                self.state = 268
                self.match(PrismQLParser.T__2)
                pass
            elif token in [55]:
                self.enterOuterAlt(localctx, 11)
                self.state = 269
                self.match(PrismQLParser.ContainsLink)
                self.state = 270
                self.match(PrismQLParser.T__1)
                self.state = 271
                self.match(PrismQLParser.T__2)
                pass
            elif token in [56]:
                self.enterOuterAlt(localctx, 12)
                self.state = 272
                self.match(PrismQLParser.HasFeature)
                self.state = 273
                self.match(PrismQLParser.T__1)
                self.state = 274
                self.feature_name()
                self.state = 275
                self.match(PrismQLParser.T__2)
                pass
            elif token in [57]:
                self.enterOuterAlt(localctx, 13)
                self.state = 277
                self.match(PrismQLParser.LabeledAs)
                self.state = 278
                self.match(PrismQLParser.T__1)
                self.state = 279
                self.feature_name()
                self.state = 280
                self.match(PrismQLParser.T__2)
                pass
            elif token in [58]:
                self.enterOuterAlt(localctx, 14)
                self.state = 282
                self.match(PrismQLParser.HasWordOfDict)
                self.state = 283
                self.match(PrismQLParser.T__1)
                self.state = 284
                self.hdict()
                self.state = 285
                self.match(PrismQLParser.T__2)
                pass
            elif token in [66]:
                self.enterOuterAlt(localctx, 15)
                self.state = 287
                self.match(PrismQLParser.ByUser)
                self.state = 288
                self.match(PrismQLParser.T__1)
                self.state = 289
                self.huser()
                self.state = 290
                self.match(PrismQLParser.T__2)
                pass
            elif token in [65]:
                self.enterOuterAlt(localctx, 16)
                self.state = 292
                self.match(PrismQLParser.HasUserMentioned)
                self.state = 293
                self.match(PrismQLParser.T__1)
                self.state = 294
                self.huser()
                self.state = 295
                self.match(PrismQLParser.T__2)
                pass
            elif token in [64]:
                self.enterOuterAlt(localctx, 17)
                self.state = 297
                self.match(PrismQLParser.HasQuestion)
                self.state = 298
                self.match(PrismQLParser.T__1)
                self.state = 299
                self.match(PrismQLParser.T__2)
                pass
            elif token in [63]:
                self.enterOuterAlt(localctx, 18)
                self.state = 300
                self.match(PrismQLParser.HasDate)
                self.state = 301
                self.match(PrismQLParser.T__1)
                self.state = 302
                self.match(PrismQLParser.T__2)
                pass
            elif token in [59]:
                self.enterOuterAlt(localctx, 19)
                self.state = 303
                self.match(PrismQLParser.HasTime)
                self.state = 304
                self.match(PrismQLParser.T__1)
                self.state = 305
                self.match(PrismQLParser.T__2)
                pass
            elif token in [60]:
                self.enterOuterAlt(localctx, 20)
                self.state = 306
                self.match(PrismQLParser.HasLocation)
                self.state = 307
                self.match(PrismQLParser.T__1)
                self.state = 308
                self.match(PrismQLParser.T__2)
                pass
            elif token in [61]:
                self.enterOuterAlt(localctx, 21)
                self.state = 309
                self.match(PrismQLParser.HasOrganization)
                self.state = 310
                self.match(PrismQLParser.T__1)
                self.state = 311
                self.match(PrismQLParser.T__2)
                pass
            elif token in [62]:
                self.enterOuterAlt(localctx, 22)
                self.state = 312
                self.match(PrismQLParser.HasURL)
                self.state = 313
                self.match(PrismQLParser.T__1)
                self.state = 314
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
        self.enterRule(localctx, 22, self.RULE_temporal_filter)
        try:
            self.state = 334
            self._errHandler.sync(self)
            token = self._input.LA(1)
            if token in [34]:
                self.enterOuterAlt(localctx, 1)
                self.state = 317
                self.match(PrismQLParser.Before)
                self.state = 318
                self.match(PrismQLParser.T__1)
                self.state = 319
                self.timestamp()
                self.state = 320
                self.match(PrismQLParser.T__2)
                pass
            elif token in [35]:
                self.enterOuterAlt(localctx, 2)
                self.state = 322
                self.match(PrismQLParser.After)
                self.state = 323
                self.match(PrismQLParser.T__1)
                self.state = 324
                self.timestamp()
                self.state = 325
                self.match(PrismQLParser.T__2)
                pass
            elif token in [36]:
                self.enterOuterAlt(localctx, 3)
                self.state = 327
                self.match(PrismQLParser.Between)
                self.state = 328
                self.match(PrismQLParser.T__1)
                self.state = 329
                self.timestamp()
                self.state = 330
                self.match(PrismQLParser.T__3)
                self.state = 331
                self.timestamp()
                self.state = 332
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
        self.enterRule(localctx, 24, self.RULE_timestamp)
        try:
            self.state = 340
            self._errHandler.sync(self)
            token = self._input.LA(1)
            if token in [69]:
                localctx = PrismQLParser.AbsoluteTimestampContext(self, localctx)
                self.enterOuterAlt(localctx, 1)
                self.state = 336
                self.match(PrismQLParser.QUOTED_STRING)
                pass
            elif token in [67]:
                localctx = PrismQLParser.RelativeTimestampContext(self, localctx)
                self.enterOuterAlt(localctx, 2)
                self.state = 337
                self.time_value()
                self.state = 338
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
        self.enterRule(localctx, 26, self.RULE_groupby_clause)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 342
            self.match(PrismQLParser.GroupBy)
            self.state = 343
            self.groupby_field()
            self.state = 348
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            while _la==4:
                self.state = 344
                self.match(PrismQLParser.T__3)
                self.state = 345
                self.groupby_field()
                self.state = 350
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
        self.enterRule(localctx, 28, self.RULE_groupby_field)
        try:
            self.state = 357
            self._errHandler.sync(self)
            token = self._input.LA(1)
            if token in [68]:
                localctx = PrismQLParser.SimpleGroupByContext(self, localctx)
                self.enterOuterAlt(localctx, 1)
                self.state = 351
                self.field_name()
                pass
            elif token in [40, 41, 42, 43, 44]:
                localctx = PrismQLParser.TemporalGroupByContext(self, localctx)
                self.enterOuterAlt(localctx, 2)
                self.state = 352
                self.temporal_group_func()
                self.state = 353
                self.match(PrismQLParser.T__1)
                self.state = 354
                self.field_name()
                self.state = 355
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
        self.enterRule(localctx, 30, self.RULE_temporal_group_func)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 359
            _la = self._input.LA(1)
            if not((((_la) & ~0x3f) == 0 and ((1 << _la) & 34084860461056) != 0)):
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
        self.enterRule(localctx, 32, self.RULE_aggregate_clause)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 361
            self.match(PrismQLParser.Aggregate)
            self.state = 362
            self.aggregation_func()
            self.state = 367
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            while _la==4:
                self.state = 363
                self.match(PrismQLParser.T__3)
                self.state = 364
                self.aggregation_func()
                self.state = 369
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
        self.enterRule(localctx, 34, self.RULE_aggregation_func)
        try:
            self.state = 404
            self._errHandler.sync(self)
            la_ = self._interp.adaptivePredict(self._input,30,self._ctx)
            if la_ == 1:
                localctx = PrismQLParser.CountAllContext(self, localctx)
                self.enterOuterAlt(localctx, 1)
                self.state = 370
                self.match(PrismQLParser.Count)
                self.state = 371
                self.match(PrismQLParser.T__1)
                self.state = 372
                self.match(PrismQLParser.T__2)
                pass

            elif la_ == 2:
                localctx = PrismQLParser.CountDistinctContext(self, localctx)
                self.enterOuterAlt(localctx, 2)
                self.state = 373
                self.match(PrismQLParser.Count)
                self.state = 374
                self.match(PrismQLParser.T__1)
                self.state = 375
                self.match(PrismQLParser.Distinct)
                self.state = 376
                self.field_name()
                self.state = 377
                self.match(PrismQLParser.T__2)
                pass

            elif la_ == 3:
                localctx = PrismQLParser.DistinctValuesContext(self, localctx)
                self.enterOuterAlt(localctx, 3)
                self.state = 379
                self.match(PrismQLParser.Distinct)
                self.state = 380
                self.match(PrismQLParser.T__1)
                self.state = 381
                self.field_name()
                self.state = 382
                self.match(PrismQLParser.T__2)
                pass

            elif la_ == 4:
                localctx = PrismQLParser.SumFuncContext(self, localctx)
                self.enterOuterAlt(localctx, 4)
                self.state = 384
                self.match(PrismQLParser.Sum)
                self.state = 385
                self.match(PrismQLParser.T__1)
                self.state = 386
                self.field_name()
                self.state = 387
                self.match(PrismQLParser.T__2)
                pass

            elif la_ == 5:
                localctx = PrismQLParser.AvgFuncContext(self, localctx)
                self.enterOuterAlt(localctx, 5)
                self.state = 389
                self.match(PrismQLParser.Avg)
                self.state = 390
                self.match(PrismQLParser.T__1)
                self.state = 391
                self.field_name()
                self.state = 392
                self.match(PrismQLParser.T__2)
                pass

            elif la_ == 6:
                localctx = PrismQLParser.MinFuncContext(self, localctx)
                self.enterOuterAlt(localctx, 6)
                self.state = 394
                self.match(PrismQLParser.Min)
                self.state = 395
                self.match(PrismQLParser.T__1)
                self.state = 396
                self.field_name()
                self.state = 397
                self.match(PrismQLParser.T__2)
                pass

            elif la_ == 7:
                localctx = PrismQLParser.MaxFuncContext(self, localctx)
                self.enterOuterAlt(localctx, 7)
                self.state = 399
                self.match(PrismQLParser.Max)
                self.state = 400
                self.match(PrismQLParser.T__1)
                self.state = 401
                self.field_name()
                self.state = 402
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
        self.enterRule(localctx, 36, self.RULE_orderby_clause)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 406
            self.match(PrismQLParser.OrderBy)
            self.state = 407
            self.field_name()
            self.state = 409
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if _la==30 or _la==31:
                self.state = 408
                _la = self._input.LA(1)
                if not(_la==30 or _la==31):
                    self._errHandler.recoverInline(self)
                else:
                    self._errHandler.reportMatch(self)
                    self.consume()


            self.state = 418
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            while _la==4:
                self.state = 411
                self.match(PrismQLParser.T__3)
                self.state = 412
                self.field_name()
                self.state = 414
                self._errHandler.sync(self)
                _la = self._input.LA(1)
                if _la==30 or _la==31:
                    self.state = 413
                    _la = self._input.LA(1)
                    if not(_la==30 or _la==31):
                        self._errHandler.recoverInline(self)
                    else:
                        self._errHandler.reportMatch(self)
                        self.consume()


                self.state = 420
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
        self.enterRule(localctx, 38, self.RULE_limit_clause)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 421
            self.match(PrismQLParser.Limit)
            self.state = 422
            self.number()
            self.state = 425
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if _la==33:
                self.state = 423
                self.match(PrismQLParser.Offset)
                self.state = 424
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
        self.enterRule(localctx, 40, self.RULE_time_value)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 427
            self.number()
            self.state = 428
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
        self.enterRule(localctx, 42, self.RULE_time_unit)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 430
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
        self.enterRule(localctx, 44, self.RULE_number)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 432
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
        self.enterRule(localctx, 46, self.RULE_hdict)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 434
            _la = self._input.LA(1)
            if not(((((_la - 68)) & ~0x3f) == 0 and ((1 << (_la - 68)) & 13) != 0)):
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
        self.enterRule(localctx, 48, self.RULE_huser)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 436
            _la = self._input.LA(1)
            if not(((((_la - 68)) & ~0x3f) == 0 and ((1 << (_la - 68)) & 13) != 0)):
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
        self.enterRule(localctx, 50, self.RULE_feature_name)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 438
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
        self.enterRule(localctx, 52, self.RULE_field_name)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 440
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
        self._predicates[9] = self.bool_restriction_sempred
        pred = self._predicates.get(ruleIndex, None)
        if pred is None:
            raise Exception("No predicate with index:" + str(ruleIndex))
        else:
            return pred(localctx, predIndex)

    def restriction_sempred(self, localctx:RestrictionContext, predIndex:int):
            if predIndex == 0:
                return self.precpred(self._ctx, 5)
         

            if predIndex == 1:
                return self.precpred(self._ctx, 4)
         

            if predIndex == 2:
                return self.precpred(self._ctx, 3)
         

            if predIndex == 3:
                return self.precpred(self._ctx, 2)
         

    def bool_restriction_sempred(self, localctx:Bool_restrictionContext, predIndex:int):
            if predIndex == 4:
                return self.precpred(self._ctx, 4)
         

            if predIndex == 5:
                return self.precpred(self._ctx, 3)
         




