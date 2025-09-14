import streamlit as st
from datetime import datetime
import requests
from googletrans import Translator, LANGUAGES
import json
import os

# --- Page Configuration ---
st.set_page_config(
    page_title="My Reading Journal",
    page_icon="📚",
    layout="wide"
)

# --- Data Persistence ---
# Define the file where we will store the journal data.
DATA_FILE = "journal_data.json"

def load_data():
    """Load the journal data from the JSON file."""
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    # If the file doesn't exist, return a default structure.
    return {"books": {}}

def save_data(data):
    """Save the journal data to the JSON file."""
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

# --- Session State Initialization ---
# Load all journal data into session state on the first run.
if 'journal' not in st.session_state:
    st.session_state.journal = load_data()

# Keep track of the currently selected book.
if 'current_book_title' not in st.session_state:
    # Set the first book as current, or None if the journal is empty.
    book_titles = list(st.session_state.journal['books'].keys())
    st.session_state.current_book_title = book_titles[0] if book_titles else None

def update_book_details():
    """Callback function to save data when book details are changed."""
    save_data(st.session_state.journal)

# --- Sidebar ---
st.sidebar.title("My Book Collection")

# Dropdown to select a book from the journal.
book_titles = list(st.session_state.journal['books'].keys())
if book_titles:
    # If a book is deleted, the old title might still be in session_state.
    # We check if the current title is still valid.
    current_index = book_titles.index(st.session_state.current_book_title) if st.session_state.current_book_title in book_titles else 0
    st.session_state.current_book_title = st.sidebar.selectbox(
        "Select a book to view your notes:",
        options=book_titles,
        index=current_index
    )

st.sidebar.markdown("---")

# Section to add a new book.
st.sidebar.subheader("Add a New Book")
new_book_title = st.sidebar.text_input("Title")
new_book_author = st.sidebar.text_input("Author")
if st.sidebar.button("Add Book"):
    if new_book_title and new_book_author:
        if new_book_title not in st.session_state.journal['books']:
            # Add new book with default values.
            st.session_state.journal['books'][new_book_title] = {
                "author": new_book_author,
                "current_page": 0,
                "total_pages": 100, # Default total pages
                "notes": []
            }
            save_data(st.session_state.journal)
            st.session_state.current_book_title = new_book_title # Switch to the new book
            st.rerun() # Rerun the app to update the selectbox and view
        else:
            st.sidebar.warning("This book already exists in your journal.")
    else:
        st.sidebar.error("Please provide both a title and an author.")

# --- Book Details and Progress Tracking (only if a book is selected) ---
if st.session_state.current_book_title:
    st.sidebar.markdown("---")
    st.sidebar.subheader("Reading Progress")
    
    current_book = st.session_state.journal['books'][st.session_state.current_book_title]

    # Use a key to link the number input to the specific book's data.
    current_book['current_page'] = st.sidebar.number_input(
        "Current Page", min_value=0, 
        value=current_book['current_page'], 
        key=f"current_page_{st.session_state.current_book_title}",
        on_change=update_book_details # Save data whenever this changes
    )
    current_book['total_pages'] = st.sidebar.number_input(
        "Total Pages", min_value=1, 
        value=current_book['total_pages'],
        key=f"total_pages_{st.session_state.current_book_title}",
        on_change=update_book_details # Save data whenever this changes
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

    # --- Column 1: Analysis and Note-Taking ---
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

    # --- Column 2: Word Lookup Tool ---
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
            lang_names = list(LANGUAGES.values())
            default_index = lang_names.index("hindi") if "hindi" in lang_names else 0
            target_language_name = st.selectbox("Translate to:", options=lang_names, index=default_index)
            if st.button(f"Translate to {target_language_name.capitalize()}"):
                target_code = [code for code, name in LANGUAGES.items() if name == target_language_name.lower()][0]
                with st.spinner("Translating..."):
                    try:
                        translator = Translator()
                        translation = translator.translate(word_to_lookup, dest=target_code)
                        st.success(f"**Translation:** {translation.text}")
                    except Exception as e:
                        st.error("Translation failed. Please try again.")

