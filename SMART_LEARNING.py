elif app_mode == "Quiz Challenge":
    st.header("Quiz Challenge")
    st.write("Upload a PDF and take a quiz based on its content.")

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

        # Display quiz and collect user answers
        st.write("### Quiz Questions")
        user_answers = {}
        for i, q in enumerate(questions, 1):
            st.markdown(f"**Question {i}: {q['text']}**")
            # Display options as radio buttons
            user_answer = st.radio(
                f"Select your answer for Question {i}",
                q["options"],
                key=f"quiz_q{i}"
            )
            user_answers[i] = user_answer

        # Submit and evaluate
        if st.button("Submit Quiz"):
            score = 0
            feedback = []
            for i, q in enumerate(questions, 1):
                user_answer = user_answers.get(i)
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
