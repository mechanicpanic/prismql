# Changelog

All notable changes to PrismQL will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Full publishing pipeline with GitHub Actions
- Pre-commit hooks for code quality
- Comprehensive type checking with mypy
- Code formatting and linting with ruff

## [0.1.0] - 2024-12-XX

### Added
- Initial PrismQL implementation
- ANTLR4-based query language parser
- Search backend abstraction with memory implementation
- Basic NLP backend support
- Window-based query processing
- Fluent syntax operators (contains, from, is_question, etc.)
- Legacy syntax backward compatibility
- Comprehensive test suite
- Documentation and examples

### Features
- **Query Language**: Complete PrismQL DSL with SELECT, INWIN, UNR support
- **Operators**: Both fluent and legacy syntax for all conditions
- **Backends**: Pluggable search and NLP backend architecture
- **Memory Backend**: Full-featured in-memory implementation for testing
- **Type Safety**: Complete type annotations for all APIs
- **Testing**: 14 comprehensive tests covering all functionality

[Unreleased]: https://github.com/prismql/prismql/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/prismql/prismql/releases/tag/v0.1.0