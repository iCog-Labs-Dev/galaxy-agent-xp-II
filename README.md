# Galaxy Tools Fetcher using BioBlend

This Python script connects to a Galaxy instance using the [BioBlend](https://bioblend.readthedocs.io/en/latest/) library. It retrieves available tools and outputs their information in JSON format. The connection credentials (URL and API key) are securely managed using a `.env` file.

---

## Features

✅ Connect to a Galaxy instance  
✅ Retrieve and list available tools  
✅ Securely manage API credentials via environment variables  
✅ Extendable to use SBERT for further processing 

---

## Prerequisites

- Python 3.7+
- Access to a Galaxy instance with an API key

---

## Installation

1. **Clone this repository**  
   ```bash
   git clone https://github.com/johnnas12/galaxy_tool_suggestion.git
   cd galaxy_tool_suggestion
   ```
2. **Create and activate a virtual environment (optional but recommended)**
   ```
   python -m venv venv
   source venv/bin/activate    # On Windows, use venv\Scripts\activate
   ```
 3. Install the required packages
    ```
    pip install -r requirements.txt
    ```
4. Create a .env file in the project root directory.
   ```
   GALAXY_URL=https://usegalaxy.org
   GALAXY_API_KEY=your_api_key_here

   ```
 5. Usage
    ```
    python fetch_tools.py
    ```
# Galaxy Tools Fetcher using BioBlend
 ```
cd galaxy_tool_suggestion/tool_suggestion_model
```
## Training and Fine Tuning
1. Make sure requirements are upto date ore once again run
   ```
   pip install -r requirements.txt
   ```
2.  Open Notebook and run all the blocks
   The fine tuned model should appear in your current directory.
## Usage 
1. Add data and model path to .env (Enviroment Variables)
   ```
   MODEL_PATH = '/home/john/galaxy_tool_suggestion/tool_suggestion_model/fine_tuned_E5_for_galaxy_v'
   DATA_PATH = '/home/john/galaxy_tool_suggestion/tool_suggestion_model/dataset.json'
   ```
2. Run python file
   ```
   python main.py
   ```


