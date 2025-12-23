# Error Autopsy CLI
> A tool for high-performance students to analyze exam errors, understand their own patterns, and optimize study routines.

## Why?
The best strategy to achieve top grades isn't just to study hard, but to study smart and optimize your time.

**Error Autopsy** is a command-line interface (CLI) tool designed to track, categorize, and analyze mistakes made in mock exams. By shifting the focus from the score you got to *why* you lost those points, this tool provides data-driven insights to fix the root cause of academic gaps.

## Features
### 1. Smart Logging
- Log errors with specific metadata: **Subject**, **Topic**, **Description**, and **Error Type**.
- Automatic date handling.
- Data persistence using JSON.

### 2. Visual Analytics (Matplotlib)
- **Dashboard View:** Generates a 4-panel dashboard to visualize:
  - Error distribution by Type.
  - Most problematic Subjects.
  - Specific Topics with high error rates.
  - Timeline of errors (Monthly).

### 3. AI Performance Coach (Google Gemini 2.5)
- Integrated with **Google Gemini 2.5 Flash**.
- **Deep Diagnosis:** Uses a "Senior Performance Psychologist" prompt to analyze your patterns and distinguish between lack of knowledge vs. lack of exam technique.
- **Study Plans:** Generates tactical, short-term study plans based on your weakest topics.

## Tech Stack
- **Language:** Python 3.13+
- **Database:** JSON (Local storage)
- **Data Visualization:** Matplotlib
- **AI Integration:** Google GenAI SDK (`google-genai`)
- **Environment Management:** Python Dotenv

## Installation
1. Clone the repository:
   ```bash
   git clone [https://github.com/SEU_USUARIO/error-autopsy.git](https://github.com/SEU_USUARIO/error-autopsy.git)
2.Install Dependencies:
   pip install matplotlib google-genai python-dotenv
3. Configure API Key:
   • Get you free key at Google AI Studio
   • Create a file with you key inside: GEMINI_API_KEY=your_api_key_here
