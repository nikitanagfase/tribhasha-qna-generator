"""
streamlit_app.py
-----------------
TriBhasha — Multilingual QnA Generator
Entry point for the app: theme, login/register, upload, generate, download.

Run with:  streamlit run streamlit_app.py
"""

import os
import base64
import tempfile
from pathlib import Path

import pandas as pd
import streamlit as st
from PIL import Image
from dotenv import load_dotenv

from app.extractor import extract_text, ExtractionError
from app.qna_generator import generate_qna_pairs, QnAGenerationError
from app.translator import translate_qna_pairs, TranslationError
from app.excel_writer import build_excel, ExcelBuildError
from auth.database import init_db, register_user, verify_user

load_dotenv()
init_db()

BASE_DIR = Path(__file__).parent
LOGO_HORIZONTAL = BASE_DIR / "assets" / "logo_horizontal.png"  # symbol + "TriBhasha", side by side
FAVICON = BASE_DIR / "assets" / "logo_favicon.png"             # symbol only, for the browser tab

try:
    _page_icon = Image.open(FAVICON) if FAVICON.exists() else "📘"
except Exception:
    _page_icon = "📘"

st.set_page_config(page_title="TriBhasha", page_icon=_page_icon, layout="wide")

# ---------------------------------------------------------------------------
# THEME
# Core colors (background/text/primary) live in .streamlit/config.toml so
# every native widget — tabs, buttons, sliders, inputs — picks them up
# automatically and stays consistent regardless of OS/browser dark mode.
# The CSS below only adds card layout, spacing and typography on top of that.
# ---------------------------------------------------------------------------
NAVY = "#172554"
BLUE = "#1E3A8A"
ORANGE = "#E8873A"
TEXT = "#1E293B"
TEXT_MUTED = "#64748B"
BORDER = "#E2E8F0"
CARD_BG = "#FFFFFF"

CUSTOM_CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

html, body, [class*="css"] {{
    font-family: 'Inter', 'Segoe UI', sans-serif !important;
}}

.block-container {{
    padding-top: 2rem;
    padding-bottom: 3rem;
    max-width: 1100px;
    margin-left: auto !important;
    margin-right: auto !important;
}}

/* Buttons (default/secondary — e.g. Logout) */
.stButton > button, .stDownloadButton > button {{
    border-radius: 10px;
    font-weight: 600;
    padding: 0.55rem 1.5rem;
    border: 1px solid {BORDER};
    transition: background-color 0.15s ease-in-out, border-color 0.15s ease-in-out;
}}
.stButton > button:hover, .stDownloadButton > button:hover {{
    background-color: {ORANGE} !important;
    border-color: {ORANGE} !important;
    color: white !important;
}}

/* Buttons marked type="primary" — Login, Register, Generate, Download */
.stButton > button[kind="primary"], .stDownloadButton > button[kind="primary"] {{
    background-color: {NAVY} !important;
    color: #FFFFFF !important;
    border: 1px solid {NAVY} !important;
}}
.stButton > button[kind="primary"]:hover, .stDownloadButton > button[kind="primary"]:hover {{
    background-color: {ORANGE} !important;
    border-color: {ORANGE} !important;
}}

/* Cards produced by st.container(border=True) — login/register/upload/preview panels */
div[data-testid="stVerticalBlockBorderWrapper"] {{
    background: {CARD_BG} !important;
    border: 1.5px solid {NAVY} !important;
    border-radius: 14px !important;
    box-shadow: 0 4px 16px rgba(23, 37, 84, 0.12) !important;
    transition: box-shadow 0.2s ease-in-out, border-color 0.2s ease-in-out;
}}
div[data-testid="stVerticalBlockBorderWrapper"]:hover {{
    border-color: {ORANGE} !important;
    box-shadow: 0 8px 24px rgba(23, 37, 84, 0.18) !important;
}}

/* Sidebar */
section[data-testid="stSidebar"] {{ background-color: {NAVY}; }}
section[data-testid="stSidebar"] * {{ color: #E7ECF7 !important; }}
section[data-testid="stSidebar"] img {{ display: block; margin: 0 auto 0.75rem auto; }}
section[data-testid="stSidebar"] hr {{ border-color: rgba(231,236,247,0.18); }}

/* Sidebar's own Logout button needs its own contrast — it sits on navy,
   so it gets a translucent "ghost" style instead of the white default. */
section[data-testid="stSidebar"] .stButton > button {{
    background-color: rgba(255,255,255,0.08) !important;
    border: 1px solid rgba(255,255,255,0.35) !important;
    color: #FFFFFF !important;
}}
section[data-testid="stSidebar"] .stButton > button:hover {{
    background-color: {ORANGE} !important;
    border-color: {ORANGE} !important;
    color: #FFFFFF !important;
}}
.sidebar-step {{
    background: rgba(255,255,255,0.06);
    border: 1px solid rgba(255,255,255,0.12);
    border-radius: 10px;
    padding: 0.5rem 0.8rem;
    margin-bottom: 0.5rem;
    font-size: 0.88rem;
}}
.sidebar-step b {{ color: {ORANGE} !important; margin-right: 0.4rem; }}

/* Hero banner */
.hero-banner {{
    background: linear-gradient(135deg, {NAVY} 0%, {BLUE} 100%);
    padding: 1.8rem 2.2rem;
    border-radius: 16px;
    margin-bottom: 1.6rem;
}}
.hero-banner h1 {{
    color: #FFFFFF !important;
    margin: 0 0 0.4rem 0;
    font-size: 1.85rem;
    font-weight: 800;
}}
.hero-banner p {{ color: #C9D6F2; margin: 0; font-size: 1.02rem; }}

/* Feature cards */
.feature-card {{
    background: {CARD_BG};
    border: 1px solid {BORDER};
    border-radius: 14px;
    padding: 1.2rem 1.3rem;
    box-shadow: 0 1px 3px rgba(23, 37, 84, 0.05);
    height: 100%;
}}
.feature-card .icon {{ font-size: 1.4rem; margin-bottom: 0.4rem; }}
.feature-card h4 {{ color: {NAVY}; margin: 0 0 0.25rem 0; font-size: 1.02rem; font-weight: 700; }}
.feature-card p {{ color: {TEXT_MUTED}; margin: 0; font-size: 0.9rem; }}

/* Language badge cards */
.lang-card {{
    background: {CARD_BG};
    border: 1px solid {BORDER};
    border-radius: 12px;
    padding: 0.75rem 0.5rem;
    text-align: center;
    box-shadow: 0 1px 2px rgba(23, 37, 84, 0.04);
}}
.lang-badge {{
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 34px; height: 34px;
    border-radius: 50%;
    font-weight: 700;
    font-size: 0.85rem;
    color: white;
    margin-bottom: 0.35rem;
}}
.lang-card p {{ margin: 0; color: {TEXT}; font-weight: 600; font-size: 0.88rem; }}

/* Auth screen heading + description */
.auth-eyebrow {{
    text-align: center;
    color: {ORANGE};
    font-weight: 700;
    font-size: 0.78rem;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    margin: 0.9rem 0 0.35rem 0;
}}
.auth-heading {{ text-align: center; color: {NAVY}; font-weight: 800; font-size: 1.55rem; margin: 0 0 0.5rem 0; }}
.auth-desc {{ text-align: center; color: {TEXT_MUTED}; font-size: 1rem; line-height: 1.5; margin: 0 0 1.6rem 0; }}

[data-testid="stFileUploaderDropzone"] {{ border-radius: 12px !important; }}
hr {{ border-color: {BORDER}; }}

/* st.image() is left-aligned inside its column by default — center it
   everywhere it's used (auth-screen logo, sidebar logo). */
div[data-testid="stImage"] {{ display: flex; justify-content: center; width: 100%; }}
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


@st.cache_data(show_spinner=False)
def _image_to_base64(path: str) -> str:
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def render_logo(width=170):
    """Renders the logo centered via raw HTML — guaranteed centering that
    doesn't depend on Streamlit's internal DOM structure (which can change
    between versions and silently break CSS selectors like [data-testid=...])."""
    if LOGO_HORIZONTAL.exists():
        b64 = _image_to_base64(str(LOGO_HORIZONTAL))
        st.markdown(
            f"""
            <div style="width:100%; display:flex; justify-content:center; margin-bottom:0.5rem;">
                <img src="data:image/png;base64,{b64}" width="{width}" />
            </div>
            """,
            unsafe_allow_html=True,
        )



# SESSION STATE
    
st.session_state.setdefault("logged_in", False)
st.session_state.setdefault("username", None)
st.session_state.setdefault("qna_result", None)



# AUTH SCREEN

def show_auth_screen():
    st.write("")
    left, center, right = st.columns([1, 1.3, 1])

    with center:
        render_logo(width=300)
        st.markdown('<p class="auth-eyebrow">Multilingual QnA Generator</p>', unsafe_allow_html=True)
        st.markdown('<p class="auth-heading">Turn documents into ready-to-use Q&amp;A</p>', unsafe_allow_html=True)
        st.markdown(
            '<p class="auth-desc">Upload an English PDF, DOCX or TXT file and get accurate '
            "Question–Answer pairs — instantly generated in English, Hindi and Marathi.</p>",
            unsafe_allow_html=True,
        )

        login_tab, register_tab = st.tabs(["Login", "Register"])

        with login_tab:
            with st.container(border=True):
                with st.form("login_form"):
                    username = st.text_input("Username")
                    password = st.text_input("Password", type="password")
                    submitted = st.form_submit_button(
                        "Login", use_container_width=True, type="primary"
                    )
                    if submitted:
                        ok, message = verify_user(username, password)
                        if ok:
                            st.session_state.logged_in = True
                            st.session_state.username = username.strip()
                            st.success(message)
                            st.rerun()
                        else:
                            st.error(message)

        with register_tab:
            with st.container(border=True):
                with st.form("register_form"):
                    new_username = st.text_input("Choose a username")
                    new_password = st.text_input("Choose a password", type="password")
                    confirm_password = st.text_input("Confirm password", type="password")
                    submitted = st.form_submit_button(
                        "Create account", use_container_width=True, type="primary"
                    )
                    if submitted:
                        if new_password != confirm_password:
                            st.error("Passwords do not match.")
                        else:
                            ok, message = register_user(new_username, new_password)
                            if ok:
                                st.success(message + " You can log in now.")
                            else:
                                st.error(message)


# MAIN APP
 
def save_uploaded_file(uploaded_file) -> str:
    suffix = os.path.splitext(uploaded_file.name)[1]
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(uploaded_file.getbuffer())
        return tmp.name


def _preview_df(pairs: list) -> pd.DataFrame:
    """Same data shown in the on-screen preview, just numbered from 1 instead
    of pandas' default 0-based index — purely cosmetic, the actual QnA.xlsx
    file already has no index column at all (see excel_writer.py)."""
    df = pd.DataFrame(pairs)
    df.index = df.index + 1
    return df


def show_main_app():
    with st.sidebar:
        render_logo(width=170)
        st.markdown(
            f"<div style='text-align:center; opacity:0.9; margin-bottom:0.8rem;'>"
            f"Logged in as <b>{st.session_state.username}</b></div>",
            unsafe_allow_html=True,
        )
        if st.button("Logout", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.username = None
            st.session_state.qna_result = None
            st.rerun()

        st.markdown("---")
        st.markdown("**HOW IT WORKS**")
        steps = [
            "Upload document",
            "Generate English QnA",
            "Translate to Hindi",
            "Translate to Marathi",
            "Download Excel",
        ]
        for i, step in enumerate(steps, start=1):
            st.markdown(
                f'<div class="sidebar-step"><b>{i:02d}</b>{step}</div>',
                unsafe_allow_html=True,
            )

    st.markdown(
        """
        <div class="hero-banner">
            <h1>Multilingual QnA Generator</h1>
            <p>Upload an English document and generate accurate Question–Answer pairs
            in English, Hindi and Marathi.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Feature cards
    f1, f2, f3 = st.columns(3)
    with f1:
        st.markdown(
            '<div class="feature-card"><div class="icon">📄</div>'
            "<h4>Document Input</h4><p>PDF • DOCX • TXT</p></div>",
            unsafe_allow_html=True,
        )
    with f2:
        st.markdown(
            '<div class="feature-card"><div class="icon">✨</div>'
            "<h4>Smart QnA</h4><p>Generate structured Question–Answer pairs</p></div>",
            unsafe_allow_html=True,
        )
    with f3:
        st.markdown(
            '<div class="feature-card"><div class="icon">🌐</div>'
            "<h4>Three Languages</h4><p>English • Hindi • Marathi</p></div>",
            unsafe_allow_html=True,
        )

    st.write("")

    # Language cards
    l1, l2, l3 = st.columns(3)
    for col, color, code, label in [
        (l1, NAVY, "EN", "English"),
        (l2, ORANGE, "हि", "Hindi"),
        (l3, BLUE, "मर", "Marathi"),
    ]:
        with col:
            st.markdown(
                f'<div class="lang-card"><div class="lang-badge" '
                f'style="background:{color};">{code}</div><p>{label}</p></div>',
                unsafe_allow_html=True,
            )

    st.write("")

    # Upload card
    with st.container(border=True):
        st.markdown(f"<h4 style='color:{NAVY}; margin-top:0;'>Upload your document</h4>", unsafe_allow_html=True)
        st.markdown(
            f"<p style='color:{TEXT_MUTED}; margin-top:-0.5rem;'>Upload an English document to "
            "generate multilingual Question–Answer pairs.</p>",
            unsafe_allow_html=True,
        )
        uploaded_file = st.file_uploader(
            "Upload document", type=["pdf", "docx", "txt"], label_visibility="collapsed"
        )
        num_pairs = st.slider("Number of QnA pairs", min_value=10, max_value=15, value=12)
        generate_clicked = st.button(
            "Generate Multilingual QnA",
            disabled=uploaded_file is None,
            use_container_width=True,
            type="primary",
        )

    if generate_clicked and uploaded_file is not None:
        temp_path = None
        try:
            with st.spinner("Reading document..."):
                temp_path = save_uploaded_file(uploaded_file)
                document_text = extract_text(temp_path)

            with st.spinner("Generating English QnA pairs..."):
                english_pairs = generate_qna_pairs(document_text, num_pairs=num_pairs)

            with st.spinner("Translating to Hindi..."):
                hindi_pairs = translate_qna_pairs(english_pairs, "hi")

            with st.spinner("Translating to Marathi..."):
                marathi_pairs = translate_qna_pairs(english_pairs, "mr")

            with st.spinner("Building QnA.xlsx..."):
                excel_bytes = build_excel(english_pairs, hindi_pairs, marathi_pairs)

            st.session_state.qna_result = {
                "english": english_pairs,
                "hindi": hindi_pairs,
                "marathi": marathi_pairs,
                "excel_bytes": excel_bytes,
            }
            st.success(f"Done! Generated {len(english_pairs)} QnA pairs in 3 languages.")

        except ExtractionError as e:
            st.error(f"Could not read the document: {e}")
        except QnAGenerationError as e:
            st.error(f"Could not generate QnA pairs: {e}")
        except TranslationError as e:
            st.error(f"Translation failed: {e}")
        except ExcelBuildError as e:
            st.error(f"Could not build the Excel file: {e}")
        except Exception as e:
            st.error(f"Something unexpected went wrong: {e}")
        finally:
            if temp_path and os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except OSError:
                    pass

    result = st.session_state.qna_result
    if result:
        st.write("")
        with st.container(border=True):
            st.markdown(f"<h4 style='color:{NAVY}; margin-top:0;'>Generated QnA Preview</h4>", unsafe_allow_html=True)
            eng_tab, hin_tab, mar_tab = st.tabs(["English", "Hindi", "Marathi"])
            with eng_tab:
                st.dataframe(_preview_df(result["english"]), use_container_width=True)
            with hin_tab:
                st.dataframe(_preview_df(result["hindi"]), use_container_width=True)
            with mar_tab:
                st.dataframe(_preview_df(result["marathi"]), use_container_width=True)

        st.write("")
        with st.container(border=True):
            st.markdown(
                f"<p style='color:{TEXT}; margin:0 0 0.7rem 0;'>Your multilingual QnA workbook is ready.</p>",
                unsafe_allow_html=True,
            )
            st.download_button(
                label="Download QnA.xlsx",
                data=result["excel_bytes"],
                file_name="QnA.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
                type="primary",
            )


#ROUTER
if not st.session_state.logged_in:
    show_auth_screen()
else:
    show_main_app()