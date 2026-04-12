import sys
import os
import fitz  # PyMuPDF
from PIL import Image

def create_thumbnail(pdf_path, page_number, thumbnail_folder):
    doc = fitz.open(pdf_path)

    if page_number < 1 or page_number > len(doc):
        print(f"Invalid page number: {page_number}. PDF only has {len(doc)} pages.")
        return
    
    page = doc.load_page(page_number - 1)
    pix = page.get_pixmap()
    image = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
    pdf_filename = os.path.splitext(os.path.basename(pdf_path))[0]
    output_path = os.path.join(thumbnail_folder, f"{pdf_filename}.png")
    image.save(output_path)

    print(f"Thumbnail saved at {output_path}")


def remove_pages_before(pdf_path, page_number):
    doc = fitz.open(pdf_path)

    if page_number < 1 or page_number > len(doc):
        print(f"Error: Page number {page_number} is out of range.")
        return
    
    if page_number == 1:
        print("Page number is 1. No pages removed. Original PDF is unchanged.")
        return pdf_path
    
    new_doc = fitz.open()
    new_doc.insert_pdf(doc, from_page=page_number - 1)
    new_doc.save(pdf_path) 
    
    print(f"Original PDF replaced with modified version: {pdf_path}")
    return pdf_path



def main():
    if len(sys.argv) != 3:
        print("Usage: python thumbnail.py <pdf-name.pdf> <page-number>")
        sys.exit(1)

    pdf_name = sys.argv[1]
    page_number = int(sys.argv[2])
    thumbnails_folder = os.path.join("publications", "thumbnails")
    os.makedirs(thumbnails_folder, exist_ok=True)
    pdf_path = os.path.join("publications", pdf_name)
    
    if not os.path.isfile(pdf_path):
        print(f"Error: PDF file '{pdf_name}' not found in 'publications' folder.")
        sys.exit(1)
    
    modified_pdf_path = remove_pages_before(pdf_path, page_number)

    create_thumbnail(modified_pdf_path, page_number, thumbnails_folder)


if __name__ == "__main__":
    main()
