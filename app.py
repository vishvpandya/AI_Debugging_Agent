import streamlit as st
from dotenv import load_dotenv
import os
from groq import Groq
import requests

# Load env
load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# Memory
if "history" not in st.session_state:
    st.session_state.history = []

# -------------------------------
# Error classifier
# -------------------------------
def classify_error(error_text):
    if "TypeError" in error_text:
        return "TypeError"
    elif "IndexError" in error_text:
        return "IndexError"
    elif "KeyError" in error_text:
        return "KeyError"
    elif "ValueError" in error_text:
        return "ValueError"
    else:
        return "GeneralError"

# -------------------------------
# Real Web Search Tool
# -------------------------------
def web_search_tool(query):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}

        url = "https://en.wikipedia.org/w/api.php"
        params = {
            "action": "query",
            "list": "search",
            "srsearch": query,
            "format": "json"
        }

        res = requests.get(url, params=params, headers=headers)
        data = res.json()

        if data["query"]["search"]:
            title = data["query"]["search"][0]["title"]

            summary_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{title}"
            summary_res = requests.get(summary_url, headers=headers)
            summary_data = summary_res.json()

            return summary_data.get("extract", "No result found.")
        
        return "No useful result found."

    except Exception as e:
        return f"Error: {str(e)}"

# -------------------------------
# Agent
# -------------------------------
def debugging_agent(user_input):

    error_type = classify_error(user_input)

    use_tool = "why" in user_input.lower() or "how" in user_input.lower()

    tool_result = ""
    tool_used = False

    if use_tool:
        tool_used = True
        search_query = f"{error_type} Python error explanation"
        tool_result = web_search_tool(search_query)

    system_prompt = f"""
    You are an AI debugging agent.

    Error Type: {error_type}

    Provide:
    🔍 Explanation:
    🛠 Fix:
    💻 Improved Code:
    """

    messages = [{"role": "system", "content": system_prompt}]
    messages += st.session_state.history
    messages.append({"role": "user", "content": user_input})

    if tool_used:
        messages.append({"role": "system", "content": f"External info: {tool_result}"})

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=messages
    )

    reply = response.choices[0].message.content

    # Save memory
    st.session_state.history.append({"role": "user", "content": user_input})
    st.session_state.history.append({"role": "assistant", "content": reply})

    return reply, tool_result if tool_used else None

# -------------------------------
# UI
# -------------------------------
st.title("🤖 AI Debugging Agent")

user_input = st.text_input("Enter your error or question:")

if st.button("Debug"):
    if user_input:
        reply, tool_data = debugging_agent(user_input)

        if tool_data:
            st.subheader("🌐 Web Search Used")
            st.write(tool_data)

        st.subheader("💡 AI Response")
        st.write(reply)