from dotenv import load_dotenv

load_dotenv()  # Loading all environment variables

from google.cloud import bigquery
from google.oauth2 import service_account
import google.generativeai as genai
import streamlit as st
import os
import json

# Define Your Prompt
file = open("input_prompt.txt", "r")
prompt = file.read()
file.close()

# Configure Genai key
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
key_path = "halogen-episode-433706-a4-6a1ca4a71658.json"
project_id = "halogen-episode-433706-a4"


# Function to load Google Gemini model and provide queries as response
def get_gemini_response(user_input, prompt):
    model = genai.GenerativeModel('gemini-pro')
    response = model.generate_content([prompt, user_input])
    output_query = response.text.strip()
    # Remove ```sql ``` formatting
    if output_query.startswith("```sql"):
        output_query = output_query[6:-3].strip()
    return output_query


# Connecting to BigQuery and get results using our table in the project
def execute_sql_from_file(key_path, project_id, output_query):
    credentials = service_account.Credentials.from_service_account_file(
        key_path, scopes=["https://www.googleapis.com/auth/cloud-platform"],
    )

    client = bigquery.Client(credentials=credentials, project=project_id)
    try:
        query_job = client.query(output_query)
        results = query_job.result()
        formatted_results = [dict(row) for row in results]
        return formatted_results
    except Exception as e:
        print(f"Error executing query: {e}")
        return []


# Streamlit app
image_url="https://freepngimg.com/thumb/disney/128008-genie-download-free-image.png"
st.image(image_url, caption='', width=200 , use_column_width=None)
st.markdown("<h1 style='text-align: center;'>DBGenie<h1>", unsafe_allow_html=True)
st.header("Gemini App To Retrieve SQL Data")
st.write("Hi I'm DBGenie. Ask me anything about the data in your table and I'll answer in seconds")

question = st.text_input("Enter the question: ", key="input")

submit = st.button("Submit")

# If submit is clicked
if submit:
    response = get_gemini_response(question, prompt)
    st.subheader("Generated SQL Query")
    st.code(response, language='sql')

    if response:
        data = execute_sql_from_file(key_path, project_id, response)
        st.subheader("The Response is")
        if data:
            for row in data:
                row_string = json.dumps(row)
                file1 = open("output_prompt.txt", "r")
                prompt1 = file1.read()
                file.close()
                def convert_to_nl(row_string, prompt1, question):
                    model = genai.GenerativeModel('gemini-pro')
                    response = model.generate_content([prompt1, row_string, question])
                    output_query = response.text.strip()
                    return output_query
                natural=convert_to_nl(row_string, prompt1, question)
                st.write(natural)
        else:
            st.write("No data found for the given query.")

