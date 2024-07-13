import streamlit as st
import nltk
import concurrent.futures
from streamlit_TTS import auto_play, text_to_audio
import plotly.express as px
import ollama
import warnings
from config import df, hr, clean_keywords


warnings.filterwarnings('ignore')
nltk.download('stopwords')
nltk.download('punkt')
nltk.download('corpus')


# model_name = "deepset/roberta-base-squad2"
# nlp = pipeline('question-answering', model=model_name, tokenizer=model_name)


st.title('CV Filteration')

files = st.file_uploader('Upload files', accept_multiple_files=True, type=['PDF', 'DOCX', 'DOC'])
keywords = st.text_area('Enter the keywords here...')


df = hr.go_to_threads(files)
try:
    clean_keywords = hr.filter_text(keywords)
except:
    pass

if clean_keywords != '':
    scores = []
    for cv in df.iloc[:, 0].values.tolist():
        with concurrent.futures.ThreadPoolExecutor() as executor:
            thread = executor.submit(hr.get_scores, cv, clean_keywords)
            result_value = thread.result()
            scores.append(result_value)
    
    df['scores'] = scores
    df['scores'] = df['scores'] * 100

    record = hr.show(df[['bytes', 'title', 'scores', 'postition', 'phone_number', 'email']].sort_values(by='scores', ascending=False).drop_duplicates())

    new_phone_number = ''
    row = ''

    try:
        row = df[df['title']==record['title']]
        new_phone_number = st.text_input("Is this the phone number that you want to send the message to ?", row['phone_number'].values[0])
    except:
            pass


    try:
        for file in files:
            if file.name == record['title']:
                st.download_button(
                    label="Download file",
                    data=bytes(file.getbuffer()),
                    file_name=row['title'].values[0],
                )
    except:
        pass


    st.write('--------------------------------------------------------------')
    st.header('Chatbot')
    question = st.text_input('Ask A Question...')


    years_of_experience = st.checkbox('What is the total years of experience ?')
    nationality = st.checkbox('What is the nationality ?')
    work_experience = st.checkbox('What is the work experience ?')
    skills = st.checkbox('What are the skills ?')
    technical_skills = st.checkbox('What are the technical skills ?')
    education_certificate = st.checkbox('What is the education certificate (degree) ?')
    visa_type = st.checkbox('What is the visa type if it\'s exist (visit / residence) ?')
    Custom = st.checkbox('Custom question')
    
    questions_list = []
    if years_of_experience:
        questions_list.append('What is the total years of experience ?')
    if nationality:
        questions_list.append('What is the nationality ?')
    if education_certificate:
        questions_list.append('What is the work experience ?')
    if work_experience:
        questions_list.append('What is the education certificate (degree) ?')
    if skills:
        questions_list.append('What is the skills ?')
    if technical_skills:
        questions_list.append('What is the technical skills ?')
    if visa_type:
        questions_list.append('What is the visa type if it\'s exist (visit / residence) ?')

    if Custom:
        question = st.text_input(label='Ask A Question...', key='Ask A Question...')
        questions_list.append(question)
    

    
    try:
        response = ollama.chat(model='llama3', messages=[
            {
                'role': 'user',
                'content':f'''
                    answer the user question from this context as points and highlight the important information and be direct in your response
                    context: {' '.join(row['cv'].values)}
                    question: {' '.join(questions_list)}
                    don't add extra information just answer the question
                ''',
            },
        ])
        
        res = response['message']['content']

        if st.button('ask'):
            st.write('The answer is: ', response['message']['content'])

        if st.button('read the answer'):
            audio=text_to_audio(response['message']['content'], language='en')
            auto_play(audio)
    except:
        pass


    st.write('---------------------------------------------')
    st.bar_chart(df['postition'].value_counts())

    fig = px.pie(df, names='postition', title='Positions Percentage')
    st.write('---------------------------------------------')
    st.plotly_chart(fig, use_container_width=True)

else:
    st.error('Enter Some Keywords...')