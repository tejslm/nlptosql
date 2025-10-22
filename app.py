from google.cloud import bigquery
from google.oauth2 import service_account
import google.generativeai as genai
import streamlit as st
import json

# Configure Google Generative AI
GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
genai.configure(api_key=GEMINI_API_KEY)

# Configure project ID
project_id = st.secrets["project_id"]

# Define Your Prompt
with open("finalprompt.txt", "r") as file:
    prompt = file.read()

def get_gemini_response(user_input, prompt):
    from langchain_google_genai import ChatGoogleGenerativeAI
    model = ChatGoogleGenerativeAI(model='gemini-2.5-flash', api_key=GEMINI_API_KEY)
    question_for_llm = [("system", prompt), ("human", user_input)]
    response = model.invoke(question_for_llm)
    output_query = response.content.strip()
    
    # Remove ```sql ``` formatting
    if output_query.startswith("```sql"):
        output_query = output_query[6:-3].strip()
    elif output_query.startswith("```"):
        output_query = output_query[3:-3].strip()
    
    return output_query

# Connecting to BigQuery using TOML secrets
def execute_sql_from_file(output_query):
    # Load credentials from Streamlit secrets
    credentials = service_account.Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=["https://www.googleapis.com/auth/cloud-platform"]
    )

    client = bigquery.Client(
        credentials=credentials,
        project=project_id
    )
    
    try:
        query_job = client.query(output_query)
        results = query_job.result()
        formatted_results = [dict(row) for row in results]
        return formatted_results
    except Exception as e:
        st.error(f"Error executing query: {e}")
        return []

def convert_to_nl(row_string, prompt1):
    from langchain_google_genai import ChatGoogleGenerativeAI
    model = ChatGoogleGenerativeAI(model='gemini-2.5-flash', api_key=GEMINI_API_KEY)
    question_for_llm = [("system", prompt1), ("human", row_string)]
    response = model.invoke(question_for_llm)
    output_query = response.content.strip()
    return output_query

# Streamlit app
image_url = "https://freepngimg.com/thumb/disney/128008-genie-download-free-image.png"
st.image(image_url, caption='', width=200, use_column_width=None)
st.markdown("<h1 style='text-align: center;'>DBGenie</h1>", unsafe_allow_html=True)
st.header("Gemini App To Retrieve SQL Data")
st.write("Hi I'm DBGenie. Ask me anything about the data in your table and I'll answer in seconds")

question = st.text_input("Enter the question: ", key="input")
submit = st.button("Submit")

# If submit is clicked
if submit:
    with st.spinner("Generating SQL query..."):
        response = get_gemini_response(question, prompt)
    
    st.subheader("Generated SQL Query")
    st.code(response, language='sql')

    if response:
        with st.spinner("Executing query..."):
            data = execute_sql_from_file(response)
        
        st.subheader("The Response is")
        if data:
            # Load output prompt once
            with open("output_prompt.txt", "r") as file1:
                prompt1 = file1.read()
            
            # Process each row
            for row in data:
                row_string = json.dumps(row)
                natural = convert_to_nl(row_string, prompt1)
                st.write(natural)
        else:
            st.write("No data found for the given query.")
