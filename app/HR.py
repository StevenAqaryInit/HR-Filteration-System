import streamlit as st
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
from nltk.tokenize import word_tokenize
import string
import io
from docx import Document
import re
from st_aggrid.grid_options_builder import GridOptionsBuilder
from st_aggrid import AgGrid
import concurrent.futures
from pdfminer.high_level import extract_text
from sklearn.feature_extraction.text import CountVectorizer
from nltk.corpus import stopwords

class HRCV:
    def __init__(self):
        self.titles = []
        self.stop_words = set(stopwords.words('english'))
        self.vectorizer = CountVectorizer(stop_words='english')

    def extract_job_titles_1(self, text):
        # Define a regular expression pattern to match potential job titles
        pattern = r'\b(?:UI/UX\s*(?:Designer|Developer)|Marketing\s*Specialist|Programmer|Call\s*Center\s*Agent|Back[-\s]*End\s*Developer|UI\s*designer|Junior\s*Android\s*Developer|MOBILE\s*APPLICATION\s*DEVELOPER|UX\s*designer|Graphic\s*designer|Front[-\s]*End\s*Developer|Software\s*Developer|Technical\s*Writer|Mobile\s*Developer|Flutter\s*Developer|DevOps|Sales\s*Manager|Machine\s*Learning\s*(?:Developer|Engineer|ML\s*Engineer|Data\s*Scientist|ML\s*Developer)|Python\s*Developer|Data\s*Analyst|Go\s*Developer|Golang\s*Developer|Full[-\s]*Stack\s*(?:Developer)?|System\s*Analyst|Cyber[-\s]*Security\s*Engineer|React\s*js\s*Developer|Quality\s*Assurance\s*(?:Developer)?|Software\s*Solution\s*Architect|Digital\s*Marketing\s*Expert|Listing\s*Manager|Real\s*Estate\s*[-\s]*Sales\s*and\s*Leasing\s*Agent|Video\s*Editor|Photographer|Real\s*estate\s*Listing\s*Coordinator|Team\s*Leader\s*[-\s]*Real\s*Estate|Leasing\s*Agent|Sales\s*and\s*Leasing\s*Agent|Sales\s*Agent)\b'

        # Use the findall function to extract all occurrences of job titles in the text
        job_titles = re.findall(pattern, text, flags=re.IGNORECASE)

        return job_titles



    @st.cache_data
    def get_main_phones(_self, raw_phone_numbers):
        
        phone_pattern = re.compile(r'\d*\.?\d+')
        phone_numbers = [match.group() for match in phone_pattern.finditer(raw_phone_numbers)]
        for phone in phone_numbers:
            if len(phone) > 8:
                return phone



    def show(self, df):
        try:
            gd = GridOptionsBuilder.from_dataframe(df.iloc[:, 1:])
            gd.configure_selection(selection_mode='single'
                                , use_checkbox=True)
            gd.configure_grid_options(alwaysShowVerticalScroll = True, enableRangeSelection=True, pagination=True)
            grid_options = gd.build()

            grid_table = AgGrid(df
                                , gridOptions=grid_options
                                , height=600)
            
            values = grid_table.selected_rows.values[0][1:]
            keys = list(grid_table.selected_rows)[1:]
            
            record = {}
            for key, value in zip(keys, values):
                record[key] = value

            return record
        except:
            pass

        
        
    @st.cache_data
    def filter_text(_self, text_content):
        tokens = word_tokenize(text_content)
        filtered_tokens = [word for word in tokens if word.lower() not in _self.stop_words]
        text = ' '.join(filtered_tokens)
        translation_table = str.maketrans('', '', string.punctuation)
        text = text.translate(translation_table)

        return text.lower()


    @st.cache_data
    def read_docx(_self, file):
        doc = Document(file)
        text_content = ""
        for paragraph in doc.paragraphs:
            text_content += ' '.join(paragraph.text.split('\n'))

        new_text = ' '.join(text_content.split('\n'))
        return new_text.lower().strip()


    @st.cache_data
    def read_pdf(_self, file):
        text = extract_text(pdf_file=file)
        new_text = ' '.join(text.split('\n'))
        return new_text.strip().lower()



    @st.cache_data
    def get_files_content(_self, cv):
        file_bytes = b''

        if cv.name.split('.')[-1] == 'pdf':
            file_bytes = io.BytesIO(cv.read())
            cleaned_text = _self.read_pdf(file_bytes)

        elif cv.name.split('.')[-1] == 'docx' or cv.split('.')[-1] == 'doc':
            file_bytes = io.BytesIO(cv.read())
            cleaned_text = _self.read_docx(file_bytes)

        postition = ''
        try:
            postition = _self.extract_job_titles_1(cleaned_text)[0]
        except:
            pass

        email_pattern = r'[\w\.-]+@[\w\.-]+'

        emails = ''
        try:
            emails = re.findall(email_pattern, cleaned_text)[0]
        except:
            pass

        phone_number = _self.get_main_phones(''.join(cleaned_text.split()).lower())
        return postition, phone_number, emails, file_bytes, cleaned_text


    @st.cache_data
    def go_to_threads(_self, files):
        df = pd.DataFrame()
        files_bytes = []
        position_list = []
        phone_number_list = []
        email_list = []
        _self.titles = []
        
        for cv in files:
            with concurrent.futures.ThreadPoolExecutor() as executor:
                thread = executor.submit(_self.get_files_content, cv)
                result_value = thread.result()
                
                position_list.append(result_value[0])
                phone_number_list.append(result_value[1])
                email_list.append(result_value[2])
                files_bytes.append(result_value[3])
                cleaned_text =  result_value[4]
                _self.titles.append(cv.name)
                df = pd.concat([df, pd.DataFrame([cleaned_text.lower()], columns=['cv'])], ignore_index=True)
                
        print('>>>>>>>>>>>>>', len(_self.titles))
        print('>>>>>>>>>>>>>', df.shape)
        
        df['title'] = _self.titles
        df['bytes'] = files_bytes
        df['postition'] = position_list
        df['phone_number'] = phone_number_list
        df['email'] = email_list

        return df


    # @st.cache
    def get_scores(self, cv, clean_keywords):
        matrix = self.vectorizer.fit_transform([cv, clean_keywords])
        scores = cosine_similarity(matrix)[0][1]

        return scores

