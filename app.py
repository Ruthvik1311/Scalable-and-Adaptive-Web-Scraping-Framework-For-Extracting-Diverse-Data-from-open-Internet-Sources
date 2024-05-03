import json
import os
import streamlit as st
import datetime
import random
import string
import re
import smtplib
import hashlib
import asyncio
import aiohttp
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import datetime
load_dotenv()
session_state = st.session_state
if "user_index" not in st.session_state:
    st.session_state["user_index"] = 0

st.set_page_config(
    page_title="Web Scraping App",
    page_icon="favicon.ico",
    layout="wide",
    initial_sidebar_state="expanded",
)

async def scrape_url(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            html_content = await response.text()
    st.markdown(f"## Scraping URL: {url}")
    soup = BeautifulSoup(html_content, "html.parser")
    text_elements = soup.find_all()
    with st.expander("Show full HTML content"):
        st.code(html_content, language="html")
    with st.expander("Show full text content"):
        text = "\n".join([element.get_text() for element in text_elements])
        st.code(text, language="html")
    name = url.split("/")[-1].split(".")[0]
    time = str(datetime.datetime.now()).replace(" ", "_").replace(":", "_")
    with open(f"scraped_content_{session_state['user_index']}_{name}_{time}.html", "w",encoding='utf-8') as file:
        file.write(html_content)


def user_exists(email, json_file_path):
    # Function to check if user with the given email exists
    with open(json_file_path, "r") as file:
        users = json.load(file)
        for user in users["users"]:
            if user["email"] == email:
                return True
    return False

def send_verification_code(email, code):
    SENDER_MAIL_ID = os.getenv("SENDER_MAIL_ID")
    APP_PASSWORD = os.getenv("APP_PASSWORD")
    RECEIVER = email
    server = smtplib.SMTP_SSL("smtp.googlemail.com", 465)
    server.login(SENDER_MAIL_ID, APP_PASSWORD)
    message = f"Subject: Your Verification Code\n\nYour verification code is: {code}"
    server.sendmail(SENDER_MAIL_ID, RECEIVER, message)
    server.quit()
    st.success("Email sent successfully!")
    return True

def generate_verification_code(length=6):
    return "".join(random.choices(string.ascii_uppercase + string.digits, k=length))

def signup(json_file_path="data.json"):
    st.title("Signup Page")
    with st.form("signup_form"):
        st.write("Fill in the details below to create an account:")
        name = st.text_input("Name:")
        email = st.text_input("Email:")
        age = st.number_input("Age:", min_value=0, max_value=120)
        sex = st.radio("Sex:", ("Male", "Female", "Other"))
        password = st.text_input("Password:", type="password")
        confirm_password = st.text_input("Confirm Password:", type="password")
        if (
            session_state.get("verification_code_eval") is None
            or session_state.get("verification_time_eval") is None
            or datetime.datetime.now() - session_state.get("verification_time_eval")
            > datetime.timedelta(minutes=5)
        ):
            verification_code = generate_verification_code()
            session_state["verification_code_eval"] = verification_code
            session_state["verification_time_eval"] = datetime.datetime.now()
        if st.form_submit_button("Signup"):
            if not name:
                st.error("Name field cannot be empty.")
            elif not email:
                st.error("Email field cannot be empty.")
            elif not re.match(r"^[\w\.-]+@[\w\.-]+$", email):
                st.error("Invalid email format. Please enter a valid email address.")
            elif user_exists(email, json_file_path):
                st.error(
                    "User with this email already exists. Please choose a different email."
                )
            elif not age:
                st.error("Age field cannot be empty.")
            elif not password or len(password) < 6:  # Minimum password length of 6
                st.error("Password must be at least 6 characters long.")
            elif password != confirm_password:
                st.error("Passwords do not match. Please try again.")
            else:
                verification_code = session_state["verification_code_eval"]
                send_verification_code(email, verification_code)
                entered_code = st.text_input(
                    "Enter the verification code sent to your email:"
                )
                if entered_code == verification_code:
                    user = create_account(
                        name, email, age, sex, password, json_file_path
                    )
                    session_state["logged_in"] = True
                    session_state["user_info"] = user
                    st.success("Signup successful. You are now logged in!")
                elif len(entered_code) == 6 and entered_code != verification_code:
                    st.error("Incorrect verification code. Please try again.")

def check_login(username, password, json_file_path="data.json"):
    try:
        with open(json_file_path, "r") as json_file:
            data = json.load(json_file)


        for user in data["users"]:
            if user["email"] == username and user["password"] == password:
                session_state["logged_in"] = True
                session_state["user_info"] = user
                st.success("Login successful!")
                return user
        return None
    except Exception as e:
        st.error(f"Error checking login: {e}")
        return None

def initialize_database(
    json_file_path="data.json"
):
    try:
        if not os.path.exists(json_file_path):
            data = {"users": []}
            with open(json_file_path, "w") as json_file:
                json.dump(data, json_file)

        
    except Exception as e:
        print(f"Error initializing database: {e}")

def create_account(name, email, age, sex, password, json_file_path="data.json"):
    try:
        if not os.path.exists(json_file_path) or os.stat(json_file_path).st_size == 0:
            data = {"users": []}
        else:
            with open(json_file_path, "r") as json_file:
                data = json.load(json_file)

        # Append new user data to the JSON structure
        email = email.lower()
        password = hashlib.md5(password.encode()).hexdigest()
        user_info = {
            "name": name,
            "email": email,
            "age": age,
            "sex": sex,
            "password": password,
        }

        data["users"].append(user_info)

        with open(json_file_path, "w") as json_file:
            json.dump(data, json_file, indent=4)

        st.success("Account created successfully! You can now login.")
        return user_info
    except json.JSONDecodeError as e:
        st.error(f"Error decoding JSON: {e}")
        return None
    except Exception as e:
        st.error(f"Error creating account: {e}")
        return None

def login(json_file_path="data.json"):
    st.title("Login Page")
    username = st.text_input("Email:")
    password = st.text_input("Password:", type="password")
    password = hashlib.md5(password.encode()).hexdigest()
    username = username.lower()

    login_button = st.button("Login")

    if login_button:
        user = check_login(username, password, json_file_path)
        if user is not None:
            session_state["logged_in"] = True
            session_state["user_info"] = user
        else:
            st.error("Invalid credentials. Please try again.")

def get_user_info(email, json_file_path="data.json"):
    try:
        with open(json_file_path, "r") as json_file:
            data = json.load(json_file)
            for user in data["users"]:
                if user["email"] == email:
                    return user
        return None
    except Exception as e:
        st.error(f"Error getting user information: {e}")
        return None

def render_dashboard(user_info, json_file_path="data.json"):
    try:
        st.title(f"Welcome to the Dashboard, {user_info['name']}!")
        st.subheader("User Information:")
        st.write(f"Name: {user_info['name']}")
        st.write(f"Sex: {user_info['sex']}")
        st.write(f"Age: {user_info['age']}")
        
        st.image("https://i.imgur.com/6zM7JBq.png", use_column_width=True)
        st.markdown("## What is Web Scraping?")
        st.markdown("Web scraping is a technique to automatically access and extract large amounts of information from a website, which can save a huge amount of time and effort.")
        st.markdown("## How does Web Scraping work?")
        st.markdown("Web scraping involves fetching the web page and extracting the data from it. The fetching process is done by a piece of code called a scraper.")
        st.markdown("## Why Web Scraping?")
        st.markdown("Web scraping is used to collect large information from websites and process it into structured data for further use.")
        st.markdown("## Applications of Web Scraping:")
        st.markdown("1. Price Monitoring")
        st.markdown("2. Email Address Gathering")
        st.markdown("3. Social Media Scraping")
        st.markdown("4. Job Posting Details")
        st.markdown("5. Real Estate Data")
        st.markdown("6. Research and Development")
        st.markdown("7. Weather Data Monitoring")
        st.markdown("8. Government Data Monitoring")
        st.markdown("9. Sports Data Monitoring")
        st.markdown("10. News Monitoring")
        st.markdown("11. Stock Market Data Monitoring")
        st.markdown("12. Travel Data Monitoring")
        st.markdown("13. Data for Machine Learning")
        st.markdown("14. Data for Data Analysis")
        st.markdown("15. Data for Data Visualization")

        st.markdown("## How to perform Web Scraping?")
        st.markdown("1. **Find the URL that you want to scrape**")
        st.markdown("2. **Inspecting the Page**")
        st.markdown("3. **Find the data you want to extract**")
        st.markdown("4. **Write the code**")
        st.markdown("5. **Run the code and extract the data**")
        st.markdown("6. **Store the data in the required format**")
        
    except Exception as e:
        st.error(f"Error rendering dashboard: {e}")
async def scraper(urls):
    start_time = datetime.datetime.now()
    tasks = [scrape_url(url) for url in urls]
    await asyncio.gather(*tasks)
    end_time = datetime.datetime.now()
    duration = end_time - start_time
    st.markdown(f"## Total scraping time: {duration}")
    
    
def main():
    st.title("Web Scraping App")
    page = st.sidebar.radio(
        "Go to",
        (
            "Signup/Login",
            "Dashboard",
            "Perform Web Scraping",
        ),
        key="page",
    )

    if page == "Signup/Login":
        st.title("Signup/Login Page")
        login_or_signup = st.radio(
            "Select an option", ("Login", "Signup"), key="login_signup"
        )
        if login_or_signup == "Login":
            login()
        else:
            signup()

    elif page == "Dashboard":
        if session_state.get("logged_in"):
            render_dashboard(session_state["user_info"])
        else:
            st.warning("Please login/signup to view the dashboard.")

    elif page == "Perform Web Scraping":
        if session_state.get("logged_in"):

            st.title("Perform Web Scraping")
            urls = st.text_area("Enter the URLs to scrape (one URL per line):")
            urls = urls.split("\n")
            
            if st.button("Scrape"):
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(scraper(urls))
        else:
            st.warning("Please login/signup to access this page.")
            
if __name__ == "__main__":
    initialize_database()
    main()
