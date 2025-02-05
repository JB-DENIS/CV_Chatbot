import os
from typing import Iterator, List, Union

import openparse
from docling.document_converter import DocumentConverter
from langchain_core.document_loaders import BaseLoader
from langchain_core.documents import Document as LCDocument
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.settings import Settings


def get_pdf_paths(directory_or_file: Union[str, os.PathLike]) -> List[str]:
    """
    Retrieve all PDF file paths from a given directory, including its subdirectories, or from a single file.

    Args:
        directory_or_file (Union[str, os.PathLike]): Path to a directory or a single file.

    Returns:
        List[str]: A list of file paths to PDF files.

    Raises:
        FileNotFoundError: If the given path does not exist.
        ValueError: If the input path is neither a directory nor a PDF file.
    """
    if not os.path.exists(directory_or_file):
        raise FileNotFoundError(f"The path '{directory_or_file}' does not exist.")

    pdf_paths = []

    if os.path.isdir(directory_or_file):
        for root, _, files in os.walk(directory_or_file):
            for file in files:
                if file.lower().endswith(".pdf"):
                    pdf_paths.append(os.path.join(root, file))

    elif os.path.isfile(directory_or_file):
        if directory_or_file.lower().endswith(".pdf"):
            pdf_paths.append(directory_or_file)
        else:
            raise ValueError(f"The file '{directory_or_file}' is not a PDF.")
    else:
        raise ValueError(
            f"The path '{directory_or_file}' is neither a directory nor a valid file."
        )

    return pdf_paths


settings = Settings()


def parse_document(doc_path, parser=settings.parser):
    if parser == "openparse":
        parser = openparse.DocumentParser()
        parsed_basic_doc = parser.parse(doc_path)

        parsed_doc = [
            node.text.replace("<br><br>", "\n") for node in parsed_basic_doc.nodes
        ]

    if parser == "docling":  # FIXME
        converter = DocumentConverter()
        parsed_doc = converter.convert(doc_path)

        # loader = DoclingPDFLoader(file_path=doc_path)
        # parsed_doc = loader.load()

    return parsed_doc


def split_documents(text_splitter, docs):
    return text_splitter.split_documents(docs)


def get_text_chunker():
    return RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)


# class DoclingPDFLoader(BaseLoader):

#     def __init__(self, file_path: str | list[str]) -> None:
#         self._file_paths = file_path if isinstance(
#             file_path, list) else [file_path]
#         self._converter = DocumentConverter()

#     def lazy_load(self) -> Iterator[LCDocument]:
#         for source in self._file_paths:
#             dl_doc = self._converter.convert(source).document
#             text = dl_doc.export_to_markdown()
#             yield LCDocument(page_content=text)


# loader = DoclingPDFLoader(file_path=path)
# text_splitter = RecursiveCharacterTextSplitter(
#     chunk_size=1000,
#     chunk_overlap=200,
# )

# docs = loader.load()
# splits = text_splitter.split_documents(docs)

# splits
