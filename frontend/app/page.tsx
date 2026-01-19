import { UploadForm } from "./components/UploadForm";

export default function Home() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-white to-blue-50 dark:from-slate-950 dark:via-slate-900 dark:to-slate-800">
      {/* Hero Section */}
      <header className="py-16 px-4 text-center">
        <div className="max-w-3xl mx-auto space-y-6">
          <h1 className="text-5xl font-bold bg-gradient-to-r from-primary via-blue-600 to-purple-600 bg-clip-text text-transparent">
            JobFit Finder
          </h1>
          <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
            Upload your resume, describe your ideal role, and paste a company job link. 
            We&apos;ll find the best matching jobs for you with detailed explanations.
          </p>
          
          {/* Feature highlights */}
          <div className="flex flex-wrap justify-center gap-4 pt-4">
            <div className="flex items-center gap-2 text-sm text-muted-foreground bg-white dark:bg-slate-800 px-4 py-2 rounded-full shadow-sm">
              <span className="text-green-500">✓</span> AI-Powered Matching
            </div>
            <div className="flex items-center gap-2 text-sm text-muted-foreground bg-white dark:bg-slate-800 px-4 py-2 rounded-full shadow-sm">
              <span className="text-green-500">✓</span> Greenhouse & Lever Support
            </div>
            <div className="flex items-center gap-2 text-sm text-muted-foreground bg-white dark:bg-slate-800 px-4 py-2 rounded-full shadow-sm">
              <span className="text-green-500">✓</span> Detailed Explanations
            </div>
          </div>
        </div>
      </header>

      {/* Main Form */}
      <main className="container mx-auto px-4 pb-16">
        <UploadForm />
      </main>

      {/* Footer */}
      <footer className="py-8 text-center text-sm text-muted-foreground border-t">
        <p>
          JobFit Finder • Powered by AI • Your resume is never stored
        </p>
      </footer>
    </div>
  );
}
