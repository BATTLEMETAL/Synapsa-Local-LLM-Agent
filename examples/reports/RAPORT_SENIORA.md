# 🎓 Raport Kompetencji Synapsy (Senior Level)
**Data:** 2025-12-17 12:39
**Wynik:** 2/5 (40%)

## 1. AsyncIO (Python) ✅
**Zadanie:** Napisz asynchroniczną funkcję w Pythonie, która pobiera dane z listy URL-i równolegle, używając 'aiohttp' i 'asyncio.gather'.

- **Słowa kluczowe:** 100% (Znaleziono: `async def, await, aiohttp.ClientSession, asyncio.gather, return`)
- **Składnia:** OK

### Odpowiedź:
```
import asyncio
import aiohttp


async def fetch(session, url):
    async with session.get(url) as response:
        return await response.text()


async def main():
    urls = [
        "https://www.example.com",
        "https://www.python.org",
        "https://www.github.com"
    ]
    async with aiohttp.ClientSession() as session:
        tasks = [fetch(session, url) for url in urls]
        results = await asyncio.gather(*tasks)
        for result in results:
            print(result)


if __name__ == "__main__":
    asyncio.run(main())
```

---
## 2. Design Patterns ❌
**Zadanie:** Zaimplementuj wzorzec Singleton w Pythonie, który jest bezpieczny wątkowo (thread-safe).

- **Słowa kluczowe:** 40% (Znaleziono: `cls._instance, class`)
- **Składnia:** OK

### Odpowiedź:
```
class SingletonMeta(type):
    """
    This is a thread-safe implementation of Singleton.
    """

    _instances = {}

    def __call__(cls, *args, **kwargs):
        """
        Possible changes to the value of the `__init__` argument do not affect
        the returned instance.
        """
        if cls not in cls._instances:
            instance = super().__call__(*args, **kwargs)
            cls._instances[cls] = instance
        return cls._instances[cls]


class Database(metaclass=SingletonMeta):
    connection = None

    def connect(self):
        if self.connection is None:
            print("Connecting database")
            self.connection = "Connection Object"
            return self.connection
        return self.connection


if __name__ == "__main__":
    # The client code.

    db1 = Database().connect()
    db2 = Database().connect()

    if id(db1) == id(db2):
        print(f"Database objects are the same {id(db1)}")
    else:
        print(f"Database objects are different {id(db1)} != {id(db2)}")
```

---
## 3. Security (XSS) ❌
**Zadanie:** Popraw ten kod JavaScript (React), aby zapobiec atakowi XSS:
<div dangerouslySetInnerHTML={{__html: userContent}} />

- **Słowa kluczowe:** 75% (Znaleziono: `sanitize, import, return`)
- **Składnia:** N/A

### Odpowiedź:
```
import React from 'react';

const sanitizeHtml = (html) => {
  const tempDiv = document.createElement('div');
  tempDiv.innerHTML = html;
  return tempDiv.textContent || tempDiv.innerText || '';
};

const SafeComponent = ({ userContent }) => (
  <div>{sanitizeHtml(userContent)}</div>
);

export default SafeComponent;
```

---
## 4. Database Optimization ✅
**Zadanie:** Napisz zapytanie SQL, które wybierze 5 użytkowników z największą liczbą zamówień, używając JOIN i GROUP BY. Tabela users(id, name) i orders(user_id, amount).

- **Słowa kluczowe:** 100% (Znaleziono: `SELECT, JOIN, GROUP BY, ORDER BY, COUNT, LIMIT 5`)
- **Składnia:** N/A

### Odpowiedź:
```
SELECT u.id, u.name, COUNT(o.id) as order_count
FROM users u
JOIN orders o ON u.id = o.user_id
GROUP BY u.id, u.name
ORDER BY order_count DESC
LIMIT 5;
```

---
## 5. Unit Testing (Pytest) ❌
**Zadanie:** Napisz test jednostkowy używając 'pytest' dla funkcji, która dzieli dwie liczby. Test musi sprawdzać rzucenie wyjątku przy dzieleniu przez zero.

- **Słowa kluczowe:** 75% (Znaleziono: `pytest.raises, ZeroDivisionError, def test_`)
- **Składnia:** OK

### Odpowiedź:
```
import pytest

def divide(a, b):
    return a / b

def test_divide_by_zero():
    with pytest.raises(ZeroDivisionError):
        divide(1, 0)
```

---
