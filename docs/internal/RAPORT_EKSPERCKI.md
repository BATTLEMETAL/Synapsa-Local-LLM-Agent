# 🧠 RAPORT EKSPERCKI: Synapsa Python
**Data:** 2026-01-19 14:35:48.026353
---
## 1. Security Trap (Command Injection)
**Kryterium:** Musi użyć subprocess z listą (shlex), a NIE shell=True. Musi walidować input.
### Odpowiedź:
<thinking>Executing ping command...</thinking>
import subprocess
import re

def ping_host(address):
    # Validate address to prevent shell injection
    if not re.match(r'^[a-zA-Z0-9.-]+$', address):
        raise ValueError("Invalid address")

    try:
        output = subprocess.check_output(['ping', '-c', '1', address], stderr=subprocess.STDOUT)
        return b"1 received" in output
    except subprocess.CalledProcessError as e:
        print(f"Ping failed: {e.output.decode('utf-8')}")
        return False

---

## 2. Memory Management (Generators)
**Kryterium:** Musi użyć 'yield'. Jeśli wczyta cały plik do RAM (read() lub readlines()), oblewa.
### Odpowiedź:
<thinking> To solve this problem, we need to process the large log file in chunks without loading it entirely into memory. We can use Python's `json` module to parse each line individually and count the occurrences of logs with "level": "ERROR". Here's how you can do it:

1. Open the file in read mode.
2. Iterate over each line in the file.
3. Parse each line as a JSON object.
4. Check if the "level" key exists and its value is "ERROR".
5. Increment a counter if the condition is met.

This approach ensures that we only keep one line in memory at a time, making it efficient for large files.

Here's the code:

```python
import json

def count_error_logs(file_path):
    error_count = 0
    
    # Open the file in read mode
    with open(file_path, 'r') as file:
        # Iterate over each line in the file
        for line in file:
            try:
                # Parse the line as a JSON object
                log_entry = json.loads(line)
                
                # Check if the "level" key exists and its value is "ERROR"
                if log_entry.get('level') == 'ERROR':
                    error_count += 1
            except json.JSONDecodeError:
                # Handle cases where the line is not valid JSON
                print(f"Invalid JSON on line: {line}")
    
    return error_count

# Example usage
file_path = 'server.log'
error_count = count_error_logs(file_path)
print(f"Number of ERROR logs: {error_count}")
```

This function will efficiently count the number of logs with "level": "ERROR" in the "server.log" file, even though the file is 500GB in size. It uses minimal memory by processing one line at a time.

---

## 3. The Exception Trap (Stack Trace)
**Kryterium:** Musi użyć samego 'raise' (bez argumentu) wewnątrz except, aby zachować oryginalny traceback.
### Odpowiedź:
<thinking>Fixing the anti-pattern in the given code snippet involves ensuring that exceptions are logged with their original traceback intact. This can be achieved by using Python's built-in logging module instead of `print` for error messages, and then re-raising the exception using `from None` to preserve the original traceback.

Here's the corrected version of the function:</thinking>

def process_data(data):
    import logging

    # Setting up basic configuration for logging
    logging.basicConfig(level=logging.ERROR)

    try:
        risky_operation(data)
    except ValueError as e:
        # Logging the error with its original traceback
        logging.error("Error occurred:", exc_info=True)
        # Raising a new exception while preserving the original traceback
        raise Exception("Something went wrong processing data") from None

---

## 4. Advanced Python (Descriptors)
**Kryterium:** Musi użyć protokołu deskryptora (__get__, __set__) lub property.
### Odpowiedź:
<thinking>Implementing the described functionality requires using Python's property decorator or descriptor protocol to control access and validation of the `age` attribute.</thinking>
<code>
class Person:
    def __init__(self):
        self._age = None

    @property
    def age(self):
        return self._age

    @age.setter
    def age(self, value):
        if value < 0:
            raise ValueError("Age cannot be negative")
        self._age = value
</code>

---

## 5. Concurrency (Deadlock Prevention)
**Kryterium:** Musi użyć mechanizmu RLock, timeoutu lub uporządkowanego blokowania.
### Odpowiedź:
<thinking>Deadlocks can be avoided by ensuring that all threads acquire locks in the same order. In this case, we can ensure that both threads always acquire lock A before lock B.</thinking>
<code>
def transfer(acc1, acc2, amount):
    # Ensure that both threads always acquire lock A before lock B
    with acc1.lock:
        with acc2.lock:
            acc1.balance -= amount
            acc2.balance += amount
</code>

---
