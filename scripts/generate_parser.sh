#!/bin/bash

# Script to generate PrismQL parser from ANTLR grammar

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"
GRAMMAR_DIR="$PROJECT_ROOT/src/prismql/grammar"
GENERATED_DIR="$GRAMMAR_DIR/generated"

# Check if ANTLR jar exists
ANTLR_JAR="$PROJECT_ROOT/antlr-4.13.1-complete.jar"
if [ ! -f "$ANTLR_JAR" ]; then
    echo "Downloading ANTLR 4.13.1..."
    curl -o "$ANTLR_JAR" https://www.antlr.org/download/antlr-4.13.1-complete.jar
fi

# Create generated directory if it doesn't exist
mkdir -p "$GENERATED_DIR"

# Generate Python parser
echo "Generating PrismQL parser..."
java -jar "$ANTLR_JAR" \
    -Dlanguage=Python3 \
    -visitor \
    -no-listener \
    -o "$GENERATED_DIR" \
    "$GRAMMAR_DIR/PrismQL.g4"

# Create __init__.py in generated directory
touch "$GENERATED_DIR/__init__.py"

echo "Parser generation complete!"
echo "Generated files in: $GENERATED_DIR"
