# Error Autopsy
> A modern web application for high-performance students to analyze exam errors, understand their patterns, and optimize study routines.

## 🎯 Why?
The best strategy to achieve top grades isn't just to study hard, but to study smart and optimize your time.

**Error Autopsy** is a web application designed to track, categorize, and analyze mistakes made in exams. By shifting the focus from the score you got to *why* you lost those points, this tool provides data-driven insights to fix the root cause of academic gaps.

## ✨ Features

### 1. Smart Error Logging
- Log errors with specific metadata: **Subject**, **Topic**, **Description**, and **Error Type**
- Automatic date handling
- Persistent storage with Supabase

### 2. Visual Analytics Dashboard
- **Interactive Charts:** Real-time visualization with Altair
  - Error distribution by Type (Pie Chart)
  - Most problematic Subjects (Bar Chart)
  - Specific Topics with high error rates
  - Timeline of errors over time

### 3. AI-Powered Insights
- Pattern recognition to identify your weakest areas
- Actionable recommendations based on error types
- Focus on avoidable errors vs. knowledge gaps

### 4. User Authentication
- Secure login with Supabase Auth
- Session persistence
- Multi-user support

## 🛠️ Tech Stack
- **Frontend:** Streamlit
- **Database:** Supabase (PostgreSQL)
- **Authentication:** Supabase Auth
- **Data Visualization:** Altair
- **Language:** Python 3.10+

## 🚀 Quick Start

### Local Development

1. Clone the repository
```bash
git clone https://github.com/YOUR_USERNAME/error-autopsy.git
cd error-autopsy
```

2. Create and activate a virtual environment
```bash
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install dependencies
```bash
pip install -r requirements.txt
```

4. Configure environment variables
Create a `.env` file in the project root:
```bash
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_anon_key
```

5. Run the app
```bash
streamlit run app.py
```

### Deploy to Streamlit Cloud

1. Push your code to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your repository
4. Add secrets in Settings → Secrets:
   ```toml
   SUPABASE_URL = "your_url"
   SUPABASE_KEY = "your_key"
   ```
5. Deploy! 🎉

## 📊 Usage

1. **Sign Up / Login:** Create an account or log in
2. **Log Errors:** Navigate to "Log a Mistake" and record your errors
3. **Analyze:** View your dashboard to see patterns
4. **Review History:** Check past errors and edit if needed
5. **Improve:** Use insights to focus your studies

## 🔒 Security
- Environment variables are never committed to git
- Supabase handles authentication securely
- User data is isolated per account
