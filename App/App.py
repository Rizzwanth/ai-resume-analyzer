###### Packages Used ######
import streamlit as st # core package used in this project
import pandas as pd
import base64, random
import time,datetime
import sqlite3
import os
import socket
import platform
import geocoder
import glob
import secrets
import io,random
import plotly.express as px # to create visualisations at the admin session
import plotly.graph_objects as go
from geopy.geocoders import Nominatim
# libraries used to parse the pdf files
from pdfminer3.layout import LAParams, LTTextBox
from pdfminer3.pdfpage import PDFPage
from pdfminer3.pdfinterp import PDFResourceManager
from pdfminer3.pdfinterp import PDFPageInterpreter
from pdfminer3.converter import TextConverter
from PIL import Image
# pre stored data for prediction purposes

import nltk
nltk.download('stopwords')
# Add this line
from gemini_helper import get_job_match_analysis, get_recruiter_match_score, generate_tailored_bullets
###### Preprocessing functions ######


# Generates a link allowing the data in a given panda dataframe to be downloaded in csv format 
def get_csv_download_link(df,filename,text):
    csv = df.to_csv(index=False)
    ## bytes conversions
    b64 = base64.b64encode(csv.encode()).decode()      
    href = f'<a href="data:file/csv;base64,{b64}" download="{filename}">{text}</a>'
    return href


# Reads Pdf file and check_extractable
def pdf_reader(file):
    resource_manager = PDFResourceManager()
    fake_file_handle = io.StringIO()
    converter = TextConverter(resource_manager, fake_file_handle, laparams=LAParams())
    page_interpreter = PDFPageInterpreter(resource_manager, converter)
    with open(file, 'rb') as fh:
        for page in PDFPage.get_pages(fh,
                                      caching=True,
                                      check_extractable=True):
            page_interpreter.process_page(page)
            print(page)
        text = fake_file_handle.getvalue()

    ## close open handles
    converter.close()
    fake_file_handle.close()
    return text


# show uploaded file path to view pdf_display
def show_pdf(file_path):
    with open(file_path, "rb") as f:
        base64_pdf = base64.b64encode(f.read()).decode('utf-8')
    pdf_display = F'<iframe src="data:application/pdf;base64,{base64_pdf}" width="700" height="1000" type="application/pdf"></iframe>'
    st.markdown(pdf_display, unsafe_allow_html=True)


# course recommendations which has data already loaded from Courses.py


###### Database Stuffs ######


# sql connector
connection = sqlite3.connect('cv.db')
cursor = connection.cursor()

# inserting feedback data into user_feedback table
def insertf_data(feed_name,feed_email,feed_score,comments,Timestamp):
    DBf_table_name = 'user_feedback'
    insertfeed_sql = "insert into " + DBf_table_name + """
    values (NULL,?,?,?,?,?)"""
    rec_values = (feed_name, feed_email, feed_score, comments, Timestamp)
    cursor.execute(insertfeed_sql, rec_values)
    connection.commit()


###### Setting Page Configuration (favicon, Logo, Title) ######
# === Custom Theme and Styling ===

st.set_page_config(
   page_title="Smart Resume Matcher",
   page_icon='🎯',  # An emoji is clean and requires no file
   layout="wide"  # Use the full page width
)


###### Main function run() ######

def run():
    # === Add this initialization ===
    if 'ranked_candidates' not in st.session_state:
        st.session_state.ranked_candidates = None
    # ===============================

    # (Logo, Heading, Sidebar etc)
    # ... rest of the run function
    # (Logo, Heading, Sidebar etc)
    img = Image.open('./Logo/RESUM.png')
    st.image(img)
    st.sidebar.markdown("# Navigation")
    activities = ["User", "Feedback", "About", "Recruiter"]
    choice = st.sidebar.selectbox("Choose among the given options:", activities)


    # Create table user_data and user_feedback
    DBf_table_name = 'user_feedback'
    tablef_sql = "CREATE TABLE IF NOT EXISTS " + DBf_table_name + """
                (ID INTEGER PRIMARY KEY AUTOINCREMENT,
                    feed_name varchar(50) NOT NULL,
                    feed_email VARCHAR(50) NOT NULL,
                    feed_score VARCHAR(5) NOT NULL,
                    comments VARCHAR(100) NULL,
                    Timestamp VARCHAR(50) NOT NULL
                );
            """
    cursor.execute(tablef_sql)


    ###### CODE FOR CLIENT SIDE (USER) ######

    if choice == 'User':
        
        # Collecting Miscellaneous Information
        act_name = st.text_input('Name*')
        act_mail = st.text_input('Mail*')
        act_mob  = st.text_input('Mobile Number*')
        sec_token = secrets.token_urlsafe(12)
        host_name = socket.gethostname()
        ip_add = socket.gethostbyname(host_name)
        dev_user = os.getlogin()
        os_name_ver = platform.system() + " " + platform.release()
        city = 'Not Found'
        state = 'Not Found'
        country = 'Not Found'
        latlong = None
        try:
            g = geocoder.ip('me')
            latlong = g.latlng
            geolocator = Nominatim(user_agent="http")
            if latlong:
                location = geolocator.reverse(latlong, language='en')
                if location and 'address' in location.raw:
                    address = location.raw['address']
                    city = address.get('city', '')
                    state = address.get('state', '')
                    country = address.get('country', '')
        except Exception as e:
            # If there's any error during geocoding, just pass silently
            pass

        # Upload Resume
        st.markdown('''<h5 style='text-align: left; color: white;'> Upload Your Resume, And Get Smart Recommendations</h5>''',unsafe_allow_html=True)
        
        ## file upload in pdf format
        pdf_file = st.file_uploader("Choose your Resume", type=["pdf", "txt"])

        # This is the new part that will fix the issue
        if 'pdf_file_name' not in st.session_state or st.session_state.pdf_file_name != pdf_file.name:
            if pdf_file is not None:
                st.session_state.pdf_file_name = pdf_file.name
                st.session_state.resume_data = None  # Clear previous data
        
        if pdf_file is not None:
            # 1. --- Original Code (Saving and Reading) ---
            pdf_name = pdf_file.name
            save_image_path = os.path.join('./Uploaded_Resumes/', pdf_name)
            
            with open(save_image_path, "wb") as f:
                f.write(pdf_file.getbuffer())
            
            # Show the PDF
            show_pdf(save_image_path)

            # Get the whole resume text
            resume_text = pdf_reader(save_image_path)
                    
            
            
            st.header("🎯 Job Description Analysis")
            job_description = st.text_area("Paste the Job Description here to analyze your match:", height=300)

            if st.button("Analyze My Resume Match"):
                if not job_description:
                    st.error("Please paste a job description to analyze.")
                else:
                    with st.spinner('Our AI Coach is analyzing your resume... This may take a moment.'):
                        progress = st.progress(0, text="Initializing...")

                        txt_filename = os.path.splitext(pdf_name)[0] + ".txt"
                        txt_save_path = os.path.join('./Uploaded_Resumes/', txt_filename)
                        time.sleep(0.9)
                        progress.progress(30, text="Extracting Resume Data...")
                        time.sleep(1.9)
                        # your resume parsing code here
                        

                        try:
                            with open(txt_save_path, "w", encoding="utf-8") as f:
                                f.write(resume_text)
                                progress.progress(60, text="Analyzing Skills Match...")
                                time.sleep(1.5)
                        # skill extraction and matching
                        except Exception as e:
                            st.warning(f"Could not save .txt resume file: {e}")

                        progress.progress(97, text="Finalizing...")
                        time.sleep(1.9)
                        # --- Call the AI Engine (Step 2) ---
                        analysis_json = get_job_match_analysis(resume_text, job_description)
                    
                    st.success("Analysis Complete!")
                    progress.progress(100, text="Complete!")
                    st.balloons()
                    
                    # --- Display the new AI-powered output (Step 3) ---
                    

                    # 1. Display the Score
                    score = analysis_json.get('match_score', 0)
                    st.subheader(f"Your Job Match Score: {score}%")
                    
                    # Custom CSS for the progress bar
                    st.markdown(
                        f"""
                        <style>
                            .stProgress > div > div > div > div {{
                                background-image: linear-gradient(to right, #1ed760, #fba171, #d73b5c);
                            }}
                        </style>""",
                        unsafe_allow_html=True,
                    )
                    st.progress(score)
                    st.markdown(f"**Based on the AI's analysis, you are a {score}% match for this role.**")
                    
                    st.divider()

                    # 2. Display Strengths and Gaps
                    col1, col2 = st.columns(2)
                    with col1:
                        st.subheader("✅ Your Strengths")
                        strengths = analysis_json.get('strengths', [])
                        if strengths:
                            for item in strengths:
                                st.markdown(f"<li>{item}</li>", unsafe_allow_html=True)
                        else:
                            st.write("No specific strengths identified.")
                    
                    with col2:
                        st.subheader("⚠️ Your Gaps")
                        gaps = analysis_json.get('gaps', [])
                        if gaps:
                            for item in gaps:
                                st.markdown(f"<li>{item}</li>", unsafe_allow_html=True)
                        else:
                            st.write("No specific gaps identified.")

                    st.divider()
                    
                    # 3. Display Tailoring Suggestions
                    st.subheader("💡 AI Tailoring Suggestions")
                    st.info("Consider adding these AI-suggested keywords and phrases to your resume to improve your match.")
                    suggestions = analysis_json.get('suggestions', [])
                    if suggestions:
                        for item in suggestions:
                            st.markdown(f"<li>{item}</li>", unsafe_allow_html=True)
                    else:
                        st.write("No specific suggestions provided.")
                
    ###### CODE FOR FEEDBACK SIDE ######
    elif choice == 'Feedback':   
        
        # timestamp 
        ts = time.time()
        cur_date = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d')
        cur_time = datetime.datetime.fromtimestamp(ts).strftime('%H:%M:%S')
        timestamp = str(cur_date+'_'+cur_time)

        # Feedback Form
        with st.form("my_form"):
            st.write("Feedback form")            
            feed_name = st.text_input('Name')
            feed_email = st.text_input('Email')
            feed_score = st.slider('Rate Us From 1 - 5', 1, 5)
            comments = st.text_input('Comments')
            Timestamp = timestamp        
            submitted = st.form_submit_button("Submit")
            if submitted:
                ## Calling insertf_data to add dat into user feedback
                insertf_data(feed_name,feed_email,feed_score,comments,Timestamp)    
                ## Success Message 
                st.success("Thanks! Your Feedback was recorded.") 
                ## On Successful Submit
                st.balloons()    


        # query to fetch data from user feedback table
        query = 'select * from user_feedback'        
        plotfeed_data = pd.read_sql(query, connection)                        


        # fetching feed_score from the query and getting the unique values and total value count 
        labels = plotfeed_data.feed_score.unique()
        values = plotfeed_data.feed_score.value_counts()


        # plotting pie chart for user ratings
        st.subheader("**Past User Rating's**")
        fig = px.pie(values=values, names=labels, title="Chart of User Rating Score From 1 - 5", color_discrete_sequence=px.colors.sequential.Aggrnyl)
        st.plotly_chart(fig)


        #  Fetching Comment History
        cursor.execute('select feed_name, comments from user_feedback')
        plfeed_cmt_data = cursor.fetchall()

        st.subheader("**User Comment's**")
        dff = pd.DataFrame(plfeed_cmt_data, columns=['User', 'Comment'])
        st.dataframe(dff, width=1000)

    
    ###### CODE FOR ABOUT PAGE ######
    elif choice == 'About':   

        st.subheader("**About The Tool - AI RESUME ANALYZER**")

        st.markdown('''
        <p align='justify'>
            This is an advanced <b>Smart Resume Analyzer with Job Matching</b>, built in 24 hours for the hackathon. It leverages a powerful Generative AI model (Google's Gemini) to bridge the gap between job seekers and recruiters.
        </p>

        <p align="justify">
            <b>How to use it: -</b> <br/><br/>
            <b>User -</b> <br/>
            1. Go to the <b>User</b> page and fill in your details.<br/>
            2. Upload your PDF resume.<br/>
            3. Paste the complete job description for a role you are targeting.<br/>
            4. Click "Analyze" to get an instant AI-powered breakdown of your match score, strengths, gaps, and specific suggestions to tailor your resume for that exact job.<br/><br/>
            
            <b>Recruiter -</b> <br/>
            1. Go to the <b>Recruiter</b> page and log in (use <b>admin</b> / <b>admin@resume-analyzer</b>).<br/>
            2. Paste a job description for a role you are hiring for.<br/>
            3. Click "Rank Candidates" to instantly scan every resume in the database.<br/>
            4. The AI will analyze and rank all candidates from best-match to worst-match, helping you find the perfect talent in seconds.<br/><br/>
            
            <b>Feedback -</b> <br/>
            A place where users can submit feedback about the tool.
        </p><br/><br/>
        ''', unsafe_allow_html=True)


    ###### CODE FOR ADMIN SIDE (ADMIN) ######
   ###### CODE FOR RECRUITER SIDE ######
    ###### CODE FOR RECRUITER SIDE ######
    else:
        st.success('Welcome to the Recruiter Portal')

        # --- Initialize Login State ---
        if 'logged_in' not in st.session_state:
            st.session_state.logged_in = False

        # --- Show Login Form ONLY if not logged in ---
        if not st.session_state.logged_in:
            ad_user = st.text_input("Username")
            ad_password = st.text_input("Password", type='password')

            st.markdown('''
                        <h6 style='text-align: left; color: white;'>For login use <b>admin</b> as username and <b>admin@resume-analyzer</b> as password.</h6>''', unsafe_allow_html=True)

            if st.button('Login'):
                if ad_user == 'admin' and ad_password == 'admin@resume-analyzer':
                    st.session_state.logged_in = True # Set login state
                    st.rerun() # Rerun the script immediately to reflect login
                else:
                    st.error("Wrong ID & Password Provided")
        
        # --- Show Recruiter Tools ONLY if logged in ---
        if st.session_state.logged_in:
            st.success("Login Successful!") # Good feedback

            # --- Initialize ranked_candidates state if needed ---
            if 'ranked_candidates' not in st.session_state:
                st.session_state.ranked_candidates = None

            # --- Recruiter UI ---
            st.header("🔎 Find Top Talent")
            jd_recruiter = st.text_area("Paste a Job Description here to find the best candidates:", height=300)

            if st.button("Rank Candidates"):
                if not jd_recruiter:
                    st.error("Please paste a job description to find candidates.")
                else:
                    with st.spinner('Analyzing all resumes in the database... This may take a few moments.'):
                        resume_dir = "./Uploaded_Resumes/"
                        all_resume_files = glob.glob(os.path.join(resume_dir, "*.txt"))
                        
                        st.session_state.ranked_candidates = [] # Initialize/clear results

                        if not all_resume_files:
                            st.warning("No resumes (.txt files) found in the Uploaded_Resumes folder.")
                        else:
                            for txt_file_path in all_resume_files:
                                try:
                                    with open(txt_file_path, 'r', encoding='utf-8') as f:
                                        resume_text = f.read()

                                    # --- MODIFIED CODE ---
                                    # Call the main analysis function instead of the simple one
                                    analysis_json = get_job_match_analysis(resume_text, jd_recruiter)
                                    # Extract the score from the JSON
                                    score = analysis_json.get('match_score', 0)
                                    # --- END MODIFICATION ---

                                    candidate_name = os.path.basename(txt_file_path)
                                    st.session_state.ranked_candidates.append((score, candidate_name))
                                except Exception as e:
                                    st.error(f"Error analyzing {txt_file_path}: {e}")

                            # Sort results after the loop
                            if st.session_state.ranked_candidates:
                                st.session_state.ranked_candidates.sort(reverse=True)


            # --- Display Ranked Results (uses session state) ---
            if st.session_state.ranked_candidates is not None: # Check if analysis has run
                if st.session_state.ranked_candidates:
                    st.success(f"Ranking complete! Found {len(st.session_state.ranked_candidates)} candidates.")
                    st.subheader(f"Top {len(st.session_state.ranked_candidates)} Matches:")

                    for i, (score, txt_filename) in enumerate(st.session_state.ranked_candidates):
                        expander_title = f"#{i+1}: {txt_filename}  (Match: {score}%)"
                        with st.expander(expander_title):
                            base_filename = os.path.splitext(txt_filename)[0]
                            pdf_filename = base_filename + ".pdf"
                            pdf_path = os.path.join("./Uploaded_Resumes/", pdf_filename)
                            st.write(f"**Candidate File:** {pdf_filename}")

                            if st.button("View Original Resume", key=f"view_{i}_{txt_filename}"): # Unique key per file
                                if os.path.exists(pdf_path):
                                    show_pdf(pdf_path)
                                else:
                                    st.error(f"Could not find the original PDF: {pdf_filename}")

                            if st.button("Show AI Strengths for this Candidate", key=f"strength_{i}_{txt_filename}"): # Unique key per file
                                with st.spinner("Asking AI for this candidate's top strengths..."):
                                    txt_path = os.path.join("./Uploaded_Resumes/", txt_filename)
                                    with open(txt_path, 'r', encoding='utf-8') as f:
                                        resume_text_for_strength = f.read()
                                    analysis_json = get_job_match_analysis(resume_text_for_strength, jd_recruiter)
                                    st.subheader("✅ Top Strengths for this Role:")
                                    strengths = analysis_json.get('strengths', [])
                                    if strengths:
                                        for item in strengths:
                                            st.markdown(f"<li>{item}</li>", unsafe_allow_html=True)
                                    else:
                                        st.write("No specific strengths identified by the AI.")
                else:
                    # If analysis ran but found no files or results
                    st.info("No candidates found or analyzed in the database.")

# Calling the main (run()) function to make the whole process run
# run() # Keep run() at the end, outside the else block

# --- Remove Duplicate/Misplaced Code ---
# Delete the extra CSS and spinner block that was previously at the end.
                        # else:
                        #    st.info("Click 'Rank Candidates' to see results.")

            ## For Wrong Credentials
           

# Calling the main (run()) function to make the whole process run
run()
# === UI Polish & Interactivity Enhancements ===
st.markdown("""
    <style>
        /* App-wide font & color tweaks */
        html, body, [class*="css"]  {
            font-family: 'Inter', sans-serif;
            color: #1e1e1e;
        }

        /* Consistent card design */
        .stCard {
            background-color: #f8f9fa;
            border-radius: 16px;
            padding: 20px;
            margin-top: 10px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        }

        /* Button hover animation */
        div.stButton > button:first-child {
            background-color: #3b82f6;
            color: white;
            border-radius: 10px;
            transition: all 0.3s ease;
        }
        div.stButton > button:first-child:hover {
            background-color: #2563eb;
            transform: scale(1.05);
        }
    </style>
""", unsafe_allow_html=True)

