st.markdown(
    """
    <style>
    .stApp {
        background: linear-gradient(135deg, #87CEEB, #FFD700, #FF6347);
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
        background-color: #4682B4; /* Ocean blue */
        color: white;
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
    </style>
    """,
    unsafe_allow_html=True
)
