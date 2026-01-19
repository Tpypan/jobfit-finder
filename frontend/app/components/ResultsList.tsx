"use client";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

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

interface ResultsListProps {
  results: MatchResult[];
}

function ScoreBadge({ score }: { score: number }) {
  let colorClass = "bg-yellow-100 text-yellow-800";
  if (score >= 80) {
    colorClass = "bg-green-100 text-green-800";
  } else if (score >= 60) {
    colorClass = "bg-blue-100 text-blue-800";
  } else if (score < 40) {
    colorClass = "bg-red-100 text-red-800";
  }
  
  return (
    <span className={`px-3 py-1 rounded-full text-sm font-semibold ${colorClass}`}>
      {score}% Match
    </span>
  );
}

function JobCard({ result, rank }: { result: MatchResult; rank: number }) {
  const isTopThree = rank <= 3;
  
  return (
    <Card className={`transition-all hover:shadow-lg ${isTopThree ? "border-2 border-primary/50 bg-primary/5" : ""}`}>
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1">
            <div className="flex items-center gap-3 mb-1">
              {isTopThree && (
                <span className="inline-flex items-center justify-center w-7 h-7 rounded-full bg-primary text-primary-foreground text-sm font-bold">
                  {rank}
                </span>
              )}
              <CardTitle className="text-xl">{result.job.title}</CardTitle>
            </div>
            <CardDescription className="text-base">
              {result.job.location || "Location not specified"} • via {result.job.source}
            </CardDescription>
          </div>
          <ScoreBadge score={result.match_score} />
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Why it matches */}
        <div>
          <h4 className="font-semibold text-green-700 mb-2 flex items-center gap-2">
            <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
            </svg>
            Why This Matches
          </h4>
          <ul className="space-y-1">
            {result.why_matches.map((reason, i) => (
              <li key={i} className="text-sm text-muted-foreground flex items-start gap-2">
                <span className="text-green-600 mt-1">•</span>
                {reason}
              </li>
            ))}
          </ul>
        </div>
        
        {/* Potential gaps */}
        {result.gaps.length > 0 && result.gaps[0] !== "No significant gaps identified" && (
          <div>
            <h4 className="font-semibold text-amber-700 mb-2 flex items-center gap-2">
              <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
              </svg>
              Potential Gaps
            </h4>
            <ul className="space-y-1">
              {result.gaps.map((gap, i) => (
                <li key={i} className="text-sm text-muted-foreground flex items-start gap-2">
                  <span className="text-amber-600 mt-1">•</span>
                  {gap}
                </li>
              ))}
            </ul>
          </div>
        )}
        
        {/* Apply button */}
        <div className="pt-2">
          <Button asChild className="w-full sm:w-auto">
            <a href={result.job.apply_url} target="_blank" rel="noopener noreferrer">
              Apply Now →
            </a>
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}

export function ResultsList({ results }: ResultsListProps) {
  if (results.length === 0) {
    return (
      <Card className="text-center py-12">
        <CardContent>
          <p className="text-muted-foreground">No matching jobs found. Try a different company or adjust your preferences.</p>
        </CardContent>
      </Card>
    );
  }
  
  return (
    <div className="space-y-6">
      {/* Summary */}
      <div className="text-center">
        <h2 className="text-2xl font-bold mb-2">
          Found {results.length} Matching Jobs
        </h2>
        <p className="text-muted-foreground">
          Top 3 highlighted • Sorted by match score
        </p>
      </div>
      
      {/* Top 3 */}
      <div className="space-y-4">
        <h3 className="text-lg font-semibold text-primary">🏆 Top Recommendations</h3>
        {results.slice(0, 3).map((result, index) => (
          <JobCard key={result.job.id} result={result} rank={index + 1} />
        ))}
      </div>
      
      {/* Rest of results */}
      {results.length > 3 && (
        <div className="space-y-4">
          <h3 className="text-lg font-semibold">Other Matches</h3>
          {results.slice(3).map((result, index) => (
            <JobCard key={result.job.id} result={result} rank={index + 4} />
          ))}
        </div>
      )}
    </div>
  );
}
