# C# Reference Implementation

## Attribution

This implementation is based on the original work by **Yakov Kuzmin**:
- Paper: "Query Processing and Optimization for a Custom Retrieval Language"
- Authors: Kuzmin, Smirnova, Slobodkin, Chernishev
- Conference: PANDL 2022
- Original repository: https://github.com/yakovypg/Chat-Corpora-Annotator
- Original file: `Chat-Corpora-Annotator/Infrastructure/Helpers/WindowIndexer.cs`

The histogram-based window merging algorithms (N+NS, N+S, P+NS, P+S) were originally developed by Yakov Kuzmin as part of his undergraduate thesis at SPbU (2020) and later published at PANDL 2022.

## Modifications Made

This standalone benchmark implementation was extracted and modified from the original Chat-Corpora-Annotator project to enable direct comparison with the Rust implementation. The following changes were made:

### 1. CSV Field Mapping Fix
**Problem**: The original code expected pre-processed data from the WPF application
**Fix**: Updated to read raw CSV with correct field mappings:
- Field 12: `fromUser.username`
- Field 22: `text` (message content)

### 2. CSV Parser Replacement
**Problem**: Initial manual CSV parsing with `string.Split(',')` couldn't handle:
- Quoted fields containing commas
- Escaped quotes within quoted fields
- Special characters and newlines

**Fix**: Added CsvHelper NuGet package for robust CSV parsing:
```xml
<PackageReference Include="CsvHelper" Version="33.1.0" />
```

### 3. User Mention Search
**Problem**: Username search format inconsistency
**Fix**: Changed to search without @ prefix to match actual data format
- Was searching: "@Kadams223"
- Now searching: "Kadams223"

### 4. JSON Export Addition
**Added**: JSON export functionality to enable automated comparison with Rust implementation
- Exports algorithm name, timing, count, and first 100 results
- Enables verification that both implementations find identical message combinations

### 5. Standalone Execution
**Changed**: Converted from library code to standalone console application
- Added command-line argument for CSV path
- Added progress output during loading
- Self-contained benchmark runner

## Running the Benchmark

```bash
dotnet build --configuration Release
dotnet run --configuration Release -- /path/to/data.csv
```

## Validation

After fixes, this implementation produces identical results to the Rust implementation:
- Q1: 19 results ✅
- Q2: 3,420 results ✅
- Q3: 6,370 results ✅

All message ID combinations match exactly between implementations, confirming correctness.