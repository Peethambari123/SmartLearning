import os
import time
import streamlit as st
import google.generativeai as genai
from PyPDF2 import PdfReader
from googleapiclient.discovery import build
from google.api_core import retry

# Configure Google Gemini API key
API_KEY = "YOUR_GEMINI_API_KEY"  # Replace with your actual key
genai.configure(api_key=API_KEY)

# Configure YouTube Data API key
YOUTUBE_API_KEY = "YOUR_YOUTUBE_API_KEY"  # Replace with your actual key
youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)

# Safety settings for Gemini API
SAFETY_SETTINGS = [
    {
        "category": "HARM_CATEGORY_HARASSMENT",
        "threshold": "BLOCK_NONE",
    },
    {
        "category": "HARM_CATEGORY_HATE_SPEECH",
        "threshold": "BLOCK_NONE",
    },
    {
        "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
        "threshold": "BLOCK_NONE",
    },
    {
        "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
        "threshold": "BLOCK_NONE",
    },
]

# Function to read the PDF file
def read_pdf(file_path):
    """Reads the text from a PDF file."""
    try:
        with open(file_path, 'rb') as file:
            reader = PdfReader(file)
            text = ""
            for page_num in range(len(reader.pages)):
                page = reader.pages[page_num]
                text += page.extract_text()
            return text
    except Exception as e:
        st.error(f"Error reading PDF: {str(e)}")
        return None

# Function to query the Gemini LLM with preloaded context
@retry.Retry()
def query_with_cag(context: str, query: str) -> str:
    """Query the Gemini LLM with preloaded context."""
    try:
        prompt = f"Context:\n{context[:10000]}\n\nQuery: {query}\nAnswer:"
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(
            prompt,
            safety_settings=SAFETY_SETTINGS
        )
        return response.text.strip()
    except Exception as e:
        st.error(f"Error querying model: {str(e)}")
        return None

# Function to search YouTube and generate links
def search_youtube(query: str, max_results: int = 5):
    """Search YouTube for videos related to the query."""
    try:
        request = youtube.search().list(
            q=query + " tutorial",
            part="snippet",
            type="video",
            maxResults=max_results
        )
        response = request.execute()
        videos = []
        for item in response["items"]:
            video_id = item["id"]["videoId"]
            video_title = item["snippet"]["title"]
            video_link = f"https://www.youtube.com/watch?v={video_id}"
            videos.append({"title": video_title, "link": video_link})
        return videos
    except Exception as e:
        st.error(f"YouTube API error: {str(e)}")
        return []

# Function to generate quiz questions from PDF text
@retry.Retry()
def generate_quiz_from_pdf(pdf_text: str, num_questions: int = 5):
    """Generate quiz questions from the PDF text."""
    try:
        truncated_text = pdf_text[:10000]  # Limit to first 10,000 characters
        
        prompt = f"""
        Generate {num_questions} multiple-choice questions based on the following text.
        Each question should have 4 options (a, b, c, d) and indicate the correct answer.
        Format each question like this:
        
        Q1. [Question text]
        a) [Option 1]
        b) [Option 2]
        c) [Option 3]
        d) [Option 4]
        Correct Answer: [letter]
        
        Text to use:
        {truncated_text}
        """
        
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(
            prompt,
            safety_settings=SAFETY_SETTINGS
        )
        return response.text
    except Exception as e:
        st.error(f"Error generating quiz: {str(e)}")
        return None

def parse_quiz(raw_text: str):
    """Parse generated quiz questions into structured format"""
    questions = []
    current_q = {}
    options = []
    
    if not raw_text:
        return questions
    
    for line in raw_text.split("\n"):
        line = line.strip()
        if not line:
            continue
            
        # Question detected
        if line.startswith(("Q", "Question")) and (". " in line[:5] or ") " in line[:5]):
            if current_q:
                questions.append(current_q)
            current_q = {
                "text": line.split(". ", 1)[1].strip() if ". " in line[:5] else line.split(") ", 1)[1].strip(),
                "options": [],
                "correct": None
            }
            options = []
            
        # Option detected
        elif line[:2].lower() in ["a)", "b)", "c)", "d)"] or line[:1].lower() in ["a", "b", "c", "d"]:
            options.append(line)
            current_q["options"] = options
            
        # Correct answer detected
        elif "correct answer:" in line.lower():
            answer_part = line.split(":")[1].strip().lower()
            if answer_part:
                current_q["correct"] = answer_part[0]
    
    if current_q:
        questions.append(current_q)
    return questions

# Custom CSS for dark elegant theme
st.markdown(
    """
    <style>
    .stApp {
        background: #121212;
        color: #E0E0E0;
        font-family: 'Arial', sans-serif;
    }
    .stButton>button {
        background-color: #BB86FC !important;
        color: #000000 !important;
        border: none;
        border-radius: 8px;
        padding: 10px 20px;
        transition: all 0.3s;
        font-weight: bold;
    }
    .stButton>button:hover {
        background-color: #9C64F6 !important;
        transform: scale(1.02);
        box-shadow: 0 0 12px rgba(187, 134, 252, 0.5);
    }
    .stTextInput>div>div>input {
        background-color: rgba(30, 30, 30, 0.9) !important;
        color: #FFFFFF !important;
        border: 1px solid #BB86FC;
        border-radius: 8px;
        padding: 10px;
    }
    .stRadio>div {
        background-color: rgba(30, 30, 30, 0.9) !important;
        border-radius: 10px;
        padding: 15px;
        border: 1px solid #BB86FC;
    }
    .stHeader {
        color: #BB86FC !important;
        text-shadow: 0 0 8px rgba(187, 134, 252, 0.3);
    }
    .timer {
        color: #BB86FC;
        font-weight: bold;
        font-size: 1.3rem;
        background-color: rgba(30, 30, 30, 0.7);
        padding: 5px 15px;
        border-radius: 20px;
        display: inline-block;
        border: 1px solid #BB86FC;
    }
    .quiz-card {
        background-color: rgba(30, 30, 30, 0.9) !important;
        color: #E0E0E0 !important;
        border-radius: 10px;
        padding: 20px;
        margin-bottom: 20px;
        border: 1px solid #BB86FC;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
    }
    .sidebar .sidebar-content {
        background-color: #1E1E1E !important;
        border-right: 1px solid #BB86FC;
    }
    .stChatMessage {
        background-color: rgba(30, 30, 30, 0.9) !important;
        border-radius: 10px;
        padding: 15px;
        margin: 10px 0;
        border: 1px solid #BB86FC;
    }
    .stMarkdown {
        color: #E0E0E0 !important;
    }
    .stTextArea>div>div>textarea {
        background-color: rgba(30, 30, 30, 0.9) !important;
        color: #FFFFFF !important;
        border: 1px solid #BB86FC !important;
    }
    .error-box {
        background-color: #FF5252;
        color: white;
        padding: 10px;
        border-radius: 5px;
        margin: 10px 0;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Initialize session state
if "chat" not in st.session_state:
    st.session_state.chat = genai.GenerativeModel('gemini-1.5-flash').start_chat(history=[])

if "messages" not in st.session_state:
    st.session_state.messages = []

if "uploaded_file" not in st.session_state:
    st.session_state.uploaded_file = None
    st.session_state.pdf_text = None

# App Interface
st.title("🤖 Smart Learning Assistant")
st.write("Chat with AI, query PDFs, search YouTube, or take quizzes!")

# Sidebar navigation
app_mode = st.sidebar.radio(
    "Choose Mode", 
    ["Chat with AI", "Query a PDF", "Search YouTube", "Quiz Challenge"],
    key="nav"
)

# Chat with AI mode
if app_mode == "Chat with AI":
    st.header("💬 AI Chat")
    st.write("Ask me anything!")

    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Chat input
    if prompt := st.chat_input("Type your message..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        try:
            response = st.session_state.chat.send_message(
                prompt,
                safety_settings=SAFETY_SETTINGS
            )
            st.session_state.messages.append({"role": "assistant", "content": response.text})
            with st.chat_message("assistant"):
                st.markdown(response.text)
        except Exception as e:
            st.error(f"Error in chat: {str(e)}")

# Query a PDF mode
elif app_mode == "Query a PDF":
    st.header("📄 PDF Query")
    st.write("Upload a PDF and ask questions about its content.")

    uploaded_file = st.file_uploader("Choose a PDF file", type="pdf")
    if uploaded_file is not None:
        temp_dir = "temp"
        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir)

        temp_file_path = os.path.join(temp_dir, uploaded_file.name)
        with open(temp_file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        pdf_text = read_pdf(temp_file_path)
        if pdf_text:
            st.session_state.uploaded_file = uploaded_file
            st.session_state.pdf_text = pdf_text
            st.text_area("PDF Preview", value=pdf_text[:500], height=100)

    if st.session_state.pdf_text:
        query = st.text_input("Ask a question about the PDF:")
        if query:
            with st.spinner("Processing..."):
                answer = query_with_cag(st.session_state.pdf_text, query)
                if answer:
                    st.markdown(f"**Answer:** {answer}")

# Search YouTube mode
elif app_mode == "Search YouTube":
    st.header("🎥 YouTube Search")
    st.write("Find educational videos on any topic.")

    youtube_query = st.text_input("Enter search term:")
    if youtube_query:
        with st.spinner("Searching..."):
            videos = search_youtube(youtube_query)
            if videos:
                st.write("### Results:")
                for video in videos:
                    st.markdown(f"📹 [{video['title']}]({video['link']})")
            else:
                st.warning("No videos found. Try a different search term.")

# Quiz Challenge mode
elif app_mode == "Quiz Challenge":
    st.header("✏️ Quiz Generator")
    st.write("Upload a PDF and test your knowledge.")

    # Initialize quiz state
    if "quiz_start_time" not in st.session_state:
        st.session_state.quiz_start_time = None
    if "time_remaining" not in st.session_state:
        st.session_state.time_remaining = 300
    if "user_answers" not in st.session_state:
        st.session_state.user_answers = {}
    if "quiz_submitted" not in st.session_state:
        st.session_state.quiz_submitted = False
    if "questions" not in st.session_state:
        st.session_state.questions = []

    uploaded_file = st.file_uploader("Upload PDF for Quiz", type="pdf", key="quiz_pdf")
    if uploaded_file and not st.session_state.questions:
        with st.spinner("Generating quiz..."):
            temp_file = f"quiz_{uploaded_file.name}"
            with open(temp_file, "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            pdf_text = read_pdf(temp_file)
            if pdf_text:
                quiz_text = generate_quiz_from_pdf(pdf_text)
                if quiz_text:
                    st.session_state.questions = parse_quiz(quiz_text)
                    st.session_state.quiz_start_time = time.time()

    if st.session_state.questions:
        # Timer logic
        elapsed = time.time() - st.session_state.quiz_start_time
        st.session_state.time_remaining = max(0, 300 - int(elapsed))
        
        st.markdown(
            f'<div class="timer">⏱️ Time Remaining: '
            f'{st.session_state.time_remaining//60}:{st.session_state.time_remaining%60:02d}</div>',
            unsafe_allow_html=True
        )

        if st.session_state.time_remaining <= 0:
            st.session_state.quiz_submitted = True
            st.error("Time's up! Submitting your answers...")

        if not st.session_state.quiz_submitted:
            with st.form("quiz_form"):
                for i, q in enumerate(st.session_state.questions, 1):
                    with st.container():
                        st.markdown(f'<div class="quiz-card"><b>Q{i}: {q["text"]}</b>', 
                                   unsafe_allow_html=True)
                        st.session_state.user_answers[i] = st.radio(
                            f"Options for Q{i}",
                            q["options"],
                            key=f"q_{i}",
                            label_visibility="collapsed"
                        )
                        st.markdown("</div>", unsafe_allow_html=True)
                
                if st.form_submit_button("Submit Quiz"):
                    st.session_state.quiz_submitted = True
                    st.rerun()

    if st.session_state.quiz_submitted and st.session_state.questions:
        score = 0
        feedback = []
        
        for i, q in enumerate(st.session_state.questions, 1):
            user_ans = st.session_state.user_answers.get(i, "Not answered")
            correct = False
            if user_ans and q["correct"]:
                correct = user_ans[0].lower() == q["correct"].lower()
            if correct:
                score += 1
            
            feedback.append({
                "question": q["text"],
                "user": user_ans,
                "correct": next((opt for opt in q["options"] if opt[0].lower() == q["correct"].lower()), 
                "is_correct": correct
            })
        
        # Results display
        st.markdown(
            f"""
            <div style="background-color: #BB86FC; padding: 20px; border-radius: 10px; margin-bottom: 20px; color: #000000;">
                <h2>Quiz Results</h2>
                <h3>Score: {score}/{len(feedback)} ({(score/len(feedback))*100:.1f}%)</h3>
            </div>
            """,
            unsafe_allow_html=True
        )
        
        st.write("### Detailed Feedback")
        for fb in feedback:
            st.markdown(
                f"""
                <div class="quiz-card">
                    <b>Question:</b> {fb['question']}<br><br>
                    <span style="color: {'#00C853' if fb['is_correct'] else '#FF5252'}">
                    {'✅' if fb['is_correct'] else '❌'} Your Answer: {fb['user']}</span><br>
                    <b>Correct Answer:</b> {fb['correct']}
                </div>
                """,
                unsafe_allow_html=True
            )
        
        if st.button("Retake Quiz"):
            st.session_state.quiz_submitted = False
            st.session_state.quiz_start_time = None
            st.session_state.time_remaining = 300
            st.session_state.user_answers = {}
            st.session_state.questions = []
            st.rerun()
