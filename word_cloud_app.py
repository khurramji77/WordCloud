import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from wordcloud import WordCloud, STOPWORDS
import PyPDF2
from docx import Document
import plotly.express as px
import base64
from io import BytesIO

# Function for reading file
def read_txt(file):
    return file.getvalue().decode("utf-8")

def read_docx(file):
    doc =  Document(file)
    return "".join([para.text for para in doc.paragraphs])

def read_pdf(file):
    pdf = PyPDF2.PdfReader(file)
    return "".join([page.extract_text() for page in pdf.pages])

# function to filter out stop words
def filter_stopwords(text, additional_stopwords=[]):
    words = text.split()
    all_stopwords = STOPWORDS.union(set(additional_stopwords))
    filter_words = [word for word in words if word.lower() not in all_stopwords]
    return "".join(filter_words)

# Function to create download link for plot
def get_image_download_link(buffered, format_):
    image_base64 = base64.b64encode(buffered.getvalue()).decode()
    return f'<a href="data:image{format_};base64,{image_base64}" download="wordcloud.{format_}">Download Plot as {format_}</a>'

# Function to download a dataframe
def get_table_download_link(df, filename, file_label):
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()
    return f'<a href="data:file/csv;base64,{b64}" download="{filename}">{file_label}</a>'

# Streamlit code
st.title("Word Cloud Generator")
st.subheader("Upload a pdf, docx, or text file to generate word cloud")

uploaded_file = st.file_uploader("Choose a file", type=["txt","pdf", "docx"])
st.set_option('deprecation.showPyplotGlobalUse', False)

if uploaded_file:
    file_details = {"FileName": uploaded_file.name, "FileType":uploaded_file.type, "FileSize":uploaded_file.size}
    st.write(file_details)

    # Check the file type and read the file
    if uploaded_file.type == 'text/plain':
        text = read_txt(uploaded_file)
    elif uploaded_file.type == 'application/pdf':
        text = read_pdf(uploaded_file)
    elif uploaded_file.type == 'application/vnd.openxmlformats-officedocument.wordprocessingml.document':
        text = read_docx(uploaded_file)
    else:
        st.error("File type not supported, Please upload a text, pdf, or docx file")
        st.stop()

    # Generate word count table
    words = text.split()
    word_count = pd.DataFrame({"Word":words}).groupby('Word').size().reset_index(name="Count").sort_values('Count', ascending=False)

    #Sidebar: Checkbox and Multiselect box for stopwords
    use_standard_stopwords = st.sidebar.checkbox("Use standard stopwords", True)
    top_words = word_count['Word'].head(50).tolist()
    additional_stopwords = st.sidebar.multiselect("Additional stopwords:", sorted(top_words))

    if use_standard_stopwords:
        all_stopwords = STOPWORDS.union(set(additional_stopwords))
    else:
        all_stopwords = set(additional_stopwords)

    text = filter_stopwords(text, all_stopwords)

    if text:
        # word cloud dimensions
        width =  st.sidebar.slider("Select word cloud width", 400, 2000, 1200, 50)
        height =  st.sidebar.slider("Select word cloud height", 200, 2000, 800, 50)

        # Generate word cloud
        st.subheader("Generated Word Cloud")
        fig, ax = plt.subplots(figsize=(width/100, height/100)) # convert pixels to inches for figs
        wordcloud_img = WordCloud(width=width, height=height, background_color='white', max_words=200, contour_width=3, contour_color='steelblue').generate(text)
        ax.imshow(wordcloud_img, interpolation='bilinear')
        ax.axis('off')
        # save plot functionality
        format = st.selectbox("Select the file format to save the plot", ["png","jpeg","svg","pdf"])
        resolution = st.slider("Select resolution", 100, 500, 300, 50)
        # Generate word count table
        st.subheader("Word Count Table")
        words = text.split()
        word_count = pd.DataFrame({"Word":words}).groupby('Word').size().reset_index(name="Count").sort_values('Count', ascending=False)
        st.write(word_count)
    st.pyplot(fig)
    if st.button(f"Save as {format}"):
        buffered = BytesIO()
        plt.savefig(buffered, format=format, dpi=resolution)
        st.markdown(get_image_download_link(buffered, format), unsafe_allow_html=True)

    # Word clout table at the end
    st.subheader("Word Cloud Table")
    st.write(word_count)
    # provide download link for table
    if st.button('Download Word Count Table as csv'):
        st.markdown(get_table_download_link(word_count, "word_count.csv", "Click here to download"), unsafe_allow_html=True)