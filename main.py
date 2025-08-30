import streamlit as st
import os
import random
import json
from docx import Document
from docx.shared import Pt
import io
import time
import re

# --- Page Setup ---
st.set_page_config(
    page_title="English Test Generator",
    page_icon="📄",
    layout="wide"
)

# --- Logic Constants and Functions ---
BOOKS_DIR = "BOOKS"
SECTIONS = ["GRAMMAR", "VOCABULARY", "PRONUNCIATION"]
DEFAULT_QUESTIONS = {"grammar": 3, "vocabulary": 3, "pronunciation": 2}


def setup_test_environment():
    """
    Creates a test directory and file structure in JSON format.
    This is for demonstration purposes if the BOOKS directory is missing.
    """
    if not os.path.exists(BOOKS_DIR):
        st.info("Creating test environment with .json files... Please reload the page in a few seconds.")
        
        sample_question_data = {
            "questions": [
                {
                    "type": "order_the_words",
                    "instructions": "Order the words to make questions.",
                    "example": "Example: work / do / you / where\nWhere do you work?",
                    "qa_pairs": [{"item": "1 do / what / you / do", "answer": "What do you do?"}]
                }
            ]
        }

        structure = {
            "Elementary": {"GRAMMAR": ["1A", "1B", "2A", "2C", "3A"], "VOCABULARY": ["1A", "2C", "3A"]},
            "Pre-Intermediate": {"GRAMMAR": ["1A", "1B", "1C"], "VOCABULARY": ["1A", "1B"]},
        }

        for book, sections in structure.items():
            for section, units in sections.items():
                for unit in units:
                    folder_name = f"{book}_{section}_Unit_{unit}"
                    path = os.path.join(BOOKS_DIR, book, section, folder_name)
                    os.makedirs(path, exist_ok=True)
                    
                    for i in range(1, 3):
                        file_name = f"{folder_name}_Questão_{i}.json"
                        file_path = os.path.join(path, file_name)
                        with open(file_path, 'w', encoding='utf-8') as f:
                            json.dump(sample_question_data, f, indent=2, ensure_ascii=False)
        st.rerun()

@st.cache_data
def get_available_books(directory: str) -> list:
    """Returns a list of directories (books) inside the main directory."""
    if not os.path.exists(directory): return []
    return [d for d in os.listdir(directory) if os.path.isdir(os.path.join(directory, d))]

@st.cache_data
def parse_available_units(book_name: str) -> dict:
    """
    Analyzes unit folders for a given book and separates them into a dictionary
    where keys are numeric parts and values are sets of alphabetical parts.
    Example: {'1': ['A', 'B'], '2': ['A', 'C']}
    """
    if not book_name: return {}
    
    parsed_units = {}
    book_path = os.path.join(BOOKS_DIR, book_name)
    
    for section in SECTIONS:
        section_path = os.path.join(book_path, section)
        if os.path.exists(section_path):
            for folder in os.listdir(section_path):
                try:
                    # Extracts the unit part from folder names like "Book_SECTION_Unit_1A"
                    unit_part_str = folder.split("_Unit_")[-1]
                    match = re.match(r"(\d+)([A-Za-z]*)", unit_part_str)
                    if match:
                        num_part, alpha_part = match.groups()
                        if num_part not in parsed_units:
                            parsed_units[num_part] = set()
                        if alpha_part:
                            parsed_units[num_part].add(alpha_part.upper())
                except Exception:
                    # Silently ignore folders that don't match the pattern
                    continue
                    
    # Convert sets to sorted lists for consistent ordering
    for num_part in parsed_units:
        parsed_units[num_part] = sorted(list(parsed_units[num_part]))

    return parsed_units

def write_question_to_doc(doc, question_data, question_number):
    """
    Formats and writes a single question to the docx document based on its type.
    """
    # Write question number and instructions
    p_question_num = doc.add_paragraph()
    p_question_num.add_run(f"{question_number}. ").bold = True
    p_question_num.add_run(question_data.get("instructions", "")).bold = True
    
    # Write example if it exists
    if question_data.get("example"):
        doc.add_paragraph(question_data.get("example", ""))
    
    doc.add_paragraph()

    # --- Conditional Formatting based on Question Type ---
    q_type = question_data.get("type")

    if q_type == "fill_in_from_word_bank":
        options = question_data.get("options", [])
        if options:
            doc.add_paragraph(f"Options: {', '.join(options)}")
            doc.add_paragraph()
        for pair in question_data.get("qa_pairs", []):
            doc.add_paragraph(pair.get("item", ""))

    elif q_type == "multiple_choice":
        for pair in question_data.get("qa_pairs", []):
            item_text = pair.get("item", "")
            options_text = f"({ ' / '.join(pair.get('options', [])) })"
            doc.add_paragraph(f"{item_text} {options_text}")

    else: # Default formatting for other types (fill_in_the_blanks, order_the_words, etc.)
        for pair in question_data.get("qa_pairs", []):
            doc.add_paragraph(pair.get("item", ""))
            if q_type == "order_the_words":
                doc.add_paragraph("____________________________________")

    doc.add_paragraph()


def generate_exam_docx(book: str, units: list, questions_config: dict) -> io.BytesIO:
    """
    Generates a .docx document with numbered questions and an answer key at the end.
    """
    final_doc = Document()
    style = final_doc.styles['Normal']
    font = style.font
    font.name = 'Calibri'
    font.size = Pt(11)

    units_str = ", ".join(sorted(units))
    final_doc.add_heading(f"English Test - Book: {book} | Unit(s): {units_str}", level=0)
    final_doc.add_paragraph(f"Name: __________________________________________________ Date: ___/___/______")
    final_doc.add_paragraph()

    final_question_list = []
    for section, num_requested in questions_config.items():
        if num_requested <= 0:
            continue

        pool_for_this_section = []
        for unit in units:
            section_path = os.path.join(BOOKS_DIR, book, section.upper())
            if not os.path.exists(section_path):
                continue
            
            # Find all folders that end with the target unit string (e.g., "_Unit_1A")
            matching_folders = [f for f in os.listdir(section_path) if f.endswith(f"_Unit_{unit}")]
            
            for folder in matching_folders:
                unit_path = os.path.join(section_path, folder)
                for filename in [f for f in os.listdir(unit_path) if f.endswith('.json')]:
                    file_path = os.path.join(unit_path, filename)
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            for q in data.get("questions", []):
                                q['section'] = section
                                pool_for_this_section.append(q)
                    except Exception as e:
                        st.warning(f"Unable to read JSON file {filename}: {e}")

        # Pick random questions from the collected pool for the section
        num_to_pick = min(num_requested, len(pool_for_this_section))
        if num_to_pick > 0:
            chosen_questions = random.sample(pool_for_this_section, num_to_pick)
            final_question_list.extend(chosen_questions)

    if not final_question_list:
        final_doc.add_paragraph("No questions were found with the selected criteria.")
    else:
        question_counter = 1
        answer_key = []
        current_section = None

        # Sort questions by section to group them in the final document
        final_question_list.sort(key=lambda q: q['section'])

        for q_data in final_question_list:
            if q_data['section'] != current_section:
                current_section = q_data['section']
                final_doc.add_heading(f"Section: {current_section.capitalize()}", level=1)
            
            write_question_to_doc(final_doc, q_data, question_counter)
            
            answers_for_this_question = [pair.get("answer", "") for pair in q_data.get("qa_pairs", [])]
            answer_key.append({"number": question_counter, "answers": answers_for_this_question})
            question_counter += 1

        # Add the Answer Key at the end of the document
        final_doc.add_page_break()
        final_doc.add_heading("Answer Key (For Teacher's Use)", level=1)
        
        for item in answer_key:
            p_answer_header = final_doc.add_paragraph()
            p_answer_header.add_run(f"Question {item['number']}:").bold = True
            for i, answer in enumerate(item['answers']):
                final_doc.add_paragraph(f"{i+1}. {answer}", style='List Bullet')
            final_doc.add_paragraph()

    # Save the document to a byte stream in memory
    doc_io = io.BytesIO()
    final_doc.save(doc_io)
    doc_io.seek(0)
    return doc_io

# --- Streamlit Interface ---
st.title("CCB English Test Generator")
st.markdown("Accurate, fast, and simple. Just as your CCB studies should be.")

if not os.path.exists(BOOKS_DIR):
    st.warning(f"The `{BOOKS_DIR}` directory was not found.")
    if st.button("Click here to create a sample folder structure and .json files"):
        setup_test_environment()

# --- Sidebar for Configuration ---
with st.sidebar:
    st.header("📖 Test Configuration")
    books = get_available_books(BOOKS_DIR)
    if not books:
        st.error(f"No books found in the '{BOOKS_DIR}' directory.")
        st.stop()
    selected_book = st.selectbox("Choose Book", options=books, index=0)

    parsed_units = parse_available_units(selected_book)
    if not parsed_units:
        st.error(f"No units found for the book '{selected_book}'. Please check the folder structure.")
        st.stop()

    # --- MODIFIED SECTION: Granular Unit Selection ---
    st.markdown("---")
    st.subheader("🎯 Select Desired Units")
    
    final_selected_units = []
    sorted_numeric_units = sorted(parsed_units.keys(), key=int)

    for num_unit in sorted_numeric_units:
        alpha_units = parsed_units[num_unit]
        
        # Create an expandable container for each numeric unit
        with st.expander(f"Unit {num_unit}"):
            # Inside, a multiselect for its specific sub-units
            selected_alphas = st.multiselect(
                label=f"Select sub-units for Unit {num_unit}",
                options=alpha_units,
                default=alpha_units, # Pre-select all available sub-units
                key=f"multiselect_{selected_book}_{num_unit}" # Unique key is crucial
            )
            
            # Add the fully formed unit strings (e.g., "1A", "1B") to the final list
            for alpha in selected_alphas:
                final_selected_units.append(f"{num_unit}{alpha}")

    # --- End of Modified Section ---

    st.markdown("---")
    st.subheader("⚙️ Number of Questions per Section")
    
    questions_config = {
        "grammar": st.number_input("Grammar", min_value=0, max_value=50, value=DEFAULT_QUESTIONS["grammar"], step=1),
        "vocabulary": st.number_input("Vocabulary", min_value=0, max_value=50, value=DEFAULT_QUESTIONS["vocabulary"], step=1),
        "pronunciation": st.number_input("Pronunciation", min_value=0, max_value=50, value=DEFAULT_QUESTIONS["pronunciation"], step=1)
    }
    total_questions = sum(questions_config.values())
    st.info(f"**Total questions on the test: {total_questions}**")

# --- Main Page Display ---
if not final_selected_units:
    st.warning("Please select at least one unit from the sidebar to continue.")
    st.stop()

st.subheader("Configuration Summary")
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("**📖 Book**")
    st.markdown(f"`{selected_book}`")

with col2:
    units_display = ", ".join(sorted(final_selected_units))
    st.markdown("**📚 Selected Units**")
    st.markdown(f"`{units_display}`")

with col3:
    st.markdown("**⚙️ Questions per Section**")
    questions_summary = f"G: {questions_config['grammar']} | V: {questions_config['vocabulary']} | P: {questions_config['pronunciation']}"
    st.markdown(f"`{questions_summary}`")

st.markdown("---")

# Determine button text based on whether the configuration is default or custom
is_default_config = (
    questions_config["grammar"] == DEFAULT_QUESTIONS["grammar"] and
    questions_config["vocabulary"] == DEFAULT_QUESTIONS["vocabulary"] and
    questions_config["pronunciation"] == DEFAULT_QUESTIONS["pronunciation"]
)
button_text = "🚀 Generate Standard Test" if is_default_config else "🚀 Generate Custom Test"

# Initialize session state for storing generated exam data
if 'exam_data' not in st.session_state:
    st.session_state.exam_data = None

if st.button(button_text, type="primary", use_container_width=True, disabled=(total_questions == 0)):
    if total_questions > 0:
        with st.spinner("Reading JSON files and assembling your test..."):
            try:
                exam_bytes = generate_exam_docx(selected_book, final_selected_units, questions_config)
                st.session_state.exam_data = exam_bytes
                units_filename = "_".join(sorted(final_selected_units))
                st.session_state.exam_filename = f"Test_{selected_book}_Units_{units_filename}.docx"
                time.sleep(1) # Small delay for better UX
                st.success("Test generated successfully! Click the button below to download.")
            except Exception as e:
                st.error(f"An error occurred while generating the test: {e}")
                st.session_state.exam_data = None
    else:
        st.warning("Please select at least one question to generate the test.")

# Show download button if an exam has been generated and is in session state
if st.session_state.get('exam_data'):
    st.download_button(
        label="📥 Download Test (.docx)",
        data=st.session_state.exam_data,
        file_name=st.session_state.get('exam_filename', 'test.docx'),
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        use_container_width=True
    )

st.markdown("---")
st.markdown("Developed with ❤️ by CCB students")
