import streamlit as st
import tempfile
from PyPDF2 import PdfReader
import docx
from fpdf import FPDF
import openai
import io
from dotenv import load_dotenv
import os

load_dotenv()  # This loads the .env file at the project root

openai.api_key = os.getenv('OPENAI_API_KEY')

def process_pdf(uploaded_file):
    # Save the BytesIO content to a temporary file
    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        temp_file.write(uploaded_file.getvalue())
        temp_file_path = temp_file.name

    # Read the PDF using the temporary file path
    reader = PdfReader(temp_file_path)
    text = ""
    for page in reader.pages:
        text += page.extract_text() if page.extract_text() else ""
    return text

def process_docx(file):
    doc = docx.Document(file)
    text = "\n".join(paragraph.text for paragraph in doc.paragraphs)
    return text

def generate_notes(text):
    prompt = (
        "You are a helpful assistant. Please convert the following text into clear, "
        "concise, and easy-to-understand notes that would be ideal for a student studying for a test. "
        "Focus on key concepts, important details, and summaries that aid in quick revision and understanding.\n\n"
        "Text:\n" + text
    )

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": prompt},
        ]
    )

    return response['choices'][0]['message']['content'].strip()



def create_downloadable_pdf(text):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.multi_cell(0, 10, text)

    # Generate PDF in memory
    pdf_content = pdf.output(dest='S').encode('latin-1')
    pdf_output = io.BytesIO(pdf_content)
    pdf_output.seek(0)  # Reset buffer position to the beginning

    return pdf_output

st.title('Document to Notes Converter')

uploaded_files = st.file_uploader("Choose a file", accept_multiple_files=True, type=['pdf', 'docx'])

if st.button('Generate Notes'):
    if uploaded_files:
        all_text = ""
        for uploaded_file in uploaded_files:
            if uploaded_file.type == "application/pdf":
                all_text += process_pdf(uploaded_file)
            elif uploaded_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
                all_text += process_docx(uploaded_file)

        if all_text:
            notes = generate_notes(all_text)
            st.write(notes)

            pdf = create_downloadable_pdf(notes)
            st.download_button(label="Download Notes as PDF",
                               data=pdf,
                               file_name="notes.pdf",
                               mime="application/octet-stream")
