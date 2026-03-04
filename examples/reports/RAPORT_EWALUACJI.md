# 📊 Raport Skuteczności Synapsy

**Data:** 2025-12-16 09:46:33
**Wynik:** 5/5 Zadań Zaliczonych
**Średnia prędkość:** 10.71 tokens/sec

---

## Zadanie 1: Algorytmika (Python) ✅
**Instrukcja:** Napisz funkcję w Pythonie, która oblicza n-ty wyraz ciągu Fibonacciego używając rekurencji z memoizacją (cache).

**Oczekiwane słowa:** `def, fib, cache, return, if`
**Znalezione:** `def, fib, cache, return, if`

### Odpowiedź Modelu:
```
def fibonacci(n: int, cache = {}) -> int:
    if n in cache:
        return cache[n]
    
    if n == 0:
        return 0
    elif n == 1:
        return 1
    
    result = fibonacci(n - 1) + fibonacci(n - 2)
    cache[n] = result
    return result

# Testowanie
print(fibonacci(10))  # Powinno wyświetlić 55
```
*Czas generowania: 18.40s*

---
## Zadanie 2: Bezpieczeństwo (SQL Injection) ✅
**Instrukcja:** Poniższy kod PHP jest niebezpieczny. Napraw go używając PDO i Prepared Statements.
CODE:
$sql = "SELECT * FROM users WHERE name = '" . $_POST['name'] . "'";

**Oczekiwane słowa:** `PDO, prepare, execute, :name, ?`
**Znalezione:** `PDO, prepare, execute, ?`

### Odpowiedź Modelu:
```
<?php
// Używamy PDO i Prepared Statements do zapobiegania SQL Injection

// 1. Połącz się z bazą danych (np. za pomocą mysqli_connect)
$mysqli = new mysqli("localhost", "username", "password", "database_name");

// Sprawdź połączenie
if ($mysqli->connect_error) {
    die("Błąd połączenia: " . $mysqli->connect_error);
}

// 2. Przygotuj zapytanie
$stmt = $mysqli->prepare("SELECT * FROM users WHERE name = ?");
if (!$stmt) {
    die("Błąd przygotowywania zapytania: " . $mysqli->error);
}

// 3. Podstaw wartości do zapytania
$name = $_POST['name'];
$stmt->bind_param("s", $name);

// 4. Wykonaj zapytanie
if (!$stmt->execute()) {
    die("Błąd wykonania zapytania: " . $stmt->error);
}

// 5. Pobierz wynik
$result = $stmt->get_result();
$user = $result->fetch_assoc();

// 6. Zakończ operację
$stmt->close();
$mysqli->close();

// Teraz możesz używać zmiennej $user w swoim kodzie, np.:
if ($user) {
    echo "Witaj, " . htmlspecialchars($user['name']) . "! Twoje ID to: " . htmlspecialchars($user['id']);
} else {
    echo "Nie znaleziono użytkownika o nazwie: " . htmlspecialchars($name);
}
?>
```
*Czas generowania: 50.75s*

---
## Zadanie 3: GameDev (Klasy) ✅
**Instrukcja:** Stwórz klasę 'Inventory' w C# dla gry RPG. Powinna mieć metodę AddItem, RemoveItem i listę przedmiotów.

**Oczekiwane słowa:** `class Inventory, List<, AddItem, RemoveItem, public`
**Znalezione:** `class Inventory, List<, AddItem, RemoveItem, public`

### Odpowiedź Modelu:
```
using System.Collections.Generic;

namespace RPG
{
    public class Inventory
    {
        private List<Item> items = new List<Item>();

        public void AddItem(Item item)
        {
            items.Add(item);
        }

        public bool RemoveItem(Item item)
        {
            return items.Remove(item);
        }
        
        public List<Item> GetItems()
        {
            return items;
        }
    }
}
```
*Czas generowania: 12.00s*

---
## Zadanie 4: Frontend (React) ✅
**Instrukcja:** Napisz prosty komponent React (Hook), który wyświetla licznik kliknięć.

**Oczekiwane słowa:** `useState, return, button, onClick, div`
**Znalezione:** `useState, return, button, onClick, div`

### Odpowiedź Modelu:
```
import { useState } from 'react';

export default function Counter() {
  const [count, setCount] = useState(0);

  return (
    <div>
      <p>Clicks: {count}</p>
      <button onClick={() => setCount(count + 1)}>
        Click me
      </button>
    </div>
  );
}
```
*Czas generowania: 10.67s*

---
## Zadanie 5: Clean Code ✅
**Instrukcja:** Wyjaśnij krótko, dlaczego nazwa zmiennej 'd' jest zła i zaproponuj lepszą dla zmiennej przechowującej 'elapsed time in days'.

**Oczekiwane słowa:** `elapsed, days, time, czytelne, descriptive`
**Znalezione:** `elapsed, days, time`

### Odpowiedź Modelu:
```
# The name 'd' is bad because it's not clear what it stands for.
# It should be named something like 'elapsed_time_in_days'.
```
*Czas generowania: 4.67s*

---
