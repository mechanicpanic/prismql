// PrismQLCorpusLogic: pure helpers for the corpus card (graph @aleph/prismql,
// node #86) — which corpus to show, how each field's values read, what the
// corpus can answer. No DOM; tested by tests/board/corpus-logic.test.mjs.
(function (root) {
  "use strict";

  function fmt(n) {
    return n == null ? "—" : Number(n).toLocaleString("en-US");
  }

  // The one picked in the rail, else the selected request's, else the default.
  function corpusToShow(state, entry) {
    if (state.corpusSel) return state.corpusSel;
    if (entry && entry.corpus) return entry.corpus;
    return state.corpora && state.corpora.default ? state.corpora.default : null;
  }

  var ROLE_ORDER = ["id", "time", "kind", "actor"];
  function roleOf(name, schema) {
    if (name === schema.id_field) return "id";
    if (name === schema.timestamp_field) return "time";
    var board = schema.board || {};
    if (board.kind === name) return "kind";
    if (board.actor === name) return "actor";
    return null;
  }

  // A field's values as the server counted them: the most frequent with
  // their counts, or why none are listed.
  function valuesOf(field) {
    if (field.distinct == null) {
      return { values: [], note: "over " + fmt(field.distinct_over) + " values" };
    }
    if (!field.top) {
      return { values: [], note: field.distinct ? "one value per event" : "no values" };
    }
    var values = field.top.map(function (p) { return { v: p[0], n: p[1] }; });
    var rest = field.distinct - values.length;
    return { values: values, note: rest > 0 ? "+" + fmt(rest) + " more values" : "" };
  }

  // Role fields first (id, time, kind, actor), the rest by name.
  function fieldRows(schema) {
    return Object.keys(schema.fields || {}).map(function (name) {
      var f = schema.fields[name];
      var role = roleOf(name, schema);
      // ids are unique by load contract, however many the server counted
      var vals = role === "id" ? { values: [], note: "unique per event" } : valuesOf(f);
      return {
        name: name,
        type: f.type,
        coverage: f.coverage < 1 ? Math.round(f.coverage * 100) + "% of events" : "",
        role: role,
        values: vals.values,
        note: vals.note,
      };
    }).sort(function (a, b) {
      var ra = a.role ? ROLE_ORDER.indexOf(a.role) : ROLE_ORDER.length;
      var rb = b.role ? ROLE_ORDER.indexOf(b.role) : ROLE_ORDER.length;
      return ra - rb || (a.name < b.name ? -1 : a.name > b.name ? 1 : 0);
    });
  }

  function capabilities(schema) {
    var c = schema.capabilities || {};
    var sim = c.similar || {};
    return [
      {
        label: "similar", on: !!sim.available,
        title: sim.available ? "similar_to() and /similar: " + (sim.model || "embedding index")
          : "no embeddings in this corpus: similar_to() and /similar refuse",
      },
      {
        label: "search", on: !!c.search,
        title: c.search ? "/search ranks full text" : "/search needs the tantivy extra",
      },
    ];
  }

  function dictionaryRows(schema) {
    var terms = schema.dictionary_terms || {};
    return Object.keys(terms).map(function (name) {
      return { name: name, match: terms[name].match || schema.text_match, terms: terms[name].terms };
    });
  }

  function summary(schema) {
    var s = fmt(schema.documents) + " events";
    if (schema.complete === false) s += " · values from a sample of " + fmt(schema.sampled);
    return s;
  }

  var api = {
    fmt: fmt, corpusToShow: corpusToShow, valuesOf: valuesOf, fieldRows: fieldRows,
    capabilities: capabilities, dictionaryRows: dictionaryRows, summary: summary,
  };
  if (typeof module === "object" && module.exports) module.exports = api;
  else root.PrismQLCorpusLogic = api;
})(typeof window !== "undefined" ? window : globalThis);
