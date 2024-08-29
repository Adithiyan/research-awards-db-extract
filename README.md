# Award Information Scraper

This repository contains a Python script that scrapes information about various awards from specified websites and saves the details into an Excel file. No prior knowledge of computer science is required to use this script. Follow the steps below to set up and run the scraper.

## Installation

Before running the script, you need to install the required software and libraries.

### 1. Python

Make sure Python (version 3.7 or higher) is installed on your computer. You can download it from [python.org](https://www.python.org/).

### 2. Required Libraries

Open a command prompt (Windows) or terminal (Mac/Linux) and install the necessary libraries by running the following commands:
```
pip install scrapy spacy pandas python-dateutil
python -m spacy download en_core_web_sm
```
Preparing the Script
The script will crawl specific URLs to extract information about different awards. Here's how to prepare it:

1. Download the Script
Copy the entire code provided here to a text editor (like Notepad) and save it with a .py extension, for example, award_scraper.py.

2. Customize the Award Details
At the top of the script, you'll find a section with the variable awards_dict. This is a dictionary that contains the names of awards and their corresponding URLs. Replace the existing entries with the names and URLs of the awards you want to scrape. The format should be:

```
awards_dict = {
    "Award Name 1": [
        "https://example.com/award1"
    ],
    "Award Name 2": [
        "https://link1",
        "link2"
    ]
}
```

Note: Ensure that each award name has a unique URL or list of URLs associated with it. If you need to convert a list of plain text award names and award links from excel, first make a seperate list on notepad or excel with award names and their url links and copy them, paste them on to prompt chatgpt and prompt it to convert it to a python dictionary 

Running the Script
1. Open Command Prompt/Terminal
Navigate to the directory where you saved award_scraper.py:
```
cd path/to/your/script
```
2. Execute the Script
Run the script by typing:

```
python award_scraper.py
```
The script will start crawling the websites you've provided and extract relevant information.

3. Wait for Completion
The script may take a few minutes depending on the number of awards and the complexity of the websites. Once it's done, it will generate an Excel file named award_scrape_results1.xlsx in the same directory as your script.

Understanding the Output
The Excel file award_scrape_results1.xlsx will have the following columns:

Award: The name of the award.
Disciplines: The disciplines or fields related to the award.
Possible Deadlines: Important dates such as application deadlines.
Level: The level of the award (e.g., Provincial, National, International).
Career Stage: The career stage targeted by the award (e.g., Early Career, Mid Career, Late Career, Open).
Source URLs: The URLs of the pages from which the information was scraped.

Troubleshooting
No Output: If the Excel file isn't created, ensure that the URLs in awards_dict are correct and accessible.
Incomplete Information: Some awards may not have all fields filled out, depending on the information available on the website.
Errors: If you encounter errors, ensure that all the required Python libraries are installed correctly.
Further Customization
If you have some technical knowledge, you can modify the script to extract additional information or adjust the existing logic. However, the provided setup should be sufficient for most basic needs.

Support
If you run into issues or have questions, you can look up troubleshooting tips for Python and the libraries used (e.g., Scrapy, spaCy, pandas) online, or seek help from programming communities like Stack Overflow.
