# How to Update the Lab Website Content

This README explains how to use Jekyll to update the lab website content.

---

## Content
Content can be found on the [Google Drive](https://drive.google.com/drive/folders/1YS7ioFVL623bIPBt7R1lxnIaZr9TWC4w).

## Local Setup
Before updating the lab website, you'll need to set up Jekyll locally.

### Install Jekyll
Follow the installation guide for your operating system from the official Jekyll website:
[Jekyll Installation Guide](https://jekyllrb.com/docs/installation/)

### Clone the Repository
Clone the lab website repository to your local machine using the following SSH or PAT commands:

SSH:
``` bash
git clone git@github.com:studiorobot/robotdesign.studio.git
```
PAT:
``` bash
git clone https://github.com/studiorobot/robotdesign.studio.git
```

### Navigate to the Project Directory: 
Move to the directory where the repository was cloned.

``` bash
cd robotdesign.studio
```

### Install Dependencies: 
Ensure you have all required dependencies installed by running:

``` bash
bundle install
```

### Run the Local Server: 
To view the website locally with live reload and automatic browser opening, start the Jekyll server:

``` bash
bundle exec jekyll serve --livereload -o
```

By default, this will serve the site at http://localhost:4000/robotdesign.studio/ and automatically open it in your browser. Any saved changes you make will be reflected in the browser immediately.

---

## Homepage

The homepage data file includes the following sections:

### Carousel
The `carousel` section displays images and text on the homepage slider. Each entry includes:
- `title`: The heading for the slide.
- `description`: A short description (supports HTML for line breaks).
- `image`: The image file path.

```yaml
carousel:
  - title: multidisciplinarity
    description: Our work happens at the intersection<br>of robotics, design, and psychology
    image: carousel/fabrication.jpg
```

### Research Vision
The `research_vision` key holds a multi-line text block describing the lab's mission.

```yaml
research_vision: |
  Robot Studio is a multi-disciplinary research lab that designs current and future relationships between robots and us that are inspiring, refined, and magical...
```

---

## News

The `news` section contains updates about lab activities. Each entry includes:
- `date`: The date of the event.
- `description`: A description of the event. It supports Markdown links.

### Adding Links in News
To add a link, put the text you want to display in square brackets [], followed immediately by the link in parentheses (), with no space between them.

#### Example:
```yaml
news: 
  - date: January 9th, 2025
    description: Prof. Patricia launched a new class at the Robotics Department called "Human Evaluation of Robot Systems."

  - date: March 7, 2022
    description: Organized HRI 2022 workshop on [theory-grounded HRI](https://theoriahri.wixsite.com/theoria).
```

When the website is built, the Markdown links in the description will be rendered with the corresponding text and URL.


## Updating Content

1. Locate the appropriate data file (e.g., `homepage.yml` for the homepage).
2. Add or edit entries using the provided structure.
3. Use Markdown links for clickable text in the News section.
4. Save the changes. Jekyll will regenerate the site to include your updates.

---

## Projects

The projects data file includes the following sections:

### Introduction
The `intro` key contains a brief description of the lab's project focus.

```yaml
intro: Our projects explore the intersection of robotics, creativity, and human connection across diverse domains, from health to the arts.
```

---

### Active/Completed Projects
Each project entry contains:
- `id`: A unique identifier for the project.
- `name`: The project title.
- `members`: Names of team members involved.
- `data`: Timeframe and funding source.
- `description`: A brief overview of the project.
- `poster`: Path to the thumbnail image.
- `video_webm`: Path to the project video.

#### Example:
```yaml
completed:
  - id: 1
    name: "EMOTE: Embodied-Perceptive Tutors for Empathy-Based Learning"
    members: INESC-ID (Portugal), Herriot-Watt University (UK), Goetebordgs University (Sweden), University of Bremen (Germany), University of Sunderland (UK)
    data: 2012 - 2016 
    links: 
      site: 
        - https://cordis.europa.eu/project/id/317923
      yt: 
        - https://www.youtube.com/watch?v=tzaxfyUUrCU
      doi: 
        - https://dl.acm.org/doi/abs/10.1145/3300188
        - https://link.springer.com/article/10.1007/s00146-016-0667-2
        - https://ieeexplore.ieee.org/abstract/document/7451752
    description: This European FP7 project set the challenge to create empathic robotic tutors by researching how robots can respond to learners. An empathic robot can adapt to the learning pace of children, supporting their process and at the same time challenging new curricula. Can an autonomous robot designed with empathic competencies foster collaborative learning in a group context? Can an empathic robot sustain positive educational outcomes in long-term collaborative learning interactions with groups of students? 
    keywords: educational robotics, sustainable curriculum, school deployment 
    poster: past/emote/thumbnail.jpg
    video_webm: past/emote/emote.mp4
```

---


---

## Steps to Update the Projects Page

1. **Locate the Data File**:
   Open the Jekyll data file for projects called `projects.yml` in the '_data' folder.

2. **Add or Update Content**:
   - Add a new project entry to the `active` or `completed` section.
   - Ensure that all fields (`id`, `name`, `members`, `data`, etc.) are correctly filled.
   - For `links`, specify the appropriate type under(`doi`, `yt`, or `code`) by adding a URL.
   - For poster and video, make sure the paths point to the correct files in projects folder.

3. **Verify Content**:
   - Ensure each project has a unique `id`.
   - Check that paths to images (`poster`, `video_webm`) are correct.

4. **Save and Build**:
   - Save the updated data file.
   - Rebuild the Jekyll site to apply the changes.


---

## Team

The team data file includes three main sections: `members`, `collab`, and `alumni`. You can find member images and content in this [Google Drive](https://drive.google.com/drive/folders/1YFu-pjSUnet0ZTTULpwFI7xi0Mgotswk?usp=sharing).

---

### Members
The `members` section lists current team members and their details. Each entry contains:
- `name`: Full name of the member.
- `standing`: Academic standing (e.g., Ph.D., Master's).
- `major`: Field of study or specialization.
- `university`: Name of the institution.
- `project`: Project the member is associated with.
- `joined`: The term and year the member joined.
- `personal_website`: URL of the member's personal website.
- `google_scholar`: URL to their Google Scholar profile.
- `linkedin`: URL to their LinkedIn profile.
- `github`: URL to their GitHub profile.
- `img`: Path to the member's profile image.

#### Example:
```yaml
members:
 - name: Atharva S. Kashyap
   standing: Ph.D.
   major: Robotics
   university: University of Michigan
   project: Delicious
   joined: Fall 2024
   personal_website: https://atharva-kashyap.github.io 
   google_scholar: https://scholar.google.com/citations?user=JCoq_vAAAAAJ
   linkedin: https://www.linkedin.com/in/atharva-kashyap/ 
   github: https://github.com/atharva-kashyap 
   img: phd/Atharva_S._Kashyap_PhD.jpg
```

---

### Collaborators
The `collab` section lists external collaborators. Each entry includes:
- `name`: Full name of the collaborator.
- `role`: Collaborator's role (e.g., Full Stack Engineer).
- `university`: Institution the collaborator is affiliated with.
- `department`: Department within the institution.
- `img`: Path to the collaborator's profile image.

#### Example:
```yaml
collab:
  - name: Abhishek Narula
    role: Full Stack Engineer
    university: University of Michigan
    department: Robotics
    img: collab/Abhishek_Narula_External_Collaborator.jpg
```

---

### Alumni

The **alumni** section lists former team members. Each entry contains:

- **name**: name.
- **future**: Where they went after graduating/left. 
  - **project**: The project they worked on.
- **year**: Year(s) on the team (e.g., 2024, 2024 - 2025).
- **linkedin**: A link to their LinkedIn profile.

---

For example:

```yaml
alumni:
  - name: Zhixuan Chen
    future: 
      project: Relate
    year: 2024
    linkedin: https://www.linkedin.com/in/zhixuan-chen-102695215/
```
---
## Steps to Update the Team Page

1. **Locate the Data File**:
   Open the Jekyll data file for the team named `team.yml`  in the '_data' folder.

2. **Add or Edit Entries**:
   - For current members, update the `members` section.
   - For collaborators, update the `collab` section.
   - For alumni, update the `alumni` section.

3. **Check Image Paths**:
   Ensure all `img` paths point to the correct location in the team folder. 

4. **Save and Rebuild**:
   Save the updated data file and rebuild the Jekyll site to reflect the changes.

---

By following this structure, you can maintain an up-to-date and organized team page, showcasing the members, collaborators, and alumni effectively.

## Publications

The data file for publications includes:
- `intro`: A brief introductory statement about the page.
- `publications`: A list of publications grouped by year.

Each publication entry contains:
- `title`: Title of the publication.
- `authors`: List of authors in the publication.
- `event`: Conference, journal, or event where the publication was presented or published.
- `pdf`: Path to the PDF file of the publication.
- `img`: Path to the thumbnail image for the publication.
- `project`: The project associated with the publication (if applicable).
- `doi` (optional): DOI link to the publication (if available).
- `video` (optional): Video link(if available).
---

## Example Data File Structure

```yaml
intro: We publish our research outcomes at conferences and journals in the field of Human-Robot Interaction, Design Research, Robotics, and Artificial Intelligence.

publications:
  2014:
    - title: How do you imagine robots? Children’s expectations about robots
      authors: Patrícia Alves-Oliveira, Sofia Petisca, Srinivasan Janarthanam, Helen Hastie, Ana Paiva
      event: 'Interaction Design and Children Workshop on Child-Robot Interaction: Social Bonding, Learning and Ethics'
      pdf: 6.pdf
      img: 6.png  
      project: EMOTE

  2024:
    - title: Multiple Ways of Working with Users to Develop Physically Assistive Robots
      authors: Amal Nanavati, Max Pascher, Vinitha Ranganeni, Ethan K Gordon, Taylor Kessler Faulkner, Siddhartha S Srinivasa, Maya Cakmak, Patrícia Alves-Oliveira, Jens Gerken
      event: arXiv preprint arXiv:2403.00489, arXiv
      doi: https://doi.org/10.48550/arXiv.2403.00489
      pdf: 92.pdf
      img: 92.png
      project: DELICIOUS
```

---

## Steps to Update the Publications Page

1. **Locate the Data File**:
   Open the Jekyll data file for publications called `publications.yml` in the '_data' folder.

2. **Add a New Year Section**:
   If a new year needs to be added, create a new section with the year as the key under `publications`.

   ```yaml
   2025:
     - title: Example Title
       authors: Author A, Author B
       event: Example Event
       pdf: example.pdf
       img: example.png
       project: Example Project
   ```

3. **Add a New Publication Entry**:
   Add the details for the publication under the relevant year. Ensure all fields (`title`, `authors`, `event`, etc.) are filled out correctly.

4. **Add the PDF to the `publications` Folder**:
   Place the PDF for the publication in the `publications` folder. This is the folder that will be referenced for all publication PDFs. For example, you would add `example.pdf` to the `publications/` folder.

5. **Generate the Thumbnail**:
   To generate the thumbnail for the publication's PDF, you need to run a Python script (`thumbnail.py`). Follow the steps below to set up the environment and generate the thumbnail.

   ### Steps to Generate the Thumbnail

   - **Set Up a Virtual Environment**:
   
     1. **Create the Virtual Environment**:
        Run the following command to create a virtual environment named `venv` in the project directory:

        ```bash
        python -m venv venv
        ```

     2. **Activate the Virtual Environment**:
        
        - **On macOS/Linux**:
          ```bash
          source venv/bin/activate
          ```

        - **On Windows**:
          ```bash
          .\venv\Scripts\activate
          ```

     3. **Install Dependencies**:
        Install the required dependencies from the `requirements.txt` file:

        ```bash
        pip install -r requirements.txt
        ```

   - **Run the Script**:
     After installing the dependencies, run the `thumbnail.py` script to generate a thumbnail for the publication. Pass the path to the PDF and the page number from which to generate the thumbnail.

     For example, if you have `example.pdf` in the `publications/` folder and you want to generate the thumbnail for the third page:

     ```bash
     python thumbnail.py publications/example.pdf 3
     ```

     This will generate a thumbnail image of the third page of `example.pdf` and delete the previous pages from the pdf. The thumbnail will be generated as a png in the publications/thumbnails folder with the same name as the pdf.

6. **Check Paths and Links**:
   - Verify that the `pdf` field in `publications.yml` points to the correct file path in the repository.
   - Ensure the `img` field links to the correct thumbnail image (generated by the script).
   - If available, add a `doi` field with the DOI link.

7. **Save and Rebuild**:
   Save the updated data file and rebuild the Jekyll site to reflect the changes.


---

## Notes
- Publications are grouped by year in descending order.
- Ensure consistency in formatting and file paths for seamless integration.
- The `project` field connects the publication to a specific project, enhancing cross-referencing between the projects and publications pages.

By following this structure, you can efficiently maintain an up-to-date and well-organized publications page.

## Press

Each entry in the press page can follow one of two formats:
1. **With Multiple Links**: Use this format if there are multiple links within the `description` field, using Markdown links.
2. **With a Single Link**: Use this format if there is only one link for the press item.

### Fields in a Press Entry
- `date`: Date of the press item.
- `title`: Title of the press item or publication.
- `content`: A brief description of the press item.
- `image`: Path to the thumbnail image for the press item.
- **For Multiple Links**:
  - `description`: Text where Markdown links are rendered
- **For a Single Link**:
  - `link`: URL for the press item.

---

## Example Data File Structure

```yaml
press: 
- date: November 29th, 2022 # Multiple Links
  title: PodBean
  content: Featuring Prof. Patricia’s research on human-robot interaction and creativity
  image: fueling-creativity.png
  description: "Fueling Creativity in Education Podcast with two episodes: [Building Robots to Support Childhood Creativity](https://www.podbean.com/media/share/pb-vdwv6-1327784) and on [Evaluating the Impact of Creativity Interventions on Children](https://www.podbean.com/media/share/pb-9ku6h-13276c3)."

- date: January 5th, 2022 # Single Link
  title: For UW, By UW
  content: Interview about how to design robots to help teens recognize mental health needs.
  image: w.png
  link: https://open.spotify.com/episode/5dS6uYedbwNj7Hpe5n8kBL
```

---

## Steps to Update the Press Page

1. **Locate the Data File**:
   Open the Jekyll data file for the press page called `press.yml` in the '_data' folder.

2. **Add a New Press Entry**:
   - For multiple links, use Markdown link syntax `[text](link)` in the `description` field to include the links.
   - For a single link, use the `link` field:
3. **Verify Image and Links**:
   - Ensure the `image` field points to the correct thumbnail image in the press folder.
   - Confirm all links (`link` or `links`) are valid and lead to the intended pages.

4. **Save and Rebuild**:
   Save the updated file and rebuild the Jekyll site to apply the changes.

---

## Notes
- Ensure proper formatting and consistency in the description text for multiple links.
- For single-link entries, the entire press item will be clickable.

## Join Us

The data file includes sections for introductory text and specific opportunities for different types of applicants. Text fields can contain HTML for links or formatting.

### Fields in the Data File
- `intro_text`: Introductory text about the lab and its philosophy, including links to external resources.
- `phd_students_text`: Information about Ph.D. opportunities, including links to relevant admissions pages.
- `undergraduate_master_students_text`: Details about opportunities for current undergraduate and master’s students at the university.
- `visiting_students_text`: Information for visiting students, typically self-funded.
- `postdocs_text`: Updates on postdoc openings, if available.

---

## Example Data File Structure

```yaml
intro_text: |
  We are dedicated to creating an interdisciplinary team of researchers who are ...holistically in their learning journey and career goals. Read
  <a href="https://robotics.umich.edu/academics/graduate/admissions/graduate-application/what-are-specific-faculty-looking-for-in-phd-applications/"
     target="_blank">this article</a>
  to understand what Patricia is looking for in a student application. Note that due to the...

phd_students_text: |
  We will be looking to accept one ...
  <a href="https://robotics.umich.edu/academics/graduate/admissions/" target="_blank">this admission website</a> 
  by the deadline...

undergraduate_master_students_text: |
  Current University of Michigan students are welcome to join Robot Studio for research credits...

visiting_students_text: |
  We often have self-funded visiting students for the summer and (rarely) during the academic year....

postdocs_text: "We have no openings at this time for postdocs."
```

---

## Steps to Update the Join Us Page

1. **Locate the Data File**:
   Open the Jekyll data file for the "Join Us" page called `join.yml` in the '_data' folder.

2. **Edit the Relevant Section**:
   - To update the introductory text, modify the `intro_text` field:
     ```yaml
     intro_text: |
       We welcome interdisciplinary researchers. Learn more about Patricia’s expectations
       <a href="https://example.com/article" target="_blank">here</a>.
     ```
   - To update the Ph.D. opportunities, edit the `phd_students_text` field:
     ```yaml
     phd_students_text: |
       Applications for Fall 2026 are now open. Visit 
       <a href="https://example.com/admissions" target="_blank">this page</a>.
     ```
   - Repeat this process for the other sections (`undergraduate_master_students_text`, `visiting_students_text`, and `postdocs_text`).

3. **Include Links and Formatting**:
   Use HTML tags to include links or custom formatting within text fields.

4. **Save and Rebuild**:
   Save the updated file and rebuild the Jekyll site to reflect the changes.

---

## Notes
- Use HTML within text fields to add links or customize formatting.
- Ensure all links open in a new tab by including `target="_blank"`.
- Keep the text concise and relevant to the intended audience.

By following these steps, you can keep the "Join Us" page informative and up to date for prospective members of the lab.

## Structure of the Navigation Data File

The navigation data file is divided into two main sections: `internal` for internal navigation links and `external` for social media or external links.

### Fields in the Data File

1. **Internal Navigation (`internal`)**:
   - `title`: The text displayed on the navigation bar.
   - `url`: The relative URL for the internal page (e.g., `"projects"` for `/projects/`).

2. **External Links (`external`)**:
   - `platform`: The name of the external platform (e.g., "LinkedIn").
   - `url`: The full URL to the external platform.
   - `name`: Display name for accessibility or alternative use.
   - `icon`: Font Awesome class for the platform's icon.

---

## Example Data File Structure

```yaml
internal:
  - title: "projects"
    url: "projects"
  - title: "team"
    url: "team"
  - title: "publications"
    url: "publications"
  - title: "press"
    url: "press"
  - title: "join us"
    url: "join-us"

external:
  - platform: LinkedIn
    url: https://www.linkedin.com/company/robot-studio-design/
    name: LinkedIn
    icon: fab fa-linkedin
  - platform: GitHub
    url: https://github.com/studiorobot
    name: GitHub
    icon: fab fa-github
```

---

## Steps to Update the Navigation Bars

### 1. **Internal Navigation**
   - To add a new internal link:
     ```yaml
     - title: "about"
       url: "about"
     ```
   - Insert the new entry under the `internal` section.

   - To remove a link, delete its entry:
     ```yaml
     - title: "join us"
       url: "join-us"
     ```

   - Save the file and rebuild the site to reflect changes in the header and mobile navigation bars.

---

### 2. **External Links**
   - To add a new external link, append an entry under the `external` section:
     ```yaml
     - platform: Twitter
       url: https://twitter.com/studiorobot
       name: Twitter
       icon: fab fa-twitter
     ```

   - To remove an external link, delete its entry:
     ```yaml
     - platform: GitHub
       url: https://github.com/studiorobot
       name: GitHub
       icon: fab fa-github
     ```

   - Ensure the `icon` field uses a valid Font Awesome class.

---

## Notes
- **Order Matters**: The order of links in the `internal` section determines their order in the navigation bar.
- **Icons**: Ensure that the `icon` field matches the Font Awesome version used in the website.
- **URL Formatting**:
  - Internal links use relative paths (e.g., `"team"`).
  - External links use absolute URLs (e.g., `https://...`).

By editing this file, you can control the layout and content of the navigation bars and social media links across the website.
