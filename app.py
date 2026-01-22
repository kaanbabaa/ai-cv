import streamlit as st
import google.generativeai as genai
import json
import pandas as pd
import plotly.express as px
from google.api_core import exceptions
import os
import random
import time

MODEL_POOL = [
    'gemini-flash-latest',
    'gemini-2.5-flash-lite'
]

# --- 1. CONFIG & SETUP ---
st.set_page_config(page_title="Digital Intern Kaan", layout="wide")

if "messages" not in st.session_state:
    st.session_state.messages = []
if "history_council" not in st.session_state:
    st.session_state.history_council = []
if "council_logs" not in st.session_state:
    st.session_state.council_logs = []

# --- 2. DATA (CV) - Shared ---
cv_data = {
    "personal_info": {
        "name": "Kaan Degirmenci",
        "role": "Computer Science Student & Future System Architect",
        "contact": "kaandeg@gmail.com | https://www.linkedin.com/in/kaan-degirmenci-23a5a03a4/",
        "summary": "Forward-thinking Computer Science student transitioning from a 'Coder' to a 'Solutions Architect'. . Skilled in bridging the gap between low-level hardware (Assembly/C) and high-level data architecture (SQL/AI)."
    },
    "education": {
        "university": "Frankfurt University of Applied Sciences",
        "degree": "B.Sc. Computer Science (Informatik)",
        "current_status": "3rd Year Student",
        "gpa": "2.4 (German Grading Scale)",
        "key_coursework_grades": {
            "Introduction to Programming with C": "1.0",
            "Computer Architecture (Assembly & Hardware-Software Interface)": "3.3",
            "Databases (SQL)": "2.3",
            "Probability and Statistics (Data Analysis with R)": "2.7",
            "Object Oriented Programming with C++": "1.7",
            "Real-time Systems": "1.7",
            "Artificial Intelligence": "2.3",
            "Software Engineering Analysis": "Current Focus: System Architecture",
            "IoT Sensor Lab": "Project-Based"
        }
    },
    "technical_skills": {
        "core_philosophy": ["System Architecture", "First-Principles AI", "Object-Oriented Design"],
        "programming_languages": ["Java (Advanced)", "Python (AI/ML Focus)", "C++ (Embedded)", "SQL", "R (Statistical Data Analysis)", "JavaScript"],
        "ai_ml_knowledge": [
            "Deep Learning Architecture: CNNs (Conv2D, Pooling), Backpropagation, Optimizers (Adam/SGD)",
            "Reinforcement Learning Logic: Understanding Agent-Environment interaction, Markov Decision Processes (MDP), and Delayed Rewards (Long-term Strategy vs. Short-term Penalty)",
            "Unsupervised Strategy: K-Means Clustering (Optimizing 'k' via Elbow Method, Inertia & Silhouette Score)",
            "Supervised Logic: Multi-class Classification (Softmax) vs. Binary (Sigmoid), Decision Tree, Random Forest",
            "Math Foundation: Linear Algebra (Matrix Operations), Calculus (Gradients)"
        ]
    },
    "projects": [
        {
            "name": "Advanced Traffic Simulation Wrapper (SUMO)",
            "tech_stack": "Java (OOP), GUI Framework (Swing/JavaFX), SUMO Engine",
            "link": "https://github.com/kaanbabaa/SUMO",
            "details": "Engineered a robust Java wrapper for the SUMO (Simulation of Urban MObility) engine using strict Object-Oriented principles. Developed a dynamic GUI to visualize real-time traffic data, implementing multi-threading to ensure the simulation loop ran asynchronously without freezing the user interface. Focused on parsing complex XML configuration files to control vehicle behaviors programmatically."
        },
        {
            "name": "Machine Learning & Computer Vision Fundamentals",
            "tech_stack": "Python, NumPy, Custom Neural Networks",
            "details": "Developed scalable CNN architectures for Multi-class Classification (CIFAR-10 Vehicles, MNIST Digits). Distinguished by a 'Glass Box' approach: Applied deep theoretical knowledge of the underlying mathematics (Chain Rule for Backpropagation, Matrix Operations) to fine-tune 'Black Box' model parameters. utilized Kaggle datasets with rigorous Train/Test splitting to validate model generalization and mitigate overfitting."},
        {
            "name": "Smart Trash Bin (IoT System)",
            "tech_stack": "C++, ESP8266, Firebase, Google Apps Script",
            "details": "Designed an end-to-end IoT architecture connecting physical hardware to the cloud. Programmed an ESP8266 microcontroller to read distance data from an HC-SR04 sensor. Solved hardware limitations by implementing a software-side 'Signal Smoothing Algorithm' to filter out sensor noise/fluctuations. Established a WebSocket connection to Firebase for real-time status updates on a web dashboard."        },
        {
            "name": "AI Powered CV Assistant (RAG App)",
            "tech_stack": "Python, Gemini API, Streamlit",
            "details": "Developed a 'Chat with Data' application acting as a proof-of-concept for RAG (Retrieval Augmented Generation) systems. Implemented a Multi-Agent architecture ('Visionary' vs 'Auditor') to reduce AI hallucinations. Used Streamlit Session State for memory management and designed a modular prompt engineering structure to switch between 'Professional' and 'Creative' modes dynamically."
        }
    ],
    "internship_expectations": "Seeking a challenging Summer 2026 Internship that bridges the gap between Low-Level Engineering (Embedded/IoT) and High-Level Software Architecture (AI/Cloud). I am eager to move beyond simple task execution and contribute to scalable system designs, applying my 'T-Shaped' skills in Object-Oriented Design and Data Logic to solve real-world engineering problems."
}

cv_text = json.dumps(cv_data, indent=2)

def plot_skills():
    # Data derived from 'technical_skills'
    data = pd.DataFrame({
        'Skill': ['System Architecture', 'Java (OOP/GUI)', 'C++(OOP)', 'Python (AI Math/Logic)', 'IoT/Embedded', 'Cloud/Backend'],
        'Proficiency': [7, 9, 8, 8, 7, 7]  # Self-assessed scores (1-10)
    })
    
    fig = px.line_polar(data, r='Proficiency', theta='Skill', line_close=True)
    fig.update_traces(fill='toself', line_color='#4CAF50') 
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 10])),
        showlegend=False,
        title="Technical Balance: Architect vs. Coder"
    )
    return fig

with st.sidebar:
    st.header("Configuration")
    
    # Download CV PDF
    try:
        with open("kaan_cv.pdf", "rb") as pdf_file:
            PDFbyte = pdf_file.read()
            st.download_button(
                label="Download Original CV (PDF)",
                data=PDFbyte,
                file_name="Kaan_Degirmenci_CV.pdf",
                mime='application/pdf'
            )
    except FileNotFoundError:
        st.warning("Kaan_Degirmenci_CV.pdf does not exist.")

    # AI Tone Selection
    tone = st.selectbox(
        "Select AI Tone:",
        ("Professional & Formal", "Enthusiastic & Eager", "Assertive & Confident", "Technical & Precise")
    )
    st.session_state['tone'] = tone

    # Debug View
    with st.expander("Architect View (Debug)"):
        st.json(cv_data)

    with st.sidebar.expander("System Architecture"):
        st.markdown("""
        This app demonstrates **System Design** principles applied to AI:
        
        * **Orchestration:** Multi-Agent "Refiner" Pattern (Visionary -> Auditor).
        * **Logic:** Ensemble Learning inspired (Random Forest) for variance reduction.
        * **Infrastructure:** Round-Robin API Key Load Balancing for rate-limit bypass.
        * **Data Layer:** JSON-based RAG (Retrieval Augmented Generation).
        * **Frontend:** Python (Streamlit) with Session State management.
        """)

    trace_placeholder = st.sidebar.empty()
    
    st.markdown("### Skill Distribution")
   
    st.plotly_chart(plot_skills(), use_container_width=True) 

    st.markdown("---")
    st.markdown("### Ready to talk?\nkaandeg@gmail.com\n\n" \
    "https://www.linkedin.com/in/kaan-degirmenci-23a5a03a4/")
    st.info("I am currently open for Summer 2026 Internships.")


# --- 3. UI LAYOUT ---

st.title("Hello! I'm Kaan's AI Assistant")
st.markdown("""
You can interact with my professional background in two modes:
1. **Council Mode (Advanced):** A 2-step process where a 'Creative Agent' drafts a bold answer, and a 'Critic Agent' fact-checks it against my actual CV.**Standard Mode:** Fast, direct answers from a single AI.
2. **Standard Mode:** Fast, direct answers from a single AI.
""")

def get_random_key():
    if "api_keys" in st.secrets:
        return random.choice(st.secrets["api_keys"])
    else:
        st.error("API Key not founded. Please check the secrets settings..")
        return None

def load_source_code(file_path):
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return "Error: Source code file not found."
    
def update_trace_display():
    """Updates the box in sidebar with session_state data."""

    with trace_placeholder.container():

        if "council_logs" in st.session_state and st.session_state.council_logs:
            
            st.markdown("### Decision Trace History")

            for log in reversed(st.session_state.council_logs):
            
                is_latest = (log == st.session_state.council_logs[-1])
                    
                with st.expander(f"Trace #{log['id']}: {log['query'][:20]}...", expanded=is_latest):
                    st.caption(f"Time: {log.get('timestamp', '')}")
                    st.caption(f"Full Query: {log['query']}")
                        
                    st.markdown("---")
                    st.markdown("**Visionary Draft:**")
                    st.warning(log['draft'])
                        
                    st.markdown("---")
                    st.markdown("**Auditor Output:**")
                    st.success(log['final'])
        else:
            st.info("Ask the Council in Tab 1 to see the logic trace.")

def handle_click(question_text):
    st.session_state.messages.append({"role": "user", "content": question_text})
    history_text = "\n".join([f"{msg['role']}: {msg['content']}" for msg in st.session_state.messages])
        
    selected_tone = st.session_state.get('tone', "Professional & Formal")
    
    full_prompt = f"""
        You are an AI assistant representing {cv_data['personal_info']['name']}.
        KNOWLEDGE BASE: {cv_text}
        TONE: {selected_tone}
        HISTORY: {history_text}
        QUESTION: {question_text}
    
        INSTRUCTIONS:
        Answer based ONLY on the CV data. Be impressive but grounded in facts. 
        Focus on Engineering Architecture and AI Logic.
    """
    
    try:
        
        response = smart_generate(full_prompt, temperature= 0.7)

        st.session_state.messages.append({"role": "assistant", "content": response})
        st.rerun() 
            
    except Exception as e:
        st.error(f"Error: {e}")

def smart_generate(prompt, temperature=0.7):

    for model_name in MODEL_POOL:
        try:
            current_key = get_random_key()
            genai.configure(api_key=current_key)
                
            model = genai.GenerativeModel( 
                model_name, 
                generation_config=genai.GenerationConfig(temperature=temperature)
            )
                
            response = model.generate_content(prompt)
            return response.text
                
        except exceptions.ResourceExhausted:
            # 429 Error (Cota Limit)
            print(f"Cota Full! Model: {model_name}, Key...{current_key[-4:]}. Back-up System starts...")
            continue 
                
        except Exception as e:
            print(f"Error: {e}. Trying Alternatives.")
            continue

    return "Error: System is out of Limit. Resources are empty"

def process_council_interaction(user_question):
     # 1. Append User Message to History
    st.session_state.history_council.append({"role": "user", "content": user_question})
        
    # 2. Start the Agent Process
    with st.chat_message("assistant"):
        status_box = st.status("The Council is convened...", expanded=True)
            
        try:
            # --- SAFE TONE RETRIEVAL ---
            # Prevents crashes if 'tone' hasn't been set in sidebar yet
            current_tone = st.session_state.get('tone', "Professional & Technical")

            # --- STEP 1: VISIONARY AGENT (High Creativity) ---
            status_box.write("**Agent 1 (Visionary):** Drafting creative response...")
                
            draft_prompt = f"""
            Role: Enthusiastic Job Candidate.
            CV KNOWLEDGE: {cv_text}
            USER QUESTION: {user_question}
            INSTRUCTION: Be bold, highlight potential. It is okay to be slightly creative connecting dots.
            """
            draft_response = smart_generate(draft_prompt, temperature=0.9)
                
            # --- STEP 2: AUDITOR AGENT (Strict Logic / Random Forest Filter) ---
            time.sleep(1) # Be gentle on the API
            status_box.write("**Agent 2 (Auditor):** Applying 'Random Forest' logic (Variance Reduction)...")
                
            audit_prompt = f"""
            Role: Strict Fact-Checker & CV Auditor.
            GROUND TRUTH (CV): {cv_text}
            DRAFT ANSWER: {draft_response}
                
            YOUR TASK:
            1. You are the 'Ensemble' filter. Correct any hallucinations in the draft.
            2. Ensure the answer strictly matches the CV skills (especially the ML/AI section).
            3. Convert the tone to: {current_tone}.
            4. Output ONLY the final polished answer.
            """
            final_answer = smart_generate(audit_prompt, temperature = 0.2)
                
            # --- FINALIZE ---
            status_box.update(label="Decision Reached!", state="complete", expanded=False)
            st.markdown(final_answer)
                
           # Save to History
            st.session_state.history_council.append({"role": "assistant", "content": final_answer})

            new_log = {
                "id": len(st.session_state.council_logs) + 1, # Unique ID
                "query": user_question,
                "draft": draft_response, 
                "final": final_answer,
                "timestamp": time.strftime("%H:%M:%S") 
            }
            
            st.session_state.council_logs.append(new_log)
            update_trace_display()
                
        except Exception as e:
            status_box.update(label="System Error", state="error")
            st.error(f"Council Process Error: {e}")

def get_or_create_chat_window():
        with history_placeholder.container():
            window = st.container(height=500, border=True)

            with window:
                if "history_council" not in st.session_state:
                    st.session_state.history_council = []
            
                for msg in st.session_state.history_council:
                    with st.chat_message(msg["role"]):
                        st.markdown(msg["content"])
            return window

tab1, tab2, tab3, tab4 = st.tabs(["Chat with Kaan's AI Council(Council Mode)", "Chat with Kaan's AI(Standard Mode)", "Generate Cover Letter", "Code Vault"])

# TAB 1: COUNCIL MODE 

with tab1:
    st.subheader("The Council: Architecture over Hallucination")
    st.info("""
    **How this works:** This uses a Multi-Agent 'Refiner' pattern inspired by **Random Forest / Ensemble Learning**. 
    1. **Agent A (Visionary):** Drafts a bold, creative answer (High Temperature).
    2. **Agent B (Auditor):** Checks the draft against the JSON CV data to ensure 100% factual accuracy (Low Temperature).
    
    *Result: Zero hallucination, maximum impact (Variance Reduction).*
    """)
    
    history_placeholder = st.empty()

   # --- 3. BUTTONS ---
    st.markdown("### Test the Council Logic:")
    col_c1, col_c2, col_c3 = st.columns(3)
    
    chat_window = None

    if "history_council" in st.session_state and st.session_state.history_council:
        chat_window = get_or_create_chat_window()

    # Button 1: T-Shaped Student
    if col_c1.button("T-Shaped Student", use_container_width=True):
        if chat_window is None:
            chat_window = get_or_create_chat_window()
        with chat_window:  
            process_council_interaction(
                "Analyze Kaan's technical spectrum based on the entire CV data. "
                "How does combining 'Low-Level Control' (Assembly, C, Real-time) with 'High-Level Data Science' (R, SQL, AI) "
                "make him a uniquely qualified System Architect? Prove that he is not just a coder, but a 'T-Shaped' student."
            )
    
    # Button 2: AI Knowledge
    if col_c2.button("First-Principles AI Logic", use_container_width=True):
        if chat_window is None:
            chat_window = get_or_create_chat_window()
        with chat_window:  
            process_council_interaction(
                "Does Kaan possess a true 'First-Principles' understanding of AI beyond just using libraries? "
                "Synthesize his knowledge of Neural Network math (Backprop), Unsupervised Learning metrics (Elbow Method), "
                "and Strategic Logic (Reinforcement Learning concepts)."
            )

    # Button 3: Internship Value
    if col_c3.button("High-Impact Intern Potential", use_container_width=True):
        if chat_window is None:
            chat_window = get_or_create_chat_window()
        with chat_window:  
            process_council_interaction(
                "Synthesize Kaan's academic rigor (Grades) and his 'End-to-End Ownership' in projects (IoT, SUMO). "
                "Why is he a 'High-ROI' candidate for a Summer 2026 internship? "
                "Who is eager to improve himself especially in complex architectural tasks?"
            )

    if prompt_council := st.chat_input("Ask a complex question to the Council...", key="council_input"):
        with chat_window: 
            with st.chat_message("user"):
                st.markdown(prompt_council)
            process_council_interaction(prompt_council)

# TAB 2: CHATBOT
with tab2:
    genai.configure(api_key = get_random_key())
    st.markdown("""
    You can ask me anything about Kaan's professional background, skills, and projects.
    """)

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])

    st.markdown("### Quick Insights:")
    col1, col2, col3= st.columns(3)

    if col1.button("Academic Highlights"):
        q_text = "Extract Kaan's current GPA and list his key course grades in descending order from the CV data. "
        handle_click(q_text)

    if col2.button("Java OOP Architectur"):
        q_text = "Don't just list the features. Analyze the architectural complexity of the SUMO Traffic Wrapper.How did Kaan apply strict Object-Oriented Design (OOP) and concurrency to manage the simulation?"
        handle_click(q_text)

    if col3.button("Tech Stack List"):
        q_text = "List all programming languages and tools Kaan is proficient in, categorized by domain (Backend, Embedded, AI)."
        handle_click(q_text)

    # Chat Input
    prompt = st.chat_input("Ask a question about Kaan...")

    if prompt:
        with st.chat_message("user"):
            st.write(prompt)
        handle_click(prompt) 

# TAB 3: COVER LETTER GENERATOR
with tab3:
    st.header("Job Application Generator")
    col1, col2 = st.columns(2)
    with col1:
        company_name = st.text_input("Company Name")
    with col2:
        language_opt = st.selectbox("Output Language", ["Detect Automatically", "English", "Deutsch"])
        
    job_desc = st.text_area("Paste Job Description Here", height=200)
    
    generate_btn = st.button("Generate Cover Letter", type="primary")

    if generate_btn and job_desc and company_name:
        with st.spinner("Analyzing job requirements..."):
            try:
                cl_prompt = f"""
                Act as Kaan Değirmenci. 
                MY CV DATA: {cv_text}
                TARGET JOB DESCRIPTION: '{job_desc}'
                TASK: Write a cover letter for {company_name}.
                """
                response_text = smart_generate(cl_prompt, temperature= 0.7)
                st.markdown("### Your Draft Application:")
                st.markdown(response_text)
                
            except Exception as e:
                st.error(f"Error: {e}")


# TAB 4: CODE VAULT 

with tab4:
    st.header("Under the Hood")
    project_choice = st.selectbox("Select a Project:", ["SUMO Traffic Wrapper (Java)", "IoT Handler (C++)", "ChatBot(Python)"])
    
    if project_choice == "SUMO Traffic Wrapper (Java)":
        code_content = load_source_code("SimulationManager.java")
        st.code(code_content, language= 'java')
        
    elif project_choice == "IoT Handler (C++)":
       code_content = load_source_code("IoTcode/IoTcode.ino")
       st.code(code_content, language = 'c++')
    
    elif project_choice == "ChatBot(Python)":
        code_content = load_source_code("app_display.py")
        st.code(code_content, language = 'python')