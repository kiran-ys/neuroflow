import streamlit as st
from google import genai
from google.genai import types
import json
import random
from datetime import date

# ─────────────────────────────────────────
#  PAGE CONFIG
# ─────────────────────────────────────────
st.set_page_config(
    page_title="NeuroFlow – Your Flow State Tutor",
    page_icon="🧠",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# ─────────────────────────────────────────
#  CUSTOM CSS
# ─────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=DM+Sans:wght@300;400;500;600;700&display=swap');
:root {
    --bg: #0a0a0f; --surface: #13131a; --card: #1a1a24;
    --accent: #7c6af7; --accent2: #f7c06a; --accent3: #6af7b8;
    --text: #e8e8f0; --muted: #6b6b80; --danger: #f76a6a;
}
html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; background-color: var(--bg); color: var(--text); }
.stApp { background-color: var(--bg); }
h1, h2, h3 { font-family: 'Space Mono', monospace; color: var(--text); }
#MainMenu, footer, header { visibility: hidden; }
.stButton > button {
    background: linear-gradient(135deg, var(--accent), #9b8cf9);
    color: white; border: none; border-radius: 12px;
    padding: 0.6rem 1.4rem; font-family: 'DM Sans', sans-serif;
    font-weight: 600; font-size: 1rem; cursor: pointer;
    transition: all 0.2s ease; width: 100%;
}
.stButton > button:hover { transform: translateY(-2px); box-shadow: 0 8px 24px rgba(124,106,247,0.4); }
.stTextArea textarea, .stTextInput input {
    background: var(--card) !important; border: 1.5px solid #2a2a38 !important;
    border-radius: 12px !important; color: var(--text) !important;
    font-family: 'DM Sans', sans-serif !important; font-size: 1rem !important;
}
.nf-card { background: var(--card); border: 1px solid #2a2a38; border-radius: 16px; padding: 1.5rem; margin-bottom: 1rem; }
.flow-meter-wrap { background: var(--card); border-radius: 16px; padding: 1.2rem 1.5rem; margin-bottom: 1rem; border: 1px solid #2a2a38; }
.flow-bar-bg { background: #1e1e2e; border-radius: 99px; height: 14px; width: 100%; overflow: hidden; margin: 0.5rem 0; }
.flow-bar-fill { height: 100%; border-radius: 99px; transition: width 0.6s ease; }
.reward-correct { background: rgba(106,247,184,0.1); border: 1.5px solid var(--accent3); border-radius: 14px; padding: 1.2rem; text-align: center; }
.reward-wrong { background: rgba(247,192,106,0.1); border: 1.5px solid var(--accent2); border-radius: 14px; padding: 1.2rem; text-align: center; }
.question-card { background: linear-gradient(135deg, #1a1a2e, #16162a); border: 1.5px solid var(--accent); border-radius: 16px; padding: 1.5rem; margin-bottom: 1rem; box-shadow: 0 4px 24px rgba(124,106,247,0.1); }
.level-badge { display: inline-block; padding: 0.3rem 0.9rem; border-radius: 99px; font-size: 0.8rem; font-weight: 700; font-family: 'Space Mono', monospace; letter-spacing: 0.05em; }
.beginner { background: rgba(106,247,184,0.15); color: var(--accent3); border: 1px solid var(--accent3); }
.moderate { background: rgba(247,192,106,0.15); color: var(--accent2); border: 1px solid var(--accent2); }
.advanced { background: rgba(247,106,106,0.15); color: var(--danger); border: 1px solid var(--danger); }
.hero { text-align: center; padding: 2.5rem 0 1.5rem; }
.hero h1 { font-size: 2.8rem; margin-bottom: 0.5rem; }
.hero .tagline { color: var(--muted); font-size: 1.05rem; margin-bottom: 1.5rem; }
.hero .accent-text { color: var(--accent); }
.score-card { background: linear-gradient(135deg, #1a1a2e, #16162a); border: 1.5px solid var(--accent3); border-radius: 20px; padding: 2rem; text-align: center; }
.score-num { font-family: 'Space Mono', monospace; font-size: 3.5rem; font-weight: 700; color: var(--accent3); line-height: 1; }
.progress-dots { display: flex; gap: 0.5rem; justify-content: center; margin-bottom: 1.5rem; }
.dot { width: 8px; height: 8px; border-radius: 50%; background: #2a2a38; }
.dot.active { background: var(--accent); }
.stSelectbox > div > div { background: var(--card) !important; border: 1.5px solid #2a2a38 !important; border-radius: 12px !important; color: var(--text) !important; }
hr { border-color: #2a2a38 !important; margin: 1.5rem 0 !important; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────
#  SESSION STATE
# ─────────────────────────────────────────
defaults = {
    "screen": "welcome",
    "mood": None, "level": None, "subject": None,
    "flow_score": 50, "streak": 0, "session_points": 0,
    "q_count": 0, "correct_count": 0,
    "current_question": None, "current_answer": None,
    "feedback": None, "level_q_index": 0,
    "level_answers": [], "answer_submitted": False,
    "api_key": "", "gemini_ready": False,
    "last_result": None, "level_detect_questions": [],
    "asked_questions": [], "asked_topics": [],
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ─────────────────────────────────────────
#  GEMINI SETUP (new SDK)
# ─────────────────────────────────────────
def init_gemini(api_key):
    try:
        client = genai.Client(api_key=api_key)
        # Quick validation test
        client.models.generate_content(
            model="gemini-2.0-flash-lite",
            contents="Hi",
            config=types.GenerateContentConfig(max_output_tokens=5)
        )
        st.session_state["gemini_ready"] = True
        st.session_state["api_key"] = api_key
        return True
    except Exception:
        return False

def ask_gemini(prompt, temperature=1.0):
    try:
        client = genai.Client(api_key=st.session_state["api_key"])
        response = client.models.generate_content(
            model="gemini-2.0-flash-lite",
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=temperature,
                max_output_tokens=500
            )
        )
        return response.text.strip()
    except Exception as e:
        return ""

# ─────────────────────────────────────────
#  QUESTION BANK (guaranteed unique, no API needed)
# ─────────────────────────────────────────
QUESTION_BANK = {
    "Mathematics": {
        "easy": [
            {"question": "What is 25% of 200?", "options": ["A) 25", "B) 50", "C) 75", "D) 100"], "answer": "B", "explanation": "25% = 1/4. So 200÷4 = 50. Brilliant!"},
            {"question": "What is the LCM of 4 and 6?", "options": ["A) 8", "B) 10", "C) 12", "D) 24"], "answer": "C", "explanation": "LCM of 4 and 6 is 12. Great thinking!"},
            {"question": "How many sides does a hexagon have?", "options": ["A) 5", "B) 6", "C) 7", "D) 8"], "answer": "B", "explanation": "Hexa means 6. You got it!"},
            {"question": "What is 3/4 as a decimal?", "options": ["A) 0.25", "B) 0.50", "C) 0.75", "D) 1.25"], "answer": "C", "explanation": "3÷4 = 0.75. Excellent!"},
            {"question": "What is the square of 12?", "options": ["A) 124", "B) 132", "C) 144", "D) 156"], "answer": "C", "explanation": "12×12 = 144. You're on fire!"},
            {"question": "What is 15% of 300?", "options": ["A) 30", "B) 35", "C) 45", "D) 55"], "answer": "C", "explanation": "15% of 300 = 45. Amazing work!"},
            {"question": "What is the HCF of 12 and 18?", "options": ["A) 3", "B) 6", "C) 9", "D) 12"], "answer": "B", "explanation": "HCF of 12 and 18 is 6. Fantastic!"},
            {"question": "What is the perimeter of a square with side 7cm?", "options": ["A) 14cm", "B) 21cm", "C) 28cm", "D) 49cm"], "answer": "C", "explanation": "Perimeter = 4×7 = 28cm. You nailed it!"},
            {"question": "What is the value of π approximately?", "options": ["A) 2.14", "B) 3.14", "C) 4.14", "D) 5.14"], "answer": "B", "explanation": "Pi ≈ 3.14159. Great recall!"},
            {"question": "If a triangle has angles 60° and 80°, what is the third?", "options": ["A) 30°", "B) 40°", "C) 50°", "D) 60°"], "answer": "B", "explanation": "Angles sum to 180°. 180-60-80=40°. Brilliant!"},
            {"question": "What is 8 × 7?", "options": ["A) 54", "B) 56", "C) 58", "D) 60"], "answer": "B", "explanation": "8×7 = 56. Keep going!"},
            {"question": "What is the area of a rectangle 5m × 4m?", "options": ["A) 18m²", "B) 20m²", "C) 22m²", "D) 24m²"], "answer": "B", "explanation": "Area = length × width = 5×4 = 20m². Fantastic!"},
        ],
        "medium": [
            {"question": "Solve: 3x - 7 = 14. What is x?", "options": ["A) 5", "B) 6", "C) 7", "D) 8"], "answer": "C", "explanation": "3x = 21, so x = 7. Excellent!"},
            {"question": "What is the slope of y = 3x + 5?", "options": ["A) 5", "B) 3", "C) 8", "D) -3"], "answer": "B", "explanation": "In y=mx+c, m is slope = 3. Brilliant!"},
            {"question": "What is the area of circle with radius 7? (π=22/7)", "options": ["A) 144", "B) 154", "C) 164", "D) 174"], "answer": "B", "explanation": "Area = πr² = 22/7 × 49 = 154. Amazing!"},
            {"question": "If P(A) = 0.4, what is P(not A)?", "options": ["A) 0.4", "B) 0.5", "C) 0.6", "D) 0.8"], "answer": "C", "explanation": "P(not A) = 1 - 0.4 = 0.6. Perfect logic!"},
            {"question": "Factorize: x² - 9", "options": ["A) (x-3)(x-3)", "B) (x+3)(x+3)", "C) (x-3)(x+3)", "D) (x-9)(x+1)"], "answer": "C", "explanation": "Difference of squares: (x-3)(x+3). Fantastic!"},
            {"question": "What is the median of: 3, 7, 2, 9, 5?", "options": ["A) 3", "B) 5", "C) 7", "D) 9"], "answer": "B", "explanation": "Sorted: 2,3,5,7,9. Middle = 5. Great!"},
            {"question": "Solve: 2x² = 50. What is x?", "options": ["A) 3", "B) 4", "C) 5", "D) 6"], "answer": "C", "explanation": "x² = 25, x = 5. Excellent work!"},
            {"question": "What is sin(90°)?", "options": ["A) 0", "B) 0.5", "C) 1", "D) -1"], "answer": "C", "explanation": "sin(90°) = 1. Classic! Well done!"},
            {"question": "What is cos(0°)?", "options": ["A) 0", "B) 0.5", "C) -1", "D) 1"], "answer": "D", "explanation": "cos(0°) = 1. Excellent recall!"},
            {"question": "What is 7² + 8²?", "options": ["A) 100", "B) 110", "C) 113", "D) 120"], "answer": "C", "explanation": "49 + 64 = 113. Brilliant!"},
        ],
        "hard": [
            {"question": "What is the derivative of sin(x)·cos(x)?", "options": ["A) 1", "B) cos(2x)", "C) sin(2x)", "D) -sin(2x)"], "answer": "B", "explanation": "Product rule gives cos²x - sin²x = cos(2x). Outstanding!"},
            {"question": "What is ∫x² dx?", "options": ["A) x²/2 + C", "B) x³/3 + C", "C) 2x + C", "D) x³ + C"], "answer": "B", "explanation": "Power rule: xⁿ⁺¹/(n+1). Incredible!"},
            {"question": "If A = [[1,2],[3,4]], what is det(A)?", "options": ["A) -2", "B) 2", "C) 10", "D) -10"], "answer": "A", "explanation": "det = 1×4 - 2×3 = -2. Brilliant mind!"},
            {"question": "What is i² where i is imaginary unit?", "options": ["A) 1", "B) -1", "C) i", "D) -i"], "answer": "B", "explanation": "By definition, i² = -1. Excellent!"},
            {"question": "Solve: log₂(64) = ?", "options": ["A) 4", "B) 5", "C) 6", "D) 7"], "answer": "C", "explanation": "2⁶ = 64, so log₂(64) = 6. Superb!"},
            {"question": "What is the sum of n natural numbers formula?", "options": ["A) n(n+1)", "B) n(n+1)/2", "C) n²/2", "D) n(n-1)/2"], "answer": "B", "explanation": "Sum = n(n+1)/2. Classic formula!"},
        ],
    },
    "Science": {
        "easy": [
            {"question": "Which gas do plants absorb during photosynthesis?", "options": ["A) Oxygen", "B) Nitrogen", "C) Carbon Dioxide", "D) Hydrogen"], "answer": "C", "explanation": "Plants absorb CO₂ and release O₂. Amazing!"},
            {"question": "What is the chemical symbol for Gold?", "options": ["A) Go", "B) Gd", "C) Au", "D) Ag"], "answer": "C", "explanation": "Au comes from Latin 'Aurum'. Brilliant!"},
            {"question": "How many bones are in the adult human body?", "options": ["A) 196", "B) 206", "C) 216", "D) 226"], "answer": "B", "explanation": "Adult humans have 206 bones. Excellent!"},
            {"question": "What planet is closest to the Sun?", "options": ["A) Venus", "B) Earth", "C) Mars", "D) Mercury"], "answer": "D", "explanation": "Mercury is closest to the Sun!"},
            {"question": "What is the boiling point of water?", "options": ["A) 90°C", "B) 95°C", "C) 100°C", "D) 105°C"], "answer": "C", "explanation": "Water boils at 100°C. Perfect!"},
            {"question": "Which organ pumps blood in the human body?", "options": ["A) Lungs", "B) Liver", "C) Kidney", "D) Heart"], "answer": "D", "explanation": "The heart pumps blood. Great!"},
            {"question": "What force pulls objects toward Earth?", "options": ["A) Magnetism", "B) Gravity", "C) Friction", "D) Tension"], "answer": "B", "explanation": "Gravity pulls all objects toward Earth!"},
            {"question": "What is the smallest unit of life?", "options": ["A) Atom", "B) Molecule", "C) Cell", "D) Tissue"], "answer": "C", "explanation": "The cell is the basic unit of life. Wonderful!"},
            {"question": "Which vitamin is produced by sunlight on skin?", "options": ["A) Vitamin A", "B) Vitamin B", "C) Vitamin C", "D) Vitamin D"], "answer": "D", "explanation": "Skin makes Vitamin D from sunlight!"},
            {"question": "What is H₂O commonly known as?", "options": ["A) Salt", "B) Water", "C) Acid", "D) Oxygen"], "answer": "B", "explanation": "H₂O is the formula for water. Brilliant!"},
            {"question": "What color does litmus paper turn in acid?", "options": ["A) Blue", "B) Green", "C) Red", "D) Yellow"], "answer": "C", "explanation": "Acid turns blue litmus paper red!"},
            {"question": "Which planet is known as the Blue Planet?", "options": ["A) Neptune", "B) Uranus", "C) Earth", "D) Saturn"], "answer": "C", "explanation": "Earth is called the Blue Planet due to water!"},
        ],
        "medium": [
            {"question": "What is Newton's Second Law of Motion?", "options": ["A) F=mv", "B) F=ma", "C) F=m/a", "D) F=a/m"], "answer": "B", "explanation": "Force = mass × acceleration. Classic physics!"},
            {"question": "What is the pH of a neutral solution?", "options": ["A) 0", "B) 7", "C) 14", "D) 5"], "answer": "B", "explanation": "pH 7 is neutral. Great thinking!"},
            {"question": "Which element has atomic number 6?", "options": ["A) Nitrogen", "B) Oxygen", "C) Carbon", "D) Helium"], "answer": "C", "explanation": "Carbon has atomic number 6. Excellent!"},
            {"question": "What type of bond forms in NaCl?", "options": ["A) Covalent", "B) Metallic", "C) Ionic", "D) Hydrogen"], "answer": "C", "explanation": "NaCl forms ionic bonds. Fantastic!"},
            {"question": "What is the powerhouse of the cell?", "options": ["A) Nucleus", "B) Ribosome", "C) Mitochondria", "D) Vacuole"], "answer": "C", "explanation": "Mitochondria produce ATP energy!"},
            {"question": "What is Ohm's Law?", "options": ["A) V=IR", "B) V=I/R", "C) V=I+R", "D) V=I-R"], "answer": "A", "explanation": "Voltage = Current × Resistance. Fantastic!"},
            {"question": "What is the speed of light in vacuum?", "options": ["A) 3×10⁶ m/s", "B) 3×10⁷ m/s", "C) 3×10⁸ m/s", "D) 3×10⁹ m/s"], "answer": "C", "explanation": "Light travels at 3×10⁸ m/s. Outstanding!"},
            {"question": "Which process converts glucose to energy in cells?", "options": ["A) Photosynthesis", "B) Respiration", "C) Digestion", "D) Transpiration"], "answer": "B", "explanation": "Cellular respiration converts glucose to ATP!"},
            {"question": "What is the chemical formula of common salt?", "options": ["A) NaOH", "B) KCl", "C) NaCl", "D) CaCl₂"], "answer": "C", "explanation": "Common salt is Sodium Chloride (NaCl)!"},
            {"question": "What law says energy cannot be created or destroyed?", "options": ["A) Newton's 1st", "B) Ohm's Law", "C) Law of Conservation", "D) Hooke's Law"], "answer": "C", "explanation": "Law of Conservation of Energy. Brilliant!"},
        ],
        "hard": [
            {"question": "What is the hybridization of carbon in benzene?", "options": ["A) sp", "B) sp²", "C) sp³", "D) sp³d"], "answer": "B", "explanation": "Benzene carbon is sp² hybridized!"},
            {"question": "Which enzyme unwinds DNA during replication?", "options": ["A) Ligase", "B) Polymerase", "C) Helicase", "D) Primase"], "answer": "C", "explanation": "Helicase unwinds the DNA double helix!"},
            {"question": "Heisenberg's uncertainty principle involves?", "options": ["A) Energy and time", "B) Position and momentum", "C) Mass and velocity", "D) Charge and spin"], "answer": "B", "explanation": "Position and momentum cannot both be precise!"},
            {"question": "What is the unit of radioactivity?", "options": ["A) Joule", "B) Tesla", "C) Becquerel", "D) Weber"], "answer": "C", "explanation": "Becquerel (Bq) is the SI unit of radioactivity!"},
            {"question": "What type of reaction is photosynthesis?", "options": ["A) Exothermic", "B) Endothermic", "C) Neutralization", "D) Combustion"], "answer": "B", "explanation": "Photosynthesis absorbs energy — endothermic!"},
            {"question": "What is the Krebs cycle related to?", "options": ["A) DNA replication", "B) Protein synthesis", "C) Cellular respiration", "D) Photosynthesis"], "answer": "C", "explanation": "Krebs cycle is part of cellular respiration!"},
        ],
    },
    "General Knowledge": {
        "easy": [
            {"question": "What is the capital of India?", "options": ["A) Mumbai", "B) Kolkata", "C) New Delhi", "D) Chennai"], "answer": "C", "explanation": "New Delhi is India's capital. Wonderful!"},
            {"question": "Who wrote the Indian National Anthem?", "options": ["A) Bankim Chandra", "B) Rabindranath Tagore", "C) Gandhi", "D) Nehru"], "answer": "B", "explanation": "Tagore wrote Jana Gana Mana. Brilliant!"},
            {"question": "What is the national animal of India?", "options": ["A) Lion", "B) Elephant", "C) Bengal Tiger", "D) Leopard"], "answer": "C", "explanation": "Bengal Tiger became national animal in 1973!"},
            {"question": "How many states are in India?", "options": ["A) 26", "B) 27", "C) 28", "D) 29"], "answer": "C", "explanation": "India has 28 states. Great!"},
            {"question": "What is the longest river in India?", "options": ["A) Yamuna", "B) Godavari", "C) Ganga", "D) Brahmaputra"], "answer": "C", "explanation": "The Ganga is India's longest river!"},
            {"question": "Who invented the telephone?", "options": ["A) Edison", "B) Tesla", "C) Bell", "D) Marconi"], "answer": "C", "explanation": "Alexander Graham Bell invented it in 1876!"},
            {"question": "What is the currency of Japan?", "options": ["A) Yuan", "B) Won", "C) Yen", "D) Ringgit"], "answer": "C", "explanation": "Japan's currency is the Yen. Excellent!"},
            {"question": "Which is the largest ocean on Earth?", "options": ["A) Atlantic", "B) Indian", "C) Arctic", "D) Pacific"], "answer": "D", "explanation": "The Pacific Ocean is the largest. Amazing!"},
            {"question": "Who was the first President of India?", "options": ["A) Nehru", "B) Rajendra Prasad", "C) Ambedkar", "D) Patel"], "answer": "B", "explanation": "Dr Rajendra Prasad was India's first President!"},
            {"question": "In which year did India gain independence?", "options": ["A) 1945", "B) 1946", "C) 1947", "D) 1948"], "answer": "C", "explanation": "India gained independence on 15 August 1947!"},
            {"question": "What is the national flower of India?", "options": ["A) Rose", "B) Sunflower", "C) Lotus", "D) Marigold"], "answer": "C", "explanation": "The Lotus is India's national flower!"},
            {"question": "Which country is the largest in the world by area?", "options": ["A) China", "B) USA", "C) Canada", "D) Russia"], "answer": "D", "explanation": "Russia is the world's largest country!"},
        ],
        "medium": [
            {"question": "Which article of Indian Constitution guarantees equality?", "options": ["A) Article 12", "B) Article 14", "C) Article 19", "D) Article 21"], "answer": "B", "explanation": "Article 14 guarantees equality before law!"},
            {"question": "Who founded the Indian National Congress in 1885?", "options": ["A) Gandhi", "B) Nehru", "C) A.O. Hume", "D) Tilak"], "answer": "C", "explanation": "Allan Octavian Hume founded INC in 1885!"},
            {"question": "Which Indian mission successfully orbited Mars?", "options": ["A) Chandrayaan", "B) Mangalyaan", "C) Aditya", "D) Gaganyaan"], "answer": "B", "explanation": "Mangalyaan reached Mars orbit in 2014!"},
            {"question": "Who is known as the Father of the Indian Constitution?", "options": ["A) Gandhi", "B) Nehru", "C) Ambedkar", "D) Patel"], "answer": "C", "explanation": "Dr B.R. Ambedkar is the Father of Constitution!"},
            {"question": "Which country is the largest producer of tea?", "options": ["A) India", "B) Sri Lanka", "C) China", "D) Kenya"], "answer": "C", "explanation": "China is the world's largest tea producer!"},
            {"question": "What is the headquarters of the United Nations?", "options": ["A) London", "B) Paris", "C) Geneva", "D) New York"], "answer": "D", "explanation": "UN headquarters is in New York City!"},
            {"question": "Which is the smallest country in the world?", "options": ["A) Monaco", "B) San Marino", "C) Vatican City", "D) Liechtenstein"], "answer": "C", "explanation": "Vatican City is the world's smallest country!"},
            {"question": "What does GDP stand for?", "options": ["A) Gross Domestic Product", "B) General Domestic Production", "C) Gross Direct Product", "D) General Direct Production"], "answer": "A", "explanation": "GDP = Gross Domestic Product. Excellent!"},
            {"question": "Which planet is known as the Red Planet?", "options": ["A) Jupiter", "B) Saturn", "C) Mars", "D) Venus"], "answer": "C", "explanation": "Mars appears red due to iron oxide!"},
            {"question": "Who gave the theory of relativity?", "options": ["A) Newton", "B) Einstein", "C) Bohr", "D) Hawking"], "answer": "B", "explanation": "Albert Einstein gave the theory of relativity!"},
        ],
        "hard": [
            {"question": "What is the Preamble to India's Constitution also called?", "options": ["A) Soul of Constitution", "B) Heart of Constitution", "C) Identity of Constitution", "D) Key of Constitution"], "answer": "A", "explanation": "Preamble is the Soul of the Constitution!"},
            {"question": "Which summit led to the Paris Climate Agreement?", "options": ["A) COP20", "B) COP21", "C) COP22", "D) COP19"], "answer": "B", "explanation": "COP21 in Paris produced the climate accord!"},
            {"question": "Which Indian state has the highest literacy rate?", "options": ["A) Tamil Nadu", "B) Maharashtra", "C) Kerala", "D) Himachal Pradesh"], "answer": "C", "explanation": "Kerala consistently leads India in literacy!"},
            {"question": "What is the G20 primarily focused on?", "options": ["A) Military alliances", "B) Economic cooperation", "C) Cultural exchange", "D) Space exploration"], "answer": "B", "explanation": "G20 focuses on global economic cooperation!"},
            {"question": "What does BRICS stand for?", "options": ["A) Brazil Russia India China South Africa", "B) Britain Russia India China Singapore", "C) Brazil Russia Italy China South Africa", "D) Brazil Russia India Canada Singapore"], "answer": "A", "explanation": "BRICS = Brazil, Russia, India, China, South Africa!"},
            {"question": "Which article of Indian Constitution abolishes untouchability?", "options": ["A) Article 14", "B) Article 15", "C) Article 17", "D) Article 21"], "answer": "C", "explanation": "Article 17 abolishes untouchability. Incredible!"},
        ],
    },
}

# ─────────────────────────────────────────
#  HELPERS
# ─────────────────────────────────────────
def render_flow_meter(score):
    if score < 35:
        state, color, emoji = "BORED", "#6af7b8", "😴"
    elif score < 70:
        state, color, emoji = "FLOW STATE 🌊", "#7c6af7", "🌊"
    else:
        state, color, emoji = "OVERWHELMED", "#f76a6a", "😰"
    st.markdown(f"""
    <div class="flow-meter-wrap">
        <div style="display:flex; justify-content:space-between; align-items:center;">
            <span style="font-family:'Space Mono',monospace; font-size:0.8rem; color:#6b6b80;">FLOW METER</span>
            <span style="font-weight:700; color:{color};">{emoji} {state}</span>
        </div>
        <div class="flow-bar-bg">
            <div class="flow-bar-fill" style="width:{score}%; background:linear-gradient(90deg,#6af7b8,{color});"></div>
        </div>
        <div style="display:flex; justify-content:space-between; font-size:0.75rem; color:#6b6b80;">
            <span>😴 Bored</span><span>🌊 Flow</span><span>😰 Overwhelmed</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

def update_flow_score(is_correct, score):
    new = min(100, score + 12) if is_correct else max(0, score - 8)
    if new > 75: new = max(65, new - 5)
    if new < 25: new = min(35, new + 5)
    return new

REWARD_MESSAGES = {
    "correct": ["🎉 Brilliant! You nailed it!", "⚡ Excellent! Keep going!", "🔥 That's exactly right!", "🌟 Perfect! You're in flow!", "💥 Unstoppable! On fire!"],
    "wrong":   ["💡 Great attempt! Here's the key:", "👏 Brave try! Every mistake teaches:", "🧩 Almost there! Let's understand:", "🌱 Learning in progress! Here's why:", "✨ Good effort! The answer shows:"],
}

def get_next_question(subject, level):
    """Get next unique question — tries Gemini first, falls back to bank."""
    diff_map = {"beginner": "easy", "moderate": "medium", "advanced": "hard"}
    diff = diff_map.get(level, "medium")

    # Get asked questions list
    asked = st.session_state.get("asked_questions", [])

    # Try bank first (always reliable)
    pool = QUESTION_BANK.get(subject, QUESTION_BANK["General Knowledge"])
    questions = pool.get(diff, pool["medium"])
    available = [q for q in questions if q["question"] not in asked]

    # If bank is exhausted, try Gemini for fresh question
    if not available:
        diff_text = {"easy": "Class 6-7, simple", "medium": "Class 9-10, moderate", "hard": "Class 11-12, challenging"}[diff]
        seed = random.randint(1000, 99999)
        prompt = f"""Generate ONE MCQ for {subject}, difficulty: {diff_text}, seed:{seed}.
Return ONLY JSON: {{"question":"text","options":["A) o1","B) o2","C) o3","D) o4"],"answer":"A","explanation":"short encouragement"}}"""
        raw = ask_gemini(prompt)
        if raw:
            try:
                raw = raw.replace("```json","").replace("```","").strip()
                s, e = raw.find("{"), raw.rfind("}")+1
                if s != -1 and e > s:
                    result = json.loads(raw[s:e])
                    if "question" in result and "options" in result:
                        return result
            except Exception:
                pass
        # Reset and reuse bank if all exhausted
        available = questions

    # Pick random unused question
    chosen = random.choice(available)
    return dict(chosen)  # return a copy

def generate_level_questions(subject):
    """Generate 3 level detection questions."""
    diff_map = {
        "Mathematics": [
            {"q": "What is 15% of 100?", "options": ["A) 10", "B) 15", "C) 20", "D) 25"], "answer": "B"},
            {"q": "Solve: 2x + 4 = 12. What is x?", "options": ["A) 3", "B) 4", "C) 5", "D) 6"], "answer": "B"},
            {"q": "What is the derivative of x²?", "options": ["A) x", "B) 2x", "C) x²", "D) 2x²"], "answer": "B"},
        ],
        "Science": [
            {"q": "What gas do plants absorb in photosynthesis?", "options": ["A) Oxygen", "B) Nitrogen", "C) CO₂", "D) Hydrogen"], "answer": "C"},
            {"q": "What is Newton's 2nd law?", "options": ["A) F=mv", "B) F=ma", "C) F=m/a", "D) F=v/t"], "answer": "B"},
            {"q": "What is the hybridization of carbon in benzene?", "options": ["A) sp", "B) sp²", "C) sp³", "D) sp³d"], "answer": "B"},
        ],
        "General Knowledge": [
            {"q": "What is the capital of India?", "options": ["A) Mumbai", "B) Kolkata", "C) New Delhi", "D) Chennai"], "answer": "C"},
            {"q": "Who founded INC in 1885?", "options": ["A) Gandhi", "B) Nehru", "C) A.O. Hume", "D) Tilak"], "answer": "C"},
            {"q": "What is the Preamble also called?", "options": ["A) Soul of Constitution", "B) Heart of Constitution", "C) Key of Constitution", "D) Identity of Constitution"], "answer": "A"},
        ],
    }
    return diff_map.get(subject, diff_map["General Knowledge"])

# ─────────────────────────────────────────
#  MOODS
# ─────────────────────────────────────────
MOODS = {
    "😊 Energetic": {"label": "Energetic", "hint": "normal", "msg": "Amazing! Let's channel that energy into deep learning!"},
    "😴 Tired":     {"label": "Tired",     "hint": "easy",   "msg": "No worries! We'll start easy and build up gently."},
    "🎯 Focused":   {"label": "Focused",   "hint": "normal", "msg": "Focus mode ON! Perfect state for learning."},
    "😰 Stressed":  {"label": "Stressed",  "hint": "easy",   "msg": "Take a breath. We'll ease you in with confidence-builders."},
}

# ─────────────────────────────────────────
#  SCREEN 1: WELCOME
# ─────────────────────────────────────────
def screen_welcome():
    st.markdown("""
    <div class="hero">
        <h1>🧠 <span class="accent-text">NeuroFlow</span></h1>
        <p class="tagline">The AI tutor that keeps you in your peak learning state.</p>
        <p style="color:#6b6b80; font-size:0.9rem;">Powered by Google Gemini AI &nbsp;·&nbsp; SDG 4: Quality Education</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="nf-card">', unsafe_allow_html=True)
    st.markdown("**🔑 Enter your Gemini API Key**")
    st.markdown('<p style="color:#6b6b80; font-size:0.85rem;">Get it free at aistudio.google.com — never stored beyond this session.</p>', unsafe_allow_html=True)
    api_key = st.text_input("API Key", type="password", placeholder="AIzaSy...", label_visibility="collapsed")
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="nf-card">', unsafe_allow_html=True)
    st.markdown("**📚 Choose your subject**")
    subject = st.selectbox("Subject", ["Mathematics", "Science", "General Knowledge"], label_visibility="collapsed")
    st.markdown('</div>', unsafe_allow_html=True)

    if st.session_state["streak"] > 0:
        st.markdown(f'<div style="text-align:center; margin-bottom:1rem;"><span style="font-size:1.5rem;">🔥</span><span style="font-family:Space Mono,monospace; color:#f7c06a;"> {st.session_state["streak"]} day streak!</span></div>', unsafe_allow_html=True)

    if st.button("🚀 Start Learning"):
        if not api_key:
            st.error("Please enter your Gemini API Key to continue.")
        else:
            st.session_state["api_key"] = api_key
            st.session_state["subject"] = subject
            st.session_state["gemini_ready"] = True  # trust the key, validate on first use
            st.session_state["screen"] = "mood"
            st.rerun()

# ─────────────────────────────────────────
#  SCREEN 2: MOOD
# ─────────────────────────────────────────
def screen_mood():
    st.markdown('<div class="progress-dots"><div class="dot active"></div><div class="dot"></div><div class="dot"></div></div>', unsafe_allow_html=True)
    st.markdown("## How are you feeling right now?")
    st.markdown('<p style="color:#6b6b80;">This helps NeuroFlow set the right starting pace for you.</p>', unsafe_allow_html=True)
    cols = st.columns(2)
    for i, (mood_key, mood_data) in enumerate(MOODS.items()):
        with cols[i % 2]:
            if st.button(mood_key, key=f"mood_{i}"):
                st.session_state["mood"] = mood_key
                st.session_state["level_detect_questions"] = []
                st.session_state["level_q_index"] = 0
                st.session_state["level_answers"] = []
                st.session_state["screen"] = "level_detect"
                st.rerun()

# ─────────────────────────────────────────
#  SCREEN 3: LEVEL DETECT
# ─────────────────────────────────────────
def screen_level_detect():
    st.markdown('<div class="progress-dots"><div class="dot done"></div><div class="dot active"></div><div class="dot"></div></div>', unsafe_allow_html=True)
    subject = st.session_state["subject"]

    if not st.session_state["level_detect_questions"]:
        st.session_state["level_detect_questions"] = generate_level_questions(subject)

    questions = st.session_state["level_detect_questions"]
    idx = st.session_state["level_q_index"]

    if idx >= len(questions):
        correct = sum(1 for a in st.session_state["level_answers"] if a)
        level = "beginner" if correct <= 1 else "moderate" if correct == 2 else "advanced"
        mood_data = MOODS.get(st.session_state["mood"], {})
        if mood_data.get("hint") == "easy" and level == "advanced":
            level = "moderate"
        st.session_state["level"] = level

        badge_class = level
        st.markdown(f"""
        <div style="text-align:center; padding:2rem 0;">
            <div style="font-size:3rem; margin-bottom:1rem;">🎯</div>
            <h2>Your Level: <span class="level-badge {badge_class}">{level.upper()}</span></h2>
            <p style="color:#6b6b80; margin-top:0.75rem;">{mood_data.get('msg','')}</p>
        </div>
        """, unsafe_allow_html=True)

        if st.button("🚀 Start My Learning Session →"):
            st.session_state.update({"screen": "session", "q_count": 0, "session_points": 0,
                "correct_count": 0, "flow_score": 50, "current_question": None,
                "answer_submitted": False, "asked_questions": [], "asked_topics": []})
            st.rerun()
        return

    q = questions[idx]
    st.markdown(f"### 🔍 Level Check — Question {idx+1} of {len(questions)}")
    st.markdown('<p style="color:#6b6b80; font-size:0.9rem;">Answer honestly — this helps us find YOUR perfect level.</p>', unsafe_allow_html=True)
    st.markdown(f'<div class="question-card"><strong>{q["q"]}</strong></div>', unsafe_allow_html=True)

    for opt in q["options"]:
        if st.button(opt, key=f"lvl_{idx}_{opt}"):
            is_correct = opt[0] == q["answer"]
            st.session_state["level_answers"].append(is_correct)
            st.session_state["level_q_index"] += 1
            st.rerun()

# ─────────────────────────────────────────
#  SCREEN 4: SESSION
# ─────────────────────────────────────────
def screen_session():
    subject = st.session_state["subject"]
    level = st.session_state["level"] or "beginner"
    q_count = st.session_state["q_count"]
    badge_class = level

    st.markdown(f"""
    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.75rem;">
        <div>
            <span class="level-badge {badge_class}">{level.upper()}</span>
            <span style="margin-left:0.75rem; color:#6b6b80; font-size:0.9rem;">{subject}</span>
        </div>
        <div style="font-family:'Space Mono',monospace; color:#f7c06a; font-size:0.9rem;">
            🔥 {st.session_state['streak']} streak &nbsp; ⭐ {st.session_state['session_points']} pts
        </div>
    </div>
    """, unsafe_allow_html=True)

    render_flow_meter(st.session_state["flow_score"])

    if st.session_state["current_question"] is None:
        with st.spinner("🤖 Generating your next question..."):
            q = get_next_question(subject, level)
            st.session_state["asked_questions"].append(q.get("question", ""))
            st.session_state["current_question"] = q
            st.session_state["answer_submitted"] = False
            st.session_state["last_result"] = None
            st.rerun()

    q = st.session_state["current_question"]

    if not st.session_state["answer_submitted"]:
        st.markdown(f"""
        <div class="question-card">
            <div style="font-size:0.75rem; font-family:'Space Mono',monospace; color:#6b6b80; margin-bottom:0.5rem;">
                Q{q_count + 1} &nbsp;·&nbsp; {subject.upper()}
            </div>
            <div style="font-size:1.1rem; font-weight:500; line-height:1.6;">{q['question']}</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("**Choose your answer:**")
        cols = st.columns(2)
        for i, opt in enumerate(q.get("options", [])):
            with cols[i % 2]:
                if st.button(opt, key=f"ans_{q_count}_{i}"):
                    is_correct = opt[0] == q.get("answer", "A")
                    st.session_state["answer_submitted"] = True
                    st.session_state["last_result"] = "correct" if is_correct else "wrong"
                    st.session_state["current_answer"] = opt
                    if is_correct:
                        st.session_state["session_points"] += 10
                        st.session_state["correct_count"] += 1
                    st.session_state["flow_score"] = update_flow_score(is_correct, st.session_state["flow_score"])
                    st.session_state["q_count"] += 1
                    st.rerun()
    else:
        result = st.session_state["last_result"]
        msgs = REWARD_MESSAGES[result]
        reward_msg = msgs[q_count % len(msgs)]
        explanation = q.get("explanation", "")
        correct_answer = q.get("answer", "")

        # YOU ARE THE TOPPER moment
        if st.session_state["correct_count"] > 0 and st.session_state["correct_count"] % 3 == 0 and result == "correct":
            st.markdown(f"""
            <div style="background:linear-gradient(135deg,rgba(247,192,106,0.15),rgba(124,106,247,0.15));
                border:2px solid #f7c06a; border-radius:16px; padding:1.5rem; text-align:center; margin-bottom:1rem;">
                <div style="font-size:2.5rem;">🏆</div>
                <div style="font-size:1.2rem; font-weight:800; color:#f7c06a; margin:0.5rem 0;">
                    RIGHT NOW — YOU ARE THE TOPPER!
                </div>
                <div style="color:#a8a8c0; font-size:0.9rem;">3 correct in a row! Your brain is absolutely on fire! 🔥</div>
            </div>
            """, unsafe_allow_html=True)
        elif result == "correct":
            st.markdown(f"""
            <div class="reward-correct">
                <div style="font-size:2rem; margin-bottom:0.5rem;">✅</div>
                <div style="font-size:1.1rem; font-weight:700; color:#6af7b8;">{reward_msg}</div>
                <div style="color:#a8a8c0; margin-top:0.5rem; font-size:0.9rem;">{explanation}</div>
                <div style="margin-top:0.5rem; font-family:'Space Mono',monospace; color:#f7c06a; font-size:0.9rem;">+10 pts ⭐</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="reward-wrong">
                <div style="font-size:2rem; margin-bottom:0.5rem;">💡</div>
                <div style="font-size:1.1rem; font-weight:700; color:#f7c06a;">{reward_msg}</div>
                <div style="color:#a8a8c0; margin-top:0.5rem; font-size:0.9rem;">{explanation}</div>
                <div style="margin-top:0.5rem; color:#6b6b80; font-size:0.85rem;">Correct answer: <strong style="color:#f7c06a;">{correct_answer}</strong></div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("")
        col1, col2 = st.columns([2, 1])
        with col1:
            if st.button("➡️ Next Question", key="next_q"):
                st.session_state["current_question"] = None
                st.session_state["answer_submitted"] = False
                st.rerun()
        with col2:
            if st.button("🏁 End Session", key="end_session"):
                st.session_state["streak"] += 1
                st.session_state["screen"] = "result"
                st.rerun()

# ─────────────────────────────────────────
#  SCREEN 5: RESULTS
# ─────────────────────────────────────────
def screen_result():
    q_total = st.session_state["q_count"]
    correct = st.session_state["correct_count"]
    points = st.session_state["session_points"]
    streak = st.session_state["streak"]
    accuracy = int(correct / q_total * 100) if q_total > 0 else 0

    if accuracy >= 80:
        perf_msg, perf_color = "🚀 Outstanding! You're mastering this!", "#6af7b8"
    elif accuracy >= 50:
        perf_msg, perf_color = "🌊 Great session! You're building momentum!", "#7c6af7"
    else:
        perf_msg, perf_color = "🌱 Every session makes you stronger. Keep going!", "#f7c06a"

    st.markdown(f"""
    <div style="text-align:center; padding:1.5rem 0 1rem;">
        <div style="font-size:3rem;">🏆</div>
        <h2 style="margin:0.5rem 0;">Session Complete!</h2>
        <p style="color:{perf_color}; font-weight:600;">{perf_msg}</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div class="score-card">
        <div class="score-num">{accuracy}%</div>
        <div style="color:#6b6b80; margin:0.5rem 0 1.5rem; font-size:0.9rem;">accuracy</div>
        <div style="display:flex; justify-content:center; gap:2rem;">
            <div><div style="font-family:'Space Mono',monospace; font-size:1.4rem; color:#f7c06a;">{points}</div><div style="color:#6b6b80; font-size:0.8rem;">points</div></div>
            <div><div style="font-family:'Space Mono',monospace; font-size:1.4rem; color:#7c6af7;">{q_total}</div><div style="color:#6b6b80; font-size:0.8rem;">questions</div></div>
            <div><div style="font-family:'Space Mono',monospace; font-size:1.4rem; color:#f76a6a;">🔥{streak}</div><div style="color:#6b6b80; font-size:0.8rem;">day streak</div></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("")
    level = st.session_state["level"]
    if accuracy >= 80 and level == "beginner":
        st.info("🎯 You're ready to level up! Try **Moderate** next session.")
    elif accuracy < 40 and level == "advanced":
        st.info("💡 Let's consolidate. Try **Moderate** level next session.")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 New Session"):
            for k in ["current_question","answer_submitted","last_result","q_count",
                      "correct_count","session_points","flow_score","level_detect_questions",
                      "level_q_index","level_answers","mood","level","asked_questions","asked_topics"]:
                st.session_state[k] = defaults.get(k)
            st.session_state["flow_score"] = 50
            st.session_state["screen"] = "mood"
            st.rerun()
    with col2:
        if st.button("🏠 Home"):
            for k in defaults:
                st.session_state[k] = defaults[k]
            st.session_state["screen"] = "welcome"
            st.rerun()

# ─────────────────────────────────────────
#  ROUTER
# ─────────────────────────────────────────
screen = st.session_state["screen"]
if screen == "welcome":     screen_welcome()
elif screen == "mood":      screen_mood()
elif screen == "level_detect": screen_level_detect()
elif screen == "session":   screen_session()
elif screen == "result":    screen_result()
