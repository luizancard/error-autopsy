# Error Autopsy

A performance tracking system for competitive exam prep. Built for students preparing for FUVEST, ENEM, UNICAMP, ITA/IME, SAT, and other high-stakes tests.

## What is this?

Most students focus on *what* they got wrong. This tool helps you understand *why* you're making mistakes and *how* to fix them.

Error Autopsy tracks three things that matter:
- **Speed**: Are you answering questions fast enough for exam conditions?
- **Accuracy**: Are you getting questions right consistently?
- **Patterns**: What types of mistakes are you repeating?

Instead of just logging errors, you get real-time feedback on your performance zones, pace analysis against exam benchmarks, and trajectory tracking across mock exams.

## Features

### Study Session Tracking
Log batches of practice questions with automatic performance metrics:
- Minutes per question (MPQ) vs exam-specific benchmarks
- Real-time pace warnings (too fast/too slow/optimal)
- Accuracy percentage with performance zones
- Context-aware subject selection based on exam type

### Mock Exam Logger
Track full practice exam scores over time:
- Score percentage tracking
- Performance trajectory charts
- Improvement trend analysis
- Multi-exam support (FUVEST Phase 1, ENEM Simulado, etc.)

### Performance Analytics
- **Speed vs Accuracy Scatter Plot**: Visualize the trade-off between pace and precision
- **Mock Exam Trajectory**: See your score progression over time
- **Activity Heatmap**: GitHub-style contribution calendar for study consistency
- **Error Classification**: Break down mistakes by type (Content Gap, Careless Error, Time Management, etc.)

### Excel Import/Export
Export all your data to Excel for advanced analysis or import previous study logs. Supports both Portuguese and English column names.

### Multi-User Support
Secure authentication with Supabase. Each user's data is completely isolated.

## Tech Stack

- **Frontend**: Streamlit (Python web framework)
- **Database**: Supabase (PostgreSQL with Row Level Security)
- **Visualizations**: Altair (declarative charts)
- **Auth**: Supabase Auth with cookie-based sessions
- **Excel**: openpyxl for import/export

## Setup

### Prerequisites
- Python 3.10 or higher
- A Supabase account (free tier works)

### Installation

1. Clone the repo
```bash
git clone https://github.com/YOUR_USERNAME/error-autopsy.git
cd error-autopsy
```

2. Create a virtual environment
```bash
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
```

3. Install dependencies
```bash
pip install -r requirements.txt
```

4. Set up environment variables

Create a `.env` file in the project root:
```bash
SUPABASE_URL=your_supabase_project_url
SUPABASE_KEY=your_supabase_anon_key
```

You can find these values in your Supabase project dashboard under Settings → API.

5. Set up the database

Go to your Supabase project → SQL Editor and run the migration file:
```
migrations/001_exam_telemetry_schema.sql
```

This creates three tables: `study_sessions`, `mock_exams`, and `errors` (with the new columns).

6. Run the app
```bash
streamlit run app.py
```

The app will open in your browser at `http://localhost:8501`.

## How to Use

### First Time Setup
1. Create an account on the login page
2. Log in with your credentials

### Logging a Study Session
1. Go to **Log Session** → **Study Session** tab
2. Select your exam type (FUVEST, ENEM, etc.)
3. Choose the subject (list adapts to your exam type)
4. Enter how many questions you did, how many you got right, and how long it took
5. Check the real-time performance preview
6. Submit

You'll see instant feedback on whether your pace is too fast, too slow, or optimal for that exam.

### Logging a Mock Exam
1. Go to **Log Session** → **Mock Exam** tab
2. Enter the exam name (e.g., "FUVEST 2024 Phase 1 Practice")
3. Select exam type
4. Enter your score and the maximum possible score
5. Add any notes about sections that were hard
6. Submit

### Viewing Analytics
Go to **Dashboard** to see:
- Overall KPIs (sessions logged, average accuracy, latest mock exam score)
- Speed vs Accuracy scatter plot (are you in the "Mastery Zone"?)
- Session performance by subject
- Mock exam score trajectory
- Study activity heatmap (last 6 months)
- Error breakdown by type and difficulty

### Exporting Data
1. Go to **History**
2. Click **Export to Excel**
3. Download the file with all your sessions, exams, and errors

### Importing Data
1. Prepare an Excel file with sheets named "Errors", "Sessions", and/or "Exams"
2. Go to **History**
3. Upload the file
4. System will validate and import your data

## Exam-Specific Benchmarks

The system knows the target pace for each exam:
- **FUVEST**: 3.0 min/question
- **ENEM**: 3.0 min/question
- **UNICAMP**: 3.5 min/question (longer, harder questions)
- **ITA/IME**: 4.0 min/question (extremely difficult)
- **SAT**: 1.25 min/question (~75 seconds)
- **General**: 2.5 min/question (conservative default)

Your "Optimal" pace zone is 50-120% of the benchmark. Anything under 50% flags as "Rushing", anything over 120% as "Too Slow".

## Performance Zones

**Accuracy Zones:**
- **Mastery**: 80%+ correct
- **Developing**: 60-79% correct
- **Struggling**: Below 60%

**Pace Zones:**
- **Rushing**: < 50% of benchmark (too fast, watch for careless errors)
- **Optimal**: 50-120% of benchmark (sweet spot)
- **Too Slow**: > 120% of benchmark (need to speed up for exam conditions)

**Combined Performance Zone:**
The scatter plot shows these combinations:
- **Mastery Zone** ⭐: Optimal pace + high accuracy (this is where you want to be)
- **Rushing & Accurate**: Fast + high accuracy (risky, might not scale)
- **Slow but Accurate**: Good accuracy but too slow (need speed drills)
- **Rushing & Struggling**: Fast + low accuracy (slow down and focus)
- **Needs Improvement**: Everything else

## Deployment

### Streamlit Cloud (Recommended)

1. Push your code to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your repository
4. Add your Supabase credentials in Settings → Secrets:
   ```toml
   SUPABASE_URL = "your_url"
   SUPABASE_KEY = "your_key"
   ```
5. Deploy

### Other Platforms
See `DEPLOYMENT_GUIDE.md` for detailed deployment instructions.

## Security

- Never commit your `.env` file (already in `.gitignore`)
- Supabase handles password hashing and session management
- Row Level Security (RLS) ensures users only see their own data
- All database operations validate user ownership

## Project Structure

```
error-autopsy/
├── app.py                          # Main Streamlit app
├── config/
│   └── settings.py                 # Exam types, benchmarks, constants
├── src/
│   ├── services/
│   │   ├── db_service.py           # Database CRUD operations
│   │   ├── auth_service.py         # Authentication logic
│   │   └── excel_service.py        # Import/Export functionality
│   ├── analysis/
│   │   ├── metrics.py              # Performance calculations
│   │   └── plots.py                # Chart generation
│   └── interface/
│       └── streamlit/
│           ├── telemetry_components.py  # Logging UI (tabs)
│           └── dashboard_components.py  # Analytics dashboard
├── migrations/
│   └── 001_exam_telemetry_schema.sql   # Database schema
└── requirements.txt
```

## Contributing

Found a bug? Have a feature request? Open an issue or submit a PR.

## License

MIT License - feel free to use this for your own exam prep.

---

Built for students who want to train like athletes and perform under pressure.
