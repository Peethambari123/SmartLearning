# Quiz Challenge mode (updated for user-paced completion)
elif app_mode == "Quiz Challenge":
    st.header("Quiz Challenge")
    st.write("Upload a PDF and take a quiz based on its content. Answer at your own pace and submit when ready.")

    # Step 1: Ask the user to upload a PDF file (only if no quiz is in progress)
    if not st.session_state.quiz_questions:
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

    # Step 4: Display quiz if questions exist
    if st.session_state.quiz_questions and not st.session_state.quiz_submitted:
        st.write("### Quiz Questions")
        st.write("Take your time to answer the questions below. Your progress is saved until you submit.")

        # Display each question with radio buttons for options
        for i, q in enumerate(st.session_state.quiz_questions):
            st.write(f"**Q{i+1}: {q['question']}**")
            # Use the previous answer if it exists, otherwise no default selection
            default_answer = st.session_state.user_answers.get(f"q{i+1}", None)
            user_answer = st.radio(
                f"Select your answer for Q{i+1}",
                options=q["options"],
                key=f"q{i+1}",
                index=q["options"].index(default_answer) if default_answer in q["options"] else None
            )
            if user_answer:
                st.session_state.user_answers[f"q{i+1}"] = user_answer

        # Submit button to finalize the quiz
        if st.button("Submit Quiz"):
            st.session_state.quiz_submitted = True

    # Step 5: Display score and feedback after submission
    if st.session_state.quiz_submitted and st.session_state.quiz_questions:
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
        if st.button("Start a New Quiz"):
            st.session_state.quiz_questions = []
            st.session_state.user_answers = {}
            st.session_state.quiz_submitted = False
            st.session_state.uploaded_file = None
            st.session_state.pdf_text = None
            st.experimental_rerun()

    # If no questions were generated
    if st.session_state.uploaded_file and not st.session_state.quiz_questions and not st.session_state.quiz_submitted:
        st.write("Failed to generate quiz questions. Please try uploading again.")
