import os
import time
import streamlit as st
import google.generativeai as genai
from PyPDF2 import PdfReader
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import pdfplumber  # More reliable PDF text extraction

# --- Configuration ---
# Use environment variables or Streamlit secrets for API keys
API_KEY = st.secrets.get("GEMINI_API_KEY", os.getenv("GEMINI_API_KEY"))
YOUTUBE_API_KEY = st.secrets.get("YOUTUBE_API_KEY", os.getenv("YOUTUBE_API_KEY"))

if not API_KEY or not YOUTUBE_API_KEY:
    st.error("API keys not configured. Please set GEMINI_API_KEY and YOUTUBE_API_KEY.")
    st.stop()

genai.configure(api_key=API_KEY)
youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)

# --- Functions ---
def read_pdf(file_path):
    """Extract text from PDF using pdfplumber (more reliable than PyPDF2)"""
    text = ""
    try:
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                text += page.extract_text() or ""  # Handle None returns
    except Exception as e:
        st.error(f"PDF extraction error: {str(e)}")
    return text.strip()

def query_with_cag(context: str, query: str) -> str:
    """Query Gemini with context using Cache-Augmented Generation"""
    try:
        prompt = f"Context:\n{context}\n\nQuery: {query}\nAnswer concisely:"
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return f"Error: {str(e)}"

def search_youtube(query: str, max_results: int = 5):
    """Search YouTube safely with error handling"""
    try:
        request = youtube.search().list(
            q=query,
            part="snippet",
            type="video",
            maxResults=max_results
        )
        response = request.execute()
        return [
            {
                "title": item["snippet"]["title"],
                "link": f"https://youtube.com/watch?v={item['id']['videoId']}"
            }
            for item in response.get("items", [])
        ]
    except HttpError as e:
        st.error(f"YouTube API error: {e.resp.status} {e._get_reason()}")
        return []
    except Exception as e:
        st.error(f"Search error: {str(e)}")
        return []

def generate_quiz(pdf_text: str, num_questions: int = 5):
    """Generate formatted quiz questions with Gemini"""
    try:
        prompt = f"""Generate {num_questions} MCQ questions from this text. Format each as:
        Q1. [Question]
        a) [Option1] 
        b) [Option2]
        c) [Option3]
        d) [Option4]
        Correct Answer: [Letter]
        ---
        Text: {pdf_text[:10000]}"""  # Limit context length
        
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(prompt)
        return parse_quiz(response.text)
    except Exception as e:
        st.error(f"Quiz generation failed: {str(e)}")
        return []

def parse_quiz(raw_text: str):
    """Parse Gemini's response into structured questions"""
    questions = []
    current_q = {}
    
    for line in raw_text.split("\n"):
        line = line.strip()
        if not line:
            continue
            
        # Question detected
        if line.startswith(("Q", "Question")) and "." in line[:5]:
            if current_q:
                questions.append(current_q)
            current_q = {
                "text": line.split(".", 1)[1].strip(),
                "options": [],
                "correct": None
            }
            
        # Option detected
        elif line[:2].lower() in ["a)", "b)", "c)", "d)"]:
            current_q["options"].append(line)
            
        # Correct answer detected
        elif "correct answer:" in line.lower():
            current_q["correct"] = line.split(":")[1].strip().lower()[0]  # Extract 'a', 'b', etc.
    
    if current_q:
        questions.append(current_q)
    return questions

# --- UI Setup ---
# Custom CSS with #5293BB (blue) and #E05A7F (pink) theme
st.markdown("""
<style>
.stApp {
    background: linear-gradient(135deg, #5293BB, #6EB1D6);
    color: white;
}
.stButton>button {
    background-color: #E05A7F !important;
    color: white !important;
    border: none;
    transition: all 0.3s;
}
.stButton>button:hover {
    transform: scale(1.05);
    box-shadow: 0 4px 12px rgba(224, 90, 127, 0.3);
}
.pink-card {
    background-color: #E05A7F;
    padding: 1.5rem;
    border-radius: 10px;
    margin: 1rem 0;
    color: white;
}
.timer {
    font-size: 1.5rem;
    color: #E05A7F;
    font-weight: bold;
}
</style>
""", unsafe_allow_html=True)

# --- Session State ---
if "chat" not in st.session_state:
    st.session_state.chat = genai.GenerativeModel('gemini-1.5-flash').start_chat(history=[])

if "messages" not in st.session_state:
    st.session_state.messages = []

if "quiz" not in st.session_state:
    st.session_state.quiz = {
        "start_time": None,
        "time_left": 300,
        "answers": {},
        "submitted": False,
        "questions": []
    }

# --- App Interface ---
st.title("🤖 Smart Study Assistant")
st.caption("Chat with AI • Query PDFs • YouTube Search • Quiz Generator")

# Sidebar Navigation
with st.sidebar:
    st.title("Navigation")
    mode = st.radio("Choose Mode", [
        "💬 Chat with AI", 
        "📄 Query PDF", 
        "🎥 YouTube Search", 
        "✏️ Quiz Generator"
    ])

# --- Mode Handlers ---
# Chat Mode
if "Chat" in mode:
    st.header("💬 AI Chat Assistant")
    
    # Display chat history
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
    
    # Chat input
    if prompt := st.chat_input("Ask me anything..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        with st.chat_message("user"):
            st.markdown(prompt)
        
        with st.spinner("Thinking..."):
            try:
                response = st.session_state.chat.send_message(prompt)
                st.session_state.messages.append({"role": "assistant", "content": response.text})
                with st.chat_message("assistant"):
                    st.markdown(response.text)
            except Exception as e:
                st.error(f"Chat error: {str(e)}")

# PDF Query Mode
elif "PDF" in mode:
    st.header("📄 PDF Query Tool")
    
    uploaded_file = st.file_uploader("Upload PDF", type="pdf")
    if uploaded_file:
        with st.spinner("Extracting text..."):
            temp_file = f"temp_{uploaded_file.name}"
            with open(temp_file, "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            pdf_text = read_pdf(temp_file)
            if not pdf_text:
                st.error("Failed to extract text. Try another PDF.")
                st.stop()
            
            st.session_state.pdf_text = pdf_text
            st.success(f"Extracted {len(pdf_text.split())} words")
            st.expander("View PDF Text").code(pdf_text[:2000] + "...")
    
    if "pdf_text" in st.session_state:
        query = st.text_input("Ask about the PDF:")
        if query:
            with st.spinner("Searching PDF..."):
                answer = query_with_cag(st.session_state.pdf_text[:10000], query)  # Limit context
                st.markdown(f"**Answer:**\n{answer}")

# YouTube Search Mode
elif "YouTube" in mode:
    st.header("🎥 Educational Video Search")
    
    search_term = st.text_input("Search YouTube for educational content:")
    if search_term:
        with st.spinner(f"Searching for '{search_term}'..."):
            videos = search_youtube(search_term + " tutorial")
            
            if videos:
                st.write(f"Found {len(videos)} videos:")
                for vid in videos:
                    st.markdown(f"📺 [{vid['title']}]({vid['link']})")
            else:
                st.warning("No videos found. Try another search term.")

# Quiz Mode
elif "Quiz" in mode:
    st.header("✏️ PDF Quiz Generator")
    
    # PDF Upload
    quiz_file = st.file_uploader("Upload PDF for Quiz", type="pdf", key="quiz_uploader")
    if quiz_file and not st.session_state.quiz["questions"]:
        with st.spinner("Generating quiz..."):
            temp_file = f"quiz_{quiz_file.name}"
            with open(temp_file, "wb") as f:
                f.write(quiz_file.getbuffer())
            
            pdf_text = read_pdf(temp_file)
            if pdf_text:
                st.session_state.quiz["questions"] = generate_quiz(pdf_text)
                st.session_state.quiz["start_time"] = time.time()
                st.success(f"Generated {len(st.session_state.quiz['questions'])} questions!")
    
    # Quiz Timer
    if st.session_state.quiz["start_time"]:
        elapsed = time.time() - st.session_state.quiz["start_time"]
        st.session_state.quiz["time_left"] = max(0, 300 - int(elapsed))
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f'<div class="timer">⏱️ {st.session_state.quiz["time_left"]//60}:{st.session_state.quiz["time_left"]%60:02d}</div>', 
                        unsafe_allow_html=True)
        
        # Auto-submit when time expires
        if st.session_state.quiz["time_left"] <= 0:
            st.session_state.quiz["submitted"] = True
            st.error("Time's up! Submitting your answers...")
    
    # Display Questions
    if st.session_state.quiz["questions"] and not st.session_state.quiz["submitted"]:
        with st.form("quiz_form"):
            for i, q in enumerate(st.session_state.quiz["questions"], 1):
                st.markdown(f"**Q{i}. {q['text']}**")
                st.session_state.quiz["answers"][i] = st.radio(
                    f"Options for Q{i}",
                    q["options"],
                    key=f"q_{i}",
                    label_visibility="collapsed"
                )
            
            if st.form_submit_button("Submit Quiz"):
                st.session_state.quiz["submitted"] = True
    
    # Results Display
    if st.session_state.quiz["submitted"]:
        score = 0
        feedback = []
        
        for i, q in enumerate(st.session_state.quiz["questions"], 1):
            user_ans = st.session_state.quiz["answers"].get(i, "Not answered")
            correct = user_ans[0].lower() == q["correct"]
            if correct:
                score += 1
            
            feedback.append({
                "question": q["text"],
                "user": user_ans,
                "correct": q["options"][ord(q["correct"]) - ord('a')],
                "is_correct": correct
            })
        
        # Score Card
        with st.container():
            st.markdown(f"""
            <div class="pink-card">
                <h2>Quiz Results</h2>
                <h3>Score: {score}/{len(feedback)} ({score/len(feedback)*100:.1f}%)</h3>
            </div>
            """, unsafe_allow_html=True)
        
        # Feedback
        for i, fb in enumerate(feedback, 1):
            st.markdown(f"""
            **Q{i}:** {fb['question']}  
            ✅ **Correct:** {fb['correct']}  
            {"🟢" if fb['is_correct'] else "🔴"} **Your Answer:** {fb['user']}
            """)
        
        if st.button("Retake Quiz"):
            st.session_state.quiz = {
                "start_time": None,
                "time_left": 300,
                "answers": {},
                "submitted": False,
                "questions": []
            }
            st.rerun()
