import streamlit as st
import google.generativeai as genai
import json
import pandas as pd
import plotly.express as px
import os
import random
import time

API_KEYS_POOL = []

MODEL_NAME = 'gemini-flash-latest'

# --- 1. CONFIG & SETUP ---
st.set_page_config(page_title="Digital Intern Kaan", layout="wide")

# --- 2. DATA (CV) - Shared ---
cv_data = {
    "personal_info": {
        "name": "Kaan Degirmenci",
        "role": "Computer Science Student & Future System Architect",
        "contact": "kaandeg@gmail.com | linkedin.com/in/yourprofile",
        "summary": "Forward-thinking Computer Science student transitioning from a 'Coder' to a 'Solutions Architect'..."
    },
    "education": {
        "university": "Frankfurt University of Applied Sciences",
        "degree": "B.Sc. Computer Science (Informatik)",
        "current_status": "3rd Year Student",
        "gpa": "2.4 (German Grading Scale)",
        "key_coursework_grades": {
            "Introduction to Programming with C": "1.0",
            "Object Oriented Programming": "1.7",
            "Real-time Systems": "1.7",
            "Artificial Intelligence": "2.3",
            "Software Engineering Analysis": "Current Focus: System Architecture",
            "IoT Sensor Lab": "Project-Based"
        }
    },
    "technical_skills": {
        "core_philosophy": ["System Architecture", "First-Principles AI", "Object-Oriented Design"],
        "programming_languages": ["Java (Advanced)", "Python (AI/ML Focus)", "C++ (Embedded)", "JavaScript"],
        "ai_ml_knowledge": [
            "Deep Learning: Neural Networks (From Scratch), Backpropagation",
            "Classical ML: Random Forest, Decision Trees, SVM, K-Means",
            "Math Backend: Linear/Logistic Regression, Gradient Descent",
            "Computer Vision: Pixel Manipulation, Gauss/Gray Filters"
        ]
    },
    "projects": [
        {
            "name": "Advanced Traffic Simulation Wrapper (SUMO)",
            "tech_stack": "Java (OOP), GUI Framework (Swing/JavaFX), SUMO Engine",
            "link": "https://github.com/kaanbabaa/SUMO",
            "details": "Engineered a complex Java wrapper for the SUMO traffic engine..."
        },
        {
            "name": "Machine Learning & Computer Vision Fundamentals",
            "tech_stack": "Python, NumPy, Custom Neural Networks",
            "details": "Built and trained Neural Networks from scratch..."
        },
        {
            "name": "Smart Trash Bin (IoT System)",
            "tech_stack": "C++, ESP8266, Firebase, Google Apps Script",
            "details": "Designed an end-to-end IoT architecture..."
        },
        {
            "name": "AI Powered CV Assistant (RAG App)",
            "tech_stack": "Python, Gemini API, Streamlit",
            "details": "A 'Chat with Data' tool acting as a proof-of-concept..."
        }
    ],
    "internship_expectations": "I am looking for a role that values architectural thinking over repetitive coding..."
}

cv_text = json.dumps(cv_data, indent=2)

def plot_skills():
    # Data derived from 'technical_skills'
    data = pd.DataFrame({
        'Skill': ['System Architecture', 'Java (OOP/GUI)', 'C++(OOP)', 'AI Math/Logic', 'IoT/Embedded', 'Cloud/Backend'],
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
        st.warning("kaan_cv.pdf bulunamadı, bu özellik devre dışı.")

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
    
    st.markdown("###Skill Distribution")
   
    st.plotly_chart(plot_skills(), use_container_width=True)

    st.markdown("---")
    st.markdown("### Ready to talk?\nkaandeg@gmail.com")
    st.info("I am currently open for Summer 2026 Internships.")

    # --- 3. UI LAYOUT ---
st.title("Hello! I'm Kaan's AI Assistant")
st.markdown("""
You can interact with my professional background in two modes:
1. **Standard Mode:** Fast, direct answers from a single AI.
2. **Council Mode (Advanced):** A 2-step process where a 'Creative Agent' drafts a bold answer, and a 'Critic Agent' fact-checks it against my actual CV.
""")

# --- 3. Helper Function ---
def get_random_key():
    return random.choice(API_KEYS_POOL)

def load_source_code(file_path):
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return "Error: Source code file not found."
    
def update_trace_display():
    """Updates the box in sidebox with session_state data."""
    if "council_logs" in st.session_state and st.session_state.council_logs:
        logs = st.session_state.council_logs
        
        with trace_placeholder.container():
            with st.expander("Council Decision Trace (Debug)", expanded=True):
                st.caption(f"Query: {logs['query']}")
                st.markdown("**Visionary Draft:**")
                st.warning(logs['draft'])
                st.markdown("*Refining...*")
                st.markdown("**Auditor Output:**")
                st.success(logs['final'])
    else:
        with trace_placeholder.container():
             with st.expander("Council Decision Trace (Debug)"):
                st.info("Ask the Council in Tab 2(Council Mode) to see the logic trace.")

def handle_click(question_text):
    st.session_state.messages.append({"role": "user", "content": question_text})
    history_text = "\n".join([f"{msg['role']}: {msg['content']}" for msg in st.session_state.messages])
        
    selected_tone = tone
    
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
        model = genai.GenerativeModel(MODEL_NAME)
        response = model.generate_content(full_prompt)
        st.session_state.messages.append({"role": "assistant", "content": response.text})
        st.rerun()
            
    except Exception as e:
        st.error(f"Error: {e}")

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
            genai.configure(api_key=get_random_key())
            model_creative = genai.GenerativeModel(MODEL_NAME, generation_config=genai.GenerationConfig(temperature=0.9))
                
            draft_prompt = f"""
            Role: Enthusiastic Job Candidate.
            CV KNOWLEDGE: {cv_text}
            USER QUESTION: {user_question}
            INSTRUCTION: Be bold, highlight potential. It is okay to be slightly creative connecting dots.
            """
            draft_response = model_creative.generate_content(draft_prompt).text
                
            # --- STEP 2: AUDITOR AGENT (Strict Logic / Random Forest Filter) ---
            time.sleep(1) # Be gentle on the API
            status_box.write("**Agent 2 (Auditor):** Applying 'Random Forest' logic (Variance Reduction)...")
            genai.configure(api_key=get_random_key())
            model_strict = genai.GenerativeModel(MODEL_NAME, generation_config=genai.GenerationConfig(temperature=0.2))
                
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
            final_answer = model_strict.generate_content(audit_prompt).text
                
            # --- FINALIZE ---
            status_box.update(label="Decision Reached!", state="complete", expanded=False)
            st.markdown(final_answer)
                
            # Save to History
            st.session_state.history_council.append({"role": "assistant", "content": final_answer})

            # Update Log
            st.session_state.council_logs = {
                "query": user_question,
                "draft": draft_response,
                "final": final_answer
            }
            update_trace_display()
                
        except Exception as e:
            status_box.update(label="System Error", state="error")
            st.error(f"Council Process Error: {e}")

update_trace_display()
tab1, tab2, tab3, tab4 = st.tabs(["Chat with Kaan's AI(Standard Mode)", "Chat with Kaan's AI Council(Council Mode)", "Generate Cover Letter", "Code Vault"])

# TAB 1: CHATBOT

with tab1:
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
    col1, col2, col3 = st.columns(3)

    if col1.button("Academic Highlights"):
        q_text = "Analyze Kaan's academic performance..."
        handle_click(q_text)

    if col2.button("SUMO Architecture"):
        q_text = "Explain the architectural complexity of the SUMO..."
        handle_click(q_text)

    if col3.button("Why Hire as Architect?"):
        q_text = "Why is Kaan a strong candidate for a role..."
        handle_click(q_text)

    # Chat Input
    prompt = st.chat_input("Ask a question about Kaan...")

    if prompt:
        with st.chat_message("user"):
            st.write(prompt)
        handle_click(prompt)


# TAB 2: COUNCIL MODE

with tab2:
    st.subheader("The Council: Architecture over Hallucination")
    st.info("""
    **How this works:** This uses a Multi-Agent 'Refiner' pattern inspired by **Random Forest / Ensemble Learning**. 
    1. **Agent A (Visionary):** Drafts a bold, creative answer (High Temperature).
    2. **Agent B (Auditor):** Checks the draft against the JSON CV data to ensure 100% factual accuracy (Low Temperature).
    
    *Result: Zero hallucination, maximum impact (Variance Reduction).*
    """)
    # --- PRE-SET QUESTIONS (QUICK ACTIONS) ---
    st.markdown("####Test the Council Logic:")
    col_c1, col_c2, col_c3 = st.columns(3)
    
    # Button 1: Explains your architecture using ML terms
    if col_c1.button("Random Forest Logic"):
        process_council_interaction("How does Kaan apply 'Random Forest/Ensemble' logic to this chatbot architecture?")

    # Button 2: Proves your deep technical knowledge
    if col_c2.button("Deep ML Knowledge"):
        process_council_interaction("Does Kaan understand the math behind Neural Networks (Backprop, Gradient Descent) or just use libraries?")

    # Button 3: Career analysis
    if col_c3.button("Future Potential"):
        process_council_interaction("Analyze Kaan's transition from Coding to System Architecture. Is he ready for a big role?")

    # --- DISPLAY CHAT HISTORY ---
    if "history_council" not in st.session_state:
        st.session_state.history_council = []

    for msg in st.session_state.history_council:
        # Use Scale Icon for Assistant
        avatar = "⚖️" if msg["role"] == "assistant" else None
        with st.chat_message(msg["role"], avatar=avatar):
            st.markdown(msg["content"])

    # --- CHAT INPUT ---
    if prompt_council := st.chat_input("Ask a complex question to the Council...", key="council_input"):
        # Display user message immediately for better UX
        with st.chat_message("user"):
            st.markdown(prompt_council)
        # Trigger the logic
        process_council_interaction(prompt_council)

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
                model = genai.GenerativeModel(MODEL_NAME)
                response = model.generate_content(cl_prompt)
                
                st.markdown("### Your Draft Application:")
                st.markdown(response.text)
                
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
