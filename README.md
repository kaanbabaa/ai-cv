#  Digital Intern: Multi-Agent RAG CV Assistant

An advanced, production-ready AI Assistant built with Python and Streamlit. This project serves as an interactive, AI-powered portfolio, utilizing a custom **Multi-Agent Architecture** to answer questions based on my CV data with zero hallucinations.

##  Engineering Highlights & Architecture

Standard LLM wrappers suffer from hallucinations and API rate limits. To solve these enterprise-level problems, I implemented several advanced software engineering patterns:

* **Multi-Agent "Council" Mode (Ensemble Logic):** I designed a two-step LLM pipeline to ensure 100% factual accuracy. 
  1. **The Visionary Agent (High Temp):** Generates a creative, enthusiastic draft based on the user's query.
  2. **The Auditor Agent (Low Temp):** Acts as a strict fact-checker. It cross-references the draft strictly against the underlying JSON Knowledge Base (my CV) to strip out hallucinations before outputting the final response.
* **API Load Balancing & Fault Tolerance:** The backend features a custom `smart_generate()` function with a Round-Robin API key rotator. This dynamically switches between multiple API keys to bypass Rate Limits (429 Errors) and implements fallback logic if a model's resources are exhausted.
* **State Management & Traceability:** Utilized Streamlit's `session_state` to maintain seamless conversation history and built a "Decision Trace" UI that logs the exact inputs and outputs of both the Visionary and Auditor agents for full transparency.
* **Data Layer (JSON Document Store):** Centralized all CV data into a structured JSON format, simulating a vector/document database for Retrieval-Augmented Generation (RAG) operations.
* **Dynamic UI & Analytics:** Includes an "Architect View" for debugging, real-time Plotly charts for skill distribution, and a built-in Cover Letter Generator tailored to specific job descriptions.

##  Tech Stack
* **Language:** Python
* **AI/LLM:** Google Generative AI API (Gemini Flash & Flash-Lite)
* **Frontend/Framework:** Streamlit
* **Data Handling & Visualization:** JSON, Pandas, Plotly Express

##  About the Developer
I am Kaan Degirmenci, a Computer Science student transitioning from standard coding to System Architecture and AI Engineering. This project demonstrates my ability to build resilient, logical, and user-centric Artificial Intelligence applications that solve real-world reliability issues.
