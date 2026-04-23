### An Interactive Local Python Notebook (PyCompute + Puter.js)

This is a lightweight, single-file web application that mimics the **Jupyter Notebook** experience locally. It leverages **Pyodide** to run a full Python environment directly in browser without needing a remote backend. 

- Access the **`.html`** file [**here**](_Dashboard.html).

It also has a sidebar **assistant** powered by **Puter.ai** that sees current code and output to provide debugging help or code suggestions. 

1.  **Navigate to the directory** containing **`.html`** file.
2.  **Start a Python local server** by running the following command in terminal:
    ```bash
    python -m http.server 8000
    ```
3.  **Access the dashboard** by opening browser and navigating to **`http://localhost:8000/FILENAME.html`**.

![An Interactive Local Python Notebook (PyCompute + Puter.js)](images/Images_Outlets_20260401_Dashboard.png)
