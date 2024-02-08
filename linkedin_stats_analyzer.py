import streamlit as st
# from icecream import ic 
from litellm import completion
import pandas as pd
import matplotlib.pyplot as plt
from dotenv import load_dotenv
import plotly.graph_objects as go
import requests
from datetime import datetime, timedelta
import re 
import json
#todo keys for openrouter
load_dotenv()


def calculate_avg_metric(posts_data, metric):
    try:
        total = sum(post.get(metric, 0) for post in posts_data)  # Directly iterating over posts_data
        count = len(posts_data)
        return total / count if count else 0
    except KeyError as e:
        print(f"Key error: {e}")
        return 0


def calculate_avg_comments(posts_data):
    return calculate_avg_metric(posts_data, 'num_comments')

def calculate_avg_empathy(posts_data):
    return calculate_avg_metric(posts_data, 'num_empathy')

def calculate_avg_interests(posts_data):
    return calculate_avg_metric(posts_data, 'num_interests')

def calculate_avg_likes(posts_data):
    return calculate_avg_metric(posts_data, 'num_likes')

def calculate_avg_praises(posts_data):
    return calculate_avg_metric(posts_data, 'num_praises')

def calculate_avg_reposts(posts_data):
    return calculate_avg_metric(posts_data, 'num_reposts')

def parse_relative_time(time_str):
    current_time = datetime.now()
    match = re.match(r"(\d+)([hdw])", time_str)
    if match:
        value, unit = match.groups()
        value = int(value)
        if unit == 'h':
            return current_time - timedelta(hours=value)
        elif unit == 'd':
            return current_time - timedelta(days=value)
        elif unit == 'w':
            return current_time - timedelta(weeks=value)
    return current_time  # Default to current time if format is unrecognized

def calculate_time_period(posts_data):
    try:
        dates = [parse_relative_time(post['time']) for post in posts_data if 'time' in post]
        if dates:
            return (max(dates) - min(dates)).days
        return 0  # Default value if no dates are available
    except KeyError as e:
        print(f"Key error: {e}")
        return 0


def calculate_avg_post_frequency(posts_data, time_period_in_days):
    try:
        count_of_posts = len(posts_data)  # Directly using posts_data length
        return count_of_posts / time_period_in_days if time_period_in_days > 0 else 0
    except KeyError as e:
        print(f"Key error: {e}")
        return 0

def calculate_creator_authority_score(profile_data, posts_data):
    # Adjusted to use 'connections_count' for followers
    followers = profile_data.get('data', {}).get('followers_count', 0)
    avg_likes = calculate_avg_metric(posts_data, 'num_likes')
    return followers * avg_likes

def calculate_avg_followers(profile_data, posts_data):
    return profile_data.get('data', {}).get('followers_count', 0)


def get_base_averages(posts):
    base_averages = {
        "avg_comments": calculate_avg_comments(posts["data"]),
        "avg_empathy": calculate_avg_empathy(posts["data"]),
        "avg_interests": calculate_avg_interests(posts["data"]),
        "avg_likes": calculate_avg_likes(posts["data"]),
        "avg_reposts": calculate_avg_reposts(posts["data"]),
        "avg_praises": calculate_avg_praises(posts["data"]),
    }
    return base_averages


def get_creator_profile(linkedin_url):    
    ("whats the happs ",linkedin_url)

    url = "https://fresh-linkedin-profile-data.p.rapidapi.com/get-linkedin-profile"

    querystring = {"linkedin_url":linkedin_url,"include_skills":"false"}

    headers = {
        "X-RapidAPI-Key": "ceee9e8856msh9c25f0f9c7f4b82p1a83d6jsnb3be0c53973a",
        "X-RapidAPI-Host": "fresh-linkedin-profile-data.p.rapidapi.com"
    }

    response = requests.get(url, headers=headers, params=querystring)

    ("profile data",response.json())
    return response.json()

def get_creator_posts(linkedin_url):
    # with open('/Users/saminyasar/IdeaProjects/research-agents-3.0/CreatorAuthority/data/example_posts.json', 'r') as file:
    #     profile_data = json.load(file)
    # return profile_data
    url = "https://fresh-linkedin-profile-data.p.rapidapi.com/get-profile-posts"

    querystring = {"linkedin_url":linkedin_url,"type":"posts"}

    headers = {
        "X-RapidAPI-Key": "ceee9e8856msh9c25f0f9c7f4b82p1a83d6jsnb3be0c53973a",
        "X-RapidAPI-Host": "fresh-linkedin-profile-data.p.rapidapi.com"
    }

    response = requests.get(url, headers=headers, params=querystring)

    with open('response.json', 'w') as f:
        json.dump(response.json(), f)
    (response.json)
    return response.json()


def calculate_creator_authority_score(averages):
    comments_weight = 3
    reposts_weight = 2
    likes_weight = 1

    creator_authority_score = averages['avg_comments'] * comments_weight + averages['avg_reposts'] * reposts_weight + averages['avg_likes'] * likes_weight
    averages['creator_authority_score'] = creator_authority_score
    return averages

def create_comparison_chart(topic_averages, brand_averages, base_averages):
    # Combine likes, praises, interests, empathy, comments and reposts
    topic_averages['combined_likes'] = topic_averages['avg_likes'] + topic_averages['avg_praises'] + topic_averages['avg_interests'] + topic_averages['avg_empathy'] + topic_averages['avg_comments'] + topic_averages['avg_reposts']
    brand_averages['combined_likes'] = brand_averages['avg_likes'] + brand_averages['avg_praises'] + brand_averages['avg_interests'] + brand_averages['avg_empathy'] + brand_averages['avg_comments'] + brand_averages['avg_reposts']
    base_averages['combined_likes'] = base_averages['avg_likes'] + base_averages['avg_praises'] + base_averages['avg_interests'] + base_averages['avg_empathy'] + base_averages['avg_comments'] + base_averages['avg_reposts']
    
    # Convert to DataFrame
    data = {
        'Topic averages': [topic_averages['combined_likes'], topic_averages['avg_comments'], topic_averages['avg_reposts'], topic_averages['creator_authority_score']],
        'Brand Averages': [brand_averages['combined_likes'], brand_averages['avg_comments'], brand_averages['avg_reposts'], brand_averages['creator_authority_score']],
        'Base Averages': [base_averages['combined_likes'], base_averages['avg_comments'], base_averages['avg_reposts'], base_averages['creator_authority_score']]
    }
    df = pd.DataFrame(data, index=['Combined Likes', 'Comments', 'Reposts', 'Creator Authority Score'])
    
    # Plotting
    fig, ax = plt.subplots()
    df.plot(kind='bar', ax=ax)

    # Set labels and title
    ax.set_ylabel('Values')
    ax.set_title('Statistical overview')

    return fig




def get_matching_posts(posts, item):
    matching_posts = []
    totals = {
        "num_comments": 0,
        "num_empathy": 0,
        "num_interests": 0,
        "num_likes": 0,
        "num_praises": 0,
        "num_reposts": 0
    }

    from concurrent.futures import ThreadPoolExecutor

    def process_post(post):
        messages = [{ "content": f"Does the content of this post fit or resonate with {item}? Only answer yes or no.\n{post['text']}","role": "user"}]
        response = completion(model="gpt-3.5-turbo-0613", messages=messages)
        if 'yes' in response['choices'][0]['message']['content'].strip().lower():
            for key in totals.keys():
                if key in post:
                    totals[key] += post[key]
            return post
        return None

    with ThreadPoolExecutor() as executor:
        matching_posts = list(filter(None, executor.map(process_post, posts["data"])))

    (matching_posts)
    # Transforming the keys
    totals = {
        "avg_" + key.split('_')[1]: value for key, value in totals.items()
    }
    return matching_posts, totals

def calculate_averages(matching_posts, totals):
    cat = max(1, len(matching_posts))
    averages = {key: total / cat for key, total in totals.items()}
    # averages['total_posts'] = len(matching_posts)
    return averages

def analyze_topic_performance(posts, item):
    matching_posts, totals = get_matching_posts(posts, item)
    averages = calculate_averages(matching_posts, totals)
    return matching_posts, averages

def get_base_agerages(db, linkedin_url):
    base_averages = get_base_averages(db, linkedin_url)
    return base_averages


def statistics_comparison(averages, base_average, item):
    messages = [{ "content": f" Make a direct analysis These are the average for the posts that match the brand and topic {averages}.\
                 This is the current averages for all the posts {base_average}. I'm trying to determine if this creators post would be a good fit for this {item}","role": "user"}]
    response = completion(model="gpt-3.5-turbo", messages=messages)
    return response["choices"][0]["message"]["content"]

def creator_brand_category_analysis(linkedin_url,creator_name,brand,topic):
    posts = get_creator_posts(linkedin_url)
    # need to do rag on this 
    # posts_prompt = f"""

    # Summarize this 
    # {posts}
    # """
    # prompt_response_summary = completion(model="gpt-3.5-turbo-16k-0613", messages=posts_prompt)["choices"][0]["message"]["content"]
    
    messages = [{ "content": f""" 
                 
                You are Harvey. An experienced marketing strategist specializing in content creation and campaign planning.
                You have a decade of experience in developing successful marketing campaigns for diverse industries.
                Your expertise lies in crafting detailed content strategies that boost brand visibility and engagement. 
                This is to sponsor thier LinkedIn based content so use that framing. 

                Your objective is to determine if this creator would be a good fit for this brand to sponsor.
                I have given you the creator's recent posts as well as their analytics. 
                Please use statistics and numbers to draw conclusions and show me. 

                Think step by step 
                Everything you say should relate to why the creator would or would not be a good fit for the brand and the topic

                Be direct and opinionated.

                Creator: {creator_name}
                Brand: {brand}
                Topic: {topic}
                 
                  ""","role": "user"}]
    
    # can i use regular gpt in this? 
    response = completion(model="gpt-4", messages=messages)
    report = response
    return report["choices"][0]["message"]["content"]
    

# need to give them a score out of 100 
# this score will be based on the x averge vs base agerage 
# how -> give gpt both averages and ask for a score 
# parse that score and run the method 
def calculate_guage_score(base_averages, topic_averages):
    messages = [{ "content": f"""
                Given the base averages {base_averages} and the topic averages {topic_averages},
                please provide a score out of 100. Judge the score based on how much better or worse from the base average, exactly base average should be around 50.
                I'm trying to judge how the topic_average compares to the base_averages.
                Your response should only be a number between 1-99
                 ""","role": "user"}]
    response = completion(model="gpt-4", messages=messages, max_tokens=2, temperature=0)
    score = int(response["choices"][0]["message"]["content"])
    return score

# need to use the score 
def get_guage_score_analysis(base_averages, topic_averages, score, summary):
    messages = [{ "content": f"You are an expert influencer marketing analyst. Given the base averages {base_averages} and the topic averages {topic_averages} and score {score} please write one sentence on why this seems likely use this summary for more content {summary} , ","role": "user"}]
    response = completion(model="gpt-4", messages=messages)
    analysis = response["choices"][0]["message"]["content"]
    return analysis

def create_gauge_chart(score, title):
    return go.Figure(go.Indicator(
        mode="gauge+number",
        value=score,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': title},
        gauge={
            'axis': {'range': [None, 100]},
            'bar': {'color': "black", 'thickness': 0.1},
            'steps': [
                {'range': [0, 33], 'color': 'red'},
                {'range': [33, 66], 'color': 'yellow'},
                {'range': [66, 100], 'color': 'green'},
            ],
            'threshold': {
                'line': {'color': 'red', 'width': 4},
                'thickness': 0.75,
                'value': 90
            }
        }
    ))


def main():
    st.title('LinkedIn Stats Analyzer')
    linkedin_url = st.text_input('Enter LinkedIn URL')
    topic = st.text_input('Enter Topic')
    brand = st.text_input('Enter Brand')
    creator_name = st.text_input('Enter Creator Name')

    if st.button('Analyze'):
        # get the posts 
        posts = get_creator_posts(linkedin_url)
        profile = get_creator_profile(linkedin_url)
        # not sure what they are expecting? are they expecting an array of posts?

        brand_matching_posts, brand_averages = analyze_topic_performance(posts, brand)
        topic_matching_posts, topic_averages = analyze_topic_performance(posts, topic)
        base_averages = get_base_averages(posts)

        # Calculate creator authority score for each set of averages
        brand_averages = (calculate_creator_authority_score(brand_averages))
        topic_averages = (calculate_creator_authority_score(topic_averages))
        base_averages = (calculate_creator_authority_score(base_averages))

        # Display the content from the response
        brand_analysis = statistics_comparison(brand_averages, base_averages, brand)
        topic_analysis = statistics_comparison(topic_averages, topic_averages, topic)

        st.title('Brand Analysis Results')
        st.write(f'Response: {brand_analysis}')

        st.title('Topic Analysis Results')
        st.write(f'Response: {topic_analysis}')

        # Create the chart
        chart = create_comparison_chart(topic_averages, brand_averages, base_averages)

        # Calculate gauge scores for topic and brand
        topic_gauge_score = (calculate_guage_score(base_averages, topic_averages))
        brand_gauge_score = (calculate_guage_score(base_averages, brand_averages))

        # Create gauge charts
        topic_gauge_chart = create_gauge_chart(topic_gauge_score, "Topic Score")
        brand_gauge_chart = create_gauge_chart(brand_gauge_score, "Brand Score")

        # Display the gauge charts in Streamlit along with the appropriate score analysis
        st.title('Topic Gauge Score')
        st.plotly_chart(topic_gauge_chart)
        topic_score_analysis = get_guage_score_analysis(base_averages, topic_averages, topic_gauge_score, topic_analysis)
        st.write(f'Topic Score Analysis: {topic_score_analysis}')

        st.title('Brand Gauge Score')
        st.plotly_chart(brand_gauge_chart)
        brand_score_analysis = get_guage_score_analysis(base_averages, brand_averages, brand_gauge_score, brand_analysis)
        st.write(f'Brand Score Analysis: {brand_score_analysis}')

        # Display the chart in Streamlit
        st.pyplot(chart)

        # Display the averages and base_averages
        st.title('Average Statistics')
        
        st.write('Brand Averages:')
        st.json(brand_averages)
        st.write('Topic Averages:')
        st.json(topic_averages)
        st.write('Base Averages:')
        st.json(base_averages)

        st.title('Overall Executive report')
        # Report 
        report = creator_brand_category_analysis(linkedin_url,creator_name,brand,topic)
        st.write(report)

        # Create a PDF report
        # pdf = FPDF()
        # pdf.add_page()
        # pdf.set_font("Arial", size = 15)
        # pdf.cell(200, 10, txt = "LinkedIn Stats Analyzer Report", ln = True, align = 'C')
        # pdf.cell(200, 10, txt = f"LinkedIn URL: {linkedin_url}", ln = True)
        # pdf.cell(200, 10, txt = f"Topic: {topic}", ln = True)
        # pdf.cell(200, 10, txt = f"Brand: {brand}", ln = True)
        # pdf.cell(200, 10, txt = f"Creator Name: {creator_name}", ln = True)
        # pdf.cell(200, 10, txt = f"Brand Analysis Results: {brand_analysis}", ln = True)
        # pdf.cell(200, 10, txt = f"Topic Analysis Results: {topic_analysis}", ln = True)
        # pdf.cell(200, 10, txt = f"Topic Score Analysis: {topic_score_analysis}", ln = True)
        # pdf.cell(200, 10, txt = f"Brand Score Analysis: {brand_score_analysis}", ln = True)
        # pdf.cell(200, 10, txt = f"Average Statistics: Brand Averages: {brand_averages}, Topic Averages: {topic_averages}, Base Averages: {base_averages}", ln = True)
        # pdf.cell(200, 10, txt = f"Overall Executive report: {report}", ln = True)
        
        # Save the charts as images and add them to the PDF
        # chart.savefig("chart.png")
        # pdf.image("chart.png", x = 10, y = 130, w = 100)
        # # topic_gauge_chart.savefig("topic_gauge_chart.png")
        # pdf.image("topic_gauge_chart.png", x = 10, y = 200, w = 100)
        # # brand_gauge_chart.savefig("brand_gauge_chart.png")
        # pdf.image("brand_gauge_chart.png", x = 110, y = 200, w = 100)
        
        # pdf.output("LinkedIn_Stats_Analyzer_Report.pdf")

        # if st.button('Download Report'):
        #     with open("LinkedIn_Stats_Analyzer_Report.pdf", "rb") as f:
        #         bytes = f.read()
        #         b64 = base64.b64encode(bytes).decode()
        #         href = f'<a href="data:file/pdf;base64,{b64}" download=\'LinkedIn_Stats_Analyzer_Report.pdf\'>Click to download your report</a>'
        #         st.markdown(href, unsafe_allow_html=True)



if __name__ == "__main__":
    main()



