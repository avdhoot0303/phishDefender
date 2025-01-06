# email_analysis.py

from textblob import TextBlob  # Sentiment analysis library
import language_tool_python  # For grammar checking
import re
from urllib.parse import urlparse

# Initialize language tool for grammar checking
grammar_tool = language_tool_python.LanguageTool('en-US')

# Suspicious domains for analysis (extendable)
suspicious_domains = ["phishing.com", "fraudulentdomain.com"]

def sentiment_analysis(email_body):
    """Analyze sentiment of the email body."""
    blob = TextBlob(email_body)
    sentiment = blob.sentiment.polarity  # Range from -1 (negative) to 1 (positive)
    return sentiment

def grammar_check(email_body):
    """Check for grammar/spelling mistakes in the email body."""
    matches = grammar_tool.check(email_body)
    return len(matches)  # Number of grammar issues

def is_suspicious_url(text):
    """Check if any URL in the email body is suspicious."""
    urls = re.findall(r'(https?://\S+)', text)
    if not urls:
        return False  # No URLs found

    for url in urls:
        parsed_url = urlparse(url)
        if parsed_url.netloc in suspicious_domains:
            return True
    return False

def analyze_email(email_body, sender_email):
    """Perform full analysis of the email including sender, URLs, and sentiment."""
    sender_domain = sender_email.split('@')[-1]
    
    # Get phishing prediction
    sentiment_score = sentiment_analysis(email_body)
    grammar_issues = grammar_check(email_body)
    url_suspicious = is_suspicious_url(email_body)

    # Build the analysis results
    analysis = {
        "sender_domain": sender_domain,
        "sentiment_score": sentiment_score,
        "grammar_issues": grammar_issues,
        "url_suspicious": url_suspicious,
        "sentiment_category": "Urgent/Fearful" if sentiment_score < -0.2 else "Neutral/Positive"
    }
    return analysis
