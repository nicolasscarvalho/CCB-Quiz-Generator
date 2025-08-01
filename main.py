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
            "Elementary": {"GRAMMAR": ["1A", "1B", "2A", "3A"], "VOCABULARY": ["1A", "2B", "3A"]},
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
    if not os.path.exists(directory): return []
    return [d for d in os.listdir(directory) if os.path.isdir(os.path.join(directory, d))]

@st.cache_data
def parse_available_units(book_name: str) -> dict:
    """
    Analyzes unit folders and separates them into numeric and alphabetical parts.
    """
    if not book_name: return {}
    
    parsed_units = {}
    book_path = os.path.join(BOOKS_DIR, book_name)
    
    for section in SECTIONS:
        section_path = os.path.join(book_path, section)
        if os.path.exists(section_path):
            for folder in os.listdir(section_path):
                try:
                    unit_part_str = folder.split("_Unit_")[-1]
                    match = re.match(r"(\d+)([A-Za-z]*)", unit_part_str)
                    if match:
                        num_part, alpha_part = match.groups()
                        if num_part not in parsed_units:
                            parsed_units[num_part] = set()
                        if alpha_part:
                            parsed_units[num_part].add(alpha_part.upper())
                except Exception:
                    continue
                    
    for num_part in parsed_units:
        parsed_units[num_part] = sorted(list(parsed_units[num_part]))

    return parsed_units


def generate_exam_docx(book: str, units: list, questions_config: dict) -> io.BytesIO:
    """
    Generates a .docx document with numbered questions and an answer key at the end.
    """
    final_doc = Document()
    style = final_doc.styles['Normal']
    font = style.font
    font.name = 'Calibri'
    font.size = Pt(11)

    units_str = ", ".join(units)
    final_doc.add_heading(f"English test - Book: {book} | Unit(s): {units_str}", level=0)
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

            target_folder_name = None
            for folder in os.listdir(section_path):
                if folder.endswith(f"_Unit_{unit}"):
                    target_folder_name = folder
                    break
            
            if target_folder_name:
                unit_path = os.path.join(section_path, target_folder_name)
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

        num_to_pick = min(num_requested, len(pool_for_this_section))
        if num_to_pick > 0:
            chosen_questions = random.sample(pool_for_this_section, num_to_pick)
            final_question_list.extend(chosen_questions)

    if not final_question_list:
        final_doc.add_paragraph("No questions were found with the selected filter.")
    else:
        question_counter = 1
        answer_key = []
        current_section = None

        for q_data in final_question_list:
            if q_data['section'] != current_section:
                current_section = q_data['section']
                final_doc.add_heading(f"Section: {current_section.capitalize()}", level=1)
            
            p_question_num = final_doc.add_paragraph()
            p_question_num.add_run(f"{question_counter}. ").bold = True
            p_question_num.add_run(q_data.get("instructions", "")).bold = True
            
            if q_data.get("example"):
                final_doc.add_paragraph(q_data.get("example", ""))
            
            final_doc.add_paragraph()

            answers_for_this_question = []
            for pair in q_data.get("qa_pairs", []):
                final_doc.add_paragraph(pair.get("item", ""))
                if q_data.get("type") == "order_the_words":
                    final_doc.add_paragraph("____________________________________")
                answers_for_this_question.append(pair.get("answer", ""))
            
            answer_key.append({"number": question_counter, "answers": answers_for_this_question})
            question_counter += 1
            final_doc.add_paragraph()

        final_doc.add_page_break()
        final_doc.add_heading("Answer Key", level=1)
        
        for item in answer_key:
            p_answer_header = final_doc.add_paragraph()
            p_answer_header.add_run(f"Question {item['number']}:").bold = True
            for i, answer in enumerate(item['answers']):
                final_doc.add_paragraph(f"{i+1}. {answer}", style='List Bullet')
            final_doc.add_paragraph()

    doc_io = io.BytesIO()
    final_doc.save(doc_io)
    doc_io.seek(0)
    return doc_io

# --- Streamlit interface ---
st.title("English Test Generator")
st.markdown("Accurate, fast, and simple. Just how your English language learning should be.")

if not os.path.exists(BOOKS_DIR):
    st.warning(f"The `{BOOKS_DIR}` directory was not found.")
    if st.button("Click here to create a sample folder structure and .json files"):
        setup_test_environment()

with st.sidebar:
    st.header("📖 Test configuration")
    books = get_available_books(BOOKS_DIR)
    if not books:
        st.error(f"No books found in '{BOOKS_DIR}' directory.")
        st.stop()
    selected_book = st.selectbox("Choose the book", options=books, index=0)

    parsed_units = parse_available_units(selected_book)
    if not parsed_units:
        st.error(f"No drives found for book '{selected_book}'. Check the folder structure.")
        st.stop()

    numeric_options = sorted(parsed_units.keys(), key=int)
    selected_numerics = st.multiselect(
        "Numerical Unit(s)",
        options=numeric_options,
        default=[numeric_options[0]] if numeric_options else [],
        help="Select the desired unit numbers."
    )

    alpha_options = set()
    if selected_numerics:
        for num in selected_numerics:
            alpha_options.update(parsed_units.get(num, []))
    
    sorted_alpha_options = sorted(list(alpha_options))
    
    selected_alphas = st.multiselect(
        "Sub-unit(s) (A, B or C)",
        options=sorted_alpha_options,
        default=sorted_alpha_options,
        help="Select the alphabetical parts of the units."
    )
    
    final_selected_units = []
    if selected_numerics and selected_alphas:
        for num in selected_numerics:
            for alpha in selected_alphas:
                if alpha in parsed_units.get(num, []):
                    final_selected_units.append(f"{num}{alpha}")

    st.markdown("---")
    st.subheader("⚙️ Advanced settings")
    
    questions_config = {
        "grammar": st.number_input("Grammar", min_value=0, max_value=50, value=DEFAULT_QUESTIONS["grammar"], step=1),
        "vocabulary": st.number_input("Vocabulary", min_value=0, max_value=50, value=DEFAULT_QUESTIONS["vocabulary"], step=1),
        "pronunciation": st.number_input("Pronunciation", min_value=0, max_value=50, value=DEFAULT_QUESTIONS["pronunciation"], step=1)
    }
    total_questions = sum(questions_config.values())
    st.info(f"**Total number of questions in the test: {total_questions}**")

if not final_selected_units:
    st.warning("Please select a valid combination of numeric unit and sub-unit to continue.")
    st.stop()

st.title("Summary of your configuration")
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("**📖 Book**")
    st.markdown(f"`{selected_book}`")

with col2:
    units_display = ", ".join(final_selected_units)
    st.markdown("**📚 Selected Units**")
    st.markdown(f"`{units_display}`")

with col3:
    st.markdown("**⚙️ Questions by Section**")
    questions_summary = f"G: {questions_config['grammar']} | V: {questions_config['vocabulary']} | P: {questions_config['pronunciation']}"
    st.markdown(f"`{questions_summary}`")


st.markdown("---")

is_default_config = (
    questions_config["grammar"] == DEFAULT_QUESTIONS["grammar"] and
    questions_config["vocabulary"] == DEFAULT_QUESTIONS["vocabulary"] and
    questions_config["pronunciation"] == DEFAULT_QUESTIONS["pronunciation"]
)

if is_default_config:
    button_text = "🚀 Generate standard test"
else:
    button_text = "🚀 Generate custom test"

if 'exam_data' not in st.session_state:
    st.session_state.exam_data = None

if st.button(button_text, type="primary", use_container_width=True, disabled=(total_questions == 0)):
    if total_questions > 0:
        with st.spinner("Reading JSON files and building your test..."):
            try:
                exam_bytes = generate_exam_docx(selected_book, final_selected_units, questions_config)
                st.session_state.exam_data = exam_bytes
                units_filename = "_".join(final_selected_units)
                st.session_state.exam_filename = f"Prova_{selected_book}_Unidades_{units_filename}.docx"
                time.sleep(1)
                st.success("Test generated successfully! Click the button to download.")
            except Exception as e:
                st.error(f"An error occurred while generating the test: {e}")
                st.session_state.exam_data = None
    else:
        st.warning("Please select at least one question to generate the test.")

if st.session_state.get('exam_data'):
    st.download_button(
        label="📥 Download Test (.docx)",
        data=st.session_state.exam_data,
        file_name=st.session_state.get('exam_filename', 'prova.docx'),
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        use_container_width=True
    )

st.markdown("---")
st.markdown("Developed with ❤️ by CCB students")
