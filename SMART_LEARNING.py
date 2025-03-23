import os
import streamlit as st
import google.generativeai as genai
from PyPDF2 import PdfReader
from googleapiclient.discovery import build
import requests  # For QuizAPI integration

# Configure Google Gemini API key
API_KEY = "AIzaSyAPS9hfiQ-IlF3HzybSt-SGR_ZP4S3ONgU"
genai.configure(api_key=API_KEY)

# Configure YouTube Data API key
YOUTUBE_API_KEY = "AIzaSyDjjpWFszcgYsc4qc_4cFh5n62kRBzUVqo"  # Replace with your YouTube API key
youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)

# QuizAPI configuration
QUIZAPI_KEY = "https://opentdb.com/api_config.php"  # Replace with your QuizAPI key

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
    """
    Query the Gemini LLM with preloaded context using Cache-Augmented Generation.
    """
    prompt = f"Context:\n{context}\n\nQuery: {query}\nAnswer:"
    model = genai.GenerativeModel("gemini-1.5-flash")
    response = model.generate_content(prompt)
    return response.text.strip()

# Function to search YouTube and generate links
def search_youtube(query: str, max_results: int = 5):
    """
    Search YouTube for videos related to the query and return their links.
    """
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

# Function to get challenges from QuizAPI
def get_challenges(topic: str, limit: int = 5):
    """
    Fetch quiz questions from QuizAPI based on the topic.
    """
    url = "https://quizapi.io/api/v1/questions"
    params = {
        "apiKey": QUIZAPI_KEY,
        "category": topic,
        "limit": limit
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        return response.json()
    else:
        return None

# Initialize session state for chat and PDF
if "chat" not in st.session_state:
    st.session_state.chat = genai.GenerativeModel('gemini-1.5-flash').start_chat(history=[])

if "messages" not in st.session_state:
    st.session_state.messages = []

if "uploaded_file" not in st.session_state:
    st.session_state.uploaded_file = None
    st.session_state.pdf_text = None

# Custom CSS for nature-themed background
st.markdown(
    """
    <style>
    .stApp {
        background-image: url("https://images.unsplash.com/photo-1475924156734-496f6cac6ec1?ixlib=rb-1.2.1&auto=format&fit=crop&w=1950&q=80");
        background-size: cover;
        background-position: center;
        background-repeat: no-repeat;
    }
    .stButton>button {
        background-color: #4CAF50;
        color: white;
        border-radius: 5px;
        padding: 10px 20px;
        border: none;
    }
    .stTextInput>div>div>input {
        background-color: rgba(255, 255, 255, 0.8);
        border-radius: 5px;
        padding: 10px;
    }
    .stRadio>div>label {
        color: white;
    }
    .stMarkdown {
        color: white;
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
app_mode = st.sidebar.radio("Choose Mode", ["Chat with AI", "Query a PDF", "Search YouTube", "Take a Quiz"])

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
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Get AI response
        response = st.session_state.chat.send_message(prompt)

        # Add AI response to chat history
        st.session_state.messages.append({"role": "assistant", "content": response.text})
        with st.chat_message("assistant"):
            st.markdown(response.text)

# Query a PDF mode
elif app_mode == "Query a PDF":
    st.header("Query a PDF")
    st.write("Upload a PDF and ask questions about its content.")

    # Step 1: Ask the user to upload a PDF file
    uploaded_file = st.file_uploader("Please upload a PDF file", type="pdf")

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

        # Step 3: Show a preview of the content of the PDF (optional)
        st.text_area("PDF Content Preview", value=pdf_text[:1000], height=150)

        # Step 4: Ask if the user wants to continue with the current file or upload a new one
        continue_or_upload = st.radio("Do you want to continue or upload a new file?",
                                     ("Continue", "Upload New File"))

        if continue_or_upload == "Upload New File":
            st.session_state.uploaded_file = None
            st.session_state.pdf_text = None
            st.experimental_rerun()  # Restart app to upload a new file

        # Step 5: Ask the user to enter a query based on the uploaded PDF
        if st.session_state.uploaded_file is not None:
            query = st.text_input("Ask a question based on the content of the PDF:")

            if query:
                # Step 6: Get the answer from Gemini LLM with the context of the PDF
                response = query_with_cag(st.session_state.pdf_text, query)
                st.write("Answer:", response)

# Search YouTube mode
elif app_mode == "Search YouTube":
    st.header("Search YouTube")
    st.write("Search for videos on YouTube.")

    # Step 1: Ask the user to enter a search query
    search_query = st.text_input("Enter a search query for YouTube:")

    if search_query:
        # Step 2: Search YouTube and display results
        st.write(f"Searching YouTube for: {search_query}")
        videos = search_youtube(search_query)

        if videos:
            st.write("Here are some relevant videos:")
            for video in videos:
                st.write(f"- [{video['title']}]({video['link']})")
        else:
            st.write("No videos found for your query.")

# Take a Quiz mode
elif app_mode == "Take a Quiz":
    st.header("Take a Quiz")
    st.write("Test your knowledge on a topic by taking a quiz.")

    # Step 1: Ask the user to enter a topic for the quiz
    quiz_topic = st.text_input("Enter a topic for the quiz:")

    if quiz_topic:
        # Step 2: Fetch quiz questions from QuizAPI
        st.write(f"Fetching quiz questions for: {quiz_topic}")
        challenges = get_challenges(quiz_topic)

        if challenges:
            st.write("### Quiz Questions")
            for i, question in enumerate(challenges):
                st.write(f"**Question {i+1}:** {question['question']}")
                options = [v for k, v in question['answers'].items() if v is not None]
                user_answer = st.radio(f"Options for Question {i+1}", options, key=f"quiz_{i}")
                if st.button(f"Submit Answer for Question {i+1}"):
                    correct_answer = question['correct_answers']
                    if user_answer == correct_answer:
                        st.success("Correct! 🎉")
                    else:
                        st.error("Incorrect. Try again! 🚫")
        else:
            st.write("No quiz questions found for this topic.")
