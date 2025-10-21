# PrismQL Research Papers

This directory contains the foundational research papers that introduced the concepts behind PrismQL. These papers were published during the development of the original system and present the theoretical foundations and optimization techniques.

**Note:** The implementation stack described in these papers is different from the current PrismQL implementation, but the core concepts remain the same.

---

## Papers

### 1. Situation-Based Multiparticipant Chat Summarization (ACL 2021)

**File:** `2021.acl-srw.14.pdf`

**Full Title:** Situation-Based Multiparticipant Chat Summarization: a Concept, an Exploration-Annotation Tool and an Example Collection

**Authors:** Anna Smirnova, Evgeniy Slobodkin, George Chernishev

**Venue:** 59th Annual Meeting of the Association for Computational Linguistics and the 11th International Joint Conference on Natural Language Processing: Student Research Workshop (ACL-IJCNLP 2021)

**Publication:** August 2021, Pages 127–137

**DOI:** [10.18653/v1/2021.acl-srw.14](https://doi.org/10.18653/v1/2021.acl-srw.14)

**Abstract:**

This paper introduces the concept of "situation-based summarization" for text chat navigation, where situations are defined as "a subset of messages revolving around a single event in both temporal and contextual senses." The paper presents:

- Chat Corpora Annotator (CCA): An annotation system for exploring chat logs
- A custom query language for situation extraction
- The first gold-standard dataset for this task
- Publicly available software and data

**Relevance to PrismQL:**

This paper introduced the foundational concept of pattern-based querying for conversational data. The custom query language presented here evolved into what is now PrismQL. The idea of identifying message patterns based on both temporal (window-based) and contextual (content-based) criteria is core to PrismQL's design.

---

### 2. Query Processing and Optimization (PANDL 2022)

**File:** `2022.pandl-1.8.pdf`

**Full Title:** Query Processing and Optimization for a Custom Retrieval Language

**Authors:** Yakov Kuzin, Anna Smirnova, Evgeniy Slobodkin, George Chernishev

**Venue:** First Workshop on Pattern-based Approaches to NLP in the Age of Deep Learning (PANDL 2022)

**Publication:** October 2022, Pages 61–70, Gyeongju, Republic of Korea

**Abstract:**

This paper presents Matcher, a "custom, SQL-like retrieval language used to query collections of short documents, such as chat transcripts or tweets." The system enables annotators to identify thematically and temporally related document subsets. Key contributions:

- Optimization algorithms for query execution
- Benchmark results showing up to 10x improvement in execution speed and memory efficiency
- Strategic execution strategy selection for complex language semantics

**Relevance to PrismQL:**

This paper describes the optimization techniques and execution strategies for the query language. The performance improvements and algorithmic approaches (especially window-based merging and restriction processing) directly influenced PrismQL's current implementation. While the backend stack has changed, the core optimization principles remain relevant.

---

## Key Concepts

Both papers established the foundational concepts that PrismQL implements:

### 1. Window-Based Pattern Matching
Finding messages that co-occur within a temporal window (INWIN operator in PrismQL)

### 2. Content-Based Restrictions
Filtering messages by content features (contains, is_question, etc. in PrismQL)

### 3. User-Based Filtering
Identifying messages by participant (from operator in PrismQL)

### 4. Complex Pattern Composition
Combining multiple restrictions with boolean operators (AND, OR, NOT)

### 5. Query Optimization
Efficient execution strategies for pattern matching across large conversation datasets

---

## Evolution to PrismQL

The original system described in these papers has evolved significantly:

**Then (Papers):**
- Custom annotation tool (CCA)
- Research prototype
- Focus on annotation workflows
- Specific implementation stack

**Now (PrismQL):**
- General-purpose query language
- Backend-agnostic architecture
- Python library with multiple backends (PostgreSQL, DuckDB, OpenSearch, in-memory)
- Enhanced syntax (fluent operators, pattern variables, quantifiers, subqueries)
- Production-ready for LLM research and annotation platforms

---

## Citation

If you use PrismQL in your research, please cite these foundational papers:

```bibtex
@inproceedings{smirnova-etal-2021-situation,
    title = "Situation-Based Multiparticipant Chat Summarization: a Concept, an Exploration-Annotation Tool and an Example Collection",
    author = "Smirnova, Anna and Slobodkin, Evgeniy and Chernishev, George",
    booktitle = "Proceedings of the 59th Annual Meeting of the Association for Computational Linguistics and the 11th International Joint Conference on Natural Language Processing: Student Research Workshop",
    month = aug,
    year = "2021",
    address = "Online",
    publisher = "Association for Computational Linguistics",
    url = "https://aclanthology.org/2021.acl-srw.14",
    doi = "10.18653/v1/2021.acl-srw.14",
    pages = "127--137",
}

@inproceedings{kuzin-etal-2022-query,
    title = "Query Processing and Optimization for a Custom Retrieval Language",
    author = "Kuzin, Yakov and Smirnova, Anna and Slobodkin, Evgeniy and Chernishev, George",
    booktitle = "Proceedings of the First Workshop on Pattern-based Approaches to NLP in the Age of Deep Learning",
    month = oct,
    year = "2022",
    address = "Gyeongju, Republic of Korea",
    publisher = "Association for Computational Linguistics",
    url = "https://aclanthology.org/2022.pandl-1.8",
    pages = "61--70",
}
```

---

## Links

- **ACL 2021 Paper:** https://aclanthology.org/2021.acl-srw.14/
- **PANDL 2022 Paper:** https://aclanthology.org/2022.pandl-1.8/
- **Current PrismQL Repository:** https://github.com/prismql/prismql
