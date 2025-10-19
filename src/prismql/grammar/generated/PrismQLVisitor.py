# Generated from /Users/asmirnov/Projects/vibes/prismql/src/prismql/grammar/PrismQL.g4 by ANTLR 4.13.1
from antlr4 import *

if "." in __name__:
    from .PrismQLParser import PrismQLParser
else:
    from PrismQLParser import PrismQLParser

# This class defines a complete generic visitor for a parse tree produced by PrismQLParser.


class PrismQLVisitor(ParseTreeVisitor):
    # Visit a parse tree produced by PrismQLParser#query.
    def visitQuery(self, ctx: PrismQLParser.QueryContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by PrismQLParser#body.
    def visitBody(self, ctx: PrismQLParser.BodyContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by PrismQLParser#query_seq.
    def visitQuery_seq(self, ctx: PrismQLParser.Query_seqContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by PrismQLParser#restrictions.
    def visitRestrictions(self, ctx: PrismQLParser.RestrictionsContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by PrismQLParser#restriction.
    def visitRestriction(self, ctx: PrismQLParser.RestrictionContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by PrismQLParser#condition.
    def visitCondition(self, ctx: PrismQLParser.ConditionContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by PrismQLParser#temporal_filter.
    def visitTemporal_filter(self, ctx: PrismQLParser.Temporal_filterContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by PrismQLParser#AbsoluteTimestamp.
    def visitAbsoluteTimestamp(self, ctx: PrismQLParser.AbsoluteTimestampContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by PrismQLParser#RelativeTimestamp.
    def visitRelativeTimestamp(self, ctx: PrismQLParser.RelativeTimestampContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by PrismQLParser#groupby_clause.
    def visitGroupby_clause(self, ctx: PrismQLParser.Groupby_clauseContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by PrismQLParser#SimpleGroupBy.
    def visitSimpleGroupBy(self, ctx: PrismQLParser.SimpleGroupByContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by PrismQLParser#TemporalGroupBy.
    def visitTemporalGroupBy(self, ctx: PrismQLParser.TemporalGroupByContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by PrismQLParser#temporal_group_func.
    def visitTemporal_group_func(self, ctx: PrismQLParser.Temporal_group_funcContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by PrismQLParser#aggregate_clause.
    def visitAggregate_clause(self, ctx: PrismQLParser.Aggregate_clauseContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by PrismQLParser#CountAll.
    def visitCountAll(self, ctx: PrismQLParser.CountAllContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by PrismQLParser#CountDistinct.
    def visitCountDistinct(self, ctx: PrismQLParser.CountDistinctContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by PrismQLParser#DistinctValues.
    def visitDistinctValues(self, ctx: PrismQLParser.DistinctValuesContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by PrismQLParser#SumFunc.
    def visitSumFunc(self, ctx: PrismQLParser.SumFuncContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by PrismQLParser#AvgFunc.
    def visitAvgFunc(self, ctx: PrismQLParser.AvgFuncContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by PrismQLParser#MinFunc.
    def visitMinFunc(self, ctx: PrismQLParser.MinFuncContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by PrismQLParser#MaxFunc.
    def visitMaxFunc(self, ctx: PrismQLParser.MaxFuncContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by PrismQLParser#orderby_clause.
    def visitOrderby_clause(self, ctx: PrismQLParser.Orderby_clauseContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by PrismQLParser#limit_clause.
    def visitLimit_clause(self, ctx: PrismQLParser.Limit_clauseContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by PrismQLParser#time_value.
    def visitTime_value(self, ctx: PrismQLParser.Time_valueContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by PrismQLParser#time_unit.
    def visitTime_unit(self, ctx: PrismQLParser.Time_unitContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by PrismQLParser#number.
    def visitNumber(self, ctx: PrismQLParser.NumberContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by PrismQLParser#hdict.
    def visitHdict(self, ctx: PrismQLParser.HdictContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by PrismQLParser#huser.
    def visitHuser(self, ctx: PrismQLParser.HuserContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by PrismQLParser#field_name.
    def visitField_name(self, ctx: PrismQLParser.Field_nameContext):
        return self.visitChildren(ctx)


del PrismQLParser
