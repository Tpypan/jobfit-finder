# JobFit Finder

Upload your resume + preferences, paste a company job link, get the best jobs to apply to with explanations.

## Features

- 📄 Resume parsing (PDF, DOCX, or plain text)
- 🔗 Supports Greenhouse and Lever job boards
- 🤖 AI-powered job matching with Gemini
- 📊 Ranked recommendations with match scores
- ✅ Clear explanations of why jobs match
- ⚠️ Identifies skill gaps for each role

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- Gemini API key ([Get one here](https://aistudio.google.com/))

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -e .

# Set up environment variables
cp ../.env.example .env
# Edit .env and add your GEMINI_API_KEY

# Run the server
uvicorn app.main:app --reload --port 8000
```

Backend runs at http://localhost:8000

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Run the dev server
npm run dev
```

Frontend runs at http://localhost:3000

## API Endpoints

### Health Check

```
GET /health
```

### Get Job Recommendations

```
POST /api/recommend
Content-Type: application/json

{
  "resume_text": "Your resume text here...",
  "desired_job_description": "data analyst intern, SQL, remote",
  "company_jobs_url": "https://boards.greenhouse.io/companyname"
}
```

**Response:**

```json
{
  "results": [
    {
      "job": {
        "id": "123",
        "title": "Data Analyst Intern",
        "location": "Remote",
        "description": "...",
        "apply_url": "https://...",
        "source": "greenhouse"
      },
      "match_score": 85,
      "why_matches": ["Strong SQL skills match requirements", "..."],
      "gaps": ["No experience with Tableau mentioned", "..."]
    }
  ]
}
```

## Supported Job Boards

| Platform   | URL Pattern              | Example                             |
| ---------- | ------------------------ | ----------------------------------- |
| Greenhouse | `boards.greenhouse.io/*` | https://boards.greenhouse.io/stripe |
| Lever      | `jobs.lever.co/*`        | https://jobs.lever.co/figma         |

## Development

### Run Backend Tests

```bash
cd backend
python -m pytest tests/ -v
```

### Project Structure

```
jobfit-finder/
├── backend/
│   ├── app/
│   │   ├── api/           # API routes
│   │   ├── core/          # Config & Gemini client
│   │   ├── models/        # Pydantic schemas
│   │   └── services/      # Business logic
│   └── tests/
└── frontend/
    └── app/
        ├── components/    # React components
        └── results/       # Results page
```

## Security & Privacy

- Resumes are processed in-memory only, never stored
- Job postings are cached locally for performance
- API keys loaded from environment, never hardcoded

## Disclaimer

Job recommendations are AI-generated guidance only. Always review job requirements carefully before applying.

## License

MIT
