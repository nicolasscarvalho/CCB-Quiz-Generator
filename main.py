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
# PRONUNCIATION removida
SECTIONS = ["GRAMMAR", "VOCABULARY"]
DEFAULT_QUESTIONS = {"grammar": 3, "vocabulary": 3}
EVALUATION_LINK = "https://docs.google.com/forms/d/e/1FAIpQLSdm1n218RAyl_js-lQGvbWd_voBJlu_wZ90T_9p5dBaatD6Ew/viewform?usp=header"

def setup_test_environment():
    """
    Creates a test directory and file structure based on the NEW convention:
    BOOKS/{BOOK}/UNIT-{NUMBER}/UNIT-{NUMBER}-QUESTION-{NUMBER}-{SECTION}.json
    """
    if not os.path.exists(BOOKS_DIR):
        st.info("Creating test environment with .json files... Please reload the page in a few seconds.")
        # Structure reflecting files found in sources
        units_data = {
            "UNIT-1": [
                {"q_num": 1, "section": "GRAMMAR", "topic": ["1A", "1B"], "type": "fill_in_the_blanks_verb_be", "item_ex": "I _______ a new student here.", "answer_ex": "'m"},
                {"q_num": 2, "section": "GRAMMAR", "topic": ["1C"], "type": "select_correct_possessive_adjective", "item_ex": "I’m Chinese. _______ family is from Shanghai.", "answer_ex": "My"},
                {"q_num": 3, "section": "GRAMMAR", "topic": ["1A", "1B", "1C"], "type": "underline_correct_word_subject_possessive", "item_ex": "We / Our are from Japan.", "answer_ex": "We"},
                {"q_num": 4, "section": "VOCABULARY", "topic": ["1A", "1B"], "type": "complete_the_lists_numbers_days", "item_ex": "twenty-seven, twenty-eight, twenty-nine, _______.", "answer_ex": "thirty"},
                {"q_num": 6, "section": "VOCABULARY", "topic": ["1C"], "type": "fill_in_the_blanks_one_word", "item_ex": "___________ in groups of three.", "answer_ex": "WORK"}
            ],
            "UNIT-2": [
                {"q_num": 1, "section": "GRAMMAR", "topic": ["2A"], "type": "tick_correct_sentence", "item_ex": "A The teacher has two boxs of pencils. / B The teacher has two boxes of pencils.", "answer_ex": "B"},
                {"q_num": 3, "section": "GRAMMAR", "topic": ["2B", "2C"], "type": "underline_correct_word", "item_ex": "Is Ian Rankin a Scottish / Scotland writer?", "answer_ex": "Scottish"},
                {"q_num": 6, "section": "VOCABULARY", "topic": ["2B"], "type": "short_answer", "item_ex": "terrible", "answer_ex": "fantastic"}
            ],
            "UNIT-5": [
                {"q_num": 1, "section": "GRAMMAR", "topic": ["5B"], "type": "create_sentence_from_prompts", "item_ex": "What / you / watch / on TV ?", "answer_ex": "What are you watching on TV?"},
                {"q_num": 3, "section": "GRAMMAR", "topic": ["5A"], "type": "underline_correct_word_or_phrase", "item_ex": "She can to cook / cook very well.", "answer_ex": "cook"},
            ]
        }
        for unit_folder, questions in units_data.items():
            path = os.path.join(BOOKS_DIR, "ELEMENTARY", unit_folder)
            os.makedirs(path, exist_ok=True)
            for q in questions:
                file_name = f"{unit_folder}-QUESTION-{q['q_num']}-{q['section']}.json"
                file_path = os.path.join(path, file_name)
                sample_question = {
                    "questions": [{
                        "id": q['q_num'],
                        "section": q['section'],
                        "topic": q['topic'],
                        "type": q['type'],
                        "instructions": f"Sample instructions for {q['type']}.",
                        "example": {"item": f"Example: {q['item_ex']}", "answer": q['answer_ex']},
                        "qa_pairs": [{"item": f"Item {q['q_num']}", "answer": "A"}]
                    }]
                }
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(sample_question, f, indent=2, ensure_ascii=False)
        st.rerun()

@st.cache_data
def get_available_books(directory: str) -> list:
    """Returns a list of directories (books) inside the main directory."""
    if not os.path.exists(directory): return []
    return [d for d in os.listdir(directory) if os.path.isdir(os.path.join(directory, d))]

@st.cache_data
def parse_available_units(book_name: str) -> dict:
    """
    Analyzes the folder structure and extracts all unique unit designations 
    (1A, 1B, 2C) from the JSON 'topic' field.
    """
    if not book_name: return {}
    parsed_units = {}
    book_path = os.path.join(BOOKS_DIR, book_name)
    if not os.path.exists(book_path):
        return {}
    
    for unit_folder_name in os.listdir(book_path):
        if unit_folder_name.startswith("UNIT-"):
            unit_path = os.path.join(book_path, unit_folder_name)
            if os.path.isdir(unit_path):
                for filename in os.listdir(unit_path):
                    if filename.endswith(".json"):
                        file_path = os.path.join(unit_path, filename)
                        try:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                data = json.load(f)
                                for q in data.get("questions", []):
                                    for topic_unit in q.get("topic", []):
                                        match = re.match(r"(\d+)([A-Za-z]*)", topic_unit)
                                        if match:
                                            num_part, alpha_part = match.groups()
                                            if num_part not in parsed_units:
                                                parsed_units[num_part] = set()
                                            if alpha_part:
                                                parsed_units[num_part].add(alpha_part.upper())
                                            elif not alpha_part:
                                                parsed_units[num_part] = parsed_units.get(num_part, set())
                        except Exception:
                            continue
    
    for num_part in parsed_units:
        parsed_units[num_part] = sorted(list(parsed_units[num_part]))
        
    return parsed_units


def write_question_to_doc(doc, question_data, question_number):
    """
    Formats and writes a single question to the docx document based on its type.
    CORREÇÃO: Garante que os sub-itens (1., 2., 3.) e o conteúdo da questão
    estejam no mesmo parágrafo para evitar quebras de linha indesejadas.
    """
    # --- 1. Write Header and Instructions ---
    q_instructions = question_data.get("instructions", "")
    q_type = question_data.get("type")

    # Write question number (main question) and instructions
    p_question_num = doc.add_paragraph()
    p_question_num.add_run(f"{question_number}. ").bold = True
    p_question_num.add_run(q_instructions).bold = True
    doc.add_paragraph() 

    # Write example if it exists
    example_data = question_data.get("example")
    if isinstance(example_data, dict):
        example_item = example_data.get("item", "")
        doc.add_paragraph(f"Example: {example_item}")
    elif isinstance(example_data, str):
        doc.add_paragraph(f"Example: {example_data}")

    qa_pairs = question_data.get("qa_pairs") or question_data.get("qa_pair", [])

    # --- 2. Conditional Formatting based on Question Type ---
    
    # Type A: Tick/Select Sentence (A/B comparison, elimina quebra de linha)
    if q_type in ["tick_correct_sentence", "select_correct_sentence"]:
        for i, pair in enumerate(qa_pairs):
            item_text = pair.get("item", "") 
            options = item_text.split(' / ')

            # Prepara a string do item (e.g., "A Option A. B Option B.")
            # Para o formato desejado (1. [ ] A Option A. B Option B.)
            
            options_text_list = []
            
            # Aplica o placeholder [ ] no início do primeiro item (A)
            for j, option in enumerate(options):
                if j == 0 and re.match(r"^[A-D]\s", option):
                    options_text_list.append(f"( ) {option}")
                else:
                    options_text_list.append(option)
            
            consolidated_text = f"{i+1}. {' '.join(options_text_list)}"

            # Insere tudo como um único parágrafo
            doc.add_paragraph(consolidated_text)
            doc.add_paragraph() # Espaçamento entre sub-itens
            

    # Type B: Underline/Select Word (Corrige a numeração para X. Texto)
    elif q_type.startswith(("underline_correct_word", "select_correct_possessive_adjective", 
                            "underline_correct_word_subject_possessive", "underline_correct_word_or_phrase")):
        
        for i, pair in enumerate(qa_pairs):
            item_text = pair.get("item", "")
            # Substitui '/' por ' / ' para exibição clara
            display_text = item_text.replace('/', ' / ')
            
            # Insere como um único parágrafo
            doc.add_paragraph(f"{i+1}. {display_text}")
            doc.add_paragraph() 

    # Type C: Fill-in, Completion, Ordering, Generic 
    else:
        if qa_pairs:
            
            # Display instructions/options before the numbered list begins (if applicable)
            if q_type == "fill_in_from_word_bank":
                options = question_data.get("options", [])
                if options:
                    doc.add_paragraph(f"Options: {', '.join(options)}")
            
            if q_type == "match_question_answer":
                doc.add_paragraph("Match the questions and answers:")

            for i, pair in enumerate(qa_pairs):
                item_text = pair.get("item", "")
                
                # Para Matching, mantemos a formatação (1)
                if q_type == "match_question_answer":
                    doc.add_paragraph(f"({i+1}) {item_text}")
                    doc.add_paragraph("------------------------------------")
                
                # Para Ordering/Sentence Creation
                elif q_type.startswith("order_the_words") or q_type.startswith("create_sentence"):
                    doc.add_paragraph(f"{i+1}. Prompts: {item_text}")
                    doc.add_paragraph("____________________________________________________________________")
                
                # Todos os outros (Fill-in, complete the lists, short answer)
                else:
                    doc.add_paragraph(f"{i+1}. {item_text}")
                
            doc.add_paragraph() # Espaçamento final


def generate_exam_docx(book: str, units: list, questions_config: dict) -> io.BytesIO:
    """
    Generates a .docx document.
    """
    final_doc = Document()
    style = final_doc.styles['Normal']
    font = style.font
    font.name = 'Calibri'
    font.size = Pt(11)

    try:
        selected_numeric_units = sorted(list(set(re.match(r"(\d+)", u).group(1) for u in units)), key=int)
        units_str = ", ".join(selected_numeric_units)
    except:
        units_str = ", ".join(sorted(units)) 
        
    final_doc.add_heading(f"English Test - Book: {book} | Unit(s): {units_str}", level=0)
    final_doc.add_paragraph(f"Name: __________________________________________________ Date: ___/___/______")
    final_doc.add_paragraph()

    final_question_list = []

    numeric_units_map = {}
    for unit_code in units:
        match = re.match(r"(\d+)", unit_code)
        if match:
            num_part = match.group(1)
            if num_part not in numeric_units_map:
                numeric_units_map[num_part] = []
            numeric_units_map[num_part].append(unit_code)

    total_pool_all_questions = []
    book_path = os.path.join(BOOKS_DIR, book)

    if not os.path.exists(book_path):
        return io.BytesIO()

    unit_folders_to_check = [
        f for f in os.listdir(book_path)
        if f.startswith("UNIT-") and f.split('-')[-1] in numeric_units_map.keys()
    ]

    for unit_folder in unit_folders_to_check:
        unit_folder_path = os.path.join(book_path, unit_folder)
        
        for filename in os.listdir(unit_folder_path):
            if filename.endswith(".json"):
                file_path = os.path.join(unit_folder_path, filename)
                
                filename_parts = filename.replace('.json', '').split('-')
                file_section = filename_parts[-1].upper() if len(filename_parts) >= 4 else None

                requested_sections_upper = [s.upper() for s in questions_config.keys() if questions_config[s] > 0]
                if file_section in requested_sections_upper:
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            for q in data.get("questions", []):
                                q['section'] = file_section
                                
                                question_topics = q.get("topic", [])
                                
                                is_relevant = False
                                for req_unit in units: 
                                    if req_unit in question_topics:
                                        is_relevant = True
                                        break
                                
                                if is_relevant:
                                    if 'qa_pair' in q and 'qa_pairs' not in q:
                                        q['qa_pairs'] = q['qa_pair']

                                    total_pool_all_questions.append(q)
                    except Exception:
                        continue

    # 2. Random Selection per Section
    pool_by_section = {s: [] for s in SECTIONS}
    for q in total_pool_all_questions:
        if q['section'] in pool_by_section:
            pool_by_section[q['section']].append(q)

    for section, num_requested in questions_config.items():
        section_upper = section.upper()
        if num_requested > 0 and section_upper in pool_by_section:
            pool = pool_by_section[section_upper]
            num_to_pick = min(num_requested, len(pool))
            if num_to_pick > 0:
                chosen_questions = random.sample(pool, num_to_pick)
                final_question_list.extend(chosen_questions)

    # 3. Write Document and Answer Key
    if not final_question_list:
        final_doc.add_paragraph("No questions were found with the selected criteria.")
    else:
        question_counter = 1
        answer_key = []
        current_section = None
        final_question_list.sort(key=lambda q: q['section'])

        for q_data in final_question_list:
            if q_data['section'] != current_section:
                current_section = q_data['section']
                final_doc.add_heading(f"Section: {current_section.capitalize()}", level=1)

            write_question_to_doc(final_doc, q_data, question_counter)

            answers_source = q_data.get("qa_pairs") or q_data.get("qa_pair", [])
            answers_for_this_question = [pair.get("answer", "") for pair in answers_source]
            answer_key.append({"number": question_counter, "answers": answers_for_this_question})
            
            question_counter += 1 

        # Add the Answer Key
        final_doc.add_page_break()
        final_doc.add_heading("Answer Key (For Teacher's Use)", level=1)
        for item in answer_key:
            p_answer_header = final_doc.add_paragraph()
            p_answer_header.add_run(f"Question {item['number']}:").bold = True
            
            if isinstance(item['answers'], list) and len(item['answers']) > 0:
                for i, answer in enumerate(item['answers']):
                    final_doc.add_paragraph(f"{i+1}. {answer}")
            final_doc.add_paragraph()

    # Save the document to a byte stream in memory
    doc_io = io.BytesIO()
    final_doc.save(doc_io)
    doc_io.seek(0)
    return doc_io

# --- Streamlit Interface ---

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

    # --- Unit Selection: Refactored to select numeric units only ---
    st.markdown("---")
    st.subheader("🎯 Select Desired Units")

    final_selected_units = []
    
    sorted_numeric_units = sorted(parsed_units.keys(), key=int)
    
    selected_numeric_units = st.multiselect(
        label="Select Units (1, 2, 3, 4, 5, 6)",
        options=sorted_numeric_units,
        default=sorted_numeric_units,
        key=f"multiselect_{selected_book}_main" 
    )

    for num_unit in selected_numeric_units:
        alpha_units = parsed_units.get(num_unit, [])
        if not alpha_units:
            final_selected_units.append(num_unit)
        else:
            for alpha in alpha_units:
                final_selected_units.append(f"{num_unit}{alpha}")

    # --- End of Unit Selection ---
    st.markdown("---")
    st.subheader("⚙️ Number of Questions per Section")

    questions_config = {
        "grammar": st.number_input("Grammar", min_value=0, max_value=50, value=DEFAULT_QUESTIONS["grammar"], step=1),
        "vocabulary": st.number_input("Vocabulary", min_value=0, max_value=50, value=DEFAULT_QUESTIONS["vocabulary"], step=1)
    }
    
    total_questions = sum(questions_config.values())

    st.info(f"**Total questions on the test: {total_questions}**")

# --- Main Page Display ---

if not final_selected_units:
    st.warning("Please select at least one unit from the sidebar to continue.")
    st.stop()

st.title("Configuration Summary")
col1, col2, col3 = st.columns(3)

units_display = ", ".join(selected_numeric_units)

with col1:
    st.markdown("**📖 Book**")
    st.markdown(f"`{selected_book}`")

with col2:
    st.markdown("**📚 Selected Units**")
    st.markdown(f"`{units_display}`")

with col3:
    st.markdown("**⚙️ Questions per Section**")
    questions_summary = f"G: {questions_config['grammar']} | V: {questions_config['vocabulary']}"
    st.markdown(f"`{questions_summary}`")

# Determine button text based on whether the configuration is default or custom
is_default_config = (
    questions_config["grammar"] == DEFAULT_QUESTIONS["grammar"] and
    questions_config["vocabulary"] == DEFAULT_QUESTIONS["vocabulary"]
)
button_text = "🚀 Generate Standard Test" if is_default_config else "🚀 Generate Custom Test"

# Initialize session state for storing generated exam data
if 'exam_data' not in st.session_state:
    st.session_state.exam_data = None
if 'exam_filename' not in st.session_state:
    st.session_state.exam_filename = 'test.docx'

if st.button(button_text, type="primary", use_container_width=True, disabled=(total_questions == 0)):
    if total_questions > 0:
        with st.spinner("Reading JSON files and assembling your test..."):
            try:
                exam_bytes = generate_exam_docx(selected_book, final_selected_units, questions_config) 
                
                st.session_state.exam_data = exam_bytes
                
                numeric_units_filename = "_".join(selected_numeric_units)
                st.session_state.exam_filename = f"Test_{selected_book}_Units_{numeric_units_filename}.docx"
            except Exception as e:
                st.error(f"An error occurred during test generation: {e}")
                st.session_state.exam_data = None
    else:
        st.warning("Please select at least one question to generate the test.")

if st.session_state.exam_data:
    st.markdown("---")
    st.download_button(
        label="📥 Download Generated Test (DOCX)",
        data=st.session_state.exam_data,
        file_name=st.session_state.get('exam_filename', 'test.docx'),
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        use_container_width=True
    )

st.markdown("---")
st.title("About CCB's Quiz Generator")

st.write("Teachers at the Casa de Cultura Britânica spent hours manually creating tests. We created a system that generates these same experiences in seconds, freeing them to focus on what really matters: teaching. Plus, imagine having access to constantly updated English exercises based exactly on what you're studying? This process used to be manual and slow, so we've automated it so students and teachers have access to quality materials at the click of a button.")
st.write("Our project is a web application that generates customized English questions about grammar and vocabulary content based on books in the English File collection. Our technology acts like an expert teacher, using AI to read learning materials from our database and create thousands of question variations based solely on our trusted sources.")

st.markdown("---")

st.title("Please rate us and contribute")

st.write("So that we can continue to improve this tool and ensure it remains accurate, fast, and simple, your user experience is essential. Your feedback allows us to:")
st.markdown(f"[Click here]({EVALUATION_LINK}) so we can continue improving this tool and ensure it remains accurate, fast, and simple. Your user experience is essential. Your feedback allows us to:")

st.markdown("""
1. **Validate Quality**: Ensure that the generated content aligns with your needs and the structure of the books;
2. **Prioritize Improvements**: Understand where to invest our development time, whether in optimizing question generation or interface usability;
3. **Maintain Free Access**: Your participation validates the importance of this project for the UFC community.
""")

st.markdown("---")
st.markdown("Developed with ❤️ by UFC students")