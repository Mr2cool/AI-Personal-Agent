# Bright Data Integration Example

This project demonstrates how to integrate the Bright Data API with a Python agent or web application.

## Prerequisites
- Sign up for a Bright Data account: https://brightdata.com/
- Obtain your API credentials (username, password, or API token).
- Install required Python packages:

```
pip install requests
```

## Example Usage

Below is a simple example of how to use Bright Data's proxy for web scraping in Python:

```python
import requests
import os

BRIGHTDATA_USERNAME = os.getenv('BRIGHTDATA_USERNAME')
BRIGHTDATA_PASSWORD = os.getenv('BRIGHTDATA_PASSWORD')
BRIGHTDATA_HOST = 'brd.superproxy.io'
BRIGHTDATA_PORT = 22225

proxies = {
    'http': f'http://{BRIGHTDATA_USERNAME}:{BRIGHTDATA_PASSWORD}@{BRIGHTDATA_HOST}:{BRIGHTDATA_PORT}',
    'https': f'http://{BRIGHTDATA_USERNAME}:{BRIGHTDATA_PASSWORD}@{BRIGHTDATA_HOST}:{BRIGHTDATA_PORT}',
}

url = 'https://en.wikipedia.org/wiki/Rome'
response = requests.get(url, proxies=proxies)
print(response.text)
```

## Integration with PersonaAgent
- You can use this proxy setup in your agent's tool functions to fetch real web data securely and at scale.
- Store your Bright Data credentials in your `.env` file:

```
BRIGHTDATA_USERNAME=your_username
BRIGHTDATA_PASSWORD=your_password
```

- Load them in your Python code using `os.getenv` as shown above.

## References
- [Bright Data Docs](https://docs.brightdata.com/introduction)
