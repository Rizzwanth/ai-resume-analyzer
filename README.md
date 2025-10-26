AI Resume Analyzer

## About the Project

This AI Resume Analyzer is a powerful tool designed to help both job seekers and recruiters. It uses Natural Language Processing (NLP) to parse and extract key information from PDF resumes.

For a **user**, it provides:

- Automated extraction of skills, contact information, and experience level.
- Personalized recommendations for skills and courses to improve their resume.
- A resume score based on the inclusion of important sections.

For an **admin**, it offers:

- A dashboard to view analytics on all processed resumes.
- The ability to export applicant data to a CSV file.
- Visual insights into the skill sets and experience levels of candidates.

This version has been modified to use SQLite for a simpler, file-based database, making setup and deployment much easier.

---

## Tech Stack

This project is built with the following technologies:

- **Backend:** Python
- **Web Framework:** Streamlit
- **Database:** SQLite3
- **Core Libraries:**
  - `pyresparser` for resume parsing
  - `spacy` for Natural Language Processing
  - `pandas` for data handling
  - `plotly` for data visualization

---

## Setup & Installation

Follow these steps to get the application running on your local machine.

### Prerequisites

Ensure you have **Python 3.9** or a compatible version installed on your system.

### 1\. Clone the Repository

Open your terminal or command prompt and clone the project to your computer.

```bash
git clone https://github.com/Rizzwanth/AI-Resume-Analyzer01.git
cd AI-Resume-Analyzer
```

### 2\. Create and Activate a Virtual Environment

It's best practice to use a virtual environment.

```bash
# Create the virtual environment
python -m venv venvapp

# Activate it (for Windows PowerShell)
.\venvapp\Scripts\Activate.ps1
```

_(If you get an error, run `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process` and try activating again.)_

### 3\. Install Required Packages

Navigate to the `App` directory and install all the necessary libraries from the `requirements.txt` file.

```bash
cd App
pip install -r requirements.txt
```

### 4\. Download NLP Data

The application requires data for the `nltk` and `spacy` libraries.

```bash
# Download the spaCy model
python -m spacy download en_core_web_sm

# Download the nltk stopwords
python -c "import nltk; nltk.download('stopwords')"
```

### 5\. Run the Application

You're all set\! Run the following command to start the Streamlit application.

```bash
streamlit run App.py
```

The application should now open in your web browser. You can use the sample resume in the `App/Uploaded_Resumes/` folder to test its functionality.
