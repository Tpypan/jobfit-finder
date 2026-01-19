"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { ResultsList } from "../components/ResultsList";

interface JobPosting {
  id: string;
  title: string;
  location: string;
  description: string;
  apply_url: string;
  source: string;
}

interface MatchResult {
  job: JobPosting;
  match_score: number;
  why_matches: string[];
  gaps: string[];
}

export default function ResultsPage() {
  const [results, setResults] = useState<MatchResult[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Load results from sessionStorage on mount
    const stored = sessionStorage.getItem("jobResults");
    let parsedResults: MatchResult[] = [];
    
    if (stored) {
      try {
        parsedResults = JSON.parse(stored);
      } catch {
        // Invalid JSON, use empty array
      }
    }
    
    setResults(parsedResults);
    setLoading(false);
  }, []);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4"></div>
          <p className="text-muted-foreground">Loading results...</p>
        </div>
      </div>
    );
  }

  if (results.length === 0) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 via-white to-blue-50 dark:from-slate-950 dark:via-slate-900 dark:to-slate-800">
        <div className="container mx-auto px-4 py-16 text-center">
          <h1 className="text-3xl font-bold mb-4">No Results Found</h1>
          <p className="text-muted-foreground mb-8">
            It looks like there are no job recommendations to display. 
            Please go back and submit your resume to find matching jobs.
          </p>
          <Button asChild>
            <Link href="/">← Start Over</Link>
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-white to-blue-50 dark:from-slate-950 dark:via-slate-900 dark:to-slate-800">
      {/* Header */}
      <header className="py-8 px-4 border-b bg-white/50 dark:bg-slate-900/50 backdrop-blur-sm">
        <div className="container mx-auto flex items-center justify-between">
          <Link href="/" className="text-2xl font-bold bg-gradient-to-r from-primary to-blue-600 bg-clip-text text-transparent">
            JobFit Finder
          </Link>
          <Button variant="outline" asChild>
            <Link href="/">← New Search</Link>
          </Button>
        </div>
      </header>

      {/* Results */}
      <main className="container mx-auto px-4 py-8 max-w-3xl">
        <ResultsList results={results} />
      </main>

      {/* Footer */}
      <footer className="py-8 text-center text-sm text-muted-foreground border-t">
        <p>
          Recommendations are AI-generated guidance only. Always review job requirements before applying.
        </p>
      </footer>
    </div>
  );
}
