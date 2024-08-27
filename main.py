import scrapy
import spacy
from scrapy.crawler import CrawlerProcess
import pandas as pd
import re
from dateutil.parser import parse
from datetime import datetime, timedelta
from collections import defaultdict



# Load spaCy's English model
nlp = spacy.load("en_core_web_sm")

# Define the dictionary of awards and their URLs


awards_dict= {
    "Molson Prizes": [
        "https://canadacouncil.ca/funding/prizes/molson-prizes",
        "https://canadacouncil.ca/funding/prizes/molson-prizes/guidelines-molson-prizes"
    ],
    "Global Young Academy Membership": [
        "https://globalyoungacademy.net/call-for-new-members/",
        
    ],
    "Indspire Awards": [
        "https://indspire.ca/events/indspire-awards/"
    ],
    "Humboldt Research Award": [
        "https://www.humboldt-foundation.de/en/apply/sponsorship-programmes/humboldt-research-award"
    ],
    "Prix de reconnaissance de l'AFO": [
        "https://monassemblee.ca/prix-de-reconnaissance"
    ],
    "American Educational Research Association Awards": [
        "https://www.aera.net/About-AERA/Awards"
    ],
    "College of Physicians and Surgeons of Ontario Council Award": [
        "https://cpsodev.cpso.on.ca/en/About/Council/Council-Awards"
    ],
    "Committee of Presidents of Statistical Societies Awards": [
        "https://community.amstat.org/copss/awards/awards"
    ],
    "Computing Research Association Awards": [
        "https://cra.org/cra-wp/scholarships-and-awards/awards/"
    ],
    "Dorothy Killam Fellowships": [
        "https://programmekillamprogram.powerappsportals.com/en-CA/fundingopportunities/fodetails/?foid=4b490485-049f-ec11-b400-002248d5186d"
    ],
    "Order of Canada": [
        "https://www.gg.ca/en/honours/canadian-honours/order-canada"
    ],
    "Prix de l'Acfas": [
        "https://www.acfas.ca/prix-concours/prix-acfas/appel-candidatures"
    ],
    "Royal Society of Canada College of New Scholars, Artists and Scientists": [
        "https://rsc-src.ca/en/fellows-members/college-members"
    ]
}

class AwardSpider(scrapy.Spider):
    name = 'award_spider'
    
    def __init__(self, *args, **kwargs):
        super(AwardSpider, self).__init__(*args, **kwargs)
        self.awards_dict = awards_dict
        self.start_urls = [url for urls in self.awards_dict.values() for url in urls]
        self.results = defaultdict(lambda: defaultdict(set))
        self.nlp = spacy.load('en_core_web_sm')

    def parse(self, response):
        # Find the award name corresponding to the current URL
        award_name = next((name for name, urls in self.awards_dict.items() if response.url in urls), None)
        
        if not award_name:
            self.logger.warning(f"No matching award found for URL: {response.url}")
            return
        
        # Extract all text content
        content = ' '.join(response.css('body ::text').getall())
        doc = self.nlp(content)
        
        # Extract organization name
        org_name = self.extract_organization(doc)
        if org_name:
            self.results[award_name]['organization'].add(org_name)
        
        # Extract disciplines
        disciplines = self.extract_disciplines(doc)
        self.results[award_name]['disciplines'].update(disciplines)
        
        # Extract deadlines
        deadlines = self.extract_deadlines(content)
        if deadlines:
            self.results[award_name]['deadlines'].update(deadlines)
        
        # Extract award names
        award_names = self.extract_award_names(doc, award_name)
        self.results[award_name]['award_names'].update(award_names)
        
        # Extract level
        level = self.extract_level(content)
        if level:
            self.results[award_name]['level'].add(level)
        
        # Extract career stage
        career_stage = self.extract_career_stage(content)
        if career_stage:
            self.results[award_name]['career_stage'].add(career_stage)
        
        # Extract relevant source text snippets
        relevant_text = self.extract_relevant_text(content, org_name, deadlines, award_names)
        self.results[award_name]['source_urls'].add(response.url)
        self.results[award_name]['source_text'].add(relevant_text)

    def extract_organization(self, doc):
        for ent in doc.ents:
            if ent.label_ == 'ORG':
                return ' '.join(ent.text.split())
        return None
    
    def extract_disciplines(self, doc, all_domains=False):
        """
        Extracts disciplines from a document and optionally checks if the research awards include all disciplines.

        Parameters:
        - doc: A spaCy Doc object containing the text to analyze.
        - all_domains: Boolean flag to check if all predefined domains are covered.

        Returns:
        - A set of disciplines found in the document.
        - Optionally, a boolean indicating if all domains are covered.
        """
        # Define a set of discipline keywords
        discipline_keywords = {
            'science': 'Science',
            'art': 'Art',
            'humanities': 'Humanities',
            'engineering': 'Engineering',
            'medicine': 'Medicine',
            'social sciences': 'Social Sciences',
            'technology': 'Technology',
            'education': 'Education',
            'health science': 'Health Science',
            'statistics': 'Statistics',
            'natural sciences': 'Natural Sciences'
        }       
        # Initialize a set to hold the found disciplines
        found_disciplines = set()

        # Process each token in the document
        for token in doc:
            # Normalize token text and check if it matches any discipline keywords
            normalized_token = token.lemma_.lower()
            if normalized_token in discipline_keywords:
                found_disciplines.add(discipline_keywords[normalized_token])

        # Optionally check if all predefined domains are covered
        if all_domains:
            all_disciplines = set(discipline_keywords.values())
            return found_disciplines, all_disciplines.issubset(found_disciplines)
        else:
            return found_disciplines

    def extract_deadlines(self, content):
        """
        Extracts deadlines from the content. Only includes dates within a 2-year range (±2 years) from the current date.
        """
        # Define date patterns
        date_patterns = [
            r'\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}\b',
            r'\b\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}\b',
            r'\b\d{4}-\d{2}-\d{2}\b',
            r'\b\d{2}/\d{2}/\d{4}\b',
            r'\b\d{1,2}\s*\w+\s+\d{4}\b',  # Covers formats like "5 Oct 2024"
            r'\b\d{4}[-/]\d{2}[-/]\d{2}\b'  # Additional format for date like "2024-08-26" or "2024/08/26"
        ]

        deadlines = set()
        current_date = datetime.now().date()
        two_years_ago = current_date - timedelta(days=730)
        two_years_from_now = current_date + timedelta(days=730)

        for pattern in date_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                try:
                    # Parse the date and handle various formats
                    parsed_date = parse(match, fuzzy=False, dayfirst=False)
                    parsed_date = parsed_date.date()

                    # Check if the date is within the range
                    if two_years_ago <= parsed_date <= two_years_from_now:
                        deadlines.add(parsed_date)
                except (ValueError, TypeError):
                    continue

        return sorted(deadlines)  # Return sorted dates for better readability

    def extract_award_names(self, doc, main_award_name):
        award_names = set()
        award_keywords = ['award', 'prize', 'fellowship', 'scholarship', 'grant']
        
        # Extract sentences containing award-related keywords
        for sent in doc.sents:
            if len(sent.text.split()) > 5 and any(keyword in sent.text.lower() for keyword in award_keywords):
                possible_name = sent.text.strip()
                # Avoid adding full paragraphs or irrelevant text
                if (main_award_name.lower() not in possible_name.lower() and
                    not re.search(r'[.,]', possible_name)):
                    award_names.add(possible_name)
        
        return award_names

    def extract_level(self, content):
        """
        Extracts the level (Provincial, National, International) at which the award is offered.
        Prioritizes more specific matches and considers context.
        """
        level_keywords = {
            'Provincial': [
                r'\bOntario\sresidents\b', r'\bresidents\sof\sOntario\b', r'\bprovincial\b', r'\bOntario\b'
            ],
            'National': [
                r'\ball\sCanadians\b', r'\bCanadian\scitizens\b', r'\bresidents\sof\sCanada\b', r'\bCanadian\snational', 
                r'\bPermanent\sResidents\b', r'\bCanadians\b'
            ],
            'International': [
                r'\beveryone\b', r'\bregardless\sof\snationality\b', r'\binternational\b', r'\bopen\sto\sall\b', r'\binternationally\b'
            ]
        }

        detected_levels = []

        # Check each level and corresponding keywords
        for level, patterns in level_keywords.items():
            for pattern in patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    print (pattern)
                    detected_levels.append(level)
                    break  # Stop after finding the first match for this level

        # Prioritize levels if multiple are detected
        if 'Provincial' in detected_levels:
            return 'Provincial'
        elif 'National' in detected_levels:
            return 'National'
        elif 'International' in detected_levels:
            return 'International'

        return 'Unable to find'


    def extract_career_stage(self, content):
        # Define career stage keywords and patterns
        career_stage_keywords = {
            'Early Career': [
                r'\bearly career\b',
                r'\brecent\sPh\.D\.\b',
                r'\bPh\.D\.\swithin\sthe\slast\b',
                r'\bearly-stage\sresearchers\b'
            ],
            'Mid Career': [
                r'\bmid career\b',
                r'\bmid-stage\sresearchers\b'
            ],
            'Late Career': [
                r'\blate career\b',
                r'\bsenior\sresearchers\b'
            ],
            'Open': [
                r'\bregardless\sof\scareer\sstage\b',
                r'\ball\scareer\sstages\b'
            ]
        }

        # Preprocess content
        doc = nlp(content)
        sentences = list(doc.sents)
        
        detected_stages = set()

        # Check for career stages using keywords
        for stage, patterns in career_stage_keywords.items():
            for pattern in patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    detected_stages.add(stage)
        
        # Further validation based on sentence context
        for sentence in sentences:
            sentence_text = sentence.text.lower()
            for stage, patterns in career_stage_keywords.items():
                if any(re.search(pattern, sentence_text) for pattern in patterns):
                    detected_stages.add(stage)
        
        # Prioritize detected stages if multiple are found
        if 'Early Career' in detected_stages:
            return 'Early Career'
        elif 'Mid Career' in detected_stages:
            return 'Mid Career'
        elif 'Late Career' in detected_stages:
            return 'Late Career'
        elif 'Open' in detected_stages:
            return 'Open'

        return 'Unable to Find'
    
    def extract_relevant_text(self, content, org_name, deadlines, award_names):
        """
        Extract relevant snippets from the content based on identified entities.
        """
        relevant_snippets = []
        content_sentences = content.split('. ')
        
        # Convert deadlines to strings
        deadline_strings = [d.strftime('%B %d, %Y') for d in deadlines]
        
        for sentence in content_sentences:
            # Check if any of the keywords are present in the sentence
            if any(keyword in sentence for keyword in [org_name] + deadline_strings + list(award_names)):
                relevant_snippets.append(sentence.strip())
        
        return ' '.join(relevant_snippets)
    def close(self, reason):
        # Convert results to a DataFrame
        data = []
        order = []

        for award in self.awards_dict.keys():
            if award in self.results:
                details = self.results[award]
                org = ', '.join(details['organization']) if details['organization'] else 'Not found'
                disciplines = ', '.join(details['disciplines']) if details['disciplines'] else 'Not found'
                deadlines = ', '.join(str(d) for d in sorted(details['deadlines'])) if details['deadlines'] else 'Not found'
                award_names = ', '.join(details['award_names']) if details['award_names'] else 'Not found'
                level = ', '.join(details['level']) if details['level'] else 'Not found'
                career_stage = ', '.join(details['career_stage']) if details['career_stage'] else 'Not found'
                source_urls = ', '.join(details['source_urls']) if details['source_urls'] else 'Not found'

                data.append({
                    'Award': award,
                    'Disciplines': disciplines,
                    'Possible Deadlines': deadlines,
                    'Level': level,
                    'Career Stage': career_stage,
                    'Source URLs': source_urls,
                })
                order.append(award)  # Capture the order

        # Create DataFrame
        df = pd.DataFrame(data)

        # Reindex DataFrame to match the original order
        df = df.set_index('Award').reindex(order).reset_index()

        # Clean up any excessive whitespace or unwanted formatting
        df = df.applymap(lambda x: x.strip() if isinstance(x, str) else x)

        # Save the DataFrame to an Excel file with better formatting
        with pd.ExcelWriter("award_scrape_results1.xlsx", engine='xlsxwriter') as writer:
            df.to_excel(writer, sheet_name='Awards', index=False)
            
            # Apply formatting
            workbook = writer.book
            worksheet = writer.sheets['Awards']
            format_wrap = workbook.add_format({'text_wrap': True})
            format_bold = workbook.add_format({'bold': True})
            worksheet.set_column('A:H', 30, format_wrap)
            worksheet.set_row(0, None, format_bold)
            worksheet.autofilter('A1:H1')
        
        print("Results saved to award_scrape_results.xlsx")

def run_spider():
    process = CrawlerProcess(settings={
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'LOG_LEVEL': 'ERROR'
    })
    
    process.crawl(AwardSpider)
    process.start()

if __name__ == "__main__":
    run_spider()