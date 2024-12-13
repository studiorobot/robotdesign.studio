import os
import fitz  # PyMuPDF
from PIL import Image

def pdf_to_png(pdf_path, output_path):
    # Open the PDF file
    doc = fitz.open(pdf_path)
    
    # Get the first page of the PDF
    page = doc.load_page(0)  # 0 is the first page
    
    # Convert the page to a pixmap (image)
    pix = page.get_pixmap()
    
    # Save the pixmap as a PNG image
    pix.save(output_path)

    doc.close()

def main():
    # Define the input directory (where PDFs are located)
    input_directory = "./archive"  # Folder where PDFs are located
    
    # Define the output directory (where PNGs will be saved)
    output_directory = "./pdf-covers"  # Folder where PNGs will be saved

    # Create the output folder if it doesn't exist
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)

    # Get a list of all files in the input directory
    pdf_files = [f for f in os.listdir(input_directory) if f.endswith('.pdf')]
    
    # Loop through the PDF files found in the directory
    for pdf_filename in pdf_files:
        pdf_path = os.path.join(input_directory, pdf_filename)
        
        # Create the corresponding PNG filename
        png_filename = os.path.splitext(pdf_filename)[0] + ".png"
        png_path = os.path.join(output_directory, png_filename)
        
        # Convert the PDF to PNG
        print(f"Converting {pdf_filename} to {png_filename}")
        pdf_to_png(pdf_path, png_path)

if __name__ == "__main__":
    main()
