import os
import fitz  # PyMuPDF
from PIL import Image

def pdf_to_png(pdf_path, output_path):
    doc = fitz.open(pdf_path)
    page = doc.load_page(0) 
    pix = page.get_pixmap()
    pix.save(output_path)

    doc.close()

def main():
    input_directory = "./archive" 
    output_directory = "./pdf-covers" 

    if not os.path.exists(output_directory):
        os.makedirs(output_directory)

    pdf_files = [f for f in os.listdir(input_directory) if f.endswith('.pdf')]
    
    for pdf_filename in pdf_files:
        pdf_path = os.path.join(input_directory, pdf_filename)
        
        png_filename = os.path.splitext(pdf_filename)[0] + ".png"
        png_path = os.path.join(output_directory, png_filename)
        
        print(f"Converting {pdf_filename} to {png_filename}")
        pdf_to_png(pdf_path, png_path)

if __name__ == "__main__":
    main()
