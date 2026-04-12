#!/bin/bash

# Define the parent directory
parent_directory="team"

# Define a list of filenames to exclude (only filenames, not full paths)
exclude_files=(
  "Myles_Avalon_Undergrad.jpg"
  "Leia_Stirling_External_Collaborator.jpg"
  "Peter_Kahn_External_collaborator.jpeg"
  "Mak_Draelos-External_Collaborator.jpg"
  "Ilkyaz_Sarimehmetoglu_Masters.jpeg"
  "Jim-Cogswell-External-Collaborator.jpg"
  # Add other file names to exclude here
)

# Loop through all subdirectories and files inside the 'team' directory
find "$parent_directory" -type f \( -iname \*.jpg -o -iname \*.jpeg -o -iname \*.JPG \) | while read file; do
  # Extract the file name from the full path
  filename=$(basename "$file")

  # Check if the current file is in the exclude list by file name
  if [[ " ${exclude_files[@]} " =~ " $filename " ]]; then
    echo "Skipping $filename"
  else
    echo "Optimizing $filename with max quality 80"
    jpegoptim --max=35 "$file"
  fi
done

echo "Image optimization complete!"
