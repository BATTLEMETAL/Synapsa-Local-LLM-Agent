# 🛡️ RAPORT GOTOWOŚCI PRODUKTOWEJ: Synapsa Python
**Data:** 2026-01-19 12:04
---
## Zadanie 1: 1. Modern Web (FastAPI + Pydantic)
**Wymagania:** Musi użyć Pydantic v2 (model_validate), asynchroniczności i Type Hintingu.
**Prompt:**
> Write a complete FastAPI endpoint for registering a user.
        Requirements:
        1. Receive JSON: username, email, password.
        2. Validate: email format, password min length 8.
        3. Hash the password (simulate it).
        4. Return 201 Created with the user ID (exclude password from response).
        5. Use Pydantic models for request and response.
        6. Use Python 3.10+ type hinting.

### Odpowiedź Synapsy:
<thinking>...</thinking>
from typing import Optional
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, EmailStr

router = APIRouter()

# Simulated database of users
users_db = {}

class User(BaseModel):
    username: str
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: int
    username: str
    email: EmailStr

@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register_user(user: User):
    # Step 1: Validate input data
    if not user.email.islower():
        raise HTTPException(status_code=400, detail="Email must be in lowercase")
    if len(user.password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters long")

    # Step 2: Check if user already exists
    if user.username in users_db:
        raise HTTPException(status_code=409, detail="Username already registered")

    # Step 3: Simulate hashing the password
    hashed_password = "hashed_" + user.password

    # Step 4: Add user to the database
    user_id = len(users_db) + 1
    users_db[user_id] = {
        "username": user.username,
        "email": user.email,
        "password": hashed_password
    }

    # Step 5: Return created user without the password
    return {"id": user_id, "username": user.username, "email": user.email}

---

## Zadanie 2: 2. Data Processing (Pandas Efficiency)
**Wymagania:** Nie może używać pętli for (iterrow). Musi użyć wektoryzacji.
**Prompt:**
> I have a Pandas DataFrame `df` with 10 million rows. Columns: 'price' (float), 'quantity' (int), 'category' (str).

        Write a highly optimized function to:
        1. Create a new column 'total' = price * quantity.
        2. Apply a 10% discount to 'total' ONLY where category is 'Electronics'.
        3. Remove rows where 'total' is 0.

        CRITICAL: Do NOT use any 'for' loops or .apply() if vectorization is possible. This must be fast.

### Odpowiedź Synapsy:
<thinking> To optimize this task, we need to leverage the power of vectorized operations in pandas. Here's how we can achieve the desired results efficiently:

1. **Create the 'total' column**: We can simply multiply the 'price' and 'quantity' columns to create the 'total' column.

2. **Apply the 10% discount**: For the 'Electronics' category, we can apply a 10% discount by multiplying the 'total' values for these rows by 0.9.

3. **Remove rows where 'total' is 0**: We can filter out the rows where 'total' is 0 using boolean indexing.

By following these steps, we ensure that all operations are performed using vectorized operations, which are generally much faster than applying functions row-wise or using loops.

Here's the implementation:

```python
import pandas as pd

def process_dataframe(df):
    # Step 1: Create the 'total' column
    df['total'] = df['price'] * df['quantity']

    # Step 2: Apply a 10% discount to 'total' only where category is 'Electronics'
    df.loc[df['category'] == 'Electronics', 'total'] *= 0.9

    # Step 3: Remove rows where 'total' is 0
    df = df[df['total'] != 0]

    return df
```

This function will efficiently perform the required operations on the DataFrame without using any 'for' loops or `.apply()` methods. The use of vectorized operations ensures that the function runs quickly even on large datasets like the one described.

---

## Zadanie 3: 3. Error Handling & Robustness (Retry Logic)
**Wymagania:** Musi użyć dekoratora, obsługi wyjątków i backoffu.
**Prompt:**
> Write a Python decorator `@robust_request` that wraps a function making an HTTP request (e.g., using `requests`).
        It should:
        1. Retry 3 times on specific errors (Timeout, ConnectionError).
        2. Implement exponential backoff (wait 1s, 2s, 4s).
        3. Log warnings on retries.
        4. Raise the exception after the final failure.

### Odpowiedź Synapsy:
<thinking>...</thinking>
import time
from functools import wraps

def robust_request(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        for attempt in range(3):
            try:
                return func(*args, **kwargs)
            except (Timeout, ConnectionError) as e:
                wait_time = 2 ** attempt
                print(f"Attempt {attempt + 1} failed: {e}. Retrying in {wait_time}s...")
                time.sleep(wait_time)
        raise Exception("Request failed after 3 attempts.")
    
    return wrapper


# Example usage with requests
import requests

@robust_request
def fetch_data(url):
    response = requests.get(url)
    response.raise_for_status()
    return response.json()

try:
    data = fetch_data('https://api.example.com/data')
    print(data)
except Exception as e:
    print(f"Final error: {e}")

---

## Zadanie 4: 4. The Hallucination Trap (Biblioteki)
**Wymagania:** Model nie może wymyślić funkcji, która nie istnieje.
**Prompt:**
> Using the standard `datetime` library in Python, write a function to calculate the number of *business days* (Mon-Fri) between two dates. 
        Do not use external libraries like `pandas` or `numpy` for this specific task, use only standard library.

### Odpowiedź Synapsy:
<thinking>import datetime
def business_days(start_date, end_date):
    # Convert string dates to datetime objects
    start = datetime.datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.datetime.strptime(end_date, "%Y-%m-%d")

    # Initialize count
    count = 0

    # Iterate over each day from start to end
    while start <= end:
        if start.weekday() < 5:  # Monday is 0, Friday is 4
            count += 1
        start += datetime.timedelta(days=1)

    return count</thinking>

---

## Zadanie 5: 5. Complex Architecture (Clean Arch)
**Wymagania:** Separacja warstw. Nie może mieszać logiki bazy danych z logiką biznesową.
**Prompt:**
> Design a Python class structure for a 'OrderProcessingService' following Clean Architecture principles.
        - Define an Interface (Abstract Base Class) for a `PaymentGateway`.
        - Implement a concrete `StripeGateway`.
        - Inject the gateway into the Service.
        - The Service should NOT know it's using Stripe.

### Odpowiedź Synapsy:
<thinking>Designing a clean architecture involves creating a modular system where dependencies flow in one direction. In this case, we want to design a service that processes orders without knowing which payment gateway is being used.</thinking>
<code>
# Step 1: Define the Payment Gateway Interface
from abc import ABC, abstractmethod

class PaymentGateway(ABC):
    @abstractmethod
    def process_payment(self, amount):
        pass

# Step 2: Implement a concrete Payment Gateway
class StripeGateway(PaymentGateway):
    def process_payment(self, amount):
        # Simulate a payment processing
        print(f"Processed payment of ${amount} via Stripe")
        return True

# Step 3: Create the Order Processing Service
class OrderProcessingService:
    def __init__(self, payment_gateway: PaymentGateway):
        self.payment_gateway = payment_gateway

    def place_order(self, order_id, amount):
        # Business logic here
        if not self.payment_gateway.process_payment(amount):
            raise Exception("Failed to process payment")

        # More business logic...
        print(f"Order {order_id} processed successfully")

# Usage example
if __name__ == "__main__":
    stripe_gateway = StripeGateway()
    order_service = OrderProcessingService(stripe_gateway)
    try:
        order_service.place_order("ORD123", 100)
    except Exception as e:
        print(e)
</code>

---
