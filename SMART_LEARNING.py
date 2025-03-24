# [Previous imports and functions remain exactly the same until the CSS section]

# Custom CSS for light purple (#E6E6FA) color scheme
st.markdown(
    """
    <style>
    .stApp {
        background: #E6E6FA;  /* Light lavender background */
        color: #4B0082;       /* Indigo text for contrast */
        font-family: 'Arial', sans-serif;
    }
    .stButton>button {
        background-color: #9370DB !important;  /* Medium purple */
        color: white !important;
        border: none;
        border-radius: 8px;
        padding: 10px 20px;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        background-color: #8A2BE2 !important;  /* Blue violet */
        transform: scale(1.05);
    }
    .stTextInput>div>div>input {
        background-color: rgba(255, 255, 255, 0.9);
        border-radius: 8px;
        padding: 10px;
        border: 1px solid #9370DB;
    }
    .stRadio>div {
        background-color: rgba(255, 255, 255, 0.85);
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #9370DB;
    }
    .stHeader {
        color: #4B0082 !important;  /* Indigo headers */
    }
    .stMarkdown {
        color: #4B0082;
    }
    .timer {
        color: #8A2BE2 !important;  /* Blue violet */
        font-weight: bold;
        font-size: 1.3rem;
        background-color: rgba(230, 230, 250, 0.7);
        padding: 5px 10px;
        border-radius: 5px;
        display: inline-block;
    }
    .quiz-card {
        background-color: rgba(255, 255, 255, 0.9) !important;
        color: #4B0082 !important;
        border-radius: 10px;
        padding: 20px;
        margin-bottom: 20px;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
        border: 1px solid #9370DB;
    }
    .sidebar .sidebar-content {
        background-color: #9370DB !important;  /* Medium purple sidebar */
        color: white !important;
    }
    .stChatMessage {
        background-color: rgba(255, 255, 255, 0.9) !important;
        color: #4B0082 !important;
        border-radius: 10px;
        padding: 15px;
        margin: 10px 0;
        border: 1px solid #9370DB;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# [Rest of your existing code remains exactly the same until the quiz results section]

# Only update the results display section in Quiz Challenge mode:
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

    # Results card with purple accent
    st.markdown(
        f"""
        <div style="background-color: #9370DB; padding: 20px; border-radius: 10px; margin-bottom: 20px; color: white;">
            <h2 style="color: white;">Quiz Results</h2>
            <h3>Your Score: {score}/{len(questions)} ({(score/len(questions))*100:.1f}%)</h3>
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
                <span style="color: {'#2E8B57' if fb['is_correct'] else '#B22222'}">
                {'✅' if fb['is_correct'] else '❌'} Your Answer: {fb['user_answer']}</span><br>
                <b>Correct Answer:</b> {fb['correct_answer']}
            </div>
            """,
            unsafe_allow_html=True
        )
