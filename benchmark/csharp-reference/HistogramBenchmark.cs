using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Text.Json;
using CsvHelper;
using CsvHelper.Configuration;

namespace HistogramBenchmark
{
    public class Program
    {
        // Dictionary words from the paper
        static readonly Dictionary<string, string[]> Dictionaries = new()
        {
            ["job"] = new[] { "job", "work", "position", "listing", "posting", "freelance" },
            ["code"] = new[] { "code", "coding", "program", "programming" },
            ["skill"] = new[] { "python", "django", "javascript", "js", "jquery", "css", "ruby" },
            ["dev"] = new[] { "developer", "dev", "sr", "jr", "senior", "junior", "middle" },
            ["area"] = new[] { "web", "webdev", "gamedev", "frontend", "backend", "fullstack" },
            ["money"] = new[] { "pay", "salary", "wage" }
        };

        static void Main(string[] args)
        {
            Console.WriteLine("================================================================================");
            Console.WriteLine("C# HISTOGRAM BENCHMARK - Original PANDL 2022 Implementation");
            Console.WriteLine("================================================================================");
            Console.WriteLine();

            // Load data
            var csvPath = args.Length > 0 ? args[0] : "../data/freecodecamp_casual_chatroom.csv";
            Console.WriteLine($"Loading messages from {csvPath}...");

            var messages = LoadMessages(csvPath, 1_000_000);
            Console.WriteLine($"✓ Loaded {messages.Count} messages");
            Console.WriteLine();

            // Create message groups for each dictionary
            var messageGroups = new Dictionary<string, List<int>>();
            foreach (var (name, words) in Dictionaries)
            {
                messageGroups[name] = messages
                    .Where(m => words.Any(w => m.Content.ToLower().Contains(w)))
                    .Select(m => m.Id)
                    .OrderBy(id => id)
                    .ToList();

                Console.WriteLine($"{name}: {messageGroups[name].Count} messages");
            }

            // User mentions (for Q1)
            var userMentions = messages
                .Where(m => m.Content.Contains("Kadams223"))
                .Select(m => m.Id)
                .OrderBy(id => id)
                .ToList();
            Console.WriteLine($"mentions(Kadams223): {userMentions.Count} messages");
            Console.WriteLine();

            // Run benchmarks
            RunBenchmark("Q1", new[] {
                messageGroups["job"],
                messageGroups["code"],
                userMentions
            }, 40);

            RunBenchmark("Q2", new[] {
                messageGroups["job"],
                messageGroups["skill"],
                messageGroups["skill"], // duplicate for skill×2
                messageGroups["area"],
                messageGroups["money"]
            }, 40);

            RunBenchmark("Q3", new[] {
                messageGroups["job"],
                messageGroups["dev"],
                messageGroups["skill"],
                messageGroups["skill"], // duplicate for skill×2
                messageGroups["area"],
                messageGroups["money"]
            }, 60);
        }

        static void RunBenchmark(string name, List<int>[] groups, int windowSize)
        {
            Console.WriteLine($"================================================================================");
            Console.WriteLine($"{name}: {groups.Length} groups, window {windowSize}");
            Console.WriteLine($"Group sizes: {string.Join(", ", groups.Select(g => g.Count))}");
            Console.WriteLine();

            var results = new Dictionary<string, object>();

            // Run each algorithm
            var algorithms = new (string Name, Func<List<int>[], int, List<List<int>>> Func)[]
            {
                // Skip N+NS and N+S as they're extremely slow on large datasets
                //("N+NS", MergeNaiveNoSort),
                //("N+S", MergeNaiveWithSort),
                ("P+NS", MergePositionNoSort),
                ("P+S", MergePositionWithSort)
            };

            Console.WriteLine($"{"Algorithm",-10} {"Time (ms)",15} {"Results",15}");
            Console.WriteLine(new string('-', 40));

            foreach (var (algoName, algoFunc) in algorithms)
            {
                // Warmup
                algoFunc(groups, windowSize);

                // Benchmark (3 iterations)
                var times = new List<double>();
                List<List<int>> result = null;

                for (int i = 0; i < 3; i++)
                {
                    var sw = Stopwatch.StartNew();
                    result = algoFunc(groups, windowSize);
                    sw.Stop();
                    times.Add(sw.Elapsed.TotalMilliseconds);
                }

                var avgTime = times.Average();
                Console.WriteLine($"{algoName,-10} {avgTime,15:F1} {result.Count,15}");

                // Save results for comparison
                results[algoName] = new
                {
                    Algorithm = algoName,
                    Time = avgTime,
                    Count = result.Count,
                    Results = result.Take(100).ToList() // Save first 100 for verification
                };
            }

            // Save results to JSON
            var jsonPath = $"csharp_results_{name.ToLower()}.json";
            File.WriteAllText(jsonPath, JsonSerializer.Serialize(results, new JsonSerializerOptions { WriteIndented = true }));
            Console.WriteLine($"\n✓ Results saved to {jsonPath}");
            Console.WriteLine();
        }

        // N+NS: Naive, No Sort
        static List<List<int>> MergeNaiveNoSort(List<int>[] groups, int windowSize)
        {
            if (groups.Length == 0) return new List<List<int>>();
            if (groups.Length == 1) return groups[0].Select(x => new List<int> { x }).ToList();

            var results = new List<List<int>>();
            RecurseNaiveNoSort(new List<int>(), groups, results, windowSize);
            return results;
        }

        static void RecurseNaiveNoSort(List<int> partial, List<int>[] remainingGroups, List<List<int>> results, int windowSize)
        {
            if (remainingGroups.Length == 0)
            {
                if (!results.Any(r => r.SequenceEqual(partial)))
                    results.Add(new List<int>(partial));
                return;
            }

            var firstGroup = remainingGroups[0];
            var restGroups = remainingGroups.Skip(1).ToArray();

            foreach (var msg in firstGroup)
            {
                if (partial.Count > 0 && msg <= partial.Last())
                    continue;

                if (partial.Count > 0 && Math.Abs(msg - partial[0]) > windowSize)
                    continue;

                var newPartial = new List<int>(partial) { msg };
                RecurseNaiveNoSort(newPartial, restGroups, results, windowSize);
            }
        }

        // N+S: Naive with Sort
        static List<List<int>> MergeNaiveWithSort(List<int>[] groups, int windowSize)
        {
            if (groups.Length == 0) return new List<List<int>>();
            if (groups.Length == 1) return groups[0].Select(x => new List<int> { x }).ToList();

            var results = new List<List<int>>();
            var sortedGroups = groups.Select(g => g.OrderBy(x => x).ToList()).ToArray();
            RecurseNaiveWithSort(new List<int>(), sortedGroups, results, windowSize);
            return results;
        }

        static void RecurseNaiveWithSort(List<int> partial, List<int>[] remainingGroups, List<List<int>> results, int windowSize)
        {
            if (remainingGroups.Length == 0)
            {
                if (!results.Any(r => r.SequenceEqual(partial)))
                    results.Add(new List<int>(partial));
                return;
            }

            var firstGroup = remainingGroups[0];
            var restGroups = remainingGroups.Skip(1).ToArray();

            foreach (var msg in firstGroup)
            {
                if (partial.Count > 0 && msg <= partial.Last())
                    continue;

                if (partial.Count > 0 && Math.Abs(msg - partial[0]) > windowSize)
                    break; // Early termination due to sorting

                var newPartial = new List<int>(partial) { msg };
                RecurseNaiveWithSort(newPartial, restGroups, results, windowSize);
            }
        }

        // P+NS: Position-based, No Sort
        static List<List<int>> MergePositionNoSort(List<int>[] groups, int windowSize)
        {
            if (groups.Length == 0) return new List<List<int>>();
            if (groups.Length == 1) return groups[0].Select(x => new List<int> { x }).ToList();

            var results = new List<List<int>>();

            // Create placement array (keep first group fixed, others by size)
            var placement = new int[groups.Length];
            placement[0] = 0;

            var indices = Enumerable.Range(1, groups.Length - 1)
                .OrderBy(i => groups[i].Count)
                .ToArray();

            for (int i = 0; i < indices.Length; i++)
                placement[i + 1] = indices[i];

            foreach (var firstMsg in groups[0])
            {
                var accumulated = new int?[groups.Length];
                accumulated[0] = firstMsg;
                RecursePosition(groups, placement, windowSize, accumulated, 1, results, false);
            }

            return results;
        }

        // P+S: Position-based with Sort (Paper's best)
        static List<List<int>> MergePositionWithSort(List<int>[] groups, int windowSize)
        {
            if (groups.Length == 0) return new List<List<int>>();
            if (groups.Length == 1) return groups[0].Select(x => new List<int> { x }).ToList();

            var results = new List<List<int>>();
            var sortedGroups = groups.Select(g => g.OrderBy(x => x).Distinct().ToList()).ToArray();

            // Create placement array (keep first group fixed, sort others by size)
            var placement = new int[groups.Length];
            placement[0] = 0;

            var indices = Enumerable.Range(1, groups.Length - 1)
                .OrderBy(i => sortedGroups[i].Count)
                .ToArray();

            for (int i = 0; i < indices.Length; i++)
                placement[i + 1] = indices[i];

            foreach (var firstMsg in sortedGroups[0])
            {
                var accumulated = new int?[groups.Length];
                accumulated[0] = firstMsg;
                RecursePosition(sortedGroups, placement, windowSize, accumulated, 1, results, true);
            }

            return results;
        }

        static void RecursePosition(List<int>[] groups, int[] placement, int windowSize, int?[] accumulated,
            int curIndex, List<List<int>> results, bool sorted)
        {
            if (curIndex >= placement.Length)
            {
                var result = accumulated.Where(x => x.HasValue).Select(x => x.Value).ToList();
                if (!results.Any(r => r.SequenceEqual(result)))
                    results.Add(result);
                return;
            }

            int firstMsg = accumulated[0].Value;
            int curGroupPos = placement[curIndex];
            var curGroup = groups[curGroupPos];

            // Find previous and next messages
            int? prevMsg = null;
            int? nextMsg = null;

            for (int i = curGroupPos - 1; i >= 0; i--)
            {
                if (accumulated[i].HasValue)
                {
                    prevMsg = accumulated[i].Value;
                    break;
                }
            }

            for (int i = curGroupPos + 1; i < accumulated.Length; i++)
            {
                if (accumulated[i].HasValue)
                {
                    nextMsg = accumulated[i].Value;
                    break;
                }
            }

            foreach (var msg in curGroup)
            {
                if (prevMsg.HasValue && msg <= prevMsg)
                    continue;

                if (nextMsg.HasValue && msg >= nextMsg)
                {
                    if (sorted) break; // Early termination
                    continue;
                }

                if (Math.Abs(msg - firstMsg) > windowSize)
                {
                    if (sorted) break; // Early termination
                    continue;
                }

                var newAccumulated = (int?[])accumulated.Clone();
                newAccumulated[curGroupPos] = msg;
                RecursePosition(groups, placement, windowSize, newAccumulated, curIndex + 1, results, sorted);
            }
        }

        // Load messages from CSV using CsvHelper for proper parsing
        static List<Message> LoadMessages(string path, int limit)
        {
            var messages = new List<Message>();

            var config = new CsvConfiguration(CultureInfo.InvariantCulture)
            {
                HasHeaderRecord = true,
                BadDataFound = null // Ignore bad data
            };

            using var reader = new StreamReader(path);
            using var csv = new CsvReader(reader, config);

            // Read header
            csv.Read();
            csv.ReadHeader();

            int id = 0;
            while (csv.Read() && messages.Count < limit)
            {
                try
                {
                    // Field 12: fromUser.username
                    // Field 22: text
                    var username = csv.GetField<string>(12) ?? "";
                    var text = csv.GetField<string>(22) ?? "";

                    messages.Add(new Message
                    {
                        Id = id++,
                        Author = username,
                        Content = text
                    });
                }
                catch
                {
                    // Skip rows with parsing errors
                    continue;
                }
            }

            return messages;
        }
    }

    public class Message
    {
        public int Id { get; set; }
        public string Author { get; set; }
        public string Content { get; set; }
    }
}