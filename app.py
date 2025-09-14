import streamlit as st
from datetime import datetime
import requests
# --- MODIFIED IMPORT ---
from google_trans_new import google_translator
import json
import os

# --- Page Configuration ---
st.set_page_config(
    page_title="My Reading Journal",
    page_icon="📚",
    layout="wide"
)

# --- Data Persistence ---
DATA_FILE = "journal_data.json"

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {"books": {}}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

# --- Session State Initialization ---
if 'journal' not in st.session_state:
    st.session_state.journal = load_data()
if 'current_book_title' not in st.session_state:
    book_titles = list(st.session_state.journal['books'].keys())
    st.session_state.current_book_title = book_titles[0] if book_titles else None

def update_book_details():
    save_data(st.session_state.journal)
    
# --- Language Data for New Library ---
# The new library doesn't provide a built-in dictionary, so we'll create one.
LANGUAGES = {
    'hindi': 'hi', 'spanish': 'es', 'french': 'fr', 'german': 'de', 
    'japanese': 'ja', 'russian': 'ru', 'chinese (simplified)': 'zh-cn'
}

# --- Sidebar ---
st.sidebar.title("My Book Collection")
book_titles = list(st.session_state.journal['books'].keys())
if book_titles:
    current_index = book_titles.index(st.session_state.current_book_title) if st.session_state.current_book_title in book_titles else 0
    st.session_state.current_book_title = st.sidebar.selectbox(
        "Select a book to view your notes:",
        options=book_titles,
        index=current_index
    )
st.sidebar.markdown("---")
st.sidebar.subheader("Add a New Book")
new_book_title = st.sidebar.text_input("Title")
new_book_author = st.sidebar.text_input("Author")
if st.sidebar.button("Add Book"):
    if new_book_title and new_book_author:
        if new_book_title not in st.session_state.journal['books']:
            st.session_state.journal['books'][new_book_title] = {
                "author": new_book_author, "current_page": 0, "total_pages": 100, "notes": []
            }
            save_data(st.session_state.journal)
            st.session_state.current_book_title = new_book_title
            st.rerun()
        else:
            st.sidebar.warning("This book already exists in your journal.")
    else:
        st.sidebar.error("Please provide both a title and an author.")

if st.session_state.current_book_title:
    st.sidebar.markdown("---")
    st.sidebar.subheader("Reading Progress")
    current_book = st.session_state.journal['books'][st.session_state.current_book_title]
    current_book['current_page'] = st.sidebar.number_input(
        "Current Page", min_value=0, value=current_book['current_page'], 
        key=f"current_page_{st.session_state.current_book_title}", on_change=update_book_details
    )
    current_book['total_pages'] = st.sidebar.number_input(
        "Total Pages", min_value=1, value=current_book['total_pages'],
        key=f"total_pages_{st.session_state.current_book_title}", on_change=update_book_details
    )
    if current_book['total_pages'] > 0:
        progress_percentage = current_book['current_page'] / current_book['total_pages']
        st.sidebar.progress(progress_percentage)
        st.sidebar.write(f"{current_book['current_page']} of {current_book['total_pages']} pages read ({progress_percentage:.0%})")

# --- Main Page Content ---
if not st.session_state.current_book_title:
    st.title("📚 Welcome to Your Personal Reading Journal")
    st.info("Add a book in the sidebar to get started!")
else:
    current_book_data = st.session_state.journal['books'][st.session_state.current_book_title]
    st.title(f"📖 {st.session_state.current_book_title}")
    st.subheader(f"by {current_book_data['author']}")
    col1, col2 = st.columns([2, 1.5])
    with col1:
        st.header("My Analysis & Lessons Learned")
        note_text = st.text_area("What new insights did you gain?", height=200, placeholder="Write your thoughts here...", key=f"note_{st.session_state.current_book_title}")
        if st.button("Add Note to Journal", type="primary"):
            if note_text:
                timestamp = datetime.now().strftime("%B %d, %Y at %I:%M %p")
                current_book_data['notes'].append({"text": note_text, "ts": timestamp})
                save_data(st.session_state.journal)
                st.success("Your note has been successfully saved!")
            else:
                st.warning("Please write a note before saving.")
        st.markdown("---")
        st.subheader("My Journal Entries")
        if not current_book_data['notes']:
            st.write("Your saved notes for this book will appear here.")
        else:
            for note in reversed(current_book_data['notes']):
                with st.container(border=True):
                    st.write(note["text"])
                    st.caption(f"*Saved on: {note['ts']}*")
    with col2:
        st.header("Quick Word Lookup")
        st.write("Get definitions and translations instantly, right here.")
        word_to_lookup = st.text_input("Enter a word to look up:")
        if word_to_lookup:
            st.subheader("Definition (English)")
            if st.button("Get Definition"):
                api_url = f"https://api.dictionaryapi.dev/api/v2/entries/en/{word_to_lookup}"
                with st.spinner(f"Looking up '{word_to_lookup}'..."):
                    response = requests.get(api_url)
                    if response.status_code == 200:
                        data = response.json()[0]
                        st.write(f"**Word:** {data.get('word', 'N/A')}")
                        if 'phonetic' in data: st.write(f"**Phonetic:** {data.get('phonetic', 'N/A')}")
                        for meaning in data.get('meanings', []):
                            st.markdown("---")
                            st.write(f"**Part of Speech:** {meaning.get('partOfSpeech', 'N/A')}")
                            for i, definition_info in enumerate(meaning.get('definitions', [])):
                                st.write(f"{i+1}. {definition_info.get('definition', 'No definition available.')}")
                    else:
                        st.error("Word not found. Please check the spelling and try again.")
            st.markdown("---")
            st.subheader("Translation")
            lang_names = list(LANGUAGES.keys())
            target_language_name = st.selectbox("Translate to:", options=lang_names, index=0)
            if st.button(f"Translate to {target_language_name.capitalize()}"):
                target_code = LANGUAGES[target_language_name]
                with st.spinner("Translating..."):
                    try:
                        # --- MODIFIED TRANSLATOR USAGE ---
                        translator = google_translator()
                        translation = translator.translate(word_to_lookup, lang_tgt=target_code)
                        st.success(f"**Translation:** {translation}")
                    except Exception as e:
                        st.error(f"Translation failed. Error: {e}")

