import os
import streamlit as st
import google.generativeai as genai
from PyPDF2 import PdfReader
from googleapiclient.discovery import build
import re  # For parsing quiz questions

# Configure Google Gemini API key
API_KEY = "AIzaSyAPS9hfiQ-IlF3HzybSt-SGR_ZP4S3ONgU"
genai.configure(api_key=API_KEY)

# Configure YouTube Data API key
YOUTUBE_API_KEY = "AIzaSyDjjpWFszcgYsc4qc_4cFh5n62kRBzUVqo"
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
    prompt = f"Context:\n{context}\n\nQuery: {query}\nAnswer:"
    model = genai.GenerativeModel("gemini-1.5-flash")
    response = model.generate_content(prompt)
    return response.text.strip()

# Function to search YouTube and generate links
def search_youtube(query: str, max_results: int = 5):
    request = youtube.search().list(q=query, part="snippet", type="video", maxResults=max_results)
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
    prompt = f"Generate {num_questions} multiple-choice questions based on the following text:\n\n{pdf_text}\n\nEach question should have 4 options and a correct answer, formatted as:\n\nQ1: [Question]\nA) [Option]\nB) [Option]\nC) [Option]\nD) [Option]\nCorrect Answer: [Option]"
    model = genai.GenerativeModel("gemini-1.5-flash")
    response = model.generate_content(prompt)
    return response.text

# Function to parse quiz questions into a structured format
def parse_quiz_questions(quiz_text):
    questions = []
    pattern = r"Q\d+: (.*?)\nA\) (.*?)\nB\) (.*?)\nC\) (.*?)\nD\) (.*?)\nCorrect Answer: (.*?)(?=\nQ\d+:|$)"
    matches = re.finditer(pattern, quiz_text, re.DOTALL)
    for match in matches:
        question = match.group(1).strip()
        options = [match.group(2).strip(), match.group(3).strip(), match.group(4).strip(), match.group(5).strip()]
        correct_answer = match.group(6).strip()
        questions.append({"question": question, "options": options, "correct_answer": correct_answer})
    return questions

# Initialize session state
if "chat" not in st.session_state:
    st.session_state.chat = genai.GenerativeModel('gemini-1.5-flash').start_chat(history=[])
if "messages" not in st.session_state:
    st.session_state.messages = []
if "uploaded_file" not in st.session_state:
    st.session_state.uploaded_file = None
    st.session_state.pdf_text = None
if "quiz_questions" not in st.session_state:
    st.session_state.quiz_questions = []
if "user_answers" not in st.session_state:
    st.session_state.user_answers = {}
if "quiz_submitted" not in st.session_state:
    st.session_state.quiz_submitted = False

# Custom CSS (unchanged)
st.markdown(
    """
    <style>
    /* Your existing CSS here */
    </style>
    """, unsafe_allow_html=True
)

# Streamlit app interface
st.title("🤖 Chatbot & PDF Query App")
st.write("Welcome! You can chat with the AI, upload a PDF to query its content, search for YouTube videos, or take a quiz.")

# Sidebar for navigation
st.sidebar.title("Navigation")
app_mode = st.sidebar.radio("Choose Mode", ["Chat with AI", "Query a PDF", "Search YouTube", "Quiz Challenge"])

# Chat with AI mode (unchanged)
if app_mode == "Chat with AI":
    st.header("Chat with AI")
    st.write("Ask me anything!")
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    if prompt := st.chat_input("Say something..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        response = st.session_state.chat.send_message(prompt)
        st.session_state.messages.append({"role": "assistant", "content": response.text})
        with st.chat_message("assistant"):
            st.markdown(response.text)

# Query a PDF mode (unchanged)
elif app_mode == "Query a PDF":
    st.header("Query a PDF")
    st.write("Upload a PDF and ask questions about its content.")
    uploaded_file = st.file_uploader("Please upload a PDF file", type="pdf")
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
        st.text_area("PDF Content Preview", value=pdf_text[:1000], height=150)
        continue_or_upload = st.radio("Do you want to continue or upload a new file?", ("Continue", "Upload New File"))
        if continue_or_upload == "Upload New File":
            st.session_state.uploaded_file = None
            st.session_state.pdf_text = None
            st.experimental_rerun()
        if st.session_state.uploaded_file is not None:
            query = st.text_input("Ask a question based on the content of the PDF:")
            if query:
                response = query_with_cag(st.session_state.pdf_text, query)
                st.write("Answer:", response)

# Search YouTube mode (unchanged)
elif app_mode == "Search YouTube":
    st.header("Search YouTube")
    st.write("Search for videos on YouTube.")
    search_query = st.text_input("Enter a search query for YouTube:")
    if search_query:
        st.write(f"Searching YouTube for: {search_query}")
        videos = search_youtube(search_query)
        if videos:
            st.write("Here are some relevant videos:")
            for video in videos:
                st.write(f"- [{video['title']}]({video['link']})")
        else:
            st.write("No videos found for your query.")

# Quiz Challenge mode (updated)
elif app_mode == "Quiz Challenge":
    st.header("Quiz Challenge")
    st.write("Upload a PDF and take a quiz based on its content.")

    # Step 1: Ask the user to upload a PDF file
    uploaded_file = st.file_uploader("Please upload a PDF file", type="pdf", key="quiz_uploader")

    if uploaded_file is not None:
        # Ensure the directory exists
        temp_dir = "temp"
        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir)

        # Save the uploaded file to a temporary location
        temp_file_path = os.path.join(temp_dir, uploaded_file.name)
        with open(temp_file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        # Step 2: Extract text from the uploaded PDF
        pdf_text = read_pdf(temp_file_path)
        st.session_state.uploaded_file = uploaded_file
        st.session_state.pdf_text = pdf_text

        # Step 3: Generate quiz questions from the PDF text
        st.write("### Generating Quiz Questions...")
        with st.spinner("Generating questions from the PDF..."):
            quiz_text = generate_quiz_from_pdf(pdf_text)
            st.session_state.quiz_questions = parse_quiz_questions(quiz_text)

        if st.session_state.quiz_questions:
            st.write("### Quiz Questions")
            
            # Display each question with radio buttons for options
            for i, q in enumerate(st.session_state.quiz_questions):
                st.write(f"**Q{i+1}: {q['question']}**")
                user_answer = st.radio(
                    f"Select your answer for Q{i+1}",
                    options=q["options"],
                    key=f"q{i+1}",
                    index=None  # No default selection
                )
                if user_answer:
                    st.session_state.user_answers[f"q{i+1}"] = user_answer

            # Submit button to calculate score
            if st.button("Submit Quiz"):
                st.session_state.quiz_submitted = True

            # Display score and feedback after submission
            if st.session_state.quiz_submitted:
                score = 0
                total = len(st.session_state.quiz_questions)
                feedback = []

                for i, q in enumerate(st.session_state.quiz_questions):
                    user_answer = st.session_state.user_answers.get(f"q{i+1}", "Not answered")
                    correct_answer = q["correct_answer"]
                    if user_answer == correct_answer:
                        score += 1
                    feedback.append(f"Q{i+1}: Your answer: {user_answer}, Correct answer: {correct_answer}")

                st.write(f"### Your Score: {score}/{total}")
                st.write(f"### Percentage: {(score/total)*100:.2f}%")
                st.write("### Feedback:")
                for line in feedback:
                    st.write(line)

                # Reset quiz option
                if st.button("Take Quiz Again"):
                    st.session_state.quiz_questions = []
                    st.session_state.user_answers = {}
                    st.session_state.quiz_submitted = False
                    st.session_state.uploaded_file = None
                    st.experimental_rerun()
        else:
            st.write("Failed to generate quiz questions. Please try again.")
