"use client";

import { useState, useRef } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";

interface FormData {
  resumeText: string;
  resumeFile: File | null;
  desiredJobDescription: string;
  companyJobsUrl: string;
}

interface FormErrors {
  resume?: string;
  desiredJobDescription?: string;
  companyJobsUrl?: string;
  submit?: string;
}

export function UploadForm() {
  const router = useRouter();
  const fileInputRef = useRef<HTMLInputElement>(null);
  
  const [formData, setFormData] = useState<FormData>({
    resumeText: "",
    resumeFile: null,
    desiredJobDescription: "",
    companyJobsUrl: "",
  });
  
  const [errors, setErrors] = useState<FormErrors>({});
  const [isLoading, setIsLoading] = useState(false);
  const [inputMode, setInputMode] = useState<"paste" | "upload">("paste");

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      const validTypes = ["application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"];
      if (!validTypes.includes(file.type)) {
        setErrors(prev => ({ ...prev, resume: "Please upload a PDF or DOCX file" }));
        return;
      }
      setFormData(prev => ({ ...prev, resumeFile: file, resumeText: "" }));
      setErrors(prev => ({ ...prev, resume: undefined }));
    }
  };

  const fileToBase64 = (file: File): Promise<string> => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = () => {
        const result = reader.result as string;
        // Remove the data URL prefix
        const base64 = result.split(",")[1];
        resolve(base64);
      };
      reader.onerror = reject;
      reader.readAsDataURL(file);
    });
  };

  const validateForm = (): boolean => {
    const newErrors: FormErrors = {};
    
    if (!formData.resumeText && !formData.resumeFile) {
      newErrors.resume = "Please paste your resume or upload a file";
    }
    
    if (!formData.desiredJobDescription.trim()) {
      newErrors.desiredJobDescription = "Please describe your desired job";
    }
    
    if (!formData.companyJobsUrl.trim()) {
      newErrors.companyJobsUrl = "Please enter a company jobs URL";
    } else {
      try {
        const url = new URL(formData.companyJobsUrl);
        const isSupported = url.hostname.includes("greenhouse.io") || url.hostname.includes("lever.co") || url.hostname.includes("myworkdayjobs.com");
        if (!isSupported) {
          newErrors.companyJobsUrl = "Currently only Greenhouse, Lever, and Workday URLs are supported";
        }
      } catch {
        newErrors.companyJobsUrl = "Please enter a valid URL";
      }
    }
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!validateForm()) return;
    
    setIsLoading(true);
    setErrors({});
    
    try {
      const requestBody: Record<string, string> = {
        desired_job_description: formData.desiredJobDescription,
        company_jobs_url: formData.companyJobsUrl,
      };
      
      if (formData.resumeFile) {
        const base64 = await fileToBase64(formData.resumeFile);
        requestBody.resume_file_base64 = base64;
      } else {
        requestBody.resume_text = formData.resumeText;
      }
      
      const response = await fetch("/api/recommend", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(requestBody),
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail?.message || "Failed to get recommendations");
      }
      
      const data = await response.json();
      
      // Store results in sessionStorage and navigate
      sessionStorage.setItem("jobResults", JSON.stringify(data.results));
      router.push("/results");
      
    } catch (error) {
      setErrors({ 
        submit: error instanceof Error ? error.message : "An error occurred. Please try again." 
      });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Card className="w-full max-w-2xl mx-auto">
      <CardHeader>
        <CardTitle className="text-2xl">Find Your Best Jobs</CardTitle>
        <CardDescription>
          Upload your resume, describe your ideal role, and paste a company jobs link
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Resume Input */}
          <div className="space-y-4">
            <Label className="text-base font-medium">Your Resume</Label>
            
            <div className="flex gap-2 mb-2">
              <Button
                type="button"
                variant={inputMode === "paste" ? "default" : "outline"}
                size="sm"
                onClick={() => {
                  setInputMode("paste");
                  setFormData(prev => ({ ...prev, resumeFile: null }));
                }}
              >
                Paste Text
              </Button>
              <Button
                type="button"
                variant={inputMode === "upload" ? "default" : "outline"}
                size="sm"
                onClick={() => {
                  setInputMode("upload");
                  setFormData(prev => ({ ...prev, resumeText: "" }));
                }}
              >
                Upload File
              </Button>
            </div>
            
            {inputMode === "paste" ? (
              <Textarea
                placeholder="Paste your resume text here..."
                value={formData.resumeText}
                onChange={(e) => setFormData(prev => ({ ...prev, resumeText: e.target.value }))}
                className="min-h-[200px] font-mono text-sm"
              />
            ) : (
              <div className="space-y-2">
                <Input
                  ref={fileInputRef}
                  type="file"
                  accept=".pdf,.docx"
                  onChange={handleFileChange}
                  className="cursor-pointer"
                />
                {formData.resumeFile && (
                  <p className="text-sm text-muted-foreground">
                    Selected: {formData.resumeFile.name}
                  </p>
                )}
              </div>
            )}
            
            {errors.resume && (
              <p className="text-sm text-destructive">{errors.resume}</p>
            )}
          </div>

          {/* Desired Job Description */}
          <div className="space-y-2">
            <Label htmlFor="desired-job" className="text-base font-medium">
              Desired Job Type
            </Label>
            <Textarea
              id="desired-job"
              placeholder="e.g., Data analyst or analytics intern, Toronto or remote, SQL + dashboards"
              value={formData.desiredJobDescription}
              onChange={(e) => setFormData(prev => ({ ...prev, desiredJobDescription: e.target.value }))}
              className="min-h-[80px]"
            />
            {errors.desiredJobDescription && (
              <p className="text-sm text-destructive">{errors.desiredJobDescription}</p>
            )}
          </div>

          {/* Company Jobs URL */}
          <div className="space-y-2">
            <Label htmlFor="company-url" className="text-base font-medium">
              Company Jobs URL
            </Label>
            <Input
              id="company-url"
              type="text"
              placeholder="https://boards.greenhouse.io/companyname"
              value={formData.companyJobsUrl}
              onChange={(e) => setFormData(prev => ({ ...prev, companyJobsUrl: e.target.value }))}
            />
            <p className="text-xs text-muted-foreground">
              Supported: Greenhouse, Lever, and Workday (myworkdayjobs.com)
            </p>
            {errors.companyJobsUrl && (
              <p className="text-sm text-destructive">{errors.companyJobsUrl}</p>
            )}
          </div>

          {/* Submit Error */}
          {errors.submit && (
            <div className="p-4 bg-destructive/10 border border-destructive/20 rounded-lg">
              <p className="text-sm text-destructive">{errors.submit}</p>
            </div>
          )}

          {/* Submit Button */}
          <Button 
            type="submit" 
            className="w-full text-lg py-6"
            disabled={isLoading}
          >
            {isLoading ? (
              <span className="flex items-center gap-2">
                <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                </svg>
                Analyzing Jobs...
              </span>
            ) : (
              "Find Best Jobs"
            )}
          </Button>
          
          <p className="text-xs text-center text-muted-foreground">
            Recommendations are AI-generated guidance only. Always review job requirements before applying.
          </p>
        </form>
      </CardContent>
    </Card>
  );
}
