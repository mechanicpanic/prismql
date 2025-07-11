# Generated from /Users/asmirnov/Projects/vibes/prismql/src/prismql/grammar/PrismQL.g4 by ANTLR 4.13.1
from antlr4 import *
if "." in __name__:
    from .PrismQLParser import PrismQLParser
else:
    from PrismQLParser import PrismQLParser

# This class defines a complete generic visitor for a parse tree produced by PrismQLParser.

class PrismQLVisitor(ParseTreeVisitor):

    # Visit a parse tree produced by PrismQLParser#query.
    def visitQuery(self, ctx:PrismQLParser.QueryContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PrismQLParser#body.
    def visitBody(self, ctx:PrismQLParser.BodyContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PrismQLParser#query_seq.
    def visitQuery_seq(self, ctx:PrismQLParser.Query_seqContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PrismQLParser#restrictions.
    def visitRestrictions(self, ctx:PrismQLParser.RestrictionsContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PrismQLParser#restriction.
    def visitRestriction(self, ctx:PrismQLParser.RestrictionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PrismQLParser#condition.
    def visitCondition(self, ctx:PrismQLParser.ConditionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PrismQLParser#number.
    def visitNumber(self, ctx:PrismQLParser.NumberContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PrismQLParser#hdict.
    def visitHdict(self, ctx:PrismQLParser.HdictContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PrismQLParser#huser.
    def visitHuser(self, ctx:PrismQLParser.HuserContext):
        return self.visitChildren(ctx)



del PrismQLParser