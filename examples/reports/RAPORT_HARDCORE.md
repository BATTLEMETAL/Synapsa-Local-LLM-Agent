# 📝 RAPORT EGZAMINU (OFFLINE): 2026-01-04 09:01:09.048296
---
## 1. Python Singleton (Thread-Safe)
**Pytanie:** Implement a thread-safe Singleton class in Python using a metaclass. Explain why thread safety is crucial here.

### Odpowiedź Modelu:
<thinking>Thread safety is crucial because if multiple threads try to create an instance of the Singleton at the same time, they could end up creating more than one instance. This would violate the Singleton pattern's requirement that there should be only one instance of the class throughout the application.</thinking>

class MetaSingleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        # Check if an instance already exists
        if cls not in cls._instances:
            # If no instance exists, create one and store it in the dictionary
            cls._instances[cls] = super(MetaSingleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class Database(metaclass=MetaSingleton):
    def __init__(self):
        self.connection = "Database Connection"

    def query(self, sql):
        print(f"Executing: {sql}")
        return f"Result for '{sql}'"


# Usage example
if __name__ == "__main__":
    db1 = Database()
    db2 = Database()

    print(db1.query("SELECT * FROM users"))
    print(db2.query("DELETE FROM logs"))

    # Both variables point to the same object
    print(id(db1) == id(db2))  # Output: True

    # Modifying through either variable affects both
    db1.connection = "Modified Connection"
    print(db2.connection)  # Output: Modified Connection (Context: singleton.py)

---

## 2. Android Repository (Flow/Coroutines)
**Pytanie:** Implement a Repository pattern in Kotlin. Fetch data from Network, cache in Room Database, and emit Loading/Success/Error states using Flow to ViewModel.

### Odpowiedź Modelu:
<thinking>...</thinking>

---

## 3. Backend Concurrency (SQL Locking)
**Pytanie:** Write a Python function using SQLAlchemy to transfer money between two accounts. CRITICAL: Use `with_for_update` to prevent Race Conditions. Handle deadlocks ordering.

### Odpowiedź Modelu:
<thinking>...</thinking>
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()

class Account(Base):
    __tablename__ = 'accounts'
    
    id = Column(Integer, primary_key=True)
    name = Column(String)
    balance = Column(Integer)

engine = create_engine('sqlite:///:memory:')
Session = sessionmaker(bind=engine)
session = Session()

# Create some test data
account1 = Account(name='Alice', balance=500)
account2 = Account(name='Bob', balance=300)
session.add_all([account1, account2])
session.commit()

def transfer_money(from_account_id, to_account_id, amount):
    # Order by ID to avoid deadlock
    if from_account_id < to_account_id:
        first_id, second_id = from_account_id, to_account_id
    else:
        first_id, second_id = to_account_id, from_account_id
    
    with session.begin():
        from_acc = session.query(Account).filter_by(id=first_id).with_for_update().one()
        to_acc = session.query(Account).filter_by(id=second_id).with_for_update().one()
        
        from_acc.balance -= amount
        to_acc.balance += amount

transfer_money(1, 2, 100)  # Alice sends Bob $100
print(f"Alice's Balance: {session.query(Account).filter_by(id=1).scalar().balance}")
print(f"Bob's Balance: {session.query(Account).filter_by(id=2).scalar().balance}")

---

## 4. Circuit Breaker Pattern
**Pytanie:** Implement the 'Circuit Breaker' pattern in Python from scratch. Handle CLOSED, OPEN, HALF-OPEN states and timeout logic.

### Odpowiedź Modelu:
<thinking>Design a CircuitBreaker class that can be used to wrap any function call. The circuit breaker should have three states: closed (normal operation), open (due to previous failure) and half-open (waiting for recovery). It should also support timeouts.</thinking>

---

## 5. Big Data Processing (Memory Optimization)
**Pytanie:** Write a Python generator processing a 10GB CSV file to calculate rolling average. Memory usage must stay <50MB. Use `collections.deque`.

### Odpowiedź Modelu:
<thinking> To solve this problem, we need to create a Python generator that processes a large CSV file (up to 10GB) and calculates the rolling average of its values while keeping memory usage below 50MB. We'll use the `collections.deque` data structure to efficiently manage a sliding window of values.

Here's how you can implement this:

```python
import csv
from collections import deque

def read_large_csv(file_path):
    """Generator to read a large CSV file line by line."""
    with open(file_path, 'r') as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            yield row[0]  # Assuming the first column is numeric

def rolling_average_generator(data_source, window_size=3):
    """
    Generator to calculate the rolling average of a dataset.
    
    :param data_source: A generator yielding numerical data points.
    :param window_size: The size of the moving window.
    """
    buffer = deque(maxlen=window_size)

    def get_next_value():
        return next(data_source)

    try:
        # Fill the initial buffer
        for _ in range(window_size):
            buffer.append(float(get_next_value()))
        
        # Calculate and yield the first average
        current_avg = sum(buffer) / len(buffer)
        yield current_avg
        
        # Process the rest of the data
        while True:
            new_val = float(get_next_value())
            old_val = buffer.popleft()
            buffer.append(new_val)
            current_avg += (new_val - old_val) / window_size
            yield current_avg
    except StopIteration:
        pass

# Example usage:
if __name__ == "__main__":
    file_path = "large_dataset.csv"
    avg_gen = rolling_average_generator(read_large_csv(file_path))

    # Print the first few averages
    for i, avg in enumerate(avg_gen):
        if i >= 20:  # Limiting output to avoid spamming console
            break
        print(f"Average at step {i+1}: {avg}")
```

### Explanation:
1. **read_large_csv**: This generator reads a large CSV file one line at a time using `csv.reader`. It yields only the first column assuming it contains numerical data.

2. **rolling_average_generator**:
   - Takes a data source generator (`data_source`) and an optional `window_size`.
   - Uses a `deque` to maintain a sliding window of the last `window_size` elements.
   - Calculates the initial average based on the first `window_size` elements.
   - Asynchronously receives new values from the data source, updates the buffer, and recalculates the average without storing all past values explicitly.

This approach ensures that memory usage remains constant at approximately 50MB or less, regardless of the input file size up to 10GB. The key is maintaining only the necessary subset of data in the `deque`, which allows efficient calculation of the rolling average.

---
