import streamlit as st
from PIL import Image
import os
# import langchain
# from langchain.text_splitter import RecursiveCharacterTextSplitter
# from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.vectorstores import Chroma
# from langchain import OpenAI, VectorDBQA
# from langchain.chains import RetrievalQAWithSourcesChain
# import PyPDF2
from advertools import crawl
import pandas as pd
from langchain.document_loaders import DataFrameLoader
from langchain.text_splitter import CharacterTextSplitter,RecursiveCharacterTextSplitter
from langchain import OpenAI, VectorDBQA
from langchain.embeddings.openai import OpenAIEmbeddings


st.set_page_config(layout="centered", page_title="Website QnA")
# image = Image.open('GeekAvenue_logo.png')
 

# col1, mid, col2 = st.columns([1,2,20])
# with col1:
#     st.image(image, width=80)
# with col2:
#     st.header('Geek Avenue')
# st.write("---") # horizontal separator line.


st.header("Website QnA Bot 🤖")
state = st.session_state
site = st.text_input("Enter your URL here")
if st.button("Build Model"):
  
 
  if site is None:
    st.info(f"""Enter Website to Build QnA Bot""")
  elif site:
   
    st.write(str(site) + " starting to crawl..")
    try:

      my_bar = st.progress(0, text="Crawling in progress. Please wait.")
      if os.path.exists("simp.jl"):
        os.remove("simp.jl")
      crawl(site, 'simp.jl', follow_links=False)
      crawl_df = pd.read_json('simp.jl', lines=True)
      st.write(len(crawl_df))
      crawl_df = crawl_df[['body_text']]
      my_bar.progress(50, text="Building Vector DB.")
      st.write(crawl_df)

      #load df to langchain
      loader = DataFrameLoader(crawl_df, page_content_column="body_text")
      docs = loader.load()

      #chunking
      text_splitter = RecursiveCharacterTextSplitter(
      chunk_size=1000, chunk_overlap=0, separators=[" ", ",", "\n"]
      )
      doc_texts = text_splitter.split_documents(docs)


      #extract embeddings and build QnA Model
      openAI_embeddings = OpenAIEmbeddings(openai_api_key = st.secrets["openai_api_key"])
      vStore = Chroma.from_documents(doc_texts, openAI_embeddings)

      # Initialize VectorDBQA Chain from LangChain
      #deciding model
      model_name = "gpt-3.5-turbo"
      llm = OpenAI(model_name=model_name, openai_api_key = st.secrets["openai_api_key"])
      model = VectorDBQA.from_chain_type(llm=llm, chain_type="stuff", vectorstore=vStore)
      my_bar.progress(100, text="Model is ready.")
      st.session_state['crawling'] = True
      st.session_state['model'] = model
      st.session_state['site'] = site

    except Exception as e:
              st.error(f"An error occurred: {e}")
              st.error('Oops, crawling resulted in an error :( Please try again with a different URL.')
     
if site and ("crawling" in state):
      st.header("Ask your data")
      model = st.session_state['model']
      user_q = st.text_input("Enter your questions here")
      if st.button("Get Response"):
        try:
          with st.spinner("Model is working on it..."):
#             st.write(model)
            result = model({"query":user_q}, return_only_outputs=True)
            st.subheader('Your response:')
            st.write(result["result"])
        except Exception as e:
          st.error(f"An error occurred: {e}")
          st.error('Oops, the GPT response resulted in an error :( Please try again with a different question.')
