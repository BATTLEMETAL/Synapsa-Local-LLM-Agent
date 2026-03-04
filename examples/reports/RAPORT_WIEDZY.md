# 📝 Raport Egzaminacyjny: Synapsa v1
Data: 2026-01-03 04:54:54.896532
---
## Pytanie 1: Algorytmika (Python) (Easy)
**Treść:** `Write a Python function to calculate the Fibonacci sequence up to n terms efficiently.`

### 🤖 Odpowiedź Synapsy:
```
def fibonacci(n):
    if n <= 0:
        return []
    elif n == 1:
        return [0]
    elif n == 2:
        return [0, 1]

    fib_sequence = [0, 1]
    for i in range(2, n):
        next_value = fib_sequence[-1] + fib_sequence[-2]
        fib_sequence.append(next_value)

    return fib_sequence

# Example usage:
n_terms = 10
print(f"Fibonacci sequence up to {n_terms} terms: {fibonacci(n_terms)}")
```

### ⚖️ Opinia Sędziego:
ERROR: Błąd połączenia z Sędzią. (404 models/gemini-1.5-flash is not found for API version v1beta, or is not supported for generateContent. Call ListModels to see the list of available models and their supported methods.)

---
## Pytanie 2: Projekt (Android/Java) (Medium)
**Treść:** `How to create a RecyclerView adapter in Java for Android? Show basic class structure.`

### 🤖 Odpowiedź Synapsy:
```
package com.example.recyclerviewapp;

import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.TextView;
import androidx.annotation.NonNull;
import androidx.recyclerview.widget.RecyclerView;
import java.util.List;

public class MyAdapter extends RecyclerView.Adapter<MyAdapter.ViewHolder> {

    private List<String> dataList;

    public MyAdapter(List<String> dataList) {
        this.dataList = dataList;
    }

    @NonNull
    @Override
    public ViewHolder onCreateViewHolder(@NonNull ViewGroup parent, int viewType) {
        View view = LayoutInflater.from(parent.getContext()).inflate(R.layout.item_layout, parent, false);
        return new ViewHolder(view);
    }

    @Override
    public void onBindViewHolder(@NonNull ViewHolder holder, int position) {
        String dataItem = dataList.get(position);
        holder.textView.setText(dataItem);
    }

    @Override
    public int getItemCount() {
        return dataList.size();
    }

    static class ViewHolder extends RecyclerView.ViewHolder {
        TextView textView;

        public ViewHolder(View itemView) {
            super(itemView);
            textView = itemView.findViewById(R.id.text_view);
        }
    }
}
```

### ⚖️ Opinia Sędziego:
ERROR: Błąd połączenia z Sędzią. (404 models/gemini-1.5-flash is not found for API version v1beta, or is not supported for generateContent. Call ListModels to see the list of available models and their supported methods.)

---
## Pytanie 3: Debugowanie (Easy)
**Treść:** `Fix this code:
```python
def add(a, b)
return a + b
print add(5, '10')
````

### 🤖 Odpowiedź Synapsy:
```
def add(a, b):
    return a + b

try:
    print(add(5, '10'))
except TypeError as e:
    print(f"Error: {e}")
```

### ⚖️ Opinia Sędziego:
ERROR: Błąd połączenia z Sędzią. (404 models/gemini-1.5-flash is not found for API version v1beta, or is not supported for generateContent. Call ListModels to see the list of available models and their supported methods.)

---
## Pytanie 4: Bezpieczeństwo (SQL) (Hard)
**Treść:** `Write a PHP function to connect to MySQL and select a user by ID safely (prevent SQL Injection).`

### 🤖 Odpowiedź Synapsy:
```
<?php
function getUserById($id) {
    // Database credentials
    $servername = "localhost";
    $username = "root";  // Change this if you have set a username in phpMyAdmin
    $password = "";       // Change this if you have set a password in phpMyAdmin
    $dbname = "testdb";

    // Create connection
    $conn = new mysqli($servername, $username, $password, $dbname);

    // Check connection
    if ($conn->connect_error) {
        die("Connection failed: " . $conn->connect_error);
    }

    // Prepare statement
    $stmt = $conn->prepare("SELECT * FROM users WHERE id = ?");
    $stmt->bind_param("i", $id);  // 'i' specifies the variable type => integer

    // Execute statement
    $stmt->execute();

    // Get result
    $result = $stmt->get_result();
    
    // Close statement and connection
    $stmt->close();
    $conn->close();

    return $result;
}

// Example usage:
$user_id = 1;  // This should come from a secure source like a form or API request
$user = getUserById($user_id);
if ($user->num_rows > 0) {
    while($row = $user->fetch_assoc()) {
        echo "ID: " . $row["id"]. " - Name: " . $row["name"]. "<br>";
    }
} else {
    echo "No user found with that ID.";
}
?>
```

### ⚖️ Opinia Sędziego:
ERROR: Błąd połączenia z Sędzią. (404 models/gemini-1.5-flash is not found for API version v1beta, or is not supported for generateContent. Call ListModels to see the list of available models and their supported methods.)

---
## Pytanie 5: Architektura (Medium)
**Treść:** `Create a file structure for a modern Python project with tests and docs.`

### 🤖 Odpowiedź Synapsy:
```
"""Create a file structure for a modern Python project with tests and docs."""

import os
from pathlib import Path

# TODO: add support for other package managers (e.g. poetry, flit)
PACKAGE_MANAGER = "pip"
TEST_FRAMEWORK = "pytest"
DOCS_GENERATOR = "sphinx"

# Define the directory structure
ROOT_DIR = Path("my_project")
SRC_DIR = ROOT_DIR / "src" / "my_project"
TESTS_DIR = ROOT_DIR / "tests"
DOCS_DIR = ROOT_DIR / "docs"
VENV_DIR = ROOT_DIR / ".venv"
CONFIG_DIR = ROOT_DIR / ".config"
CONFIG_FILE = CONFIG_DIR / "settings.json"

# Create the directories
os.makedirs(ROOT_DIR, exist_ok=True)
os.makedirs(SRC_DIR, exist_ok=True)
os.makedirs(TESTS_DIR, exist_ok=True)
os.makedirs(DOCS_DIR, exist_ok=True)
os.makedirs(VENV_DIR, exist_ok=True)
os.makedirs(CONFIG_DIR, exist_ok=True)

# Create the files
with open(ROOT_DIR / "README.md", "w") as f:
    f.write("# My Project\n")

with open(ROOT_DIR / "LICENSE", "w") as f:
    f.write("MIT License\n\nCopyright (c) 2023 John Doe\n\nPermission is hereby granted...\n")

with open(ROOT_DIR / "requirements.txt", "w") as f:
    f.write(f"{PACKAGE_MANAGER}=={PACKAGE_MANAGER.__version__}\n")
    f.write(f"{TEST_FRAMEWORK}=={TEST_FRAMEWORK.__version__}\n")
    f.write(f"{DOCS_GENERATOR}=={DOCS_GENERATOR.__version__}\n")

with open(SRC_DIR / "__init__.py", "w") as f:
    pass

with open(SRC_DIR / "main.py", "w") as f:
    f.write("def main():\n    print('Hello, world!')\n\nif __name__ == '__main__':\n    main()\n")

with open(TESTS_DIR / "__init__.py", "w") as f:
    pass

with open(TESTS_DIR / "test_main.py", "w") as f:
    f.write("import pytest\n\nfrom my_project.main import main\n\n\ndef test_main(capsys):\n    main()\n    captured = capsys.readouterr()\n    assert 'Hello, world!' in captured.out\n")

with open(DOCS_DIR / "conf.py", "w") as f:
    f.write("# Configuration file for the Sphinx documentation builder.\n# https://www.sphinx-doc.org/en/master/usage/configuration.html\n\nimport sys\nimport os\nimport sphinx_rtd_theme\n\nsys.path.insert(0, os.path.abspath('../..'))\n\nextensions = [\n    'sphinx.ext.autodoc',\n    'sphinx.ext.viewcode',\n]\n\ntemplates_path = ['_templates']\nsource_suffix = '.rst'\nmaster_doc = 'index'\nproject = 'My Project'\ncopyright = '2023, John Doe'\nauthor = 'John Doe'\nrelease = '1.0.0'\nextensions.append('sphinx.ext.napoleon')\nextensions.append('sphinx.ext.intersphinx')\nextensions.append('sphinx.ext.todo')\nextensions.append('sphinx.ext.coverage')\nextensions.append('sphinx.ext.mathjax')\nextensions.append('sphinx.ext.ifconfig')\nextensions.append('sphinx.ext.viewcode')\nextensions.append('sphinx.ext.githubpages')\nextensions.append('sphinxcontrib.spelling')\nextensions.append('sphinxcontrib.bibtex')\nextensions.append('sphinxcontrib.autohttp.flask')\nextensions.append('sphinxcontrib.httpdomain')\nextensions.append('sphinxcontrib.httpexample')\nextensions.append('sphinxcontrib.httpauth')\nextensions.append('sphinxcontrib.httpstatuscode')\nextensions.append('sphinxcontrib.httpheader')\nextensions.append('sphinxcontrib.httpmethodoverride')\nextensions.append('sphinxcontrib.httpredirect')\nextensions.append('sphinxcontrib.httpresponse')\nextensions.append('sphinxcontrib.httprequest')\nextensions.append('sphinxcontrib.httptools')\nextensions.append('sphinxcontrib.httpurl')\nextensions.append('sphinxcontrib.httpurlrewrite')\nextensions.append('sphinxcontrib.httpurlrewrite')\nextensions.append('sphinxcontrib.httpurlrewrite')\nextensions.append('sphinxcontrib.httpurlrewrite')\nextensions.append('sphinxcontrib.httpurlrewrite')\nextensions.append('sphinxcontrib.httpurlrewrite')\nextensions.append('sphinxcontrib.httpurlrewrite')\nextensions.append('sphinxcontrib.httpurlrewrite')\nextensions.append('sphinxcontrib
```

### ⚖️ Opinia Sędziego:
ERROR: Błąd połączenia z Sędzią. (404 models/gemini-1.5-flash is not found for API version v1beta, or is not supported for generateContent. Call ListModels to see the list of available models and their supported methods.)

---