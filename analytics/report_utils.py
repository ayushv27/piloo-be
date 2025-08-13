import os
import io
from pypdf import PdfWriter, PdfReader
from weasyprint import HTML
from django.template import engines
from core.models import Client, Report
from django.core.files.base import ContentFile



def generate_single_pdf(html_file_path: str, base_url: str, context: dict) -> bytes:
    if not os.path.exists(html_file_path):
        raise FileNotFoundError(f"HTML file not found: {html_file_path}")

    with open(html_file_path, 'r', encoding='utf-8') as f:
        raw_html = f.read()
        
    django_engine = engines['django']
    template = django_engine.from_string(raw_html)
    rendered_html = template.render(context)


    html_doc = HTML(string=rendered_html, base_url=base_url)
    pdf_buffer = io.BytesIO()
    html_doc.write_pdf(pdf_buffer, pdf_version='1.7')
    pdf_buffer.seek(0)

    return pdf_buffer.read()


def merge_pdfs(pdf_bytes_list: list, output_path: str) -> bytes:        
    pdf_writer = PdfWriter()
    for pdf_bytes in pdf_bytes_list:
        pdf_reader = PdfReader(io.BytesIO(pdf_bytes))
        for page in pdf_reader.pages:
            pdf_writer.add_page(page)

    with open(output_path, 'wb') as f:
        pdf_writer.write(f)