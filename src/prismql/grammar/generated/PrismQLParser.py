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
        4,1,75,506,2,0,7,0,2,1,7,1,2,2,7,2,2,3,7,3,2,4,7,4,2,5,7,5,2,6,7,
        6,2,7,7,7,2,8,7,8,2,9,7,9,2,10,7,10,2,11,7,11,2,12,7,12,2,13,7,13,
        2,14,7,14,2,15,7,15,2,16,7,16,2,17,7,17,2,18,7,18,2,19,7,19,2,20,
        7,20,2,21,7,21,2,22,7,22,2,23,7,23,2,24,7,24,2,25,7,25,2,26,7,26,
        2,27,7,27,2,28,7,28,2,29,7,29,2,30,7,30,2,31,7,31,2,32,7,32,1,0,
        1,0,1,0,1,1,1,1,1,1,1,2,1,2,3,2,75,8,2,1,2,3,2,78,8,2,1,2,1,2,1,
        2,1,2,1,2,1,2,1,2,1,2,3,2,88,8,2,1,2,3,2,91,8,2,1,2,3,2,94,8,2,1,
        2,3,2,97,8,2,1,2,3,2,100,8,2,1,2,3,2,103,8,2,1,3,1,3,1,3,1,3,5,3,
        109,8,3,10,3,12,3,112,9,3,1,4,1,4,1,4,1,4,1,4,1,4,1,4,1,4,1,4,1,
        4,1,4,1,4,1,4,1,4,1,4,1,4,1,4,1,4,1,4,3,4,133,8,4,1,5,1,5,1,6,1,
        6,1,6,5,6,140,8,6,10,6,12,6,143,9,6,1,7,1,7,3,7,147,8,7,1,7,1,7,
        3,7,151,8,7,1,8,1,8,1,8,1,8,1,8,1,8,1,8,1,8,1,8,1,8,1,8,1,8,1,8,
        1,8,1,8,3,8,168,8,8,1,9,1,9,1,9,1,9,1,9,1,9,3,9,176,8,9,1,9,3,9,
        179,8,9,1,9,1,9,1,9,1,9,1,9,1,9,1,9,1,9,1,9,3,9,190,8,9,1,9,1,9,
        1,9,1,9,1,9,1,9,1,9,1,9,1,9,3,9,201,8,9,1,9,1,9,1,9,1,9,1,9,1,9,
        1,9,1,9,1,9,3,9,212,8,9,1,9,1,9,1,9,1,9,1,9,1,9,1,9,1,9,1,9,3,9,
        223,8,9,5,9,225,8,9,10,9,12,9,228,9,9,1,10,1,10,3,10,232,8,10,1,
        11,1,11,1,11,1,11,1,11,1,11,1,11,1,11,3,11,242,8,11,3,11,244,8,11,
        1,11,1,11,1,11,1,12,1,12,1,12,1,12,1,12,1,12,1,12,1,12,3,12,257,
        8,12,1,12,1,12,1,12,1,12,1,12,1,12,5,12,265,8,12,10,12,12,12,268,
        9,12,1,13,1,13,1,13,1,13,1,13,1,13,1,13,1,13,1,13,1,13,1,13,1,13,
        1,13,1,13,1,13,1,13,1,13,1,13,1,13,1,13,1,13,1,13,1,13,1,13,1,13,
        1,13,1,13,1,13,1,13,1,13,1,13,1,13,1,13,1,13,1,13,1,13,1,13,1,13,
        1,13,1,13,1,13,1,13,1,13,1,13,1,13,1,13,1,13,1,13,1,13,1,13,1,13,
        1,13,1,13,1,13,1,13,1,13,1,13,1,13,1,13,3,13,329,8,13,1,13,1,13,
        1,13,1,13,1,13,1,13,1,13,1,13,1,13,1,13,1,13,1,13,1,13,1,13,1,13,
        1,13,1,13,1,13,1,13,1,13,1,13,1,13,1,13,1,13,1,13,1,13,1,13,1,13,
        1,13,1,13,1,13,1,13,1,13,1,13,1,13,1,13,1,13,1,13,1,13,1,13,1,13,
        1,13,3,13,373,8,13,1,14,1,14,1,14,1,14,1,14,1,14,1,14,1,14,1,14,
        1,14,1,14,1,14,1,14,1,14,1,14,1,14,1,14,3,14,392,8,14,1,15,1,15,
        1,15,1,15,3,15,398,8,15,1,16,1,16,1,16,1,16,5,16,404,8,16,10,16,
        12,16,407,9,16,1,17,1,17,1,17,1,17,1,17,1,17,3,17,415,8,17,1,18,
        1,18,1,19,1,19,1,19,1,19,5,19,423,8,19,10,19,12,19,426,9,19,1,20,
        1,20,1,20,1,20,1,20,1,20,1,20,1,20,1,20,1,20,1,20,1,20,1,20,1,20,
        1,20,1,20,1,20,1,20,1,20,1,20,1,20,1,20,1,20,1,20,1,20,1,20,1,20,
        1,20,1,20,1,20,1,20,1,20,1,20,1,20,3,20,462,8,20,1,21,1,21,1,21,
        3,21,467,8,21,1,21,1,21,1,21,3,21,472,8,21,5,21,474,8,21,10,21,12,
        21,477,9,21,1,22,1,22,1,22,1,22,3,22,483,8,22,1,23,1,23,1,23,1,24,
        1,24,1,25,1,25,1,26,1,26,1,27,1,27,1,28,1,28,1,29,1,29,1,30,1,30,
        1,31,1,31,1,32,1,32,1,32,0,2,18,24,33,0,2,4,6,8,10,12,14,16,18,20,
        22,24,26,28,30,32,34,36,38,40,42,44,46,48,50,52,54,56,58,60,62,64,
        0,8,1,0,16,19,1,0,39,43,1,0,29,30,1,0,37,41,1,0,69,70,3,0,59,59,
        71,71,73,74,2,0,59,59,71,74,2,0,59,59,71,71,557,0,66,1,0,0,0,2,69,
        1,0,0,0,4,74,1,0,0,0,6,104,1,0,0,0,8,132,1,0,0,0,10,134,1,0,0,0,
        12,136,1,0,0,0,14,144,1,0,0,0,16,167,1,0,0,0,18,178,1,0,0,0,20,231,
        1,0,0,0,22,233,1,0,0,0,24,256,1,0,0,0,26,372,1,0,0,0,28,391,1,0,
        0,0,30,397,1,0,0,0,32,399,1,0,0,0,34,414,1,0,0,0,36,416,1,0,0,0,
        38,418,1,0,0,0,40,461,1,0,0,0,42,463,1,0,0,0,44,478,1,0,0,0,46,484,
        1,0,0,0,48,487,1,0,0,0,50,489,1,0,0,0,52,491,1,0,0,0,54,493,1,0,
        0,0,56,495,1,0,0,0,58,497,1,0,0,0,60,499,1,0,0,0,62,501,1,0,0,0,
        64,503,1,0,0,0,66,67,3,2,1,0,67,68,5,0,0,1,68,1,1,0,0,0,69,70,5,
        7,0,0,70,71,3,4,2,0,71,3,1,0,0,0,72,75,3,6,3,0,73,75,3,12,6,0,74,
        72,1,0,0,0,74,73,1,0,0,0,75,77,1,0,0,0,76,78,5,1,0,0,77,76,1,0,0,
        0,77,78,1,0,0,0,78,87,1,0,0,0,79,80,5,9,0,0,80,88,3,50,25,0,81,82,
        5,10,0,0,82,88,3,50,25,0,83,84,5,11,0,0,84,88,3,46,23,0,85,86,5,
        12,0,0,86,88,3,46,23,0,87,79,1,0,0,0,87,81,1,0,0,0,87,83,1,0,0,0,
        87,85,1,0,0,0,87,88,1,0,0,0,88,90,1,0,0,0,89,91,3,28,14,0,90,89,
        1,0,0,0,90,91,1,0,0,0,91,93,1,0,0,0,92,94,3,32,16,0,93,92,1,0,0,
        0,93,94,1,0,0,0,94,96,1,0,0,0,95,97,3,38,19,0,96,95,1,0,0,0,96,97,
        1,0,0,0,97,99,1,0,0,0,98,100,3,42,21,0,99,98,1,0,0,0,99,100,1,0,
        0,0,100,102,1,0,0,0,101,103,3,44,22,0,102,101,1,0,0,0,102,103,1,
        0,0,0,103,5,1,0,0,0,104,105,5,2,0,0,105,106,3,2,1,0,106,110,5,3,
        0,0,107,109,3,8,4,0,108,107,1,0,0,0,109,112,1,0,0,0,110,108,1,0,
        0,0,110,111,1,0,0,0,111,7,1,0,0,0,112,110,1,0,0,0,113,114,5,1,0,
        0,114,115,5,2,0,0,115,116,3,2,1,0,116,117,5,3,0,0,117,133,1,0,0,
        0,118,119,3,10,5,0,119,120,5,2,0,0,120,121,3,2,1,0,121,122,5,3,0,
        0,122,123,5,9,0,0,123,124,3,50,25,0,124,133,1,0,0,0,125,126,3,10,
        5,0,126,127,5,2,0,0,127,128,3,2,1,0,128,129,5,3,0,0,129,130,5,12,
        0,0,130,131,3,50,25,0,131,133,1,0,0,0,132,113,1,0,0,0,132,118,1,
        0,0,0,132,125,1,0,0,0,133,9,1,0,0,0,134,135,7,0,0,0,135,11,1,0,0,
        0,136,141,3,14,7,0,137,138,5,4,0,0,138,140,3,14,7,0,139,137,1,0,
        0,0,140,143,1,0,0,0,141,139,1,0,0,0,141,142,1,0,0,0,142,13,1,0,0,
        0,143,141,1,0,0,0,144,146,3,18,9,0,145,147,3,16,8,0,146,145,1,0,
        0,0,146,147,1,0,0,0,147,150,1,0,0,0,148,149,5,8,0,0,149,151,5,72,
        0,0,150,148,1,0,0,0,150,151,1,0,0,0,151,15,1,0,0,0,152,153,5,5,0,
        0,153,154,3,50,25,0,154,155,5,6,0,0,155,168,1,0,0,0,156,157,5,5,
        0,0,157,158,3,50,25,0,158,159,5,4,0,0,159,160,5,6,0,0,160,168,1,
        0,0,0,161,162,5,5,0,0,162,163,3,50,25,0,163,164,5,4,0,0,164,165,
        3,50,25,0,165,166,5,6,0,0,166,168,1,0,0,0,167,152,1,0,0,0,167,156,
        1,0,0,0,167,161,1,0,0,0,168,17,1,0,0,0,169,170,6,9,-1,0,170,175,
        3,22,11,0,171,172,5,9,0,0,172,176,3,50,25,0,173,174,5,11,0,0,174,
        176,3,46,23,0,175,171,1,0,0,0,175,173,1,0,0,0,175,176,1,0,0,0,176,
        179,1,0,0,0,177,179,3,24,12,0,178,169,1,0,0,0,178,177,1,0,0,0,179,
        226,1,0,0,0,180,181,10,6,0,0,181,182,5,16,0,0,182,189,3,20,10,0,
        183,184,5,9,0,0,184,190,3,50,25,0,185,186,5,11,0,0,186,190,3,46,
        23,0,187,188,5,12,0,0,188,190,3,50,25,0,189,183,1,0,0,0,189,185,
        1,0,0,0,189,187,1,0,0,0,189,190,1,0,0,0,190,225,1,0,0,0,191,192,
        10,5,0,0,192,193,5,17,0,0,193,200,3,20,10,0,194,195,5,9,0,0,195,
        201,3,50,25,0,196,197,5,11,0,0,197,201,3,46,23,0,198,199,5,12,0,
        0,199,201,3,50,25,0,200,194,1,0,0,0,200,196,1,0,0,0,200,198,1,0,
        0,0,200,201,1,0,0,0,201,225,1,0,0,0,202,203,10,4,0,0,203,204,5,18,
        0,0,204,211,3,20,10,0,205,206,5,9,0,0,206,212,3,50,25,0,207,208,
        5,11,0,0,208,212,3,46,23,0,209,210,5,12,0,0,210,212,3,50,25,0,211,
        205,1,0,0,0,211,207,1,0,0,0,211,209,1,0,0,0,211,212,1,0,0,0,212,
        225,1,0,0,0,213,214,10,3,0,0,214,215,5,19,0,0,215,222,3,20,10,0,
        216,217,5,9,0,0,217,223,3,50,25,0,218,219,5,11,0,0,219,223,3,46,
        23,0,220,221,5,12,0,0,221,223,3,50,25,0,222,216,1,0,0,0,222,218,
        1,0,0,0,222,220,1,0,0,0,222,223,1,0,0,0,223,225,1,0,0,0,224,180,
        1,0,0,0,224,191,1,0,0,0,224,202,1,0,0,0,224,213,1,0,0,0,225,228,
        1,0,0,0,226,224,1,0,0,0,226,227,1,0,0,0,227,19,1,0,0,0,228,226,1,
        0,0,0,229,232,3,22,11,0,230,232,3,24,12,0,231,229,1,0,0,0,231,230,
        1,0,0,0,232,21,1,0,0,0,233,234,5,59,0,0,234,235,5,2,0,0,235,243,
        3,24,12,0,236,241,5,4,0,0,237,238,5,9,0,0,238,242,3,50,25,0,239,
        240,5,11,0,0,240,242,3,46,23,0,241,237,1,0,0,0,241,239,1,0,0,0,242,
        244,1,0,0,0,243,236,1,0,0,0,243,244,1,0,0,0,244,245,1,0,0,0,245,
        246,5,3,0,0,246,247,3,16,8,0,247,23,1,0,0,0,248,249,6,12,-1,0,249,
        250,5,13,0,0,250,257,3,24,12,5,251,252,5,2,0,0,252,253,3,18,9,0,
        253,254,5,3,0,0,254,257,1,0,0,0,255,257,3,26,13,0,256,248,1,0,0,
        0,256,251,1,0,0,0,256,255,1,0,0,0,257,266,1,0,0,0,258,259,10,4,0,
        0,259,260,5,14,0,0,260,265,3,24,12,5,261,262,10,3,0,0,262,263,5,
        15,0,0,263,265,3,24,12,4,264,258,1,0,0,0,264,261,1,0,0,0,265,268,
        1,0,0,0,266,264,1,0,0,0,266,267,1,0,0,0,267,25,1,0,0,0,268,266,1,
        0,0,0,269,270,5,44,0,0,270,271,5,2,0,0,271,272,3,54,27,0,272,273,
        5,3,0,0,273,373,1,0,0,0,274,275,5,45,0,0,275,276,5,2,0,0,276,277,
        3,54,27,0,277,278,5,3,0,0,278,373,1,0,0,0,279,280,5,46,0,0,280,281,
        5,2,0,0,281,282,5,72,0,0,282,373,5,3,0,0,283,284,5,47,0,0,284,285,
        5,2,0,0,285,286,3,56,28,0,286,287,5,3,0,0,287,373,1,0,0,0,288,289,
        5,48,0,0,289,290,5,2,0,0,290,291,3,56,28,0,291,292,5,3,0,0,292,373,
        1,0,0,0,293,294,5,49,0,0,294,295,5,2,0,0,295,373,5,3,0,0,296,297,
        5,50,0,0,297,298,5,2,0,0,298,373,5,3,0,0,299,300,5,51,0,0,300,301,
        5,2,0,0,301,373,5,3,0,0,302,303,5,52,0,0,303,304,5,2,0,0,304,373,
        5,3,0,0,305,306,5,53,0,0,306,307,5,2,0,0,307,373,5,3,0,0,308,309,
        5,54,0,0,309,310,5,2,0,0,310,373,5,3,0,0,311,312,5,55,0,0,312,313,
        5,2,0,0,313,314,3,58,29,0,314,315,5,3,0,0,315,373,1,0,0,0,316,317,
        5,56,0,0,317,318,5,2,0,0,318,319,3,58,29,0,319,320,5,3,0,0,320,373,
        1,0,0,0,321,322,5,57,0,0,322,323,5,2,0,0,323,324,3,60,30,0,324,325,
        5,4,0,0,325,328,3,62,31,0,326,327,5,4,0,0,327,329,3,64,32,0,328,
        326,1,0,0,0,328,329,1,0,0,0,329,330,1,0,0,0,330,331,5,3,0,0,331,
        373,1,0,0,0,332,333,5,58,0,0,333,334,5,2,0,0,334,335,5,72,0,0,335,
        336,5,4,0,0,336,337,3,52,26,0,337,338,5,3,0,0,338,373,1,0,0,0,339,
        340,5,60,0,0,340,341,5,2,0,0,341,342,3,54,27,0,342,343,5,3,0,0,343,
        373,1,0,0,0,344,345,5,68,0,0,345,346,5,2,0,0,346,347,3,56,28,0,347,
        348,5,3,0,0,348,373,1,0,0,0,349,350,5,67,0,0,350,351,5,2,0,0,351,
        352,3,56,28,0,352,353,5,3,0,0,353,373,1,0,0,0,354,355,5,66,0,0,355,
        356,5,2,0,0,356,373,5,3,0,0,357,358,5,65,0,0,358,359,5,2,0,0,359,
        373,5,3,0,0,360,361,5,61,0,0,361,362,5,2,0,0,362,373,5,3,0,0,363,
        364,5,62,0,0,364,365,5,2,0,0,365,373,5,3,0,0,366,367,5,63,0,0,367,
        368,5,2,0,0,368,373,5,3,0,0,369,370,5,64,0,0,370,371,5,2,0,0,371,
        373,5,3,0,0,372,269,1,0,0,0,372,274,1,0,0,0,372,279,1,0,0,0,372,
        283,1,0,0,0,372,288,1,0,0,0,372,293,1,0,0,0,372,296,1,0,0,0,372,
        299,1,0,0,0,372,302,1,0,0,0,372,305,1,0,0,0,372,308,1,0,0,0,372,
        311,1,0,0,0,372,316,1,0,0,0,372,321,1,0,0,0,372,332,1,0,0,0,372,
        339,1,0,0,0,372,344,1,0,0,0,372,349,1,0,0,0,372,354,1,0,0,0,372,
        357,1,0,0,0,372,360,1,0,0,0,372,363,1,0,0,0,372,366,1,0,0,0,372,
        369,1,0,0,0,373,27,1,0,0,0,374,375,5,33,0,0,375,376,5,2,0,0,376,
        377,3,30,15,0,377,378,5,3,0,0,378,392,1,0,0,0,379,380,5,34,0,0,380,
        381,5,2,0,0,381,382,3,30,15,0,382,383,5,3,0,0,383,392,1,0,0,0,384,
        385,5,35,0,0,385,386,5,2,0,0,386,387,3,30,15,0,387,388,5,4,0,0,388,
        389,3,30,15,0,389,390,5,3,0,0,390,392,1,0,0,0,391,374,1,0,0,0,391,
        379,1,0,0,0,391,384,1,0,0,0,392,29,1,0,0,0,393,398,5,72,0,0,394,
        395,3,46,23,0,395,396,5,36,0,0,396,398,1,0,0,0,397,393,1,0,0,0,397,
        394,1,0,0,0,398,31,1,0,0,0,399,400,5,21,0,0,400,405,3,34,17,0,401,
        402,5,4,0,0,402,404,3,34,17,0,403,401,1,0,0,0,404,407,1,0,0,0,405,
        403,1,0,0,0,405,406,1,0,0,0,406,33,1,0,0,0,407,405,1,0,0,0,408,415,
        3,60,30,0,409,410,3,36,18,0,410,411,5,2,0,0,411,412,3,60,30,0,412,
        413,5,3,0,0,413,415,1,0,0,0,414,408,1,0,0,0,414,409,1,0,0,0,415,
        35,1,0,0,0,416,417,7,1,0,0,417,37,1,0,0,0,418,419,5,20,0,0,419,424,
        3,40,20,0,420,421,5,4,0,0,421,423,3,40,20,0,422,420,1,0,0,0,423,
        426,1,0,0,0,424,422,1,0,0,0,424,425,1,0,0,0,425,39,1,0,0,0,426,424,
        1,0,0,0,427,428,5,22,0,0,428,429,5,2,0,0,429,462,5,3,0,0,430,431,
        5,22,0,0,431,432,5,2,0,0,432,433,5,23,0,0,433,434,3,60,30,0,434,
        435,5,3,0,0,435,462,1,0,0,0,436,437,5,23,0,0,437,438,5,2,0,0,438,
        439,3,60,30,0,439,440,5,3,0,0,440,462,1,0,0,0,441,442,5,24,0,0,442,
        443,5,2,0,0,443,444,3,60,30,0,444,445,5,3,0,0,445,462,1,0,0,0,446,
        447,5,25,0,0,447,448,5,2,0,0,448,449,3,60,30,0,449,450,5,3,0,0,450,
        462,1,0,0,0,451,452,5,26,0,0,452,453,5,2,0,0,453,454,3,60,30,0,454,
        455,5,3,0,0,455,462,1,0,0,0,456,457,5,27,0,0,457,458,5,2,0,0,458,
        459,3,60,30,0,459,460,5,3,0,0,460,462,1,0,0,0,461,427,1,0,0,0,461,
        430,1,0,0,0,461,436,1,0,0,0,461,441,1,0,0,0,461,446,1,0,0,0,461,
        451,1,0,0,0,461,456,1,0,0,0,462,41,1,0,0,0,463,464,5,28,0,0,464,
        466,3,60,30,0,465,467,7,2,0,0,466,465,1,0,0,0,466,467,1,0,0,0,467,
        475,1,0,0,0,468,469,5,4,0,0,469,471,3,60,30,0,470,472,7,2,0,0,471,
        470,1,0,0,0,471,472,1,0,0,0,472,474,1,0,0,0,473,468,1,0,0,0,474,
        477,1,0,0,0,475,473,1,0,0,0,475,476,1,0,0,0,476,43,1,0,0,0,477,475,
        1,0,0,0,478,479,5,31,0,0,479,482,3,50,25,0,480,481,5,32,0,0,481,
        483,3,50,25,0,482,480,1,0,0,0,482,483,1,0,0,0,483,45,1,0,0,0,484,
        485,3,50,25,0,485,486,3,48,24,0,486,47,1,0,0,0,487,488,7,3,0,0,488,
        49,1,0,0,0,489,490,5,70,0,0,490,51,1,0,0,0,491,492,7,4,0,0,492,53,
        1,0,0,0,493,494,7,5,0,0,494,55,1,0,0,0,495,496,7,6,0,0,496,57,1,
        0,0,0,497,498,7,7,0,0,498,59,1,0,0,0,499,500,7,7,0,0,500,61,1,0,
        0,0,501,502,7,6,0,0,502,63,1,0,0,0,503,504,5,71,0,0,504,65,1,0,0,
        0,40,74,77,87,90,93,96,99,102,110,132,141,146,150,167,175,178,189,
        200,211,222,224,226,231,241,243,256,264,266,328,372,391,397,405,
        414,424,461,466,471,475,482
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
                     "<INVALID>", "<INVALID>", "<INVALID>", "'*'" ]

    symbolicNames = [ "<INVALID>", "<INVALID>", "<INVALID>", "<INVALID>", 
                      "<INVALID>", "<INVALID>", "<INVALID>", "Select", "As", 
                      "InWindow", "InWin", "During", "Within", "Not", "And", 
                      "Or", "FollowedBy", "PrecededBy", "NotFollowedBy", 
                      "NotPrecededBy", "Aggregate", "GroupBy", "Count", 
                      "Distinct", "Sum", "Avg", "Min", "Max", "OrderBy", 
                      "Asc", "Desc", "Limit", "Offset", "Before", "After", 
                      "Between", "Ago", "Seconds", "Minutes", "Hours", "Days", 
                      "Weeks", "Months", "Years", "Contains", "ContainsTokens", 
                      "ContainsPhrase", "From", "MentionsUser", "IsQuestion", 
                      "MentionsDate", "MentionsTime", "MentionsPlace", "MentionsOrg", 
                      "ContainsLink", "HasFeature", "LabeledAs", "Field", 
                      "SimilarTo", "Run", "HasWordOfDict", "HasTime", "HasLocation", 
                      "HasOrganization", "HasURL", "HasDate", "HasQuestion", 
                      "HasUserMentioned", "ByUser", "FLOAT", "INTEGER", 
                      "STRING", "QUOTED_STRING", "VARIABLE", "WILDCARD", 
                      "WS" ]

    RULE_parse = 0
    RULE_query = 1
    RULE_body = 2
    RULE_query_seq = 3
    RULE_query_seq_continuation = 4
    RULE_positional_op = 5
    RULE_restrictions = 6
    RULE_named_restriction = 7
    RULE_quantifier = 8
    RULE_restriction = 9
    RULE_link_rhs = 10
    RULE_run_restriction = 11
    RULE_bool_restriction = 12
    RULE_condition = 13
    RULE_temporal_filter = 14
    RULE_timestamp = 15
    RULE_groupby_clause = 16
    RULE_groupby_field = 17
    RULE_temporal_group_func = 18
    RULE_aggregate_clause = 19
    RULE_aggregation_func = 20
    RULE_orderby_clause = 21
    RULE_limit_clause = 22
    RULE_time_value = 23
    RULE_time_unit = 24
    RULE_number = 25
    RULE_float_number = 26
    RULE_hdict = 27
    RULE_huser = 28
    RULE_feature_name = 29
    RULE_field_name = 30
    RULE_field_value = 31
    RULE_match_mode = 32

    ruleNames =  [ "parse", "query", "body", "query_seq", "query_seq_continuation", 
                   "positional_op", "restrictions", "named_restriction", 
                   "quantifier", "restriction", "link_rhs", "run_restriction", 
                   "bool_restriction", "condition", "temporal_filter", "timestamp", 
                   "groupby_clause", "groupby_field", "temporal_group_func", 
                   "aggregate_clause", "aggregation_func", "orderby_clause", 
                   "limit_clause", "time_value", "time_unit", "number", 
                   "float_number", "hdict", "huser", "feature_name", "field_name", 
                   "field_value", "match_mode" ]

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
    Field=57
    SimilarTo=58
    Run=59
    HasWordOfDict=60
    HasTime=61
    HasLocation=62
    HasOrganization=63
    HasURL=64
    HasDate=65
    HasQuestion=66
    HasUserMentioned=67
    ByUser=68
    FLOAT=69
    INTEGER=70
    STRING=71
    QUOTED_STRING=72
    VARIABLE=73
    WILDCARD=74
    WS=75

    def __init__(self, input:TokenStream, output:TextIO = sys.stdout):
        super().__init__(input, output)
        self.checkVersion("4.13.1")
        self._interp = ParserATNSimulator(self, self.atn, self.decisionsToDFA, self.sharedContextCache)
        self._predicates = None




    class ParseContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def query(self):
            return self.getTypedRuleContext(PrismQLParser.QueryContext,0)


        def EOF(self):
            return self.getToken(PrismQLParser.EOF, 0)

        def getRuleIndex(self):
            return PrismQLParser.RULE_parse

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitParse" ):
                return visitor.visitParse(self)
            else:
                return visitor.visitChildren(self)




    def parse(self):

        localctx = PrismQLParser.ParseContext(self, self._ctx, self.state)
        self.enterRule(localctx, 0, self.RULE_parse)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 66
            self.query()
            self.state = 67
            self.match(PrismQLParser.EOF)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


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
        self.enterRule(localctx, 2, self.RULE_query)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 69
            self.match(PrismQLParser.Select)
            self.state = 70
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
        self.enterRule(localctx, 4, self.RULE_body)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 74
            self._errHandler.sync(self)
            la_ = self._interp.adaptivePredict(self._input,0,self._ctx)
            if la_ == 1:
                self.state = 72
                self.query_seq()
                pass

            elif la_ == 2:
                self.state = 73
                self.restrictions()
                pass


            self.state = 77
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if _la==1:
                self.state = 76
                self.match(PrismQLParser.T__0)


            self.state = 87
            self._errHandler.sync(self)
            token = self._input.LA(1)
            if token in [9]:
                self.state = 79
                self.match(PrismQLParser.InWindow)
                self.state = 80
                self.number()
                pass
            elif token in [10]:
                self.state = 81
                self.match(PrismQLParser.InWin)
                self.state = 82
                self.number()
                pass
            elif token in [11]:
                self.state = 83
                self.match(PrismQLParser.During)
                self.state = 84
                self.time_value()
                pass
            elif token in [12]:
                self.state = 85
                self.match(PrismQLParser.Within)
                self.state = 86
                self.time_value()
                pass
            elif token in [-1, 3, 20, 21, 28, 31, 33, 34, 35]:
                pass
            else:
                pass
            self.state = 90
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if (((_la) & ~0x3f) == 0 and ((1 << _la) & 60129542144) != 0):
                self.state = 89
                self.temporal_filter()


            self.state = 93
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if _la==21:
                self.state = 92
                self.groupby_clause()


            self.state = 96
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if _la==20:
                self.state = 95
                self.aggregate_clause()


            self.state = 99
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if _la==28:
                self.state = 98
                self.orderby_clause()


            self.state = 102
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if _la==31:
                self.state = 101
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
        self.enterRule(localctx, 6, self.RULE_query_seq)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 104
            self.match(PrismQLParser.T__1)
            self.state = 105
            self.query()
            self.state = 106
            self.match(PrismQLParser.T__2)
            self.state = 110
            self._errHandler.sync(self)
            _alt = self._interp.adaptivePredict(self._input,8,self._ctx)
            while _alt!=2 and _alt!=ATN.INVALID_ALT_NUMBER:
                if _alt==1:
                    self.state = 107
                    self.query_seq_continuation() 
                self.state = 112
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
        self.enterRule(localctx, 8, self.RULE_query_seq_continuation)
        try:
            self.state = 132
            self._errHandler.sync(self)
            la_ = self._interp.adaptivePredict(self._input,9,self._ctx)
            if la_ == 1:
                localctx = PrismQLParser.UnorderedSubqueryContext(self, localctx)
                self.enterOuterAlt(localctx, 1)
                self.state = 113
                self.match(PrismQLParser.T__0)
                self.state = 114
                self.match(PrismQLParser.T__1)
                self.state = 115
                self.query()
                self.state = 116
                self.match(PrismQLParser.T__2)
                pass

            elif la_ == 2:
                localctx = PrismQLParser.PositionalSubqueryContext(self, localctx)
                self.enterOuterAlt(localctx, 2)
                self.state = 118
                self.positional_op()
                self.state = 119
                self.match(PrismQLParser.T__1)
                self.state = 120
                self.query()
                self.state = 121
                self.match(PrismQLParser.T__2)
                self.state = 122
                self.match(PrismQLParser.InWindow)
                self.state = 123
                self.number()
                pass

            elif la_ == 3:
                localctx = PrismQLParser.PositionalSubqueryDeprecatedContext(self, localctx)
                self.enterOuterAlt(localctx, 3)
                self.state = 125
                self.positional_op()
                self.state = 126
                self.match(PrismQLParser.T__1)
                self.state = 127
                self.query()
                self.state = 128
                self.match(PrismQLParser.T__2)
                self.state = 129
                self.match(PrismQLParser.Within)
                self.state = 130
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
        self.enterRule(localctx, 10, self.RULE_positional_op)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 134
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


        def getRuleIndex(self):
            return PrismQLParser.RULE_restrictions

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitRestrictions" ):
                return visitor.visitRestrictions(self)
            else:
                return visitor.visitChildren(self)




    def restrictions(self):

        localctx = PrismQLParser.RestrictionsContext(self, self._ctx, self.state)
        self.enterRule(localctx, 12, self.RULE_restrictions)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 136
            self.named_restriction()
            self.state = 141
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            while _la==4:
                self.state = 137
                self.match(PrismQLParser.T__3)
                self.state = 138
                self.named_restriction()
                self.state = 143
                self._errHandler.sync(self)
                _la = self._input.LA(1)

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
        self.enterRule(localctx, 14, self.RULE_named_restriction)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 144
            self.restriction(0)
            self.state = 146
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if _la==5:
                self.state = 145
                self.quantifier()


            self.state = 150
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if _la==8:
                self.state = 148
                self.match(PrismQLParser.As)
                self.state = 149
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
        self.enterRule(localctx, 16, self.RULE_quantifier)
        try:
            self.state = 167
            self._errHandler.sync(self)
            la_ = self._interp.adaptivePredict(self._input,13,self._ctx)
            if la_ == 1:
                localctx = PrismQLParser.ExactQuantifierContext(self, localctx)
                self.enterOuterAlt(localctx, 1)
                self.state = 152
                self.match(PrismQLParser.T__4)
                self.state = 153
                self.number()
                self.state = 154
                self.match(PrismQLParser.T__5)
                pass

            elif la_ == 2:
                localctx = PrismQLParser.AtLeastQuantifierContext(self, localctx)
                self.enterOuterAlt(localctx, 2)
                self.state = 156
                self.match(PrismQLParser.T__4)
                self.state = 157
                self.number()
                self.state = 158
                self.match(PrismQLParser.T__3)
                self.state = 159
                self.match(PrismQLParser.T__5)
                pass

            elif la_ == 3:
                localctx = PrismQLParser.RangeQuantifierContext(self, localctx)
                self.enterOuterAlt(localctx, 3)
                self.state = 161
                self.match(PrismQLParser.T__4)
                self.state = 162
                self.number()
                self.state = 163
                self.match(PrismQLParser.T__3)
                self.state = 164
                self.number()
                self.state = 165
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

        def run_restriction(self):
            return self.getTypedRuleContext(PrismQLParser.Run_restrictionContext,0)


        def InWindow(self):
            return self.getToken(PrismQLParser.InWindow, 0)

        def number(self):
            return self.getTypedRuleContext(PrismQLParser.NumberContext,0)


        def During(self):
            return self.getToken(PrismQLParser.During, 0)

        def time_value(self):
            return self.getTypedRuleContext(PrismQLParser.Time_valueContext,0)


        def bool_restriction(self):
            return self.getTypedRuleContext(PrismQLParser.Bool_restrictionContext,0)


        def restriction(self):
            return self.getTypedRuleContext(PrismQLParser.RestrictionContext,0)


        def FollowedBy(self):
            return self.getToken(PrismQLParser.FollowedBy, 0)

        def link_rhs(self):
            return self.getTypedRuleContext(PrismQLParser.Link_rhsContext,0)


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
        _startState = 18
        self.enterRecursionRule(localctx, 18, self.RULE_restriction, _p)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 178
            self._errHandler.sync(self)
            token = self._input.LA(1)
            if token in [59]:
                self.state = 170
                self.run_restriction()
                self.state = 175
                self._errHandler.sync(self)
                la_ = self._interp.adaptivePredict(self._input,14,self._ctx)
                if la_ == 1:
                    self.state = 171
                    self.match(PrismQLParser.InWindow)
                    self.state = 172
                    self.number()

                elif la_ == 2:
                    self.state = 173
                    self.match(PrismQLParser.During)
                    self.state = 174
                    self.time_value()


                pass
            elif token in [2, 13, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 60, 61, 62, 63, 64, 65, 66, 67, 68]:
                self.state = 177
                self.bool_restriction(0)
                pass
            else:
                raise NoViableAltException(self)

            self._ctx.stop = self._input.LT(-1)
            self.state = 226
            self._errHandler.sync(self)
            _alt = self._interp.adaptivePredict(self._input,21,self._ctx)
            while _alt!=2 and _alt!=ATN.INVALID_ALT_NUMBER:
                if _alt==1:
                    if self._parseListeners is not None:
                        self.triggerExitRuleEvent()
                    _prevctx = localctx
                    self.state = 224
                    self._errHandler.sync(self)
                    la_ = self._interp.adaptivePredict(self._input,20,self._ctx)
                    if la_ == 1:
                        localctx = PrismQLParser.RestrictionContext(self, _parentctx, _parentState)
                        self.pushNewRecursionContext(localctx, _startState, self.RULE_restriction)
                        self.state = 180
                        if not self.precpred(self._ctx, 6):
                            from antlr4.error.Errors import FailedPredicateException
                            raise FailedPredicateException(self, "self.precpred(self._ctx, 6)")
                        self.state = 181
                        self.match(PrismQLParser.FollowedBy)
                        self.state = 182
                        self.link_rhs()
                        self.state = 189
                        self._errHandler.sync(self)
                        la_ = self._interp.adaptivePredict(self._input,16,self._ctx)
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

                        elif la_ == 3:
                            self.state = 187
                            self.match(PrismQLParser.Within)
                            self.state = 188
                            self.number()


                        pass

                    elif la_ == 2:
                        localctx = PrismQLParser.RestrictionContext(self, _parentctx, _parentState)
                        self.pushNewRecursionContext(localctx, _startState, self.RULE_restriction)
                        self.state = 191
                        if not self.precpred(self._ctx, 5):
                            from antlr4.error.Errors import FailedPredicateException
                            raise FailedPredicateException(self, "self.precpred(self._ctx, 5)")
                        self.state = 192
                        self.match(PrismQLParser.PrecededBy)
                        self.state = 193
                        self.link_rhs()
                        self.state = 200
                        self._errHandler.sync(self)
                        la_ = self._interp.adaptivePredict(self._input,17,self._ctx)
                        if la_ == 1:
                            self.state = 194
                            self.match(PrismQLParser.InWindow)
                            self.state = 195
                            self.number()

                        elif la_ == 2:
                            self.state = 196
                            self.match(PrismQLParser.During)
                            self.state = 197
                            self.time_value()

                        elif la_ == 3:
                            self.state = 198
                            self.match(PrismQLParser.Within)
                            self.state = 199
                            self.number()


                        pass

                    elif la_ == 3:
                        localctx = PrismQLParser.RestrictionContext(self, _parentctx, _parentState)
                        self.pushNewRecursionContext(localctx, _startState, self.RULE_restriction)
                        self.state = 202
                        if not self.precpred(self._ctx, 4):
                            from antlr4.error.Errors import FailedPredicateException
                            raise FailedPredicateException(self, "self.precpred(self._ctx, 4)")
                        self.state = 203
                        self.match(PrismQLParser.NotFollowedBy)
                        self.state = 204
                        self.link_rhs()
                        self.state = 211
                        self._errHandler.sync(self)
                        la_ = self._interp.adaptivePredict(self._input,18,self._ctx)
                        if la_ == 1:
                            self.state = 205
                            self.match(PrismQLParser.InWindow)
                            self.state = 206
                            self.number()

                        elif la_ == 2:
                            self.state = 207
                            self.match(PrismQLParser.During)
                            self.state = 208
                            self.time_value()

                        elif la_ == 3:
                            self.state = 209
                            self.match(PrismQLParser.Within)
                            self.state = 210
                            self.number()


                        pass

                    elif la_ == 4:
                        localctx = PrismQLParser.RestrictionContext(self, _parentctx, _parentState)
                        self.pushNewRecursionContext(localctx, _startState, self.RULE_restriction)
                        self.state = 213
                        if not self.precpred(self._ctx, 3):
                            from antlr4.error.Errors import FailedPredicateException
                            raise FailedPredicateException(self, "self.precpred(self._ctx, 3)")
                        self.state = 214
                        self.match(PrismQLParser.NotPrecededBy)
                        self.state = 215
                        self.link_rhs()
                        self.state = 222
                        self._errHandler.sync(self)
                        la_ = self._interp.adaptivePredict(self._input,19,self._ctx)
                        if la_ == 1:
                            self.state = 216
                            self.match(PrismQLParser.InWindow)
                            self.state = 217
                            self.number()

                        elif la_ == 2:
                            self.state = 218
                            self.match(PrismQLParser.During)
                            self.state = 219
                            self.time_value()

                        elif la_ == 3:
                            self.state = 220
                            self.match(PrismQLParser.Within)
                            self.state = 221
                            self.number()


                        pass

             
                self.state = 228
                self._errHandler.sync(self)
                _alt = self._interp.adaptivePredict(self._input,21,self._ctx)

        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.unrollRecursionContexts(_parentctx)
        return localctx


    class Link_rhsContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def run_restriction(self):
            return self.getTypedRuleContext(PrismQLParser.Run_restrictionContext,0)


        def bool_restriction(self):
            return self.getTypedRuleContext(PrismQLParser.Bool_restrictionContext,0)


        def getRuleIndex(self):
            return PrismQLParser.RULE_link_rhs

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitLink_rhs" ):
                return visitor.visitLink_rhs(self)
            else:
                return visitor.visitChildren(self)




    def link_rhs(self):

        localctx = PrismQLParser.Link_rhsContext(self, self._ctx, self.state)
        self.enterRule(localctx, 20, self.RULE_link_rhs)
        try:
            self.state = 231
            self._errHandler.sync(self)
            token = self._input.LA(1)
            if token in [59]:
                self.enterOuterAlt(localctx, 1)
                self.state = 229
                self.run_restriction()
                pass
            elif token in [2, 13, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 60, 61, 62, 63, 64, 65, 66, 67, 68]:
                self.enterOuterAlt(localctx, 2)
                self.state = 230
                self.bool_restriction(0)
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


    class Run_restrictionContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def Run(self):
            return self.getToken(PrismQLParser.Run, 0)

        def bool_restriction(self):
            return self.getTypedRuleContext(PrismQLParser.Bool_restrictionContext,0)


        def quantifier(self):
            return self.getTypedRuleContext(PrismQLParser.QuantifierContext,0)


        def InWindow(self):
            return self.getToken(PrismQLParser.InWindow, 0)

        def number(self):
            return self.getTypedRuleContext(PrismQLParser.NumberContext,0)


        def During(self):
            return self.getToken(PrismQLParser.During, 0)

        def time_value(self):
            return self.getTypedRuleContext(PrismQLParser.Time_valueContext,0)


        def getRuleIndex(self):
            return PrismQLParser.RULE_run_restriction

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitRun_restriction" ):
                return visitor.visitRun_restriction(self)
            else:
                return visitor.visitChildren(self)




    def run_restriction(self):

        localctx = PrismQLParser.Run_restrictionContext(self, self._ctx, self.state)
        self.enterRule(localctx, 22, self.RULE_run_restriction)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 233
            self.match(PrismQLParser.Run)
            self.state = 234
            self.match(PrismQLParser.T__1)
            self.state = 235
            self.bool_restriction(0)
            self.state = 243
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if _la==4:
                self.state = 236
                self.match(PrismQLParser.T__3)
                self.state = 241
                self._errHandler.sync(self)
                token = self._input.LA(1)
                if token in [9]:
                    self.state = 237
                    self.match(PrismQLParser.InWindow)
                    self.state = 238
                    self.number()
                    pass
                elif token in [11]:
                    self.state = 239
                    self.match(PrismQLParser.During)
                    self.state = 240
                    self.time_value()
                    pass
                else:
                    raise NoViableAltException(self)



            self.state = 245
            self.match(PrismQLParser.T__2)
            self.state = 246
            self.quantifier()
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
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
        _startState = 24
        self.enterRecursionRule(localctx, 24, self.RULE_bool_restriction, _p)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 256
            self._errHandler.sync(self)
            token = self._input.LA(1)
            if token in [13]:
                self.state = 249
                self.match(PrismQLParser.Not)
                self.state = 250
                self.bool_restriction(5)
                pass
            elif token in [2]:
                self.state = 251
                self.match(PrismQLParser.T__1)
                self.state = 252
                self.restriction(0)
                self.state = 253
                self.match(PrismQLParser.T__2)
                pass
            elif token in [44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 60, 61, 62, 63, 64, 65, 66, 67, 68]:
                self.state = 255
                self.condition()
                pass
            else:
                raise NoViableAltException(self)

            self._ctx.stop = self._input.LT(-1)
            self.state = 266
            self._errHandler.sync(self)
            _alt = self._interp.adaptivePredict(self._input,27,self._ctx)
            while _alt!=2 and _alt!=ATN.INVALID_ALT_NUMBER:
                if _alt==1:
                    if self._parseListeners is not None:
                        self.triggerExitRuleEvent()
                    _prevctx = localctx
                    self.state = 264
                    self._errHandler.sync(self)
                    la_ = self._interp.adaptivePredict(self._input,26,self._ctx)
                    if la_ == 1:
                        localctx = PrismQLParser.Bool_restrictionContext(self, _parentctx, _parentState)
                        self.pushNewRecursionContext(localctx, _startState, self.RULE_bool_restriction)
                        self.state = 258
                        if not self.precpred(self._ctx, 4):
                            from antlr4.error.Errors import FailedPredicateException
                            raise FailedPredicateException(self, "self.precpred(self._ctx, 4)")
                        self.state = 259
                        self.match(PrismQLParser.And)
                        self.state = 260
                        self.bool_restriction(5)
                        pass

                    elif la_ == 2:
                        localctx = PrismQLParser.Bool_restrictionContext(self, _parentctx, _parentState)
                        self.pushNewRecursionContext(localctx, _startState, self.RULE_bool_restriction)
                        self.state = 261
                        if not self.precpred(self._ctx, 3):
                            from antlr4.error.Errors import FailedPredicateException
                            raise FailedPredicateException(self, "self.precpred(self._ctx, 3)")
                        self.state = 262
                        self.match(PrismQLParser.Or)
                        self.state = 263
                        self.bool_restriction(4)
                        pass

             
                self.state = 268
                self._errHandler.sync(self)
                _alt = self._interp.adaptivePredict(self._input,27,self._ctx)

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

        def Field(self):
            return self.getToken(PrismQLParser.Field, 0)

        def field_name(self):
            return self.getTypedRuleContext(PrismQLParser.Field_nameContext,0)


        def field_value(self):
            return self.getTypedRuleContext(PrismQLParser.Field_valueContext,0)


        def match_mode(self):
            return self.getTypedRuleContext(PrismQLParser.Match_modeContext,0)


        def SimilarTo(self):
            return self.getToken(PrismQLParser.SimilarTo, 0)

        def float_number(self):
            return self.getTypedRuleContext(PrismQLParser.Float_numberContext,0)


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
        self.enterRule(localctx, 26, self.RULE_condition)
        self._la = 0 # Token type
        try:
            self.state = 372
            self._errHandler.sync(self)
            token = self._input.LA(1)
            if token in [44]:
                self.enterOuterAlt(localctx, 1)
                self.state = 269
                self.match(PrismQLParser.Contains)
                self.state = 270
                self.match(PrismQLParser.T__1)
                self.state = 271
                self.hdict()
                self.state = 272
                self.match(PrismQLParser.T__2)
                pass
            elif token in [45]:
                self.enterOuterAlt(localctx, 2)
                self.state = 274
                self.match(PrismQLParser.ContainsTokens)
                self.state = 275
                self.match(PrismQLParser.T__1)
                self.state = 276
                self.hdict()
                self.state = 277
                self.match(PrismQLParser.T__2)
                pass
            elif token in [46]:
                self.enterOuterAlt(localctx, 3)
                self.state = 279
                self.match(PrismQLParser.ContainsPhrase)
                self.state = 280
                self.match(PrismQLParser.T__1)
                self.state = 281
                self.match(PrismQLParser.QUOTED_STRING)
                self.state = 282
                self.match(PrismQLParser.T__2)
                pass
            elif token in [47]:
                self.enterOuterAlt(localctx, 4)
                self.state = 283
                self.match(PrismQLParser.From)
                self.state = 284
                self.match(PrismQLParser.T__1)
                self.state = 285
                self.huser()
                self.state = 286
                self.match(PrismQLParser.T__2)
                pass
            elif token in [48]:
                self.enterOuterAlt(localctx, 5)
                self.state = 288
                self.match(PrismQLParser.MentionsUser)
                self.state = 289
                self.match(PrismQLParser.T__1)
                self.state = 290
                self.huser()
                self.state = 291
                self.match(PrismQLParser.T__2)
                pass
            elif token in [49]:
                self.enterOuterAlt(localctx, 6)
                self.state = 293
                self.match(PrismQLParser.IsQuestion)
                self.state = 294
                self.match(PrismQLParser.T__1)
                self.state = 295
                self.match(PrismQLParser.T__2)
                pass
            elif token in [50]:
                self.enterOuterAlt(localctx, 7)
                self.state = 296
                self.match(PrismQLParser.MentionsDate)
                self.state = 297
                self.match(PrismQLParser.T__1)
                self.state = 298
                self.match(PrismQLParser.T__2)
                pass
            elif token in [51]:
                self.enterOuterAlt(localctx, 8)
                self.state = 299
                self.match(PrismQLParser.MentionsTime)
                self.state = 300
                self.match(PrismQLParser.T__1)
                self.state = 301
                self.match(PrismQLParser.T__2)
                pass
            elif token in [52]:
                self.enterOuterAlt(localctx, 9)
                self.state = 302
                self.match(PrismQLParser.MentionsPlace)
                self.state = 303
                self.match(PrismQLParser.T__1)
                self.state = 304
                self.match(PrismQLParser.T__2)
                pass
            elif token in [53]:
                self.enterOuterAlt(localctx, 10)
                self.state = 305
                self.match(PrismQLParser.MentionsOrg)
                self.state = 306
                self.match(PrismQLParser.T__1)
                self.state = 307
                self.match(PrismQLParser.T__2)
                pass
            elif token in [54]:
                self.enterOuterAlt(localctx, 11)
                self.state = 308
                self.match(PrismQLParser.ContainsLink)
                self.state = 309
                self.match(PrismQLParser.T__1)
                self.state = 310
                self.match(PrismQLParser.T__2)
                pass
            elif token in [55]:
                self.enterOuterAlt(localctx, 12)
                self.state = 311
                self.match(PrismQLParser.HasFeature)
                self.state = 312
                self.match(PrismQLParser.T__1)
                self.state = 313
                self.feature_name()
                self.state = 314
                self.match(PrismQLParser.T__2)
                pass
            elif token in [56]:
                self.enterOuterAlt(localctx, 13)
                self.state = 316
                self.match(PrismQLParser.LabeledAs)
                self.state = 317
                self.match(PrismQLParser.T__1)
                self.state = 318
                self.feature_name()
                self.state = 319
                self.match(PrismQLParser.T__2)
                pass
            elif token in [57]:
                self.enterOuterAlt(localctx, 14)
                self.state = 321
                self.match(PrismQLParser.Field)
                self.state = 322
                self.match(PrismQLParser.T__1)
                self.state = 323
                self.field_name()
                self.state = 324
                self.match(PrismQLParser.T__3)
                self.state = 325
                self.field_value()
                self.state = 328
                self._errHandler.sync(self)
                _la = self._input.LA(1)
                if _la==4:
                    self.state = 326
                    self.match(PrismQLParser.T__3)
                    self.state = 327
                    self.match_mode()


                self.state = 330
                self.match(PrismQLParser.T__2)
                pass
            elif token in [58]:
                self.enterOuterAlt(localctx, 15)
                self.state = 332
                self.match(PrismQLParser.SimilarTo)
                self.state = 333
                self.match(PrismQLParser.T__1)
                self.state = 334
                self.match(PrismQLParser.QUOTED_STRING)
                self.state = 335
                self.match(PrismQLParser.T__3)
                self.state = 336
                self.float_number()
                self.state = 337
                self.match(PrismQLParser.T__2)
                pass
            elif token in [60]:
                self.enterOuterAlt(localctx, 16)
                self.state = 339
                self.match(PrismQLParser.HasWordOfDict)
                self.state = 340
                self.match(PrismQLParser.T__1)
                self.state = 341
                self.hdict()
                self.state = 342
                self.match(PrismQLParser.T__2)
                pass
            elif token in [68]:
                self.enterOuterAlt(localctx, 17)
                self.state = 344
                self.match(PrismQLParser.ByUser)
                self.state = 345
                self.match(PrismQLParser.T__1)
                self.state = 346
                self.huser()
                self.state = 347
                self.match(PrismQLParser.T__2)
                pass
            elif token in [67]:
                self.enterOuterAlt(localctx, 18)
                self.state = 349
                self.match(PrismQLParser.HasUserMentioned)
                self.state = 350
                self.match(PrismQLParser.T__1)
                self.state = 351
                self.huser()
                self.state = 352
                self.match(PrismQLParser.T__2)
                pass
            elif token in [66]:
                self.enterOuterAlt(localctx, 19)
                self.state = 354
                self.match(PrismQLParser.HasQuestion)
                self.state = 355
                self.match(PrismQLParser.T__1)
                self.state = 356
                self.match(PrismQLParser.T__2)
                pass
            elif token in [65]:
                self.enterOuterAlt(localctx, 20)
                self.state = 357
                self.match(PrismQLParser.HasDate)
                self.state = 358
                self.match(PrismQLParser.T__1)
                self.state = 359
                self.match(PrismQLParser.T__2)
                pass
            elif token in [61]:
                self.enterOuterAlt(localctx, 21)
                self.state = 360
                self.match(PrismQLParser.HasTime)
                self.state = 361
                self.match(PrismQLParser.T__1)
                self.state = 362
                self.match(PrismQLParser.T__2)
                pass
            elif token in [62]:
                self.enterOuterAlt(localctx, 22)
                self.state = 363
                self.match(PrismQLParser.HasLocation)
                self.state = 364
                self.match(PrismQLParser.T__1)
                self.state = 365
                self.match(PrismQLParser.T__2)
                pass
            elif token in [63]:
                self.enterOuterAlt(localctx, 23)
                self.state = 366
                self.match(PrismQLParser.HasOrganization)
                self.state = 367
                self.match(PrismQLParser.T__1)
                self.state = 368
                self.match(PrismQLParser.T__2)
                pass
            elif token in [64]:
                self.enterOuterAlt(localctx, 24)
                self.state = 369
                self.match(PrismQLParser.HasURL)
                self.state = 370
                self.match(PrismQLParser.T__1)
                self.state = 371
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
        self.enterRule(localctx, 28, self.RULE_temporal_filter)
        try:
            self.state = 391
            self._errHandler.sync(self)
            token = self._input.LA(1)
            if token in [33]:
                self.enterOuterAlt(localctx, 1)
                self.state = 374
                self.match(PrismQLParser.Before)
                self.state = 375
                self.match(PrismQLParser.T__1)
                self.state = 376
                self.timestamp()
                self.state = 377
                self.match(PrismQLParser.T__2)
                pass
            elif token in [34]:
                self.enterOuterAlt(localctx, 2)
                self.state = 379
                self.match(PrismQLParser.After)
                self.state = 380
                self.match(PrismQLParser.T__1)
                self.state = 381
                self.timestamp()
                self.state = 382
                self.match(PrismQLParser.T__2)
                pass
            elif token in [35]:
                self.enterOuterAlt(localctx, 3)
                self.state = 384
                self.match(PrismQLParser.Between)
                self.state = 385
                self.match(PrismQLParser.T__1)
                self.state = 386
                self.timestamp()
                self.state = 387
                self.match(PrismQLParser.T__3)
                self.state = 388
                self.timestamp()
                self.state = 389
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
        self.enterRule(localctx, 30, self.RULE_timestamp)
        try:
            self.state = 397
            self._errHandler.sync(self)
            token = self._input.LA(1)
            if token in [72]:
                localctx = PrismQLParser.AbsoluteTimestampContext(self, localctx)
                self.enterOuterAlt(localctx, 1)
                self.state = 393
                self.match(PrismQLParser.QUOTED_STRING)
                pass
            elif token in [70]:
                localctx = PrismQLParser.RelativeTimestampContext(self, localctx)
                self.enterOuterAlt(localctx, 2)
                self.state = 394
                self.time_value()
                self.state = 395
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
        self.enterRule(localctx, 32, self.RULE_groupby_clause)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 399
            self.match(PrismQLParser.GroupBy)
            self.state = 400
            self.groupby_field()
            self.state = 405
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            while _la==4:
                self.state = 401
                self.match(PrismQLParser.T__3)
                self.state = 402
                self.groupby_field()
                self.state = 407
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
        self.enterRule(localctx, 34, self.RULE_groupby_field)
        try:
            self.state = 414
            self._errHandler.sync(self)
            token = self._input.LA(1)
            if token in [59, 71]:
                localctx = PrismQLParser.SimpleGroupByContext(self, localctx)
                self.enterOuterAlt(localctx, 1)
                self.state = 408
                self.field_name()
                pass
            elif token in [39, 40, 41, 42, 43]:
                localctx = PrismQLParser.TemporalGroupByContext(self, localctx)
                self.enterOuterAlt(localctx, 2)
                self.state = 409
                self.temporal_group_func()
                self.state = 410
                self.match(PrismQLParser.T__1)
                self.state = 411
                self.field_name()
                self.state = 412
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
        self.enterRule(localctx, 36, self.RULE_temporal_group_func)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 416
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
        self.enterRule(localctx, 38, self.RULE_aggregate_clause)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 418
            self.match(PrismQLParser.Aggregate)
            self.state = 419
            self.aggregation_func()
            self.state = 424
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            while _la==4:
                self.state = 420
                self.match(PrismQLParser.T__3)
                self.state = 421
                self.aggregation_func()
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
        self.enterRule(localctx, 40, self.RULE_aggregation_func)
        try:
            self.state = 461
            self._errHandler.sync(self)
            la_ = self._interp.adaptivePredict(self._input,35,self._ctx)
            if la_ == 1:
                localctx = PrismQLParser.CountAllContext(self, localctx)
                self.enterOuterAlt(localctx, 1)
                self.state = 427
                self.match(PrismQLParser.Count)
                self.state = 428
                self.match(PrismQLParser.T__1)
                self.state = 429
                self.match(PrismQLParser.T__2)
                pass

            elif la_ == 2:
                localctx = PrismQLParser.CountDistinctContext(self, localctx)
                self.enterOuterAlt(localctx, 2)
                self.state = 430
                self.match(PrismQLParser.Count)
                self.state = 431
                self.match(PrismQLParser.T__1)
                self.state = 432
                self.match(PrismQLParser.Distinct)
                self.state = 433
                self.field_name()
                self.state = 434
                self.match(PrismQLParser.T__2)
                pass

            elif la_ == 3:
                localctx = PrismQLParser.DistinctValuesContext(self, localctx)
                self.enterOuterAlt(localctx, 3)
                self.state = 436
                self.match(PrismQLParser.Distinct)
                self.state = 437
                self.match(PrismQLParser.T__1)
                self.state = 438
                self.field_name()
                self.state = 439
                self.match(PrismQLParser.T__2)
                pass

            elif la_ == 4:
                localctx = PrismQLParser.SumFuncContext(self, localctx)
                self.enterOuterAlt(localctx, 4)
                self.state = 441
                self.match(PrismQLParser.Sum)
                self.state = 442
                self.match(PrismQLParser.T__1)
                self.state = 443
                self.field_name()
                self.state = 444
                self.match(PrismQLParser.T__2)
                pass

            elif la_ == 5:
                localctx = PrismQLParser.AvgFuncContext(self, localctx)
                self.enterOuterAlt(localctx, 5)
                self.state = 446
                self.match(PrismQLParser.Avg)
                self.state = 447
                self.match(PrismQLParser.T__1)
                self.state = 448
                self.field_name()
                self.state = 449
                self.match(PrismQLParser.T__2)
                pass

            elif la_ == 6:
                localctx = PrismQLParser.MinFuncContext(self, localctx)
                self.enterOuterAlt(localctx, 6)
                self.state = 451
                self.match(PrismQLParser.Min)
                self.state = 452
                self.match(PrismQLParser.T__1)
                self.state = 453
                self.field_name()
                self.state = 454
                self.match(PrismQLParser.T__2)
                pass

            elif la_ == 7:
                localctx = PrismQLParser.MaxFuncContext(self, localctx)
                self.enterOuterAlt(localctx, 7)
                self.state = 456
                self.match(PrismQLParser.Max)
                self.state = 457
                self.match(PrismQLParser.T__1)
                self.state = 458
                self.field_name()
                self.state = 459
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
        self.enterRule(localctx, 42, self.RULE_orderby_clause)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 463
            self.match(PrismQLParser.OrderBy)
            self.state = 464
            self.field_name()
            self.state = 466
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if _la==29 or _la==30:
                self.state = 465
                _la = self._input.LA(1)
                if not(_la==29 or _la==30):
                    self._errHandler.recoverInline(self)
                else:
                    self._errHandler.reportMatch(self)
                    self.consume()


            self.state = 475
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            while _la==4:
                self.state = 468
                self.match(PrismQLParser.T__3)
                self.state = 469
                self.field_name()
                self.state = 471
                self._errHandler.sync(self)
                _la = self._input.LA(1)
                if _la==29 or _la==30:
                    self.state = 470
                    _la = self._input.LA(1)
                    if not(_la==29 or _la==30):
                        self._errHandler.recoverInline(self)
                    else:
                        self._errHandler.reportMatch(self)
                        self.consume()


                self.state = 477
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
        self.enterRule(localctx, 44, self.RULE_limit_clause)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 478
            self.match(PrismQLParser.Limit)
            self.state = 479
            self.number()
            self.state = 482
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if _la==32:
                self.state = 480
                self.match(PrismQLParser.Offset)
                self.state = 481
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
        self.enterRule(localctx, 46, self.RULE_time_value)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 484
            self.number()
            self.state = 485
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
        self.enterRule(localctx, 48, self.RULE_time_unit)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 487
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
        self.enterRule(localctx, 50, self.RULE_number)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 489
            self.match(PrismQLParser.INTEGER)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class Float_numberContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def FLOAT(self):
            return self.getToken(PrismQLParser.FLOAT, 0)

        def INTEGER(self):
            return self.getToken(PrismQLParser.INTEGER, 0)

        def getRuleIndex(self):
            return PrismQLParser.RULE_float_number

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitFloat_number" ):
                return visitor.visitFloat_number(self)
            else:
                return visitor.visitChildren(self)




    def float_number(self):

        localctx = PrismQLParser.Float_numberContext(self, self._ctx, self.state)
        self.enterRule(localctx, 52, self.RULE_float_number)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 491
            _la = self._input.LA(1)
            if not(_la==69 or _la==70):
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

        def Run(self):
            return self.getToken(PrismQLParser.Run, 0)

        def getRuleIndex(self):
            return PrismQLParser.RULE_hdict

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitHdict" ):
                return visitor.visitHdict(self)
            else:
                return visitor.visitChildren(self)




    def hdict(self):

        localctx = PrismQLParser.HdictContext(self, self._ctx, self.state)
        self.enterRule(localctx, 54, self.RULE_hdict)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 493
            _la = self._input.LA(1)
            if not(((((_la - 59)) & ~0x3f) == 0 and ((1 << (_la - 59)) & 53249) != 0)):
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

        def QUOTED_STRING(self):
            return self.getToken(PrismQLParser.QUOTED_STRING, 0)

        def VARIABLE(self):
            return self.getToken(PrismQLParser.VARIABLE, 0)

        def WILDCARD(self):
            return self.getToken(PrismQLParser.WILDCARD, 0)

        def Run(self):
            return self.getToken(PrismQLParser.Run, 0)

        def getRuleIndex(self):
            return PrismQLParser.RULE_huser

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitHuser" ):
                return visitor.visitHuser(self)
            else:
                return visitor.visitChildren(self)




    def huser(self):

        localctx = PrismQLParser.HuserContext(self, self._ctx, self.state)
        self.enterRule(localctx, 56, self.RULE_huser)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 495
            _la = self._input.LA(1)
            if not(((((_la - 59)) & ~0x3f) == 0 and ((1 << (_la - 59)) & 61441) != 0)):
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

        def Run(self):
            return self.getToken(PrismQLParser.Run, 0)

        def getRuleIndex(self):
            return PrismQLParser.RULE_feature_name

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitFeature_name" ):
                return visitor.visitFeature_name(self)
            else:
                return visitor.visitChildren(self)




    def feature_name(self):

        localctx = PrismQLParser.Feature_nameContext(self, self._ctx, self.state)
        self.enterRule(localctx, 58, self.RULE_feature_name)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 497
            _la = self._input.LA(1)
            if not(_la==59 or _la==71):
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


    class Field_nameContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def STRING(self):
            return self.getToken(PrismQLParser.STRING, 0)

        def Run(self):
            return self.getToken(PrismQLParser.Run, 0)

        def getRuleIndex(self):
            return PrismQLParser.RULE_field_name

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitField_name" ):
                return visitor.visitField_name(self)
            else:
                return visitor.visitChildren(self)




    def field_name(self):

        localctx = PrismQLParser.Field_nameContext(self, self._ctx, self.state)
        self.enterRule(localctx, 60, self.RULE_field_name)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 499
            _la = self._input.LA(1)
            if not(_la==59 or _la==71):
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


    class Field_valueContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def STRING(self):
            return self.getToken(PrismQLParser.STRING, 0)

        def QUOTED_STRING(self):
            return self.getToken(PrismQLParser.QUOTED_STRING, 0)

        def VARIABLE(self):
            return self.getToken(PrismQLParser.VARIABLE, 0)

        def WILDCARD(self):
            return self.getToken(PrismQLParser.WILDCARD, 0)

        def Run(self):
            return self.getToken(PrismQLParser.Run, 0)

        def getRuleIndex(self):
            return PrismQLParser.RULE_field_value

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitField_value" ):
                return visitor.visitField_value(self)
            else:
                return visitor.visitChildren(self)




    def field_value(self):

        localctx = PrismQLParser.Field_valueContext(self, self._ctx, self.state)
        self.enterRule(localctx, 62, self.RULE_field_value)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 501
            _la = self._input.LA(1)
            if not(((((_la - 59)) & ~0x3f) == 0 and ((1 << (_la - 59)) & 61441) != 0)):
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


    class Match_modeContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def STRING(self):
            return self.getToken(PrismQLParser.STRING, 0)

        def getRuleIndex(self):
            return PrismQLParser.RULE_match_mode

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitMatch_mode" ):
                return visitor.visitMatch_mode(self)
            else:
                return visitor.visitChildren(self)




    def match_mode(self):

        localctx = PrismQLParser.Match_modeContext(self, self._ctx, self.state)
        self.enterRule(localctx, 64, self.RULE_match_mode)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 503
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
        self._predicates[9] = self.restriction_sempred
        self._predicates[12] = self.bool_restriction_sempred
        pred = self._predicates.get(ruleIndex, None)
        if pred is None:
            raise Exception("No predicate with index:" + str(ruleIndex))
        else:
            return pred(localctx, predIndex)

    def restriction_sempred(self, localctx:RestrictionContext, predIndex:int):
            if predIndex == 0:
                return self.precpred(self._ctx, 6)
         

            if predIndex == 1:
                return self.precpred(self._ctx, 5)
         

            if predIndex == 2:
                return self.precpred(self._ctx, 4)
         

            if predIndex == 3:
                return self.precpred(self._ctx, 3)
         

    def bool_restriction_sempred(self, localctx:Bool_restrictionContext, predIndex:int):
            if predIndex == 4:
                return self.precpred(self._ctx, 4)
         

            if predIndex == 5:
                return self.precpred(self._ctx, 3)
         




