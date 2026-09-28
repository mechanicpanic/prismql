window.EXAMPLES = {
  "fcc": [
    {
      "label": "Questions about code help",
      "blurb": "Boolean AND over an annotation dictionary",
      "classic": "SELECT is_question() AND contains(CodeHelp)",
      "pipe": "is_question() and contains(CodeHelp)"
    },
    {
      "label": "Question then a non-question reply",
      "blurb": "Ordered sequence (FOLLOWED_BY / ~>) with a positional window",
      "classic": "SELECT is_question() FOLLOWED_BY NOT is_question() INWINDOW 3",
      "pipe": "is_question() ~> not is_question() |> within(3)"
    },
    {
      "label": "Same user follows up on their own question",
      "blurb": "Pattern variable ($u) binding the same field value across a sequence",
      "classic": "SELECT from($u) AND is_question() FOLLOWED_BY from($u) INWINDOW 10",
      "pipe": "from($u) and is_question() ~> from($u) |> within(10)"
    },
    {
      "label": "Bursts of three or more messages from one user",
      "blurb": "RUN: one group per maximal run of repeats, not one per starting message",
      "classic": "SELECT RUN(from($u)){3,} INWINDOW 1",
      "pipe": "run(from($u)){3,} |> within(1)"
    },
    {
      "label": "Unanswered code-help question",
      "blurb": "Negative sequence (NOT_FOLLOWED_BY / !~>) over a co-occurring restriction",
      "classic": "SELECT contains(CodeHelp) AND is_question() NOT_FOLLOWED_BY contains(SoftwareSupport) INWINDOW 20",
      "pipe": "contains(CodeHelp) and is_question() !~> contains(SoftwareSupport) |> within(20)"
    },
    {
      "label": "Questions and job-search chatter within an hour",
      "blurb": "Temporal co-occurrence (DURING / during) across two topics",
      "classic": "SELECT is_question(), contains(JobSearch) DURING 1 hour",
      "pipe": "is_question() + contains(JobSearch) |> during(1h)"
    },
    {
      "label": "Questions per day",
      "blurb": "Aggregation with a temporal GROUP BY bucket",
      "classic": "SELECT is_question() GROUP BY day(timestamp) AGGREGATE count()",
      "pipe": "is_question() |> group(day(timestamp)) |> count()"
    }
  ],
  "chicago": [
    {
      "label": "Theft then battery within an hour",
      "blurb": "Ordered sequence with a temporal window",
      "classic": "SELECT field(type, THEFT) FOLLOWED_BY field(type, BATTERY) DURING 1 hour",
      "pipe": "field(type, THEFT) ~> field(type, BATTERY) |> during(1h)"
    },
    {
      "label": "Assault then battery, escalation chain",
      "blurb": "Ordered sequence with an inline temporal window on the link",
      "classic": "SELECT field(type, ASSAULT) FOLLOWED_BY field(type, BATTERY) DURING 1 hour",
      "pipe": "field(type, ASSAULT) ~>(1h) field(type, BATTERY)"
    },
    {
      "label": "Thefts per day",
      "blurb": "Aggregation with a temporal GROUP BY bucket",
      "classic": "SELECT field(type, THEFT) GROUP BY day(timestamp) AGGREGATE count()",
      "pipe": "field(type, THEFT) |> group(day(timestamp)) |> count()"
    },
    {
      "label": "Narcotics and weapons violations within 30 minutes",
      "blurb": "Unordered temporal co-occurrence across two crime types",
      "classic": "SELECT field(type, NARCOTICS), field(type, \"WEAPONS VIOLATION\") DURING 30 minutes",
      "pipe": "field(type, NARCOTICS) + field(type, \"WEAPONS VIOLATION\") |> during(30m)"
    },
    {
      "label": "Count of burglaries",
      "blurb": "Simple aggregation over a filtered restriction",
      "classic": "SELECT field(type, BURGLARY) AGGREGATE count()",
      "pipe": "field(type, BURGLARY) |> count()"
    },
    {
      "label": "Robbery near a motor vehicle theft within 3 positions",
      "blurb": "Positional co-occurrence window over crime type (any key)",
      "classic": "SELECT field(type, ROBBERY), field(type, \"MOTOR VEHICLE THEFT\") INWINDOW 3",
      "pipe": "field(type, ROBBERY) + field(type, \"MOTOR VEHICLE THEFT\") |> within(3)"
    }
  ]
};
