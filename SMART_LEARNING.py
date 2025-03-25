import os
import time
import streamlit as st
import google.generativeai as genai
from PyPDF2 import PdfReader
from googleapiclient.discovery import build

# Configure Google Gemini API key
API_KEY = "AIzaSyAPS9hfiQ-IlF3HzybSt-SGR_ZP4S3ONgU"
genai.configure(api_key=API_KEY)

# Configure YouTube Data API key
YOUTUBE_API_KEY = "AIzaSyDjjpWFszcgYsc4qc_4cFh5n62kRBzUVqo"  # Replace with your YouTube API key
youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)

# Function to read the PDF file
def read_pdf(file_path):
    """Reads the text from a PDF file."""
    with open(file_path, 'rb') as file:
        reader = PdfReader(file)
        text = ""
        for page_num in range(len(reader.pages)):
            page = reader.pages[page_num]
            text += page.extract_text()
    return text

# Function to query the Gemini LLM with preloaded context (CAG)
def query_with_cag(context: str, query: str) -> str:
    """Query the Gemini LLM with preloaded context using Cache-Augmented Generation."""
    prompt = f"Context:\n{context}\n\nQuery: {query}\nAnswer:"
    model = genai.GenerativeModel("gemini-1.5-flash")
    response = model.generate_content(prompt)
    return response.text.strip()

# Function to search YouTube and generate links
def search_youtube(query: str, max_results: int = 5):
    """Search YouTube for videos related to the query and return their links."""
    request = youtube.search().list(
        q=query,
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

# Function to generate quiz questions from PDF text using Gemini API
def generate_quiz_from_pdf(pdf_text: str, num_questions: int = 5):
    """Generate quiz questions from the PDF text using Gemini API."""
    prompt = f"Generate {num_questions} multiple-choice questions based on the following text:\n\n{pdf_text}\n\nEach question should have 4 options (a), b), c), d)) and a correct answer labeled as 'Correct Answer:'."
    model = genai.GenerativeModel("gemini-1.5-flash")
    response = model.generate_content(prompt)
    return response.text

# Initialize session state for chat and PDF
if "chat" not in st.session_state:
    st.session_state.chat = genai.GenerativeModel('gemini-1.5-flash').start_chat(history=[])

if "messages" not in st.session_state:
    st.session_state.messages = []

if "uploaded_file" not in st.session_state:
    st.session_state.uploaded_file = None
    st.session_state.pdf_text = None

# Custom CSS for #5293BB color scheme
st.markdown(
    """
    <style>
    .stApp {
        background: black;
        background-size: 400% 400%;
        animation: gradientBG 15s ease infinite;
        perspective: 1000px;
        overflow: hidden;
    }
    @keyframes gradientBG {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }
    .stButton>button {
        background-color: purple;
        color: purple;
        border-radius: 5px;
        padding: 10px 20px;
        border: none;
        transform: translateZ(50px);
        transition: transform 0.3s ease, box-shadow 0.3s ease;
    }
    .stButton>button:hover {
        transform: translateZ(70px);
        box-shadow: 0 10px 20px rgba(0, 0, 0, 0.2);
    }
    .stTextInput>div>div>input {
        background-color: rgba(255, 255, 255, 0.8);
        border-radius: 5px;
        padding: 10px;
        transform: translateZ(30px);
        transition: transform 0.3s ease;
    }
    .stTextInput>div>div>input:focus {
        transform: translateZ(50px);
    }
    .stRadio>div>label {
        color: white;
        transform: translateZ(20px);
        transition: transform 0.3s ease;
    }
    .stRadio>div>label:hover {
        transform: translateZ(40px);
    }
    .stMarkdown {
        color: white;
        transform: translateZ(10px);
    }
    .stHeader {
        color: white;
        transform: translateZ(40px);
    }
    .stApp::before {
        content: "";
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='100' height='100' viewBox='0 0 100 100'%3E%3Cpath d='M50 10L60 30H40L50 10ZM50 90L40 70H60L50 90ZM10 50L30 60V40L10 50ZM90 50L70 40V60L90 50Z' fill='none' stroke='%23ffffff' stroke-width='2' opacity='0.1'/%3E%3C/svg%3E");
        opacity: 0.1;
        pointer-events: none;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Streamlit app interface
st.title("🤖 Chatbot & PDF Query App")
st.write("Welcome! You can chat with the AI, upload a PDF to query its content, search for YouTube videos, or take a quiz.")

# Sidebar for navigation
st.sidebar.title("Navigation")
app_mode = st.sidebar.radio("Choose Mode", ["Chat with AI", "Query a PDF", "Search YouTube", "Quiz Challenge"])

# Chat with AI mode
if app_mode == "Chat with AI":
    st.header("Chat with AI")
    st.write("Ask me anything!")

    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Chat input
    if prompt := st.chat_input("Say something..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        response = st.session_state.chat.send_message(prompt)
        st.session_state.messages.append({"role": "assistant", "content": response.text})
        with st.chat_message("assistant"):
            st.markdown(response.text)

# Query a PDF mode
elif app_mode == "Query a PDF":
    st.header("Query a PDF")
    st.write("Upload a PDF and ask questions about its content.")

    uploaded_file = st.file_uploader("Upload a PDF file", type="pdf")
    if uploaded_file is not None:
        temp_dir = "temp"
        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir)

        temp_file_path = os.path.join(temp_dir, uploaded_file.name)
        with open(temp_file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        pdf_text = read_pdf(temp_file_path)
        st.session_state.uploaded_file = uploaded_file
        st.session_state.pdf_text = pdf_text
        st.text_area("PDF Content Preview", value=pdf_text[:500], height=100)

    if st.session_state.pdf_text:
        query = st.text_input("Ask a question about the PDF:")
        if query:
            with st.spinner("Processing your query..."):
                answer = query_with_cag(st.session_state.pdf_text, query)
                st.markdown(f"**Answer:** {answer}")

# Search YouTube mode
elif app_mode == "Search YouTube":
    st.header("Search YouTube")
    st.write("Search for YouTube videos related to your query.")

    youtube_query = st.text_input("Enter a search term:")
    if youtube_query:
        with st.spinner("Searching YouTube..."):
            videos = search_youtube(youtube_query)
            st.write("### Results:")
            for video in videos:
                st.markdown(f"[{video['title']}]({video['link']})")

# Quiz Challenge mode
elif app_mode == "Quiz Challenge":
    st.header("Quiz Challenge")
    st.write("Upload a PDF and take a timed quiz based on its content.")

    # Initialize session state for quiz timer and user answers
    if "quiz_start_time" not in st.session_state:
        st.session_state.quiz_start_time = None
    if "time_remaining" not in st.session_state:
        st.session_state.time_remaining = 300  # 5 minutes (300 seconds)
    if "user_answers" not in st.session_state:
        st.session_state.user_answers = {}
    if "quiz_submitted" not in st.session_state:
        st.session_state.quiz_submitted = False

    uploaded_file = st.file_uploader("Please upload a PDF file", type="pdf", key="quiz_pdf_uploader")
    if uploaded_file is not None:
        temp_dir = "temp"
        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir)

        temp_file_path = os.path.join(temp_dir, uploaded_file.name)
        with open(temp_file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        pdf_text = ""
        try:
            pdf_text = read_pdf(temp_file_path)
            if not pdf_text.strip():
                st.error("The PDF appears to be empty or text could not be extracted.")
                st.stop()
        except Exception as e:
            st.error(f"Error extracting text from PDF: {str(e)}")
            st.stop()

        st.session_state.uploaded_file = uploaded_file
        st.session_state.pdf_text = pdf_text
        st.text_area("PDF Content Preview", value=pdf_text[:500], height=100)

        st.write("### Generating Quiz Questions...")
        quiz_questions = ""
        with st.spinner("Generating questions from the PDF..."):
            try:
                quiz_questions = generate_quiz_from_pdf(pdf_text)
                if not quiz_questions:
                    st.error("No quiz questions were generated. The PDF content might be insufficient.")
                    st.stop()
            except Exception as e:
                st.error(f"Error generating quiz questions: {str(e)}")
                st.stop()

        # Parse the quiz questions into a structured format
        lines = quiz_questions.split("\n")
        questions = []
        current_question = {}
        options = []

        for line in lines:
            line = line.strip()
            if not line:
                continue
            # Match question (e.g., "1. What is...")
            if line[0].isdigit() and "." in line[:3]:
                if current_question and options:
                    current_question["options"] = options
                    questions.append(current_question)
                question_text = line.split(".", 1)[1].strip()
                current_question = {"text": question_text}
                options = []
            # Match options (e.g., "a) Some text")
            elif any(line.startswith(opt) for opt in ["a)", "b)", "c)", "d)"]):
                options.append(line)
            # Match correct answer (e.g., "Correct Answer: c)")
            elif line.lower().startswith("correct answer:"):
                correct_answer = line.split(":", 1)[1].strip()
                current_question["correct"] = correct_answer

        if current_question and options:
            current_question["options"] = options
            questions.append(current_question)

        if not questions or any(not q.get("correct") or not q.get("options") for q in questions):
            st.error("Failed to parse quiz questions properly. Raw output:")
            st.text_area("Raw Quiz Output (Debug)", quiz_questions, height=200)
            st.stop()

        # Start the quiz timer if not already started
        if st.session_state.quiz_start_time is None:
            st.session_state.quiz_start_time = time.time()

        # Calculate time remaining
        elapsed_time = time.time() - st.session_state.quiz_start_time
        st.session_state.time_remaining = max(0, 300 - int(elapsed_time))  # 5 minutes limit

        # Display the timer
        st.write(f"### Time Remaining: {st.session_state.time_remaining // 60}:{st.session_state.time_remaining % 60:02d}")

        # Display quiz questions if time is remaining
        if st.session_state.time_remaining > 0 and not st.session_state.quiz_submitted:
            st.write("### Quiz Questions")
            for i, q in enumerate(questions, 1):
                st.markdown(f"**Question {i}: {q['text']}**")
                # Display options as radio buttons
                user_answer = st.radio(
                    f"Select your answer for Question {i}",
                    q["options"],
                    key=f"quiz_q{i}"
                )
                st.session_state.user_answers[i] = user_answer

            # Submit button
            if st.button("Submit Quiz"):
                st.session_state.quiz_submitted = True
        else:
            if st.session_state.time_remaining <= 0:
                st.error("Time's up! Your quiz has been automatically submitted.")
                st.session_state.quiz_submitted = True

        # Evaluate the quiz if submitted
        if st.session_state.quiz_submitted:
            score = 0
            feedback = []
            for i, q in enumerate(questions, 1):
                user_answer = st.session_state.user_answers.get(i)
                correct_answer = q["correct"]
                is_correct = user_answer == correct_answer
                if is_correct:
                    score += 1
                feedback.append({
                    "question": q["text"],
                    "user_answer": user_answer,
                    "correct_answer": correct_answer,
                    "is_correct": is_correct
                })

            st.write(f"### Your Score: {score}/{len(questions)} ({(score/len(questions))*100:.1f}%)")
            st.write("### Detailed Feedback")
            for fb in feedback:
                st.markdown(
                    f"**Question:** {fb['question']}<br>"
                    f"**Your Answer:** {fb['user_answer']}<br>"
                    f"**Correct Answer:** {fb['correct_answer']}<br>"
                    f"**Result:** {'✅ Correct' if fb['is_correct'] else '❌ Incorrect'}",
                    unsafe_allow_html=True
                )
