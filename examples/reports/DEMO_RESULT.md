# 1. Integracja API (Weather)
```python
import requests
from typing import Optional

def get_weather(city: str) -> None:
    try:
        response = requests.get(f'https://api.weather.com/v1/current?city={city}', timeout=5)
        response.raise_for_status()
        
        data = response.json()
        temperature = data.get('temperature')
        if temperature is not None:
            print(f'Temperature: {temperature}')
        else:
            print("Error: Temperature key not found in the response.")
    
    except requests.exceptions.Timeout:
        print("Error: Request timed out.")
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            print("Error: City not found.")
        else:
            print(f"HTTP Error: {e}")
    except requests.exceptions.RequestException as e:
        print(f"Request Exception: {e}")

# Example usage:
get_weather('New York')
get_weather('InvalidCityName')  # This should trigger the 404 error handling.
```

# 2. Analiza Logów (Regex)
```python
import re

def parse_logs(log_text):
    # Regular expression to find IPs and errors
    ip_pattern = r'\b(?:\d{1,3}\.){3}\d{1,3}\b'
    error_pattern = r'(\d{3})'

    # Find all IPs and errors in the log text
    ips = re.findall(ip_pattern, log_text)
    errors = re.findall(error_pattern, log_text)

    return {
        "ips": ips,
        "errors": list(map(int, errors))  # Convert strings to integers
    }

# Example usage:
log_data = """
2024-01-01 12:00 [IP: 192.168.1.1] GET /index.html 200
2024-01-01 12:01 [IP: 192.168.1.2] GET /about.html 404
2024-01-01 12:02 [IP: 192.168.1.3] GET /contact.html 500
"""

result = parse_logs(log_data)
print(result)
# Output: {'ips': ['192.168.1.1', '192.168.1.2', '192.168.1.3'], 'errors': [200, 404, 500]}
```

# 3. Generator PDF (ReportLab)
```python
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

def create_invoice(filename, items):
    c = canvas.Canvas(filename, pagesize=letter)
    width, height = letter
    
    # Title
    c.setFont("Helvetica-Bold", 16)
    c.drawString(72, height-50, "INVOICE")
    
    # Items and Prices
    y_position = height - 80
    for item in items:
        c.setFont("Helvetica", 12)
        c.drawString(72, y_position, f"{item['name']}: ${item['price']:.2f}")
        y_position -= 20
    
    # Total Sum
    total_sum = sum(item['price'] for item in items)
    c.drawString(72, y_position-40, f"Total: ${total_sum:.2f}")
    
    # Save the PDF
    c.save()

# Example usage:
items = [
    {"name": "Item 1", "price": 10.99},
    {"name": "Item 2", "price": 5.50},
    {"name": "Item 3", "price": 2.75}
]
create_invoice("invoice.pdf", items)
print("Invoice created successfully.")
```
