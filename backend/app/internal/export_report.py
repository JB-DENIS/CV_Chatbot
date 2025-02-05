import logging
import re
from typing import List
from fpdf import FPDF
from datetime import datetime

# Initialisation du logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_pdf_report(output_path: str, logo_path: str, report_text: str):
    """
    Creates a PDF report with a logo, the current date, and a given text.

    Args:
        output_path (str): The path where the generated PDF will be saved.
        logo_path (str): The path to the logo image to include in the report.
        report_text (str): The text content to include in the report.

    Returns
    -------
        None: The function saves the PDF to the specified output path.

    Raises
    ------
        FileNotFoundError: If the logo file does not exist.
        ValueError: If the provided paths or text are invalid.
    """
    pdf = FPDF()
    pdf.add_page()

    # Set font for the document
    pdf.set_font("Arial", size=12)

    # Add logo
    try:
        pdf.image(logo_path, x=10, y=8, w=30)
    except FileNotFoundError:
        raise FileNotFoundError(f"Logo file not found at: {logo_path}")  # noqa: B904

    # Add title
    pdf.set_font("Arial", style="B", size=16)
    pdf.cell(200, 10, txt="Rapport de conversation avec Dis-ADEME", ln=True, align="C")

    # Add date
    pdf.set_font("Arial", size=12)
    creation_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    pdf.ln(10)  # Add some space
    pdf.cell(
        200,
        10,
        txt=f"Date de création : {
             creation_date}",
        ln=True,
        align="R",
    )

    # Add content
    pdf.ln(20)  # Add some space
    pdf.set_font("Arial", size=12)
    pdf.multi_cell(0, 10, txt=report_text)

    # Save the PDF
    try:
        pdf.output(output_path)
        logger.info(f"PDF report created successfully at: {output_path}")
    except Exception as e:  # noqa: BLE001
        raise ValueError(f"Failed to save PDF: {e}")  # noqa: B904


def extract_pdf_references(conversation: List[dict]) -> List[str]:
    """
    Extract unique PDF references from the chatbot's responses in the conversation.

    Args:
        conversation (List[dict]): List of dictionaries representing the conversation.
                                   Each dictionary contains 'role' ('user' or 'assistant')
                                   and 'content' (message string).

    Returns:
        List[str]: A list of unique PDF references mentioned in the chatbot's responses.
    """
    pdf_references = set()

    for message in conversation:
        if (
            message.get("role") == "assistant"
            and "Consultez les documents suivants pour plus d'information:"
            in message.get("content", "")
        ):
            # Extract all PDF file names using regex
            matches = re.findall(r"[\w\s-]+\.pdf", message["content"])
            pdf_references.update(matches)
    return sorted(pdf_references)
