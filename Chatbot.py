import streamlit as st
import time
import re

import urllib.request
import json
import os
import ssl

def allowSelfSignedHttps(allowed):
    # bypass the server certificate verification on client side
    if allowed and not os.environ.get('PYTHONHTTPSVERIFY', '') and getattr(ssl, '_create_unverified_context', None):
        ssl._create_default_https_context = ssl._create_unverified_context

def topic_service(text):
    allowSelfSignedHttps(True) # this line is needed if you use self-signed certificate in your scoring service.

    # Request data goes here
    # The example below assumes JSON formatting which may be updated
    # depending on the format your endpoint expects.
    # More information can be found here:
    # https://docs.microsoft.com/azure/machine-learning/how-to-deploy-advanced-entry-script
    data = {"data": text}

    body = str.encode(json.dumps(data))

    url = 'http://172.165.150.123:80/api/v1/service/gpu-rn50/score'


    headers = {'Content-Type':'application/json'}

    req = urllib.request.Request(url, body, headers)

    try:
        response = urllib.request.urlopen(req)

        result = response.read()
        return result
    except urllib.error.HTTPError as error:
        print("The request failed with status code: " + str(error.code))

        # Print the headers - they include the requert ID and the timestamp, which are useful for debugging the failure
        print(error.info())
        print(error.read().decode("utf8", 'ignore'))
        error_str = error.info() + "\n" + error.read().decode("utf8", 'ignore')
        return error_str

st.title("💬 Get the Topic")
st.caption("🚀 A complaint topic finder by Notting Hill Genesis")
if "messages" not in st.session_state:
    st.session_state["messages"] = [{"role": "assistant", "content": "Please write your complaint?"}]

for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])


if prompt := st.chat_input():
    
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user").write(prompt)
    
    res = topic_service(prompt)
    # Decode byte string into a regular string
    response_str = res.decode("utf-8")

    # Parse the inner JSON string into a dictionary
    inner_dict = json.loads(response_str)

    # Extract the 'result' key
    result_str = inner_dict.strip('"')

    # Parse the extracted JSON string into a dictionary
    result_dict = json.loads(result_str)

    
    # Access the value corresponding to the key 'result'
    main_topic_values = result_dict.get('main_topic', [])

    # Extract the single value from the list if it exists
    main_topic_value = main_topic_values[0] if main_topic_values else 'No main topic found'

    ner_topics_values = result_dict.get('ner_topics', [])

    # Initialize an empty list to collect the strings
    ner_strings = []

    # Iterate over the topics and add them to the list
    for t in ner_topics_values:
        # Skip empty topics
        if t.strip():
            ner_strings.append(f"- {t.strip()}")  # Add stripped topic to the list

    # Join the strings with commas and newlines
    ner_string = '\n\n'.join(ner_strings)

    if ner_topics_values:
        # If ner_topics_values is not empty, create a message with the topics
        msg = f"**Main Topic:** *{main_topic_value}* \n\n **Ner Topics:** \n\n {ner_string}"
    else:
        # If ner_topics_values is empty, indicate that no topics were found
        msg = f"**Main Topic:** *{main_topic_value}* \nNo ner topics found."


    message_placeholder = st.empty()

    # Initialize the full response
    full_response = ""

    # # Loop through each chunk of the response
    # for chunk in re.split(r'(\s+)', msg):
    #     # Add the chunk to the full response
    #     full_response += chunk + " "
        
    #     # Add a slight delay
    #     time.sleep(0.03)

    #     # Display the response with a blinking cursor
    #     message_placeholder.markdown(full_response + "|")

    # # Remove the blinking cursor after the loop completes
    # message_placeholder.markdown(full_response)
    # st.session_state.messages.append({"role": "assistant", "content": msg})
    # st.chat_message("assistant").write(msg)

    # Add the chunk to session state messages list
    # st.session_state.messages.append({"role": "assistant", "content": full_response})

    def stream_data():
        for word in msg.split(" "):
            yield word + " "
            time.sleep(0.02)
    
    with st.chat_message("assistant"):
        full_response = st.write_stream(stream_data())

    # Add the assistant's response to the chat history
    st.session_state.messages.append({"role": "assistant", "content": full_response})