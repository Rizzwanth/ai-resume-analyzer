import streamlit as st
import google.generativeai as genai
import json
import re

# Configure the Gemini API key from Streamlit secrets
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
except (AttributeError, KeyError):
    st.error("GEMINI_API_KEY not found in Streamlit secrets. Please add it to your .streamlit/secrets.toml file.")
    st.stop()

# --- AI Model Configuration ---

# Generation settings for the "Job Seeker" function
generation_config = {
    "temperature": 0.5,
    "top_p": 1,
    "top_k": 1,
    "max_output_tokens": 2048,
    # We removed "response_mime_type" as gemini-1.0-pro doesn't always support it
}

# Generation settings for the "Recruiter" function (simple text)
generation_config_recruiter = {
    "temperature": 0.2,
    "top_p": 1,
    "top_k": 1,
    "max_output_tokens": 50,
}

# Safety settings (set to be permissive for the hackathon)
safety_settings = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
]

# --- Helper function to extract JSON ---
def extract_json_from_text(text):
    """
    Finds and extracts the first valid JSON object (starting with { and ending with })
    from a block of text.
    """
    # This regex finds the first occurrence of a JSON object
    match = re.search(r'\{.*\}', text, re.DOTALL)
    if match:
        json_string = match.group(0)
        try:
            # Try to parse the found string
            return json.loads(json_string)
        except json.JSONDecodeError as e:
            print(f"Failed to decode extracted JSON: {e}")
            return None
    else:
        print("No JSON object found in the text.")
        return None

# Initialize the Generative Model for Job Seeker
model = genai.GenerativeModel(
    model_name="gemini-2.5-pro",
    generation_config=generation_config,
    safety_settings=safety_settings
)

# Initialize the Generative Model for Recruiter
model_recruiter = genai.GenerativeModel(
    model_name="gemini-2.5-pro",

    generation_config=generation_config_recruiter,
    safety_settings=safety_settings
)

# --- Function 1: Job Seeker Analysis ---

def get_job_match_analysis(resume_text, job_description):
    """
    Analyzes a resume against a job description and returns a detailed JSON analysis.
    """
    
    prompt_parts = [
        "You are an expert ATS (Applicant Tracking System) and professional career coach.",
        "Analyze the provided resume against the provided job description.",
        "\n--- JOB DESCRIPTION ---\n", job_description,
        "\n--- RESUME ---\n", resume_text,
        "\n--- ANALYSIS ---\n",
        "Your response MUST contain a single, valid JSON object.",
        "That JSON object MUST include these four exact keys:",
        "1. 'match_score': An integer percentage (e.g., 85) representing how well the resume matches the job.",
        "2. 'strengths': A list of 2-3 specific bullet points highlighting the candidate's top qualifications for this role.",
        "3. 'gaps': A list of 2-3 critical skills or experiences from the job description that are missing from the resume.",
        "4. 'suggestions': A list of 2-3 actionable, short bullet-point suggestions for the candidate to add to their resume to improve their match score. These should be phrases, not general advice."
    ]

    try:
        response = model.generate_content(prompt_parts)
        # NEW: Use our helper function to find the JSON in the response text
        response_json = extract_json_from_text(response.text)
        
        if response_json is None:
            raise ValueError("No valid JSON found in AI response.")
            
        return response_json
        
    except Exception as e:
        print(f"Error in get_job_match_analysis: {e}")
        # Provide a fallback error response
        return {
            "match_score": 0,
            "strengths": ["Error: Could not analyze the resume."],
            "gaps": ["Please check the console for error details."],
            "suggestions": ["Try again later."]
        }

# --- Function 2: Recruiter Simple Score ---

def get_recruiter_match_score(resume_text, job_description):
    """
    Quickly returns just the match percentage for the recruiter's ranked list.
    """
    
    prompt_parts = [
        "You are a recruiter's ATS assistant.",
        "How well does this resume match this job description?",
        "\n--- JOB DESCRIPTION ---\n", job_description,
        "\n--- RESUME ---\n", resume_text,
        "\n--- SCORE ---\n",
        "Respond with ONLY the integer percentage (e.g., '85'). Do not add the '%' sign, any text, or any markdown."
    ]

    try:
        response = model_recruiter.generate_content(prompt_parts)
        # Clean up the response to get only the number
        score_text = re.findall(r'\d+', response.text)
        if score_text:
            return int(score_text[0])
        else:
            return 0 # No number found
            
    except Exception as e:
        print(f"Error getting recruiter score: {e}")
        return 0 # Return a 0 score on error

# --- Function 3: Tailored Bullet Point Generator ---

def generate_tailored_bullets(resume_text, job_description, strengths, gaps):
    """
    Generates tailored resume bullet points based on the analysis.
    """
    
    prompt_parts = [
        "You are an expert resume writer and career coach.",
        "A candidate has just received an analysis of their resume against a job description.",
        "\n--- JOB DESCRIPTION ---"
        "\n", job_description,
        "\n--- CANDIDATE'S RESUME ---"
        "\n", resume_text,
        "\n--- ANALYSIS ---"
        f"\nStrengths: {strengths}"
        f"\nGaps: {gaps}",
        "\n--- YOUR TASK ---"
        "\nBased on this analysis, your task is to write 3-4 professional, tailored bullet points that the candidate can *copy and paste* directly into their resume (e.g., under a 'Projects' or 'Experience' section).",
        "These bullet points should:",
        "1. Emphasize the candidate's 'Strengths' as they relate to the job.",
        "2. Cleverly re-frame their experience to minimize the 'Gaps.'",
        "3. Use strong, action-oriented verbs and keywords from the job description.",
        "\n--- TAILORED BULLET POINTS (Respond with ONLY the bullet points) ---"
    ]

    try:
        # We can use the simple recruiter model for this text-only generation
        response = model_recruiter.generate_content(prompt_parts)
        return response.text
        
    except Exception as e:
        print(f"Error generating tailored bullets: {e}")
        return "Error: Could not generate bullet points. Please try again."