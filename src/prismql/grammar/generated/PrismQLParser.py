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
        4,1,72,449,2,0,7,0,2,1,7,1,2,2,7,2,2,3,7,3,2,4,7,4,2,5,7,5,2,6,7,
        6,2,7,7,7,2,8,7,8,2,9,7,9,2,10,7,10,2,11,7,11,2,12,7,12,2,13,7,13,
        2,14,7,14,2,15,7,15,2,16,7,16,2,17,7,17,2,18,7,18,2,19,7,19,2,20,
        7,20,2,21,7,21,2,22,7,22,2,23,7,23,2,24,7,24,2,25,7,25,1,0,1,0,1,
        0,1,1,1,1,3,1,58,8,1,1,1,3,1,61,8,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,
        1,1,3,1,71,8,1,1,1,3,1,74,8,1,1,1,3,1,77,8,1,1,1,3,1,80,8,1,1,1,
        3,1,83,8,1,1,1,3,1,86,8,1,1,2,1,2,1,2,1,2,5,2,92,8,2,10,2,12,2,95,
        9,2,1,3,1,3,1,3,1,3,1,3,1,3,1,3,1,3,1,3,1,3,1,3,1,3,1,3,1,3,1,3,
        1,3,1,3,1,3,1,3,3,3,116,8,3,1,4,1,4,1,5,1,5,1,5,5,5,123,8,5,10,5,
        12,5,126,9,5,1,5,3,5,129,8,5,1,6,1,6,3,6,133,8,6,1,6,1,6,3,6,137,
        8,6,1,7,1,7,1,7,1,7,1,7,1,7,1,7,1,7,1,7,1,7,1,7,1,7,1,7,1,7,1,7,
        3,7,154,8,7,1,8,1,8,1,8,1,8,1,8,1,8,1,8,1,8,3,8,164,8,8,1,8,1,8,
        1,8,1,8,1,8,1,8,1,8,1,8,1,8,1,8,1,8,1,8,1,8,3,8,179,8,8,1,8,1,8,
        1,8,1,8,1,8,1,8,1,8,3,8,188,8,8,1,8,1,8,1,8,1,8,1,8,1,8,1,8,3,8,
        197,8,8,1,8,1,8,1,8,1,8,1,8,1,8,1,8,3,8,206,8,8,1,8,1,8,1,8,1,8,
        1,8,1,8,1,8,1,8,1,8,1,8,1,8,1,8,1,8,1,8,1,8,1,8,1,8,1,8,1,8,1,8,
        1,8,1,8,1,8,1,8,5,8,232,8,8,10,8,12,8,235,9,8,1,9,1,9,1,9,1,9,1,
        9,1,9,1,9,1,9,1,9,1,9,1,9,1,9,1,9,1,9,1,9,1,9,1,9,1,9,1,9,1,9,1,
        9,1,9,1,9,1,9,1,9,1,9,1,9,1,9,1,9,1,9,1,9,1,9,1,9,1,9,1,9,1,9,1,
        9,1,9,1,9,1,9,1,9,1,9,1,9,1,9,1,9,1,9,1,9,1,9,1,9,1,9,1,9,1,9,1,
        9,1,9,1,9,1,9,1,9,1,9,1,9,1,9,1,9,1,9,1,9,1,9,1,9,1,9,1,9,1,9,1,
        9,1,9,1,9,1,9,1,9,1,9,1,9,1,9,1,9,1,9,1,9,1,9,1,9,1,9,1,9,1,9,1,
        9,3,9,322,8,9,1,10,1,10,1,10,1,10,1,10,1,10,1,10,1,10,1,10,1,10,
        1,10,1,10,1,10,1,10,1,10,1,10,1,10,3,10,341,8,10,1,11,1,11,1,11,
        1,11,3,11,347,8,11,1,12,1,12,1,12,1,12,5,12,353,8,12,10,12,12,12,
        356,9,12,1,13,1,13,1,13,1,13,1,13,1,13,3,13,364,8,13,1,14,1,14,1,
        15,1,15,1,15,1,15,5,15,372,8,15,10,15,12,15,375,9,15,1,16,1,16,1,
        16,1,16,1,16,1,16,1,16,1,16,1,16,1,16,1,16,1,16,1,16,1,16,1,16,1,
        16,1,16,1,16,1,16,1,16,1,16,1,16,1,16,1,16,1,16,1,16,1,16,1,16,1,
        16,1,16,1,16,1,16,1,16,1,16,3,16,411,8,16,1,17,1,17,1,17,3,17,416,
        8,17,1,17,1,17,1,17,3,17,421,8,17,5,17,423,8,17,10,17,12,17,426,
        9,17,1,18,1,18,1,18,1,18,3,18,432,8,18,1,19,1,19,1,19,1,20,1,20,
        1,21,1,21,1,22,1,22,1,23,1,23,1,24,1,24,1,25,1,25,1,25,0,1,16,26,
        0,2,4,6,8,10,12,14,16,18,20,22,24,26,28,30,32,34,36,38,40,42,44,
        46,48,50,0,5,1,0,17,20,1,0,40,44,1,0,30,31,1,0,38,42,2,0,68,68,70,
        71,499,0,52,1,0,0,0,2,57,1,0,0,0,4,87,1,0,0,0,6,115,1,0,0,0,8,117,
        1,0,0,0,10,119,1,0,0,0,12,130,1,0,0,0,14,153,1,0,0,0,16,163,1,0,
        0,0,18,321,1,0,0,0,20,340,1,0,0,0,22,346,1,0,0,0,24,348,1,0,0,0,
        26,363,1,0,0,0,28,365,1,0,0,0,30,367,1,0,0,0,32,410,1,0,0,0,34,412,
        1,0,0,0,36,427,1,0,0,0,38,433,1,0,0,0,40,436,1,0,0,0,42,438,1,0,
        0,0,44,440,1,0,0,0,46,442,1,0,0,0,48,444,1,0,0,0,50,446,1,0,0,0,
        52,53,5,7,0,0,53,54,3,2,1,0,54,1,1,0,0,0,55,58,3,4,2,0,56,58,3,10,
        5,0,57,55,1,0,0,0,57,56,1,0,0,0,58,60,1,0,0,0,59,61,5,1,0,0,60,59,
        1,0,0,0,60,61,1,0,0,0,61,70,1,0,0,0,62,63,5,9,0,0,63,71,3,42,21,
        0,64,65,5,10,0,0,65,71,3,42,21,0,66,67,5,11,0,0,67,71,3,38,19,0,
        68,69,5,12,0,0,69,71,3,38,19,0,70,62,1,0,0,0,70,64,1,0,0,0,70,66,
        1,0,0,0,70,68,1,0,0,0,70,71,1,0,0,0,71,73,1,0,0,0,72,74,3,20,10,
        0,73,72,1,0,0,0,73,74,1,0,0,0,74,76,1,0,0,0,75,77,3,24,12,0,76,75,
        1,0,0,0,76,77,1,0,0,0,77,79,1,0,0,0,78,80,3,30,15,0,79,78,1,0,0,
        0,79,80,1,0,0,0,80,82,1,0,0,0,81,83,3,34,17,0,82,81,1,0,0,0,82,83,
        1,0,0,0,83,85,1,0,0,0,84,86,3,36,18,0,85,84,1,0,0,0,85,86,1,0,0,
        0,86,3,1,0,0,0,87,88,5,2,0,0,88,89,3,0,0,0,89,93,5,3,0,0,90,92,3,
        6,3,0,91,90,1,0,0,0,92,95,1,0,0,0,93,91,1,0,0,0,93,94,1,0,0,0,94,
        5,1,0,0,0,95,93,1,0,0,0,96,97,5,1,0,0,97,98,5,2,0,0,98,99,3,0,0,
        0,99,100,5,3,0,0,100,116,1,0,0,0,101,102,3,8,4,0,102,103,5,2,0,0,
        103,104,3,0,0,0,104,105,5,3,0,0,105,106,5,9,0,0,106,107,3,42,21,
        0,107,116,1,0,0,0,108,109,3,8,4,0,109,110,5,2,0,0,110,111,3,0,0,
        0,111,112,5,3,0,0,112,113,5,12,0,0,113,114,3,42,21,0,114,116,1,0,
        0,0,115,96,1,0,0,0,115,101,1,0,0,0,115,108,1,0,0,0,116,7,1,0,0,0,
        117,118,7,0,0,0,118,9,1,0,0,0,119,124,3,12,6,0,120,121,5,4,0,0,121,
        123,3,12,6,0,122,120,1,0,0,0,123,126,1,0,0,0,124,122,1,0,0,0,124,
        125,1,0,0,0,125,128,1,0,0,0,126,124,1,0,0,0,127,129,5,13,0,0,128,
        127,1,0,0,0,128,129,1,0,0,0,129,11,1,0,0,0,130,132,3,16,8,0,131,
        133,3,14,7,0,132,131,1,0,0,0,132,133,1,0,0,0,133,136,1,0,0,0,134,
        135,5,8,0,0,135,137,5,69,0,0,136,134,1,0,0,0,136,137,1,0,0,0,137,
        13,1,0,0,0,138,139,5,5,0,0,139,140,3,42,21,0,140,141,5,6,0,0,141,
        154,1,0,0,0,142,143,5,5,0,0,143,144,3,42,21,0,144,145,5,4,0,0,145,
        146,5,6,0,0,146,154,1,0,0,0,147,148,5,5,0,0,148,149,3,42,21,0,149,
        150,5,4,0,0,150,151,3,42,21,0,151,152,5,6,0,0,152,154,1,0,0,0,153,
        138,1,0,0,0,153,142,1,0,0,0,153,147,1,0,0,0,154,15,1,0,0,0,155,156,
        6,8,-1,0,156,157,5,2,0,0,157,158,3,16,8,0,158,159,5,3,0,0,159,164,
        1,0,0,0,160,161,5,14,0,0,161,164,3,16,8,2,162,164,3,18,9,0,163,155,
        1,0,0,0,163,160,1,0,0,0,163,162,1,0,0,0,164,233,1,0,0,0,165,166,
        10,5,0,0,166,167,5,15,0,0,167,232,3,16,8,6,168,169,10,4,0,0,169,
        170,5,16,0,0,170,232,3,16,8,5,171,172,10,13,0,0,172,173,5,17,0,0,
        173,178,3,16,8,0,174,175,5,9,0,0,175,179,3,42,21,0,176,177,5,11,
        0,0,177,179,3,38,19,0,178,174,1,0,0,0,178,176,1,0,0,0,178,179,1,
        0,0,0,179,232,1,0,0,0,180,181,10,12,0,0,181,182,5,18,0,0,182,187,
        3,16,8,0,183,184,5,9,0,0,184,188,3,42,21,0,185,186,5,11,0,0,186,
        188,3,38,19,0,187,183,1,0,0,0,187,185,1,0,0,0,187,188,1,0,0,0,188,
        232,1,0,0,0,189,190,10,11,0,0,190,191,5,19,0,0,191,196,3,16,8,0,
        192,193,5,9,0,0,193,197,3,42,21,0,194,195,5,11,0,0,195,197,3,38,
        19,0,196,192,1,0,0,0,196,194,1,0,0,0,196,197,1,0,0,0,197,232,1,0,
        0,0,198,199,10,10,0,0,199,200,5,20,0,0,200,205,3,16,8,0,201,202,
        5,9,0,0,202,206,3,42,21,0,203,204,5,11,0,0,204,206,3,38,19,0,205,
        201,1,0,0,0,205,203,1,0,0,0,205,206,1,0,0,0,206,232,1,0,0,0,207,
        208,10,9,0,0,208,209,5,17,0,0,209,210,3,16,8,0,210,211,5,12,0,0,
        211,212,3,42,21,0,212,232,1,0,0,0,213,214,10,8,0,0,214,215,5,18,
        0,0,215,216,3,16,8,0,216,217,5,12,0,0,217,218,3,42,21,0,218,232,
        1,0,0,0,219,220,10,7,0,0,220,221,5,19,0,0,221,222,3,16,8,0,222,223,
        5,12,0,0,223,224,3,42,21,0,224,232,1,0,0,0,225,226,10,6,0,0,226,
        227,5,20,0,0,227,228,3,16,8,0,228,229,5,12,0,0,229,230,3,42,21,0,
        230,232,1,0,0,0,231,165,1,0,0,0,231,168,1,0,0,0,231,171,1,0,0,0,
        231,180,1,0,0,0,231,189,1,0,0,0,231,198,1,0,0,0,231,207,1,0,0,0,
        231,213,1,0,0,0,231,219,1,0,0,0,231,225,1,0,0,0,232,235,1,0,0,0,
        233,231,1,0,0,0,233,234,1,0,0,0,234,17,1,0,0,0,235,233,1,0,0,0,236,
        237,5,45,0,0,237,238,5,2,0,0,238,239,3,44,22,0,239,240,5,3,0,0,240,
        322,1,0,0,0,241,242,5,46,0,0,242,243,5,2,0,0,243,244,3,44,22,0,244,
        245,5,3,0,0,245,322,1,0,0,0,246,247,5,47,0,0,247,248,5,2,0,0,248,
        249,5,69,0,0,249,322,5,3,0,0,250,251,5,48,0,0,251,252,5,2,0,0,252,
        253,3,46,23,0,253,254,5,3,0,0,254,322,1,0,0,0,255,256,5,49,0,0,256,
        257,5,2,0,0,257,258,3,46,23,0,258,259,5,3,0,0,259,322,1,0,0,0,260,
        261,5,50,0,0,261,262,5,2,0,0,262,322,5,3,0,0,263,264,5,51,0,0,264,
        265,5,2,0,0,265,322,5,3,0,0,266,267,5,52,0,0,267,268,5,2,0,0,268,
        322,5,3,0,0,269,270,5,53,0,0,270,271,5,2,0,0,271,322,5,3,0,0,272,
        273,5,54,0,0,273,274,5,2,0,0,274,322,5,3,0,0,275,276,5,55,0,0,276,
        277,5,2,0,0,277,322,5,3,0,0,278,279,5,56,0,0,279,280,5,2,0,0,280,
        281,3,48,24,0,281,282,5,3,0,0,282,322,1,0,0,0,283,284,5,57,0,0,284,
        285,5,2,0,0,285,286,3,48,24,0,286,287,5,3,0,0,287,322,1,0,0,0,288,
        289,5,58,0,0,289,290,5,2,0,0,290,291,3,44,22,0,291,292,5,3,0,0,292,
        322,1,0,0,0,293,294,5,66,0,0,294,295,5,2,0,0,295,296,3,46,23,0,296,
        297,5,3,0,0,297,322,1,0,0,0,298,299,5,65,0,0,299,300,5,2,0,0,300,
        301,3,46,23,0,301,302,5,3,0,0,302,322,1,0,0,0,303,304,5,64,0,0,304,
        305,5,2,0,0,305,322,5,3,0,0,306,307,5,63,0,0,307,308,5,2,0,0,308,
        322,5,3,0,0,309,310,5,59,0,0,310,311,5,2,0,0,311,322,5,3,0,0,312,
        313,5,60,0,0,313,314,5,2,0,0,314,322,5,3,0,0,315,316,5,61,0,0,316,
        317,5,2,0,0,317,322,5,3,0,0,318,319,5,62,0,0,319,320,5,2,0,0,320,
        322,5,3,0,0,321,236,1,0,0,0,321,241,1,0,0,0,321,246,1,0,0,0,321,
        250,1,0,0,0,321,255,1,0,0,0,321,260,1,0,0,0,321,263,1,0,0,0,321,
        266,1,0,0,0,321,269,1,0,0,0,321,272,1,0,0,0,321,275,1,0,0,0,321,
        278,1,0,0,0,321,283,1,0,0,0,321,288,1,0,0,0,321,293,1,0,0,0,321,
        298,1,0,0,0,321,303,1,0,0,0,321,306,1,0,0,0,321,309,1,0,0,0,321,
        312,1,0,0,0,321,315,1,0,0,0,321,318,1,0,0,0,322,19,1,0,0,0,323,324,
        5,34,0,0,324,325,5,2,0,0,325,326,3,22,11,0,326,327,5,3,0,0,327,341,
        1,0,0,0,328,329,5,35,0,0,329,330,5,2,0,0,330,331,3,22,11,0,331,332,
        5,3,0,0,332,341,1,0,0,0,333,334,5,36,0,0,334,335,5,2,0,0,335,336,
        3,22,11,0,336,337,5,4,0,0,337,338,3,22,11,0,338,339,5,3,0,0,339,
        341,1,0,0,0,340,323,1,0,0,0,340,328,1,0,0,0,340,333,1,0,0,0,341,
        21,1,0,0,0,342,347,5,69,0,0,343,344,3,38,19,0,344,345,5,37,0,0,345,
        347,1,0,0,0,346,342,1,0,0,0,346,343,1,0,0,0,347,23,1,0,0,0,348,349,
        5,22,0,0,349,354,3,26,13,0,350,351,5,4,0,0,351,353,3,26,13,0,352,
        350,1,0,0,0,353,356,1,0,0,0,354,352,1,0,0,0,354,355,1,0,0,0,355,
        25,1,0,0,0,356,354,1,0,0,0,357,364,3,50,25,0,358,359,3,28,14,0,359,
        360,5,2,0,0,360,361,3,50,25,0,361,362,5,3,0,0,362,364,1,0,0,0,363,
        357,1,0,0,0,363,358,1,0,0,0,364,27,1,0,0,0,365,366,7,1,0,0,366,29,
        1,0,0,0,367,368,5,21,0,0,368,373,3,32,16,0,369,370,5,4,0,0,370,372,
        3,32,16,0,371,369,1,0,0,0,372,375,1,0,0,0,373,371,1,0,0,0,373,374,
        1,0,0,0,374,31,1,0,0,0,375,373,1,0,0,0,376,377,5,23,0,0,377,378,
        5,2,0,0,378,411,5,3,0,0,379,380,5,23,0,0,380,381,5,2,0,0,381,382,
        5,24,0,0,382,383,3,50,25,0,383,384,5,3,0,0,384,411,1,0,0,0,385,386,
        5,24,0,0,386,387,5,2,0,0,387,388,3,50,25,0,388,389,5,3,0,0,389,411,
        1,0,0,0,390,391,5,25,0,0,391,392,5,2,0,0,392,393,3,50,25,0,393,394,
        5,3,0,0,394,411,1,0,0,0,395,396,5,26,0,0,396,397,5,2,0,0,397,398,
        3,50,25,0,398,399,5,3,0,0,399,411,1,0,0,0,400,401,5,27,0,0,401,402,
        5,2,0,0,402,403,3,50,25,0,403,404,5,3,0,0,404,411,1,0,0,0,405,406,
        5,28,0,0,406,407,5,2,0,0,407,408,3,50,25,0,408,409,5,3,0,0,409,411,
        1,0,0,0,410,376,1,0,0,0,410,379,1,0,0,0,410,385,1,0,0,0,410,390,
        1,0,0,0,410,395,1,0,0,0,410,400,1,0,0,0,410,405,1,0,0,0,411,33,1,
        0,0,0,412,413,5,29,0,0,413,415,3,50,25,0,414,416,7,2,0,0,415,414,
        1,0,0,0,415,416,1,0,0,0,416,424,1,0,0,0,417,418,5,4,0,0,418,420,
        3,50,25,0,419,421,7,2,0,0,420,419,1,0,0,0,420,421,1,0,0,0,421,423,
        1,0,0,0,422,417,1,0,0,0,423,426,1,0,0,0,424,422,1,0,0,0,424,425,
        1,0,0,0,425,35,1,0,0,0,426,424,1,0,0,0,427,428,5,32,0,0,428,431,
        3,42,21,0,429,430,5,33,0,0,430,432,3,42,21,0,431,429,1,0,0,0,431,
        432,1,0,0,0,432,37,1,0,0,0,433,434,3,42,21,0,434,435,3,40,20,0,435,
        39,1,0,0,0,436,437,7,3,0,0,437,41,1,0,0,0,438,439,5,67,0,0,439,43,
        1,0,0,0,440,441,7,4,0,0,441,45,1,0,0,0,442,443,7,4,0,0,443,47,1,
        0,0,0,444,445,5,68,0,0,445,49,1,0,0,0,446,447,5,68,0,0,447,51,1,
        0,0,0,33,57,60,70,73,76,79,82,85,93,115,124,128,132,136,153,163,
        178,187,196,205,231,233,321,340,346,354,363,373,410,415,420,424,
        431
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


            self.state = 70
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
                self.match(PrismQLParser.During)
                self.state = 67
                self.time_value()
                pass
            elif token in [12]:
                self.state = 68
                self.match(PrismQLParser.Within)
                self.state = 69
                self.time_value()
                pass
            elif token in [3, 21, 22, 29, 32, 34, 35, 36]:
                pass
            else:
                pass
            self.state = 73
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if (((_la) & ~0x3f) == 0 and ((1 << _la) & 120259084288) != 0):
                self.state = 72
                self.temporal_filter()


            self.state = 76
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if _la==22:
                self.state = 75
                self.groupby_clause()


            self.state = 79
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if _la==21:
                self.state = 78
                self.aggregate_clause()


            self.state = 82
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if _la==29:
                self.state = 81
                self.orderby_clause()


            self.state = 85
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if _la==32:
                self.state = 84
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
            self.state = 87
            self.match(PrismQLParser.T__1)
            self.state = 88
            self.query()
            self.state = 89
            self.match(PrismQLParser.T__2)
            self.state = 93
            self._errHandler.sync(self)
            _alt = self._interp.adaptivePredict(self._input,8,self._ctx)
            while _alt!=2 and _alt!=ATN.INVALID_ALT_NUMBER:
                if _alt==1:
                    self.state = 90
                    self.query_seq_continuation() 
                self.state = 95
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
            self.state = 115
            self._errHandler.sync(self)
            la_ = self._interp.adaptivePredict(self._input,9,self._ctx)
            if la_ == 1:
                localctx = PrismQLParser.UnorderedSubqueryContext(self, localctx)
                self.enterOuterAlt(localctx, 1)
                self.state = 96
                self.match(PrismQLParser.T__0)
                self.state = 97
                self.match(PrismQLParser.T__1)
                self.state = 98
                self.query()
                self.state = 99
                self.match(PrismQLParser.T__2)
                pass

            elif la_ == 2:
                localctx = PrismQLParser.PositionalSubqueryContext(self, localctx)
                self.enterOuterAlt(localctx, 2)
                self.state = 101
                self.positional_op()
                self.state = 102
                self.match(PrismQLParser.T__1)
                self.state = 103
                self.query()
                self.state = 104
                self.match(PrismQLParser.T__2)
                self.state = 105
                self.match(PrismQLParser.InWindow)
                self.state = 106
                self.number()
                pass

            elif la_ == 3:
                localctx = PrismQLParser.PositionalSubqueryDeprecatedContext(self, localctx)
                self.enterOuterAlt(localctx, 3)
                self.state = 108
                self.positional_op()
                self.state = 109
                self.match(PrismQLParser.T__1)
                self.state = 110
                self.query()
                self.state = 111
                self.match(PrismQLParser.T__2)
                self.state = 112
                self.match(PrismQLParser.Within)
                self.state = 113
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
            self.state = 117
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
            self.state = 119
            self.named_restriction()
            self.state = 124
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            while _la==4:
                self.state = 120
                self.match(PrismQLParser.T__3)
                self.state = 121
                self.named_restriction()
                self.state = 126
                self._errHandler.sync(self)
                _la = self._input.LA(1)

            self.state = 128
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if _la==13:
                self.state = 127
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
            self.state = 130
            self.restriction(0)
            self.state = 132
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if _la==5:
                self.state = 131
                self.quantifier()


            self.state = 136
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if _la==8:
                self.state = 134
                self.match(PrismQLParser.As)
                self.state = 135
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
            self.state = 153
            self._errHandler.sync(self)
            la_ = self._interp.adaptivePredict(self._input,14,self._ctx)
            if la_ == 1:
                localctx = PrismQLParser.ExactQuantifierContext(self, localctx)
                self.enterOuterAlt(localctx, 1)
                self.state = 138
                self.match(PrismQLParser.T__4)
                self.state = 139
                self.number()
                self.state = 140
                self.match(PrismQLParser.T__5)
                pass

            elif la_ == 2:
                localctx = PrismQLParser.AtLeastQuantifierContext(self, localctx)
                self.enterOuterAlt(localctx, 2)
                self.state = 142
                self.match(PrismQLParser.T__4)
                self.state = 143
                self.number()
                self.state = 144
                self.match(PrismQLParser.T__3)
                self.state = 145
                self.match(PrismQLParser.T__5)
                pass

            elif la_ == 3:
                localctx = PrismQLParser.RangeQuantifierContext(self, localctx)
                self.enterOuterAlt(localctx, 3)
                self.state = 147
                self.match(PrismQLParser.T__4)
                self.state = 148
                self.number()
                self.state = 149
                self.match(PrismQLParser.T__3)
                self.state = 150
                self.number()
                self.state = 151
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


        def During(self):
            return self.getToken(PrismQLParser.During, 0)

        def time_value(self):
            return self.getTypedRuleContext(PrismQLParser.Time_valueContext,0)


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
            self.state = 163
            self._errHandler.sync(self)
            token = self._input.LA(1)
            if token in [2]:
                self.state = 156
                self.match(PrismQLParser.T__1)
                self.state = 157
                self.restriction(0)
                self.state = 158
                self.match(PrismQLParser.T__2)
                pass
            elif token in [14]:
                self.state = 160
                self.match(PrismQLParser.Not)
                self.state = 161
                self.restriction(2)
                pass
            elif token in [45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66]:
                self.state = 162
                self.condition()
                pass
            else:
                raise NoViableAltException(self)

            self._ctx.stop = self._input.LT(-1)
            self.state = 233
            self._errHandler.sync(self)
            _alt = self._interp.adaptivePredict(self._input,21,self._ctx)
            while _alt!=2 and _alt!=ATN.INVALID_ALT_NUMBER:
                if _alt==1:
                    if self._parseListeners is not None:
                        self.triggerExitRuleEvent()
                    _prevctx = localctx
                    self.state = 231
                    self._errHandler.sync(self)
                    la_ = self._interp.adaptivePredict(self._input,20,self._ctx)
                    if la_ == 1:
                        localctx = PrismQLParser.RestrictionContext(self, _parentctx, _parentState)
                        self.pushNewRecursionContext(localctx, _startState, self.RULE_restriction)
                        self.state = 165
                        if not self.precpred(self._ctx, 5):
                            from antlr4.error.Errors import FailedPredicateException
                            raise FailedPredicateException(self, "self.precpred(self._ctx, 5)")
                        self.state = 166
                        self.match(PrismQLParser.And)
                        self.state = 167
                        self.restriction(6)
                        pass

                    elif la_ == 2:
                        localctx = PrismQLParser.RestrictionContext(self, _parentctx, _parentState)
                        self.pushNewRecursionContext(localctx, _startState, self.RULE_restriction)
                        self.state = 168
                        if not self.precpred(self._ctx, 4):
                            from antlr4.error.Errors import FailedPredicateException
                            raise FailedPredicateException(self, "self.precpred(self._ctx, 4)")
                        self.state = 169
                        self.match(PrismQLParser.Or)
                        self.state = 170
                        self.restriction(5)
                        pass

                    elif la_ == 3:
                        localctx = PrismQLParser.RestrictionContext(self, _parentctx, _parentState)
                        self.pushNewRecursionContext(localctx, _startState, self.RULE_restriction)
                        self.state = 171
                        if not self.precpred(self._ctx, 13):
                            from antlr4.error.Errors import FailedPredicateException
                            raise FailedPredicateException(self, "self.precpred(self._ctx, 13)")
                        self.state = 172
                        self.match(PrismQLParser.FollowedBy)
                        self.state = 173
                        self.restriction(0)
                        self.state = 178
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


                        pass

                    elif la_ == 4:
                        localctx = PrismQLParser.RestrictionContext(self, _parentctx, _parentState)
                        self.pushNewRecursionContext(localctx, _startState, self.RULE_restriction)
                        self.state = 180
                        if not self.precpred(self._ctx, 12):
                            from antlr4.error.Errors import FailedPredicateException
                            raise FailedPredicateException(self, "self.precpred(self._ctx, 12)")
                        self.state = 181
                        self.match(PrismQLParser.PrecededBy)
                        self.state = 182
                        self.restriction(0)
                        self.state = 187
                        self._errHandler.sync(self)
                        la_ = self._interp.adaptivePredict(self._input,17,self._ctx)
                        if la_ == 1:
                            self.state = 183
                            self.match(PrismQLParser.InWindow)
                            self.state = 184
                            self.number()

                        elif la_ == 2:
                            self.state = 185
                            self.match(PrismQLParser.During)
                            self.state = 186
                            self.time_value()


                        pass

                    elif la_ == 5:
                        localctx = PrismQLParser.RestrictionContext(self, _parentctx, _parentState)
                        self.pushNewRecursionContext(localctx, _startState, self.RULE_restriction)
                        self.state = 189
                        if not self.precpred(self._ctx, 11):
                            from antlr4.error.Errors import FailedPredicateException
                            raise FailedPredicateException(self, "self.precpred(self._ctx, 11)")
                        self.state = 190
                        self.match(PrismQLParser.NotFollowedBy)
                        self.state = 191
                        self.restriction(0)
                        self.state = 196
                        self._errHandler.sync(self)
                        la_ = self._interp.adaptivePredict(self._input,18,self._ctx)
                        if la_ == 1:
                            self.state = 192
                            self.match(PrismQLParser.InWindow)
                            self.state = 193
                            self.number()

                        elif la_ == 2:
                            self.state = 194
                            self.match(PrismQLParser.During)
                            self.state = 195
                            self.time_value()


                        pass

                    elif la_ == 6:
                        localctx = PrismQLParser.RestrictionContext(self, _parentctx, _parentState)
                        self.pushNewRecursionContext(localctx, _startState, self.RULE_restriction)
                        self.state = 198
                        if not self.precpred(self._ctx, 10):
                            from antlr4.error.Errors import FailedPredicateException
                            raise FailedPredicateException(self, "self.precpred(self._ctx, 10)")
                        self.state = 199
                        self.match(PrismQLParser.NotPrecededBy)
                        self.state = 200
                        self.restriction(0)
                        self.state = 205
                        self._errHandler.sync(self)
                        la_ = self._interp.adaptivePredict(self._input,19,self._ctx)
                        if la_ == 1:
                            self.state = 201
                            self.match(PrismQLParser.InWindow)
                            self.state = 202
                            self.number()

                        elif la_ == 2:
                            self.state = 203
                            self.match(PrismQLParser.During)
                            self.state = 204
                            self.time_value()


                        pass

                    elif la_ == 7:
                        localctx = PrismQLParser.RestrictionContext(self, _parentctx, _parentState)
                        self.pushNewRecursionContext(localctx, _startState, self.RULE_restriction)
                        self.state = 207
                        if not self.precpred(self._ctx, 9):
                            from antlr4.error.Errors import FailedPredicateException
                            raise FailedPredicateException(self, "self.precpred(self._ctx, 9)")
                        self.state = 208
                        self.match(PrismQLParser.FollowedBy)
                        self.state = 209
                        self.restriction(0)
                        self.state = 210
                        self.match(PrismQLParser.Within)
                        self.state = 211
                        self.number()
                        pass

                    elif la_ == 8:
                        localctx = PrismQLParser.RestrictionContext(self, _parentctx, _parentState)
                        self.pushNewRecursionContext(localctx, _startState, self.RULE_restriction)
                        self.state = 213
                        if not self.precpred(self._ctx, 8):
                            from antlr4.error.Errors import FailedPredicateException
                            raise FailedPredicateException(self, "self.precpred(self._ctx, 8)")
                        self.state = 214
                        self.match(PrismQLParser.PrecededBy)
                        self.state = 215
                        self.restriction(0)
                        self.state = 216
                        self.match(PrismQLParser.Within)
                        self.state = 217
                        self.number()
                        pass

                    elif la_ == 9:
                        localctx = PrismQLParser.RestrictionContext(self, _parentctx, _parentState)
                        self.pushNewRecursionContext(localctx, _startState, self.RULE_restriction)
                        self.state = 219
                        if not self.precpred(self._ctx, 7):
                            from antlr4.error.Errors import FailedPredicateException
                            raise FailedPredicateException(self, "self.precpred(self._ctx, 7)")
                        self.state = 220
                        self.match(PrismQLParser.NotFollowedBy)
                        self.state = 221
                        self.restriction(0)
                        self.state = 222
                        self.match(PrismQLParser.Within)
                        self.state = 223
                        self.number()
                        pass

                    elif la_ == 10:
                        localctx = PrismQLParser.RestrictionContext(self, _parentctx, _parentState)
                        self.pushNewRecursionContext(localctx, _startState, self.RULE_restriction)
                        self.state = 225
                        if not self.precpred(self._ctx, 6):
                            from antlr4.error.Errors import FailedPredicateException
                            raise FailedPredicateException(self, "self.precpred(self._ctx, 6)")
                        self.state = 226
                        self.match(PrismQLParser.NotPrecededBy)
                        self.state = 227
                        self.restriction(0)
                        self.state = 228
                        self.match(PrismQLParser.Within)
                        self.state = 229
                        self.number()
                        pass

             
                self.state = 235
                self._errHandler.sync(self)
                _alt = self._interp.adaptivePredict(self._input,21,self._ctx)

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
            self.state = 321
            self._errHandler.sync(self)
            token = self._input.LA(1)
            if token in [45]:
                self.enterOuterAlt(localctx, 1)
                self.state = 236
                self.match(PrismQLParser.Contains)
                self.state = 237
                self.match(PrismQLParser.T__1)
                self.state = 238
                self.hdict()
                self.state = 239
                self.match(PrismQLParser.T__2)
                pass
            elif token in [46]:
                self.enterOuterAlt(localctx, 2)
                self.state = 241
                self.match(PrismQLParser.ContainsTokens)
                self.state = 242
                self.match(PrismQLParser.T__1)
                self.state = 243
                self.hdict()
                self.state = 244
                self.match(PrismQLParser.T__2)
                pass
            elif token in [47]:
                self.enterOuterAlt(localctx, 3)
                self.state = 246
                self.match(PrismQLParser.ContainsPhrase)
                self.state = 247
                self.match(PrismQLParser.T__1)
                self.state = 248
                self.match(PrismQLParser.QUOTED_STRING)
                self.state = 249
                self.match(PrismQLParser.T__2)
                pass
            elif token in [48]:
                self.enterOuterAlt(localctx, 4)
                self.state = 250
                self.match(PrismQLParser.From)
                self.state = 251
                self.match(PrismQLParser.T__1)
                self.state = 252
                self.huser()
                self.state = 253
                self.match(PrismQLParser.T__2)
                pass
            elif token in [49]:
                self.enterOuterAlt(localctx, 5)
                self.state = 255
                self.match(PrismQLParser.MentionsUser)
                self.state = 256
                self.match(PrismQLParser.T__1)
                self.state = 257
                self.huser()
                self.state = 258
                self.match(PrismQLParser.T__2)
                pass
            elif token in [50]:
                self.enterOuterAlt(localctx, 6)
                self.state = 260
                self.match(PrismQLParser.IsQuestion)
                self.state = 261
                self.match(PrismQLParser.T__1)
                self.state = 262
                self.match(PrismQLParser.T__2)
                pass
            elif token in [51]:
                self.enterOuterAlt(localctx, 7)
                self.state = 263
                self.match(PrismQLParser.MentionsDate)
                self.state = 264
                self.match(PrismQLParser.T__1)
                self.state = 265
                self.match(PrismQLParser.T__2)
                pass
            elif token in [52]:
                self.enterOuterAlt(localctx, 8)
                self.state = 266
                self.match(PrismQLParser.MentionsTime)
                self.state = 267
                self.match(PrismQLParser.T__1)
                self.state = 268
                self.match(PrismQLParser.T__2)
                pass
            elif token in [53]:
                self.enterOuterAlt(localctx, 9)
                self.state = 269
                self.match(PrismQLParser.MentionsPlace)
                self.state = 270
                self.match(PrismQLParser.T__1)
                self.state = 271
                self.match(PrismQLParser.T__2)
                pass
            elif token in [54]:
                self.enterOuterAlt(localctx, 10)
                self.state = 272
                self.match(PrismQLParser.MentionsOrg)
                self.state = 273
                self.match(PrismQLParser.T__1)
                self.state = 274
                self.match(PrismQLParser.T__2)
                pass
            elif token in [55]:
                self.enterOuterAlt(localctx, 11)
                self.state = 275
                self.match(PrismQLParser.ContainsLink)
                self.state = 276
                self.match(PrismQLParser.T__1)
                self.state = 277
                self.match(PrismQLParser.T__2)
                pass
            elif token in [56]:
                self.enterOuterAlt(localctx, 12)
                self.state = 278
                self.match(PrismQLParser.HasFeature)
                self.state = 279
                self.match(PrismQLParser.T__1)
                self.state = 280
                self.feature_name()
                self.state = 281
                self.match(PrismQLParser.T__2)
                pass
            elif token in [57]:
                self.enterOuterAlt(localctx, 13)
                self.state = 283
                self.match(PrismQLParser.LabeledAs)
                self.state = 284
                self.match(PrismQLParser.T__1)
                self.state = 285
                self.feature_name()
                self.state = 286
                self.match(PrismQLParser.T__2)
                pass
            elif token in [58]:
                self.enterOuterAlt(localctx, 14)
                self.state = 288
                self.match(PrismQLParser.HasWordOfDict)
                self.state = 289
                self.match(PrismQLParser.T__1)
                self.state = 290
                self.hdict()
                self.state = 291
                self.match(PrismQLParser.T__2)
                pass
            elif token in [66]:
                self.enterOuterAlt(localctx, 15)
                self.state = 293
                self.match(PrismQLParser.ByUser)
                self.state = 294
                self.match(PrismQLParser.T__1)
                self.state = 295
                self.huser()
                self.state = 296
                self.match(PrismQLParser.T__2)
                pass
            elif token in [65]:
                self.enterOuterAlt(localctx, 16)
                self.state = 298
                self.match(PrismQLParser.HasUserMentioned)
                self.state = 299
                self.match(PrismQLParser.T__1)
                self.state = 300
                self.huser()
                self.state = 301
                self.match(PrismQLParser.T__2)
                pass
            elif token in [64]:
                self.enterOuterAlt(localctx, 17)
                self.state = 303
                self.match(PrismQLParser.HasQuestion)
                self.state = 304
                self.match(PrismQLParser.T__1)
                self.state = 305
                self.match(PrismQLParser.T__2)
                pass
            elif token in [63]:
                self.enterOuterAlt(localctx, 18)
                self.state = 306
                self.match(PrismQLParser.HasDate)
                self.state = 307
                self.match(PrismQLParser.T__1)
                self.state = 308
                self.match(PrismQLParser.T__2)
                pass
            elif token in [59]:
                self.enterOuterAlt(localctx, 19)
                self.state = 309
                self.match(PrismQLParser.HasTime)
                self.state = 310
                self.match(PrismQLParser.T__1)
                self.state = 311
                self.match(PrismQLParser.T__2)
                pass
            elif token in [60]:
                self.enterOuterAlt(localctx, 20)
                self.state = 312
                self.match(PrismQLParser.HasLocation)
                self.state = 313
                self.match(PrismQLParser.T__1)
                self.state = 314
                self.match(PrismQLParser.T__2)
                pass
            elif token in [61]:
                self.enterOuterAlt(localctx, 21)
                self.state = 315
                self.match(PrismQLParser.HasOrganization)
                self.state = 316
                self.match(PrismQLParser.T__1)
                self.state = 317
                self.match(PrismQLParser.T__2)
                pass
            elif token in [62]:
                self.enterOuterAlt(localctx, 22)
                self.state = 318
                self.match(PrismQLParser.HasURL)
                self.state = 319
                self.match(PrismQLParser.T__1)
                self.state = 320
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
            self.state = 340
            self._errHandler.sync(self)
            token = self._input.LA(1)
            if token in [34]:
                self.enterOuterAlt(localctx, 1)
                self.state = 323
                self.match(PrismQLParser.Before)
                self.state = 324
                self.match(PrismQLParser.T__1)
                self.state = 325
                self.timestamp()
                self.state = 326
                self.match(PrismQLParser.T__2)
                pass
            elif token in [35]:
                self.enterOuterAlt(localctx, 2)
                self.state = 328
                self.match(PrismQLParser.After)
                self.state = 329
                self.match(PrismQLParser.T__1)
                self.state = 330
                self.timestamp()
                self.state = 331
                self.match(PrismQLParser.T__2)
                pass
            elif token in [36]:
                self.enterOuterAlt(localctx, 3)
                self.state = 333
                self.match(PrismQLParser.Between)
                self.state = 334
                self.match(PrismQLParser.T__1)
                self.state = 335
                self.timestamp()
                self.state = 336
                self.match(PrismQLParser.T__3)
                self.state = 337
                self.timestamp()
                self.state = 338
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
            self.state = 346
            self._errHandler.sync(self)
            token = self._input.LA(1)
            if token in [69]:
                localctx = PrismQLParser.AbsoluteTimestampContext(self, localctx)
                self.enterOuterAlt(localctx, 1)
                self.state = 342
                self.match(PrismQLParser.QUOTED_STRING)
                pass
            elif token in [67]:
                localctx = PrismQLParser.RelativeTimestampContext(self, localctx)
                self.enterOuterAlt(localctx, 2)
                self.state = 343
                self.time_value()
                self.state = 344
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
            self.state = 348
            self.match(PrismQLParser.GroupBy)
            self.state = 349
            self.groupby_field()
            self.state = 354
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            while _la==4:
                self.state = 350
                self.match(PrismQLParser.T__3)
                self.state = 351
                self.groupby_field()
                self.state = 356
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
            self.state = 363
            self._errHandler.sync(self)
            token = self._input.LA(1)
            if token in [68]:
                localctx = PrismQLParser.SimpleGroupByContext(self, localctx)
                self.enterOuterAlt(localctx, 1)
                self.state = 357
                self.field_name()
                pass
            elif token in [40, 41, 42, 43, 44]:
                localctx = PrismQLParser.TemporalGroupByContext(self, localctx)
                self.enterOuterAlt(localctx, 2)
                self.state = 358
                self.temporal_group_func()
                self.state = 359
                self.match(PrismQLParser.T__1)
                self.state = 360
                self.field_name()
                self.state = 361
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
            self.state = 365
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
        self.enterRule(localctx, 30, self.RULE_aggregate_clause)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 367
            self.match(PrismQLParser.Aggregate)
            self.state = 368
            self.aggregation_func()
            self.state = 373
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            while _la==4:
                self.state = 369
                self.match(PrismQLParser.T__3)
                self.state = 370
                self.aggregation_func()
                self.state = 375
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
            self.state = 410
            self._errHandler.sync(self)
            la_ = self._interp.adaptivePredict(self._input,28,self._ctx)
            if la_ == 1:
                localctx = PrismQLParser.CountAllContext(self, localctx)
                self.enterOuterAlt(localctx, 1)
                self.state = 376
                self.match(PrismQLParser.Count)
                self.state = 377
                self.match(PrismQLParser.T__1)
                self.state = 378
                self.match(PrismQLParser.T__2)
                pass

            elif la_ == 2:
                localctx = PrismQLParser.CountDistinctContext(self, localctx)
                self.enterOuterAlt(localctx, 2)
                self.state = 379
                self.match(PrismQLParser.Count)
                self.state = 380
                self.match(PrismQLParser.T__1)
                self.state = 381
                self.match(PrismQLParser.Distinct)
                self.state = 382
                self.field_name()
                self.state = 383
                self.match(PrismQLParser.T__2)
                pass

            elif la_ == 3:
                localctx = PrismQLParser.DistinctValuesContext(self, localctx)
                self.enterOuterAlt(localctx, 3)
                self.state = 385
                self.match(PrismQLParser.Distinct)
                self.state = 386
                self.match(PrismQLParser.T__1)
                self.state = 387
                self.field_name()
                self.state = 388
                self.match(PrismQLParser.T__2)
                pass

            elif la_ == 4:
                localctx = PrismQLParser.SumFuncContext(self, localctx)
                self.enterOuterAlt(localctx, 4)
                self.state = 390
                self.match(PrismQLParser.Sum)
                self.state = 391
                self.match(PrismQLParser.T__1)
                self.state = 392
                self.field_name()
                self.state = 393
                self.match(PrismQLParser.T__2)
                pass

            elif la_ == 5:
                localctx = PrismQLParser.AvgFuncContext(self, localctx)
                self.enterOuterAlt(localctx, 5)
                self.state = 395
                self.match(PrismQLParser.Avg)
                self.state = 396
                self.match(PrismQLParser.T__1)
                self.state = 397
                self.field_name()
                self.state = 398
                self.match(PrismQLParser.T__2)
                pass

            elif la_ == 6:
                localctx = PrismQLParser.MinFuncContext(self, localctx)
                self.enterOuterAlt(localctx, 6)
                self.state = 400
                self.match(PrismQLParser.Min)
                self.state = 401
                self.match(PrismQLParser.T__1)
                self.state = 402
                self.field_name()
                self.state = 403
                self.match(PrismQLParser.T__2)
                pass

            elif la_ == 7:
                localctx = PrismQLParser.MaxFuncContext(self, localctx)
                self.enterOuterAlt(localctx, 7)
                self.state = 405
                self.match(PrismQLParser.Max)
                self.state = 406
                self.match(PrismQLParser.T__1)
                self.state = 407
                self.field_name()
                self.state = 408
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
            self.state = 412
            self.match(PrismQLParser.OrderBy)
            self.state = 413
            self.field_name()
            self.state = 415
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if _la==30 or _la==31:
                self.state = 414
                _la = self._input.LA(1)
                if not(_la==30 or _la==31):
                    self._errHandler.recoverInline(self)
                else:
                    self._errHandler.reportMatch(self)
                    self.consume()


            self.state = 424
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            while _la==4:
                self.state = 417
                self.match(PrismQLParser.T__3)
                self.state = 418
                self.field_name()
                self.state = 420
                self._errHandler.sync(self)
                _la = self._input.LA(1)
                if _la==30 or _la==31:
                    self.state = 419
                    _la = self._input.LA(1)
                    if not(_la==30 or _la==31):
                        self._errHandler.recoverInline(self)
                    else:
                        self._errHandler.reportMatch(self)
                        self.consume()


                self.state = 426
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
            self.state = 427
            self.match(PrismQLParser.Limit)
            self.state = 428
            self.number()
            self.state = 431
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if _la==33:
                self.state = 429
                self.match(PrismQLParser.Offset)
                self.state = 430
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
            self.state = 433
            self.number()
            self.state = 434
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
            self.state = 436
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
        self.enterRule(localctx, 42, self.RULE_number)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 438
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
            self.state = 440
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
        self.enterRule(localctx, 46, self.RULE_huser)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 442
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
        self.enterRule(localctx, 48, self.RULE_feature_name)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 444
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
            self.state = 446
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
                return self.precpred(self._ctx, 5)
         

            if predIndex == 1:
                return self.precpred(self._ctx, 4)
         

            if predIndex == 2:
                return self.precpred(self._ctx, 13)
         

            if predIndex == 3:
                return self.precpred(self._ctx, 12)
         

            if predIndex == 4:
                return self.precpred(self._ctx, 11)
         

            if predIndex == 5:
                return self.precpred(self._ctx, 10)
         

            if predIndex == 6:
                return self.precpred(self._ctx, 9)
         

            if predIndex == 7:
                return self.precpred(self._ctx, 8)
         

            if predIndex == 8:
                return self.precpred(self._ctx, 7)
         

            if predIndex == 9:
                return self.precpred(self._ctx, 6)
         




