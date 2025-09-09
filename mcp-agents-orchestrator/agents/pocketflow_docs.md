========================
CODE SNIPPETS
========================
TITLE: Install Dependencies and Run Example
DESCRIPTION: This snippet provides the bash commands to install the necessary project dependencies using pip and then run the main Python script to execute the PocketFlow example.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-async-basic/README.md#_snippet_3

LANGUAGE: bash
CODE:
```
pip install -r requirements.txt
python main.py
```

----------------------------------------

TITLE: Install Dependencies and Run Application (Bash)
DESCRIPTION: Installs project dependencies using pip and then runs the main application script. This is the primary command to start the PocketFlow MCP demo.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-mcp/README.md#_snippet_1

LANGUAGE: bash
CODE:
```
pip install -r requirements.txt
python main.py
```

----------------------------------------

TITLE: Run PocketFlow Hello World Example
DESCRIPTION: This snippet shows how to set up and run the basic PocketFlow 'Hello World' application. It covers virtual environment creation, dependency installation, and executing the main script.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-hello-world/README.md#_snippet_0

LANGUAGE: bash
CODE:
```
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

LANGUAGE: bash
CODE:
```
pip install -r requirements.txt
```

LANGUAGE: bash
CODE:
```
python main.py
```

----------------------------------------

TITLE: Install Dependencies with Pip
DESCRIPTION: Installs the required Python packages listed in the requirements.txt file. This is a standard step for setting up Python projects.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-gradio-hitl/README.md#_snippet_0

LANGUAGE: bash
CODE:
```
pip install -r requirements.txt
```

----------------------------------------

TITLE: Python Dependency Installation
DESCRIPTION: Installs project dependencies from the requirements.txt file.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-node/README.md#_snippet_1

LANGUAGE: bash
CODE:
```
pip install -r requirements.txt
```

----------------------------------------

TITLE: Python Virtual Environment Setup
DESCRIPTION: Creates a virtual environment for the project and activates it. This isolates project dependencies.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-node/README.md#_snippet_0

LANGUAGE: bash
CODE:
```
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

----------------------------------------

TITLE: Run PocketFlow Example
DESCRIPTION: Installs dependencies and runs the main Python script for the PocketFlow Nested BatchFlow example.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-nested-batch/README.md#_snippet_0

LANGUAGE: bash
CODE:
```
pip install -r requirements.txt
python main.py
```

----------------------------------------

TITLE: Install Dependencies with Pip
DESCRIPTION: Installs the necessary Python packages listed in the requirements.txt file for the PocketFlow communication example.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-communication/README.md#_snippet_0

LANGUAGE: bash
CODE:
```
pip install -r requirements.txt
```

----------------------------------------

TITLE: Environment Setup
DESCRIPTION: Copies the example environment file and configures Langfuse credentials and tracing debug mode.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-tracing/README.md#_snippet_1

LANGUAGE: bash
CODE:
```
cp .env.example .env
```

LANGUAGE: env
CODE:
```
LANGFUSE_SECRET_KEY=your-langfuse-secret-key
LANGFUSE_PUBLIC_KEY=your-public-key
LANGFUSE_HOST=your-langfuse-host-url
POCKETFLOW_TRACING_DEBUG=true
```

----------------------------------------

TITLE: Install Dependencies
DESCRIPTION: Installs the necessary Python packages for the PocketFlow BatchNode example using pip.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-batch-node/README.md#_snippet_0

LANGUAGE: bash
CODE:
```
pip install -r requirements.txt
```

----------------------------------------

TITLE: Install Dependencies
DESCRIPTION: Installs the necessary Python packages listed in the requirements.txt file for the resume qualification workflow.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-map-reduce/README.md#_snippet_0

LANGUAGE: bash
CODE:
```
pip install -r requirements.txt
```

----------------------------------------

TITLE: Install Dependencies with Pip
DESCRIPTION: Installs the necessary Python packages listed in the requirements.txt file for the PocketFlow BatchFlow example.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-batch-flow/README.md#_snippet_0

LANGUAGE: bash
CODE:
```
pip install -r requirements.txt
```

----------------------------------------

TITLE: Install Pocket Flow using pip
DESCRIPTION: This command installs the Pocket Flow framework using Python's package installer, pip. It's the quickest way to get started with the framework.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-batch/translations/README_KOREAN.md#_snippet_0

LANGUAGE: bash
CODE:
```
pip install pocketflow
```

----------------------------------------

TITLE: Main Application Entry Point
DESCRIPTION: The main Python script that serves as the entry point for the application. It handles the setup and initialization of the Gradio interface and the PocketFlow workflow.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-gradio-hitl/README.md#_snippet_4

LANGUAGE: python
CODE:
```
# main.py: Entry point for the application and Gradio interface setup
```

----------------------------------------

TITLE: Running Examples
DESCRIPTION: Provides commands to run the basic synchronous and asynchronous PocketFlow tracing examples.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-tracing/README.md#_snippet_5

LANGUAGE: bash
CODE:
```
cd examples
python basic_example.py
```

LANGUAGE: bash
CODE:
```
cd examples  
python async_example.py
```

----------------------------------------

TITLE: Install Dependencies and Run Pocketflow
DESCRIPTION: Installs the necessary dependencies from the requirements file and then runs the main Python script to start the LLM streaming application.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-llm-streaming/README.md#_snippet_0

LANGUAGE: bash
CODE:
```
pip install -r requirements.txt
python main.py
```

----------------------------------------

TITLE: Project Setup and Execution (Bash)
DESCRIPTION: Provides bash commands for setting up the PocketFlow TAO project environment. This includes creating a virtual environment, activating it, and installing project dependencies from a requirements file.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-tao/README.md#_snippet_1

LANGUAGE: bash
CODE:
```
# Create a virtual environment
python -m venv venv

# Activate the virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set API key (example for OpenAI)
export OPENAI_API_KEY="your-api-key-here"

# Run the main application
python main.py
```

----------------------------------------

TITLE: Install Pocket Flow with Pip
DESCRIPTION: This snippet shows the command to install the Pocket Flow framework using pip, the Python package installer. It's a straightforward way to get started with the framework.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-batch/translations/README_CHINESE.md#_snippet_0

LANGUAGE: bash
CODE:
```
pip install pocketflow
```

----------------------------------------

TITLE: Run PocketFlow Gradio HITL Application
DESCRIPTION: Executes the main Python script to start the Gradio web application. The application is typically accessible via a local URL.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-gradio-hitl/README.md#_snippet_2

LANGUAGE: bash
CODE:
```
python main.py
```

----------------------------------------

TITLE: Install Dependencies
DESCRIPTION: Installs the necessary Python packages for the project using pip. This command reads the list of dependencies from the 'requirements.txt' file.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-cli-hitl/README.md#_snippet_0

LANGUAGE: bash
CODE:
```
pip install -r requirements.txt
```

----------------------------------------

TITLE: Project Dependencies List
DESCRIPTION: A file listing all the Python dependencies required for the project, used by pip for installation.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-gradio-hitl/README.md#_snippet_8

LANGUAGE: python
CODE:
```
# requirements.txt: Lists project dependencies
```

----------------------------------------

TITLE: Install Dependencies and Run Python Script
DESCRIPTION: Installs the necessary Python packages from the requirements file and then executes the main Python script to start the image processing.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-parallel-batch-flow/README.md#_snippet_0

LANGUAGE: bash
CODE:
```
pip install -r requirements.txt
python main.py
```

----------------------------------------

TITLE: Run PocketFlow Visualization Example (Bash)
DESCRIPTION: Navigates to the PocketFlow visualization example directory and runs the visualization script. This generates visualization files in the `./viz` directory.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-visualization/README.md#_snippet_1

LANGUAGE: Bash
CODE:
```
# Navigate to the directory
cd cookbook/pocketflow-minimal-flow2flow

# Run the visualization script
python visualize.py
```

----------------------------------------

TITLE: Run Resume Qualification Workflow
DESCRIPTION: Executes the main Python script to start the resume qualification process.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-map-reduce/README.md#_snippet_2

LANGUAGE: bash
CODE:
```
python main.py
```

----------------------------------------

TITLE: PocketFlow System Setup and Execution in Python
DESCRIPTION: This Python code demonstrates the setup and execution of the PocketFlow system. It includes loading data from files, defining and connecting nodes (`PrepareEmbeddings`, `FindRelevantDocument`, `AnswerQuestion`), creating the `Flow` object, and running the flow with initial shared data.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow_demo.ipynb#_snippet_80

LANGUAGE: Python
CODE:
```
# Create test data
shared = {"data": {}}

# Load all files
path = "./data/PaulGrahamEssaysLarge"
for filename in os.listdir(path):
    with open(os.path.join(path, filename), "r") as f:
        shared["data"][filename] = f.read()

# Create nodes and flow
prep_embeddings = PrepareEmbeddings()
find_relevant = FindRelevantDocument()
answer = AnswerQuestion()

# Connect nodes
prep_embeddings >> find_relevant
find_relevant - "answer" >> answer
find_relevant - "end" >> None
answer - "continue" >> find_relevant

# Create and run flow
rag_flow = Flow(start=prep_embeddings)
rag_flow.run(shared)
```

----------------------------------------

TITLE: Install Requirements and Run Application (Python/Bash)
DESCRIPTION: This command sequence installs the necessary Python packages listed in 'requirements.txt' and then runs the main application script. It's the primary way to get the travel advisor chatbot up and running.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-chat-guardrail/README.md#_snippet_1

LANGUAGE: bash
CODE:
```
pip install -r requirements.txt
python main.py
```

----------------------------------------

TITLE: Run PocketFlow Communication Example
DESCRIPTION: Executes the main Python script for the PocketFlow communication example, which prompts the user for input to perform word counting and update statistics.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-communication/README.md#_snippet_1

LANGUAGE: bash
CODE:
```
python main.py
```

----------------------------------------

TITLE: Run PocketFlow BatchNode Example
DESCRIPTION: Executes the main script for the PocketFlow BatchNode CSV processing example.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-batch-node/README.md#_snippet_1

LANGUAGE: bash
CODE:
```
python main.py
```

----------------------------------------

TITLE: Install Pocketflow and Dependencies
DESCRIPTION: Installs the Pocketflow library along with necessary dependencies like aiohttp, openai, and duckduckgo-search using pip.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-agent/demo.ipynb#_snippet_0

LANGUAGE: python
CODE:
```
! pip install pocketflow>=0.0.1
! pip install aiohttp>=3.8.0
! pip install openai>=1.0.0
! pip install duckduckgo-search>=7.5.2
```

----------------------------------------

TITLE: Install Pocket Flow Dependencies
DESCRIPTION: Installs the necessary libraries for Pocket Flow, including pocketflow, faiss-cpu, and openai.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow_demo.ipynb#_snippet_0

LANGUAGE: python
CODE:
```
! pip install pocketflow
! pip install faiss-cpu
! pip install openai
```

----------------------------------------

TITLE: Install Dependencies
DESCRIPTION: Installs the necessary Python packages for the project using pip. Ensure you have a requirements.txt file in your project directory.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-tool-search/README.md#_snippet_0

LANGUAGE: bash
CODE:
```
pip install -r requirements.txt
```

----------------------------------------

TITLE: Install Dependencies
DESCRIPTION: Installs the necessary Python packages for the web crawler project using pip. Ensure you have Python and pip installed.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-tool-crawler/README.md#_snippet_0

LANGUAGE: bash
CODE:
```
pip install -r requirements.txt
```

----------------------------------------

TITLE: Clone Repository and Install Dependencies (Bash)
DESCRIPTION: This snippet shows how to clone the project repository and install its dependencies using Pipenv. It's a standard setup procedure for Python projects managed with Pipenv.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-google-calendar/README.md#_snippet_0

LANGUAGE: Bash
CODE:
```
git clone [REPOSITORY_URL]
cd pocket-google-calendar
pipenv install
```

----------------------------------------

TITLE: Configuration Management with YAML
DESCRIPTION: This example demonstrates how to define project configurations using YAML. Proper configuration is key to setting up and running PocketFlow efficiently.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow_demo.ipynb#_snippet_33

LANGUAGE: YAML
CODE:
```
project:
  name: PocketFlow
  version: 1.0.0

database:
  type: postgresql
  host: localhost
  port: 5432
  username: user
  password: password

api:
  base_url: https://api.example.com

```

----------------------------------------

TITLE: Install Dependencies and Run (Python)
DESCRIPTION: Installs project dependencies from the requirements.txt file and runs the main application with default settings. This is the standard procedure to get the system operational.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-rag/README.md#_snippet_2

LANGUAGE: python
CODE:
```
pip install -r requirements.txt
python main.py
```

----------------------------------------

TITLE: Run PocketFlow BatchFlow Image Processor
DESCRIPTION: Executes the main Python script to start the PocketFlow BatchFlow image processing task, applying specified filters to different images.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-batch-flow/README.md#_snippet_1

LANGUAGE: bash
CODE:
```
python main.py
```

----------------------------------------

TITLE: Run Example (Bash)
DESCRIPTION: Executes the main Python script to demonstrate the PocketFlow and SQLite integration. This script initializes the database, creates a task, and lists tasks.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-tool-database/README.md#_snippet_2

LANGUAGE: bash
CODE:
```
python main.py
```

----------------------------------------

TITLE: PocketFlow Application Structure
DESCRIPTION: Illustrates the typical file structure for a PocketFlow application. Key files include the main entry point (`main.py`), PocketFlow implementation (`flow.py`), documentation, and utility directories.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-hello-world/README.md#_snippet_1

LANGUAGE: plaintext
CODE:
```
. 
├── docs/          # Documentation files
├── utils/         # Utility functions
├── flow.py        # PocketFlow implementation
├── main.py        # Main application entry point
└── README.md      # Project documentation
```

----------------------------------------

TITLE: Get Approval AsyncNode
DESCRIPTION: This AsyncNode handles user interaction by asynchronously prompting for approval of a recipe suggestion. It then returns an action ('accept' or 'retry') based on the user's input, facilitating flow control.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-async-basic/README.md#_snippet_2

LANGUAGE: python
CODE:
```
async def post_async(self, shared, prep_res, suggestion):
    # Async user input
    answer = await get_user_input(
        f"Accept {suggestion}? (y/n): "
    )
    return "accept" if answer == "y" else "retry"
```

----------------------------------------

TITLE: Install Dependencies
DESCRIPTION: Installs the necessary Python dependencies for PocketFlow tracing using Langfuse.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-tracing/README.md#_snippet_0

LANGUAGE: bash
CODE:
```
pip install -r requirements.txt
```

----------------------------------------

TITLE: Install Python Dependencies
DESCRIPTION: Installs the necessary Python packages for the Text-to-SQL workflow from the requirements.txt file.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-text2sql/README.md#_snippet_0

LANGUAGE: bash
CODE:
```
pip install -r requirements.txt
```

----------------------------------------

TITLE: PocketFlow Initialization and Configuration
DESCRIPTION: Demonstrates how to initialize and configure PocketFlow, a data processing and flow management system. This snippet covers basic setup and common configuration parameters.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow_demo.ipynb#_snippet_63

LANGUAGE: JavaScript
CODE:
```
import PocketFlow from '@the-pocket/pocketflow';

const pf = new PocketFlow({
  // Configuration options here
  logLevel: 'info',
  maxConcurrentTasks: 10
});

pf.start();
console.log('PocketFlow started successfully.');
```

----------------------------------------

TITLE: Install Dependencies
DESCRIPTION: Installs the necessary Python packages for the project using pip. Ensure you have a requirements.txt file in your project directory.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-thinking/README.md#_snippet_0

LANGUAGE: bash
CODE:
```
pip install -r requirements.txt
```

----------------------------------------

TITLE: Example Node: Summarize File
DESCRIPTION: A complete example of a Node that reads file content, summarizes it using an LLM call, and stores the summary. It includes implementations for prep, exec, exec_fallback, and post, demonstrating retry usage and graceful error handling.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/docs/core_abstraction/node.md#_snippet_3

LANGUAGE: python
CODE:
```
class SummarizeFile(Node):
    def prep(self, shared):
        return shared["data"]

    def exec(self, prep_res):
        if not prep_res:
            return "Empty file content"
        prompt = f"Summarize this text in 10 words: {prep_res}"
        summary = call_llm(prompt)  # might fail
        return summary

    def exec_fallback(self, prep_res, exc):
        # Provide a simple fallback instead of crashing
        return "There was an error processing your request."

    def post(self, shared, prep_res, exec_res):
        shared["summary"] = exec_res
        # Return "default" by not returning

summarize_node = SummarizeFile(max_retries=3)

# node.run() calls prep->exec->post
# If exec() fails, it retries up to 3 times before calling exec_fallback()
action_result = summarize_node.run(shared)

print("Action returned:", action_result)  # "default"
print("Summary stored:", shared["summary"])
```

----------------------------------------

TITLE: Install Requirements and Run Application (Bash)
DESCRIPTION: This snippet demonstrates the commands to install the necessary Python dependencies using pip and then run the main application script.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-chat/README.md#_snippet_1

LANGUAGE: bash
CODE:
```
pip install -r requirements.txt
python main.py
```

----------------------------------------

TITLE: SerpApi Integration (Python)
DESCRIPTION: Shows an example of using the SerpApi service to perform Google searches. Requires an API key. Sends a GET request to the SerpApi endpoint, specifying the search engine and query parameters.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/docs/utility_function/websearch.md#_snippet_4

LANGUAGE: Python
CODE:
```
import requests

API_KEY = "YOUR_SERPAPI_KEY"
query = "example"

url = "https://serpapi.com/search"
params = {
    "engine": "google",
    "q": query,
    "api_key": API_KEY
}

response = requests.get(url, params=params)
results = response.json()
print(results)
```

----------------------------------------

TITLE: Example Output (Python)
DESCRIPTION: This snippet provides an example of the expected output when the Pocket Google Calendar application is run. It shows a list of calendars and a confirmation message for creating an event.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-google-calendar/README.md#_snippet_3

LANGUAGE: Python
CODE:
```
=== Listing your calendars ===
- Primary Calendar
- Work
- Personal

=== Creating an example event ===
Event created successfully!
Event ID: abc123xyz
```

----------------------------------------

TITLE: Install Dependencies (Bash)
DESCRIPTION: Installs the project's Python dependencies using pip from a requirements file. This is a standard step for setting up Python projects.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-fastapi-hitl/README.md#_snippet_0

LANGUAGE: Bash
CODE:
```
pip install -r requirements.txt
```

----------------------------------------

TITLE: Test Utility Functions (Python)
DESCRIPTION: Provides examples of how to test individual utility functions within the project, such as calling the LLM or performing text-to-speech conversion, to verify the OpenAI API key and setup.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-voice-chat/README.md#_snippet_4

LANGUAGE: python
CODE:
```
python utils/call_llm.py
```

LANGUAGE: python
CODE:
```
python utils/text_to_speech.py
```

----------------------------------------

TITLE: Install Dependencies
DESCRIPTION: Installs the necessary packages for the project using pip. This is a prerequisite for running the research agent and supervisor.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-supervisor/README.md#_snippet_0

LANGUAGE: bash
CODE:
```
pip install -r requirements.txt
```

----------------------------------------

TITLE: Install Dependencies
DESCRIPTION: Installs the necessary Python packages for the project using pip from a requirements file.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-workflow/README.md#_snippet_0

LANGUAGE: bash
CODE:
```
pip install -r requirements.txt
```

----------------------------------------

TITLE: Run PocketFlow OpenAI Embeddings Example
DESCRIPTION: Executes the main Python script to run the PocketFlow example. This script handles API key loading, node creation, text processing, and embedding generation.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-tool-embeddings/README.md#_snippet_4

LANGUAGE: bash
CODE:
```
python main.py
```

----------------------------------------

TITLE: Install Dependencies with Pip
DESCRIPTION: Installs the necessary Python packages for the project using a requirements file. This is a common first step in setting up Python projects.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-structured-output/README.md#_snippet_0

LANGUAGE: bash
CODE:
```
pip install -r requirements.txt
```

----------------------------------------

TITLE: Suggest Recipe AsyncNode
DESCRIPTION: This AsyncNode takes a list of recipes and asynchronously calls a language model (LLM) to suggest the best recipe. It demonstrates integrating LLM calls within an asynchronous workflow.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-async-basic/README.md#_snippet_1

LANGUAGE: python
CODE:
```
async def exec_async(self, recipes):
    # Async LLM call
    suggestion = await call_llm_async(
        f"Choose best recipe from: {recipes}"
    )
    return suggestion
```

----------------------------------------

TITLE: Install Dependencies
DESCRIPTION: Installs the necessary Python packages for the batch translation process by referencing the requirements.txt file.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-batch/README.md#_snippet_0

LANGUAGE: bash
CODE:
```
pip install -r requirements.txt
```

----------------------------------------

TITLE: Fetch Recipes AsyncNode
DESCRIPTION: This AsyncNode prepares by taking user input for an ingredient and then asynchronously fetches recipes using that ingredient. It handles the initial data gathering and the asynchronous API call.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-async-basic/README.md#_snippet_0

LANGUAGE: python
CODE:
```
async def prep_async(self, shared):
    ingredient = input("Enter ingredient: ")
    return ingredient

async def exec_async(self, ingredient):
    # Async API call
    recipes = await fetch_recipes(ingredient)
    return recipes
```

----------------------------------------

TITLE: Install Dependencies (Bash)
DESCRIPTION: Installs the necessary Python libraries for the PocketFlow voice chat application using pip. It also provides instructions for Linux users to install PortAudio if needed for the sounddevice library.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-voice-chat/README.md#_snippet_1

LANGUAGE: bash
CODE:
```
pip install -r requirements.txt
```

LANGUAGE: bash
CODE:
```
sudo apt-get update && sudo apt-get install -y portaudio19-dev
```

----------------------------------------

TITLE: Install Python Dependencies
DESCRIPTION: Lists the Python dependencies required for the project. This file is crucial for setting up the project environment.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/docs/guide.md#_snippet_3

LANGUAGE: text
CODE:
```
PyYAML
pocketflow
```

----------------------------------------

TITLE: Install Dependencies
DESCRIPTION: Installs the necessary Python packages required for the project. This is typically the first step before running the application.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-majority-vote/README.md#_snippet_0

LANGUAGE: bash
CODE:
```
pip install -r requirements.txt
```

----------------------------------------

TITLE: Install Dependencies
DESCRIPTION: Installs the necessary Python packages required for PocketFlow to run, typically listed in a requirements.txt file.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-code-generator/README.md#_snippet_0

LANGUAGE: bash
CODE:
```
pip install -r requirements.txt
```

----------------------------------------

TITLE: Utility Functions and Helper Modules
DESCRIPTION: Houses utility functions and helper modules used throughout the project. This directory contains supporting code for various functionalities.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-gradio-hitl/README.md#_snippet_7

LANGUAGE: python
CODE:
```
# utils/: Contains utility functions and helper modules
```

----------------------------------------

TITLE: Install Dependencies and Run Application (Python/Bash)
DESCRIPTION: These commands are used to set up and run the PocketFlow chat application. The first command installs all required Python packages listed in the 'requirements.txt' file, and the second command executes the main application script.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-chat-memory/README.md#_snippet_1

LANGUAGE: bash
CODE:
```
pip install -r requirements.txt
```

LANGUAGE: bash
CODE:
```
python main.py
```

----------------------------------------

TITLE: Install Dependencies
DESCRIPTION: Installs the necessary Python packages listed in the requirements.txt file for the text converter application.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-flow/README.md#_snippet_0

LANGUAGE: bash
CODE:
```
pip install -r requirements.txt
```

----------------------------------------

TITLE: Python PocketFlow Summarization Execution
DESCRIPTION: Executes a PocketFlow summarization task with sample data and prints the resulting summary.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-node/README.md#_snippet_2

LANGUAGE: python
CODE:
```
shared = {"data": "Your text to summarize here..."}
flow.run(shared)
print("Summary:", shared["summary"])
```

----------------------------------------

TITLE: Install Dependencies
DESCRIPTION: Installs the necessary Python packages for the project using pip and a requirements.txt file.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-a2a/README.md#_snippet_0

LANGUAGE: Bash
CODE:
```
pip install -r requirements.txt
```

----------------------------------------

TITLE: Install Dependencies
DESCRIPTION: Installs the necessary Python packages for the research agent. This is a prerequisite for running the project.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-agent/README.md#_snippet_0

LANGUAGE: bash
CODE:
```
pip install -r requirements.txt
```

----------------------------------------

TITLE: Run Web Search Tool
DESCRIPTION: Executes the main script to start the web search and analysis tool. The tool will prompt the user for a search query and the number of results.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-tool-search/README.md#_snippet_2

LANGUAGE: bash
CODE:
```
python main.py
```

----------------------------------------

TITLE: Install Dependencies (Bash)
DESCRIPTION: Installs project dependencies using pip from the requirements.txt file. This command ensures all necessary libraries are available for the application to run.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-fastapi-websocket/README.md#_snippet_1

LANGUAGE: Bash
CODE:
```
pip install -r requirements.txt
```

----------------------------------------

TITLE: Install Dependencies
DESCRIPTION: Installs the necessary Python packages for the PocketFlow PDF Vision tool from the requirements.txt file.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-tool-pdf-vision/README.md#_snippet_0

LANGUAGE: bash
CODE:
```
pip install -r requirements.txt
```

----------------------------------------

TITLE: Install Dependencies
DESCRIPTION: Installs the necessary Python packages for the project from the requirements.txt file.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-multi-agent/README.md#_snippet_0

LANGUAGE: bash
CODE:
```
pip install -r requirements.txt
```

----------------------------------------

TITLE: Pocket Flow Utility Function Examples
DESCRIPTION: Pocket Flow provides examples for utility functions rather than built-in implementations. This approach avoids vendor lock-in and allows for greater flexibility. Users are encouraged to implement their own wrappers for LLMs, visualization, web search, chunking, embeddings, vector databases, and text-to-speech.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/docs/index.md#_snippet_2

LANGUAGE: Python
CODE:
```
# Example for LLM Wrapper
class LLMWrapper:
    def __init__(self, api_key):
        self.api_key = api_key

    def generate(self, prompt):
        # Implementation details for interacting with an LLM API
        pass

# Example for Viz and Debug
def visualize_flow(flow):
    # Implementation details for visualizing the flow graph
    pass

# Example for Web Search
def web_search(query):
    # Implementation details for performing a web search
    pass

# Example for Chunking
def chunk_text(text, chunk_size):
    # Implementation details for splitting text into chunks
    pass

# Example for Embedding
def create_embedding(text):
    # Implementation details for generating text embeddings
    pass

# Example for Vector Databases
class VectorDatabase:
    def add_document(self, id, embedding):
        pass
    def search(self, query_embedding, k=5):
        pass

# Example for Text-to-Speech
def text_to_speech(text, voice_id):
    # Implementation details for converting text to speech
    pass

```

----------------------------------------

TITLE: Run FastAPI Server
DESCRIPTION: Starts the FastAPI web server, making the application accessible via a web browser. This command executes the main application file.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-fastapi-background/README.md#_snippet_2

LANGUAGE: bash
CODE:
```
python main.py
```

----------------------------------------

TITLE: Implement Batch Summarization Node in Python
DESCRIPTION: Defines a `BatchSummarizeNode` class inheriting from `pocketflow.BatchNode`. The `prep` method retrieves data from the shared store, `exec` summarizes individual text items using an LLM, and `post` aggregates the summaries back into the shared store. The example also shows how to load data from a directory and run the node.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow_demo.ipynb#_snippet_39

LANGUAGE: python
CODE:
```
from pocketflow import BatchNode
import os

class BatchSummarizeNode(BatchNode):
    def prep(self, shared):
        # Return list of (filename, content) tuples from shared store
        return [(fn, content) for fn, content in shared["data"].items()]
        
    def exec(self, item):
        # Unpack the filename and content
        filename, text = item
        # Call LLM to summarize
        prompt = f"Summarize this text in 50 words:\n\n{text}"
        summary = call_llm(prompt)
        return filename, summary
    
    def post(self, shared, prep_res, exec_res_list):
        # Store all summaries in a dict by filename
        shared["summaries"] = {
            filename: summary 
            for filename, summary in exec_res_list
        }
        return "default"

# Create test data structure
shared = {
    "data": {},
    "summaries": {}
}

# Load all files from the directory
path = "./data/PaulGrahamEssaysLarge"
for filename in os.listdir(path):
    with open(os.path.join(path, filename), "r") as f:
        shared["data"][filename] = f.read()

# Create and run the batch node
batch_summarize = BatchSummarizeNode()
batch_summarize.run(shared)
```

----------------------------------------

TITLE: Install Langfuse Package using Pip
DESCRIPTION: Provides the command to install the Langfuse Python package using pip, addressing the 'langfuse package not installed' error.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-tracing/README.md#_snippet_8

LANGUAGE: bash
CODE:
```
pip install langfuse
```

----------------------------------------

TITLE: Synthesize Speech with Azure TTS (Python)
DESCRIPTION: Provides an example of synthesizing speech using the Azure Cognitive Services Speech SDK for Python. It requires an Azure subscription key and region, and configures the audio output to a file.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/docs/utility_function/text_to_speech.md#_snippet_2

LANGUAGE: Python
CODE:
```
import azure.cognitiveservices.speech as speechsdk

speech_config = speechsdk.SpeechConfig(
    subscription="AZURE_KEY", region="AZURE_REGION")
audio_cfg = speechsdk.audio.AudioConfig(filename="azure_tts.wav")

synthesizer = speechsdk.SpeechSynthesizer(
    speech_config=speech_config,
    audio_config=audio_cfg)

synthesizer.speak_text_async("Hello from Azure TTS!").get()
```

----------------------------------------

TITLE: Workflow Node Definitions
DESCRIPTION: Contains the definitions for each node used in the PocketFlow workflow. This includes the logic executed by each specific node.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-gradio-hitl/README.md#_snippet_6

LANGUAGE: python
CODE:
```
# nodes.py: Contains the node definitions for the workflow
```

----------------------------------------

TITLE: Install Main Script Dependencies
DESCRIPTION: Installs the Python package required for running the `__main__.py` script, which is Click for command-line interface creation.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-a2a/requirements.txt#_snippet_2

LANGUAGE: bash
CODE:
```
pip install click>=8.0.0,<9.0.0
```

----------------------------------------

TITLE: Pocketflow: File Handling and I/O
DESCRIPTION: This section provides examples of file handling and input/output operations within the Pocketflow project. It showcases how to read from and write to files, essential for data persistence and management.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow_demo.ipynb#_snippet_61

LANGUAGE: Python
CODE:
```
import os

def read_file(filepath):
    """Reads content from a specified file."""
    try:
        with open(filepath, 'r') as f:
            content = f.read()
            print(f"Successfully read from {filepath}")
            return content
    except FileNotFoundError:
        print(f"Error: File not found at {filepath}")
        return None

def write_file(filepath, content):
    """Writes content to a specified file."""
    try:
        with open(filepath, 'w') as f:
            f.write(content)
            print(f"Successfully wrote to {filepath}")
    except IOError:
        print(f"Error: Could not write to {filepath}")

# Example Usage:
file_path = "data.txt"
file_content = "This is sample content."

write_file(file_path, file_content)
read_content = read_file(file_path)
if read_content:
    print("File content:", read_content)

# Clean up the created file
if os.path.exists(file_path):
    os.remove(file_path)
    print(f"Cleaned up {file_path}")
```

----------------------------------------

TITLE: Install Dependencies with Pip
DESCRIPTION: Installs all necessary Python packages for the project from the requirements.txt file. This is a prerequisite for running the FastAPI application.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-fastapi-background/README.md#_snippet_0

LANGUAGE: bash
CODE:
```
pip install -r requirements.txt
```

----------------------------------------

TITLE: Call LLM Utility Function
DESCRIPTION: Demonstrates a Python utility function to call a Large Language Model (LLM) using the Google Generative AI library. It includes environment variable setup for API keys and model selection, and a basic example of how to use the function.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/docs/guide.md#_snippet_4

LANGUAGE: Python
CODE:
```
from google import genai
import os

def call_llm(prompt: str) -> str:
    client = genai.Client(
        api_key=os.getenv("GEMINI_API_KEY", ""),
    )
    model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    response = client.models.generate_content(model=model, contents=[prompt])
    return response.text

if __name__ == "__main__":
    test_prompt = "Hello, how are you?"

    # First call - should hit the API
    print("Making call...")
    response1 = call_llm(test_prompt, use_cache=False)
    print(f"Response: {response1}")
```

----------------------------------------

TITLE: Install Dependencies (Bash)
DESCRIPTION: Installs project dependencies listed in the requirements.txt file using pip. This ensures all necessary libraries are available.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-tool-database/README.md#_snippet_1

LANGUAGE: bash
CODE:
```
pip install -r requirements.txt
```

----------------------------------------

TITLE: Install Pocket Flow
DESCRIPTION: This snippet shows how to install the Pocket Flow framework using pip. It's a straightforward command for setting up the library in your Python environment.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/README.md#_snippet_0

LANGUAGE: bash
CODE:
```
pip install pocketflow
```

----------------------------------------

TITLE: Install Pocket Flow (Python)
DESCRIPTION: This snippet shows how to install the Pocket Flow framework using pip. It's a straightforward command for adding the library to your Python environment.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-batch/translations/README_FRENCH.md#_snippet_0

LANGUAGE: bash
CODE:
```
pip install pocketflow
```

----------------------------------------

TITLE: Install Dependencies (Python)
DESCRIPTION: Installs the project's Python dependencies from the requirements.txt file. This ensures all necessary libraries are available.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-streamlit-fsm/README.md#_snippet_1

LANGUAGE: bash
CODE:
```
pip install -r requirements.txt
```

----------------------------------------

TITLE: Database Operations with SQL
DESCRIPTION: This snippet illustrates common SQL operations for managing data within a database. It includes examples of creating tables, inserting data, and querying records, fundamental for data storage in PocketFlow.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow_demo.ipynb#_snippet_32

LANGUAGE: SQL
CODE:
```
-- Create a new table
CREATE TABLE projects (
    id INT PRIMARY KEY,
    name VARCHAR(255),
    status VARCHAR(50)
);

-- Insert data into the table
INSERT INTO projects (id, name, status)
VALUES (1, 'PocketFlow', 'Active');

-- Query data from the table
SELECT * FROM projects WHERE status = 'Active';

```

----------------------------------------

TITLE: PocketFlow Graph Definition
DESCRIPTION: Illustrates the workflow structure using Mermaid syntax, showing the sequence of nodes and their connections within the PocketFlow graph. This defines the orchestration logic.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-gradio-hitl/README.md#_snippet_3

LANGUAGE: mermaid
CODE:
```
flowchart TD
    DecideAction[Decide Action Node] --> |"check-weather"| CheckWeather[Check Weather Node]
    CheckWeather --> DecideAction
    DecideAction --> |"book-hotel"| BookHotel[Book Hotel Node]
    BookHotel --> DecideAction
    DecideAction --> |"follow-up"| FollowUp[Follow Up Node]
    DecideAction --> |"result-notification"| ResultNotification[Result Notification Node]
```

----------------------------------------

TITLE: Managing PocketFlow Services with Shell Commands
DESCRIPTION: Provides essential shell commands for managing PocketFlow services, including starting, stopping, and checking the status of the system.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow_demo.ipynb#_snippet_65

LANGUAGE: Shell
CODE:
```
# Start PocketFlow service
pocketflow start

# Stop PocketFlow service
pocketflow stop

# Check PocketFlow service status
pocketflow status

# Restart PocketFlow service
pocketflow restart
```

----------------------------------------

TITLE: Initialize Pocketflow
DESCRIPTION: Demonstrates the initialization process for Pocketflow, likely setting up the core components or environment. This is a fundamental step before utilizing other functionalities.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow_demo.ipynb#_snippet_50

LANGUAGE: JavaScript
CODE:
```
import Pocketflow from 'pocketflow';

const pf = new Pocketflow();
console.log('Pocketflow initialized successfully.');
```

----------------------------------------

TITLE: Install Python Dependencies
DESCRIPTION: Installs the necessary Python packages for the project using pip. It reads dependencies from the 'requirements.txt' file.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-tool-embeddings/README.md#_snippet_1

LANGUAGE: bash
CODE:
```
pip install -r requirements.txt
```

----------------------------------------

TITLE: Install Requirements
DESCRIPTION: Installs the necessary Python packages for the project, including dependencies for asynchronous operations and API interactions.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-parallel-batch/README.md#_snippet_0

LANGUAGE: bash
CODE:
```
pip install -r requirements.txt
```

----------------------------------------

TITLE: PocketFlow Graph Construction
DESCRIPTION: Demonstrates how to construct a computational flow graph using PocketFlow. It shows chaining nodes, directed branching based on node output, and initializing a flow with a start node.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow_demo.ipynb#_snippet_41

LANGUAGE: HTML
CODE:
```
<p style="font-family: Arial, sans-serif; font-size: 24px; font-weight: bold; color: #333; ">
    4. Flow
  </p>

  <!-- Brief description of Flow -->
  <p style="font-family: Arial, sans-serif; font-size: 16px; color: #333; margin: 4px 0;">
    <strong>Flow</strong> connects your Nodes to a graph.
  </p>

  <!-- Unordered list of key points -->
  <ul style="font-family: Arial, sans-serif; font-size: 16px; color: #333; list-style-type: disc; margin: 10px 0; padding-left: 20px;">
    <li style="margin-bottom: 8px;">
      <strong>Chaining</strong> 
      (<code style="background: #f2f2f2; padding: 2px 4px; border-radius: 3px;">node_1 &gt;&gt; node_2</code>): Break down complex problems into simple chained steps.
    </li>
    <li style="margin-bottom: 8px;">
      <strong>Directed Branching</strong> 
      (<code style="background: #f2f2f2; padding: 2px 4px; border-radius: 3px;">node_1 - "action" -&gt;&gt; node_2</code>): 
      Agentic decisions—where a Node’s 
      <code style="background: #f2f2f2; padding: 2px 4px; border-radius: 3px;">post()</code> return the action string.
    </li>
    <li style="margin-bottom: 8px;">
      <strong>Set a Start Point</strong>: Create flow by specifying 
      <code style="background: #f2f2f2; padding: 2px 4px; border-radius: 3px;">Flow(start=node_a)</code>. 
      Then call 
      <code style="background: #f2f2f2; padding: 2px 4px; border-radius: 3px;">flow.run(shared)</code>.
    </li>
  </ul>

  <!-- Closing note -->
  <p style="font-family: Arial, sans-serif; font-size: 16px; color: #333; margin: 0; padding: 0;">
    That’s it! You can nest Flows, branch your actions, or keep it simple with a straight chain of Nodes.
  </p>
```

----------------------------------------

TITLE: Project Entry Point
DESCRIPTION: Provides the main Python script for the project, serving as the entry point. It imports and utilizes the `create_qa_flow` function to set up and run the application.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/docs/guide.md#_snippet_7

LANGUAGE: Python
CODE:
```
# main.py
from flow import create_qa_flow

# Example main function
# Please replace this with your own main function
```

----------------------------------------

TITLE: Run Text Converter Application
DESCRIPTION: Executes the main Python script to start the interactive text converter application.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-flow/README.md#_snippet_1

LANGUAGE: bash
CODE:
```
python main.py
```

----------------------------------------

TITLE: Python Virtual Environment Setup
DESCRIPTION: Sets up a Python virtual environment for project isolation. This is a standard practice to manage project dependencies separately.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-tool-embeddings/README.md#_snippet_0

LANGUAGE: bash
CODE:
```
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

----------------------------------------

TITLE: AsyncParallelBatchFlow Example
DESCRIPTION: Illustrates the implementation of AsyncParallelBatchFlow for running a sub-flow concurrently for each item in a batch. This example shows how to process multiple files by summarizing their content in parallel.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/docs/core_abstraction/parallel.md#_snippet_1

LANGUAGE: Python
CODE:
```
class SummarizeMultipleFiles(AsyncParallelBatchFlow):
    async def prep_async(self, shared):
        return [{"filename": f} for f in shared["files"]]

sub_flow = AsyncFlow(start=LoadAndSummarizeFile())
parallel_flow = SummarizeMultipleFiles(start=sub_flow)
await parallel_flow.run_async(shared)
```

----------------------------------------

TITLE: Run Web Crawler
DESCRIPTION: Executes the main script to start the web crawling process. The script will prompt for the target URL and the maximum number of pages to crawl.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-tool-crawler/README.md#_snippet_2

LANGUAGE: bash
CODE:
```
python main.py
```

----------------------------------------

TITLE: Run PocketFlow PDF Vision Example
DESCRIPTION: Executes the main script to process PDF files located in the 'pdfs' directory, extracting text from each page using the Vision API.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-tool-pdf-vision/README.md#_snippet_2

LANGUAGE: bash
CODE:
```
python main.py
```

----------------------------------------

TITLE: Install A2A Client Dependencies
DESCRIPTION: Installs the Python packages needed for the A2A Client. This includes HTTPX for making requests, HTTPX-SSE for handling server-sent events with HTTPX, AsyncClick for asynchronous command-line interfaces, and Pydantic for data validation.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-a2a/requirements.txt#_snippet_3

LANGUAGE: bash
CODE:
```
pip install httpx>=0.27.0,<0.28.0 httpx-sse>=0.4.0 asyncclick>=8.1.8 pydantic>=2.0.0,<3.0.0
```

----------------------------------------

TITLE: PocketFlow Graph and Node Connections
DESCRIPTION: Defines the PocketFlow graph structure and the connections between different nodes. This file contains the core logic for workflow orchestration.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-gradio-hitl/README.md#_snippet_5

LANGUAGE: python
CODE:
```
# flow.py: Defines the PocketFlow graph and node connections
```

----------------------------------------

TITLE: Setup Virtual Environment (Bash)
DESCRIPTION: Creates and activates a Python virtual environment for project dependencies. This is a standard practice for isolating project environments.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-tool-database/README.md#_snippet_0

LANGUAGE: bash
CODE:
```
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

----------------------------------------

TITLE: Verify API Key Setup
DESCRIPTION: Runs a utility script to verify that the API key and environment variables are correctly set up for API interactions. This helps in debugging potential connection issues.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-thinking/README.md#_snippet_2

LANGUAGE: python
CODE:
```
python utils.py
```

----------------------------------------

TITLE: Implement Summarization Node in Python
DESCRIPTION: This Python code defines a `SummarizeNode` class inheriting from `pocketflow.Node`. The `prep` method reads data from a shared store, `exec` calls an LLM to summarize the text, and `post` writes the summary back. The example demonstrates loading data from a file and running the node.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow_demo.ipynb#_snippet_21

LANGUAGE: Python
CODE:
```
from pocketflow import Node

class SummarizeNode(Node):
    def prep(self, shared):
        # Read data from shared store
        return shared["data"]["before.txt"]
        
    def exec(self, text):
        # Call LLM to summarize
        prompt = f"Summarize this text in 50 words:\n\n{text}"
        return call_llm(prompt)
    
    def post(self, shared, prep_res, exec_res):
        # Store the summary back
        shared["summary"] = exec_res
        # No specific next action needed
        return "default"

# Create test data
shared = {
    "data": {},
    "summary": None
}

# Load the file
with open("./data/PaulGrahamEssaysLarge/before.txt", "r") as f:
    shared["data"]["before.txt"] = f.read()

# Create and run the node
summarize_node = SummarizeNode()
summarize_node.run(shared)
```

----------------------------------------

TITLE: Run A2A Server
DESCRIPTION: Starts the A2A server, which hosts the PocketFlow agent, on a specified port.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-a2a/README.md#_snippet_3

LANGUAGE: Bash
CODE:
```
python a2a_server.py --port 10003
```

----------------------------------------

TITLE: PocketFlow Resume Qualification Workflow
DESCRIPTION: Defines the PocketFlow workflow for resume qualification, including nodes for reading resumes, evaluating them with an LLM, and aggregating the results.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-map-reduce/README.md#_snippet_3

LANGUAGE: python
CODE:
```
from pocketflow.flow import Flow
from pocketflow.nodes import Node

class ReadResumesNode(Node):
    def __init__(self, data_dir):
        self.data_dir = data_dir

    def run(self, context):
        # Logic to read resume files from data_dir
        pass

class EvaluateResumesNode(Node):
    def __init__(self, llm_wrapper):
        self.llm_wrapper = llm_wrapper

    def run(self, context):
        # Logic to evaluate each resume using LLM
        pass

class ReduceResultsNode(Node):
    def run(self, context):
        # Logic to aggregate results and generate summary
        pass

def create_resume_qualification_flow():
    flow = Flow()
    flow.add_node('ReadResumes', ReadResumesNode(data_dir='data/'))
    flow.add_node('EvaluateResumes', EvaluateResumesNode(llm_wrapper=None)) # llm_wrapper needs to be initialized
    flow.add_node('ReduceResults', ReduceResultsNode())

    flow.connect('ReadResumes', 'EvaluateResumes')
    flow.connect('EvaluateResumes', 'ReduceResults')

    return flow

```

----------------------------------------

TITLE: Install A2A Server Infrastructure Dependencies
DESCRIPTION: Installs the Python packages required for the A2A Server Infrastructure. This includes Starlette for asynchronous web framework, Uvicorn for running the server, SSE-Starlette for server-sent events, Pydantic for data validation, HTTPX for making requests, and AnyIO for asynchronous operations.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-a2a/requirements.txt#_snippet_1

LANGUAGE: bash
CODE:
```
pip install "starlette>=0.37.2,<0.38.0" "uvicorn[standard]>=0.29.0,<0.30.0" sse-starlette>=1.8.2,<2.0.0 "pydantic>=2.0.0,<3.0.0" "httpx>=0.27.0,<0.28.0" "anyio>=3.0.0,<5.0.0"
```

----------------------------------------

TITLE: Set OpenAI API Key (Bash)
DESCRIPTION: Sets the OpenAI API key as an environment variable. This is a prerequisite for running the application, allowing it to authenticate with the OpenAI service.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-mcp/README.md#_snippet_0

LANGUAGE: bash
CODE:
```
export OPENAI_API_KEY="your-api-key-here"
```

----------------------------------------

TITLE: Create Question-Answering Flow
DESCRIPTION: Demonstrates how to create a question-answering flow using Pocketflow. It defines the sequence of nodes (`GetQuestionNode` and `AnswerNode`) and sets up the starting point for the flow.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/docs/guide.md#_snippet_6

LANGUAGE: Python
CODE:
```
# flow.py
from pocketflow import Flow
from nodes import GetQuestionNode, AnswerNode

def create_qa_flow():
    """Create and return a question-answering flow."""
    # Create nodes
    get_question_node = GetQuestionNode()
    answer_node = AnswerNode()
    
    # Connect nodes in sequence
    get_question_node >> answer_node
    
    # Create flow starting with input node
    return Flow(start=get_question_node)
```

----------------------------------------

TITLE: Synthesize Speech with Google Cloud TTS (Python)
DESCRIPTION: Shows how to use the Google Cloud Text-to-Speech client library in Python. It involves setting up the client, defining the input text, voice parameters, and audio configuration.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/docs/utility_function/text_to_speech.md#_snippet_1

LANGUAGE: Python
CODE:
```
from google.cloud import texttospeech

client = texttospeech.TextToSpeechClient()
input_text = texttospeech.SynthesisInput(text="Hello from Google Cloud TTS!")
voice = texttospeech.VoiceSelectionParams(language_code="en-US")
audio_cfg = texttospeech.AudioConfig(audio_encoding=texttospeech.AudioEncoding.MP3)

resp = client.synthesize_speech(input=input_text, voice=voice, audio_config=audio_cfg)

with open("gcloud_tts.mp3", "wb") as f:
    f.write(resp.audio_content)
```

----------------------------------------

TITLE: Project Dependencies (Text)
DESCRIPTION: Lists the Python packages required for the project, including FastAPI, Uvicorn, Jinja2, and PocketFlow. This file is used by pip to install necessary libraries.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-fastapi-hitl/README.md#_snippet_9

LANGUAGE: Text
CODE:
```
# Placeholder for requirements.txt content
# Example structure:
# fastapi
# uvicorn[standard]
# jinja2
# pocketflow
```

----------------------------------------

TITLE: Python Shared Store Design Example
DESCRIPTION: An example of a shared store design in Python for PocketFlow nodes. It demonstrates a nested dictionary structure for storing user context and results, adhering to the 'Don't Repeat Yourself' principle.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/docs/guide.md#_snippet_2

LANGUAGE: python
CODE:
```
shared = {
    "user": {
        "id": "user123",
        "context": {
            "weather": {"temp": 72, "condition": "sunny"},
            "location": "San Francisco"
        }
    },
    "results": {}
}
```

----------------------------------------

TITLE: Pocket Flow Chatbot
DESCRIPTION: A basic chatbot example demonstrating conversation history management within Pocket Flow.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/README.md#_snippet_0

LANGUAGE: Python
CODE:
```
from pocketflow.chat import Chat

chat = Chat()
response = chat.send_message("Hello, how are you?")
print(response)
```

----------------------------------------

TITLE: Database Interaction
DESCRIPTION: This example demonstrates how to interact with a database, likely for storing or retrieving processed data. It covers common operations such as connecting, querying, and inserting data, ensuring data persistence for the PocketFlow project.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow_demo.ipynb#_snippet_71

LANGUAGE: Java
CODE:
```
import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;

public class DatabaseUtil {
    private static final String DB_URL = "jdbc:postgresql://localhost:5432/pocketflowdb";
    private static final String USER = "user";
    private static final String PASS = "password";

    public static Connection getConnection() throws SQLException {
        return DriverManager.getConnection(DB_URL, USER, PASS);
    }

    public static void saveData(String id, double value) {
        String sql = "INSERT INTO processed_data(id, value) VALUES(?, ?)";
        try (Connection conn = getConnection();
             PreparedStatement pstmt = conn.prepareStatement(sql)) {
            pstmt.setString(1, id);
            pstmt.setDouble(2, value);
            pstmt.executeUpdate();
        } catch (SQLException e) {
            e.printStackTrace();
        }
    }

    public static void main(String[] args) {
        saveData("item123", 42.5);
    }
}
```

----------------------------------------

TITLE: JavaScript: Basic Function Example
DESCRIPTION: A simple JavaScript function demonstrating a basic operation. This snippet is likely part of a larger module or utility within the project.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow_demo.ipynb#_snippet_72

LANGUAGE: JavaScript
CODE:
```
function example() {
  return true;
}
```

----------------------------------------

TITLE: JavaScript: Basic Function Example
DESCRIPTION: A simple JavaScript function demonstrating a basic operation. This snippet is likely part of a larger library or utility set.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow_demo.ipynb#_snippet_45

LANGUAGE: JavaScript
CODE:
```
function greet(name) {
  return `Hello, ${name}!`;
}
```

----------------------------------------

TITLE: Set OpenAI API Key
DESCRIPTION: Sets the OpenAI API key as an environment variable, which is required for the LLM to evaluate resumes.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-map-reduce/README.md#_snippet_1

LANGUAGE: bash
CODE:
```
export OPENAI_API_KEY=your_api_key_here
```

----------------------------------------

TITLE: Install PocketFlow Agent Dependencies
DESCRIPTION: Installs the necessary Python packages for the PocketFlow Agent logic, including PocketFlow itself, OpenAI for AI capabilities, and DuckDuckGo Search for information retrieval. PyYAML is also required for configuration.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-a2a/requirements.txt#_snippet_0

LANGUAGE: bash
CODE:
```
pip install pocketflow>=0.0.1 openai>=1.0.0 duckduckgo-search>=7.5.2 pyyaml>=5.1
```

----------------------------------------

TITLE: Drag Start Event Handler
DESCRIPTION: Handles the start of a drag operation for a simulation node. It sets the alpha target for the simulation and fixes the node's position to its current location.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-visualization/viz/flow_visualization.html#_snippet_12

LANGUAGE: JavaScript
CODE:
```
function dragstarted(event, d) {
  if (!event.active) simulation.alphaTarget(0.3).restart();
  d.fx = d.x;
  d.fy = d.y;
}
```

----------------------------------------

TITLE: Run PocketFlow Agent with Question
DESCRIPTION: This Python code demonstrates how to execute the PocketFlow agent. It takes a question from command-line arguments or uses a default, initializes the agent flow, and prints the processed answer.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-agent/demo.ipynb#_snippet_7

LANGUAGE: python
CODE:
```
import sys

def main():
    """Simple function to process a question."""
    # Default question
    default_question = "Who won the Nobel Prize in Physics 2024?"

    # Get question from command line if provided with --
    question = default_question
    for arg in sys.argv[1:]:
        if arg.startswith("--"):
            question = arg[2:]
            break

    # Create the agent flow
    agent_flow = create_agent_flow()

    # Process the question
    shared = {"question": question}
    print(f"🤔 Processing question: {question}")
    agent_flow.run(shared)
    print("\n🎯 Final Answer:")
    print(shared.get("answer", "No answer found"))

main()

```

----------------------------------------

TITLE: Set OpenAI API Key Environment Variable
DESCRIPTION: Sets the OPENAI_API_KEY environment variable, which is necessary for the application to authenticate with OpenAI services for LLM processing.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-gradio-hitl/README.md#_snippet_1

LANGUAGE: bash
CODE:
```
export OPENAI_API_KEY="your-openai-api-key-here"
```

----------------------------------------

TITLE: Installieren Pocket Flow mit pip
DESCRIPTION: So installieren Sie das Pocket Flow-Framework mit pip. Dies ist der einfachste Weg, um mit der Verwendung des Frameworks zu beginnen.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-batch/translations/README_GERMAN.md#_snippet_0

LANGUAGE: bash
CODE:
```
pip install pocketflow
```

----------------------------------------

TITLE: Run Streamlit Application (Python)
DESCRIPTION: Starts the Streamlit web application. This command launches the user interface for the image generation HITL process.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-streamlit-fsm/README.md#_snippet_2

LANGUAGE: bash
CODE:
```
streamlit run app.py
```

----------------------------------------

TITLE: Synthesize Speech with Amazon Polly (Python)
DESCRIPTION: Demonstrates how to synthesize speech using Amazon Polly's SDK for Python. It requires AWS credentials and specifies the desired voice and output format.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/docs/utility_function/text_to_speech.md#_snippet_0

LANGUAGE: Python
CODE:
```
import boto3

polly = boto3.client("polly", region_name="us-east-1",
                     aws_access_key_id="YOUR_AWS_ACCESS_KEY_ID",
                     aws_secret_access_key="YOUR_AWS_SECRET_ACCESS_KEY")

resp = polly.synthesize_speech(
    Text="Hello from Polly!",
    OutputFormat="mp3",
    VoiceId="Joanna"
)

with open("polly.mp3", "wb") as f:
    f.write(resp["AudioStream"].read())
```

----------------------------------------

TITLE: Run Article Workflow
DESCRIPTION: Executes the main Python script to start the article writing workflow. It can be run with a default topic or a custom topic.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-workflow/README.md#_snippet_2

LANGUAGE: bash
CODE:
```
python main.py
```

LANGUAGE: bash
CODE:
```
python main.py Climate Change
```

----------------------------------------

TITLE: Synthesize Speech with ElevenLabs (Python)
DESCRIPTION: Demonstrates integrating with the ElevenLabs Text-to-Speech API using Python's requests library. It requires an ElevenLabs API key and a voice ID, and allows customization of voice settings.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/docs/utility_function/text_to_speech.md#_snippet_4

LANGUAGE: Python
CODE:
```
import requests

api_key = "ELEVENLABS_KEY"
voice_id = "ELEVENLABS_VOICE"
url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
headers = {"xi-api-key": api_key, "Content-Type": "application/json"}

json_data = {
    "text": "Hello from ElevenLabs!",
    "voice_settings": {"stability": 0.75, "similarity_boost": 0.75}
}

resp = requests.post(url, headers=headers, json=json_data)

with open("elevenlabs.mp3", "wb") as f:
    f.write(resp.content)
```

----------------------------------------

TITLE: Run Batch Translation
DESCRIPTION: Executes the main Python script to start the batch translation process for documents.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-batch/README.md#_snippet_2

LANGUAGE: bash
CODE:
```
python main.py
```

----------------------------------------

TITLE: Outline Generation (YAML)
DESCRIPTION: An example of the YAML structured output for generating an article outline, specifying sections for the content.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-workflow/README.md#_snippet_4

LANGUAGE: yaml
CODE:
```
sections:
- Introduction to AI Safety
- Key Challenges in AI Safety
- Strategies for Ensuring AI Safety
```

----------------------------------------

TITLE: Pocket Flow Map-Reduce Resume Qualification
DESCRIPTION: This example utilizes the map-reduce pattern in Pocket Flow for batch processing and evaluating resumes.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/README.md#_snippet_5

LANGUAGE: Python
CODE:
```
from pocketflow.map_reduce import MapReduce

processor = MapReduce()
resumes = ["resume1.txt", "resume2.txt"]
qualified_resumes = processor.process_batch(resumes)
print(qualified_resumes)
```

----------------------------------------

TITLE: Call Ollama LLM
DESCRIPTION: Shows how to use the 'ollama' library to interact with locally hosted LLMs. This example uses the 'llama2' model and requires the 'ollama' Python package.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/docs/utility_function/llm.md#_snippet_4

LANGUAGE: python
CODE:
```
from ollama import chat
response = chat(
    model="llama2",
    messages=[{"role": "user", "content": prompt}]
)
return response.message.content
```

----------------------------------------

TITLE: Pocket Flow Structured Output Extraction
DESCRIPTION: This example shows how to extract structured data, such as information from resumes, by leveraging Pocket Flow's prompting capabilities.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/README.md#_snippet_1

LANGUAGE: Python
CODE:
```
from pocketflow.structured_output import StructuredOutput

extractor = StructuredOutput()
resume_text = "..."
structured_data = extractor.extract(resume_text)
print(structured_data)
```

----------------------------------------

TITLE: LLM and Web Search Utilities
DESCRIPTION: Provides utility functions for interacting with OpenAI's LLM for text generation and DuckDuckGo for web searching. Includes examples of how to use these functions.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-agent/demo.ipynb#_snippet_1

LANGUAGE: python
CODE:
```
# utils.py
from openai import OpenAI
import os
from duckduckgo_search import DDGS

def call_llm(prompt):
    client = OpenAI(api_key="your-api-key")
    r = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}]
    )
    return r.choices[0].message.content

def search_web(query):
    results = DDGS().text(query, max_results=5)
    # Convert results to a string
    results_str = "\n\n".join([f"Title: {r['title']}\nURL: {r['href']}\nSnippet: {r['body']}" for r in results])
    return results_str

print("## Testing call_llm")
prompt = "In a few words, what is the meaning of life?"
print(f"## Prompt: {prompt}")
response = call_llm(prompt)
print(f"## Response: {response}")

print("## Testing search_web")
query = "Who won the Nobel Prize in Physics 2024?"
print(f"## Query: {query}")
results = search_web(query)
print(f"## Results: {results}")
```

----------------------------------------

TITLE: Mermaid Flowchart for Joke Generator
DESCRIPTION: Visualizes the workflow of the command-line joke generator. It shows the sequence of nodes: getting the topic, generating a joke, getting user feedback, and either ending or regenerating the joke.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-cli-hitl/docs/design.md#_snippet_0

LANGUAGE: mermaid
CODE:
```
flowchart TD
    GetTopic[GetTopicNode] --> GenerateJoke[GenerateJokeNode]
    GenerateJoke --> GetFeedback[GetFeedbackNode]
    GetFeedback -- "Approve" --> Z((End))
    GetFeedback -- "Disapprove" --> GenerateJoke
```

----------------------------------------

TITLE: API Interaction with JavaScript
DESCRIPTION: This example shows how to interact with an API using JavaScript, fetching data and handling responses. It's crucial for integrating PocketFlow with external services.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow_demo.ipynb#_snippet_31

LANGUAGE: JavaScript
CODE:
```
async function fetchData(apiUrl) {
  try {
    const response = await fetch(apiUrl);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    const data = await response.json();
    console.log('Data fetched successfully:', data);
    return data;
  } catch (error) {
    console.error('Error fetching data:', error);
  }
}

const apiUrl = 'https://api.example.com/data';
fetchData(apiUrl);

```

----------------------------------------

TITLE: Run Joke Generator
DESCRIPTION: Launches the main command-line joke generator application. This script orchestrates the PocketFlow workflow for generating jokes based on user input and feedback.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-cli-hitl/README.md#_snippet_3

LANGUAGE: python
CODE:
```
python main.py
```

----------------------------------------

TITLE: Pocket Flow Research Agent
DESCRIPTION: An example of a research agent built with Pocket Flow that can perform web searches and answer questions.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/README.md#_snippet_3

LANGUAGE: Python
CODE:
```
from pocketflow.agent import Agent

agent = Agent()
answer = agent.research("What is the capital of France?")
print(answer)
```

----------------------------------------

TITLE: JavaScript: Asynchronous API Call
DESCRIPTION: An example of an asynchronous API call using JavaScript's fetch API. This snippet illustrates how to interact with external services.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow_demo.ipynb#_snippet_48

LANGUAGE: JavaScript
CODE:
```
async function fetchData(url) {
  const response = await fetch(url);
  const data = await response.json();
  return data;
}
```

----------------------------------------

TITLE: Extract Key Information with YAML
DESCRIPTION: Demonstrates extracting structured product information into a YAML format. This serves as an example of defining key-value pairs for specific data.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/docs/design_pattern/structure.md#_snippet_0

LANGUAGE: yaml
CODE:
```
product:
  name: Widget Pro
  price: 199.99
  description: |
    A high-quality widget designed for professionals.
    Recommended for advanced users.
```

----------------------------------------

TITLE: Build Cursor with Cursor (Agentic Coding)
DESCRIPTION: This example demonstrates building the Cursor application using agentic coding. It focuses on the 'Agent' design pattern and provides access to the design documentation and the Python 'Flow' code.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-batch/translations/README_CHINESE.md#_snippet_3

LANGUAGE: Python
CODE:
```
https://github.com/The-Pocket/Tutorial-Cursor/blob/main/flow.py
```

----------------------------------------

TITLE: Run PocketFlow Voice Chat (Bash)
DESCRIPTION: Executes the main Python script to start the PocketFlow voice chat application. Users will be prompted to speak their queries after the application begins listening.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-voice-chat/README.md#_snippet_2

LANGUAGE: bash
CODE:
```
python main.py
```

----------------------------------------

TITLE: Run Application
DESCRIPTION: Executes the main Python script to start the Taboo game application.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-multi-agent/README.md#_snippet_2

LANGUAGE: bash
CODE:
```
python main.py
```

----------------------------------------

TITLE: Pocket Flow Parallel Image Processing
DESCRIPTION: This example demonstrates parallel image processing with multiple filters using Pocket Flow, achieving an 8x speedup.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/README.md#_snippet_11

LANGUAGE: Python
CODE:
```
from pocketflow.parallel_image import ParallelImageProcessor

processor = ParallelImageProcessor()
image = "path/to/image.jpg"
processed_image = processor.apply_filters(image, [filter1, filter2, filter3])
print(processed_image)
```

----------------------------------------

TITLE: Run Default Example
DESCRIPTION: Executes the main script to process the default Jane Street problem using the Chain-of-Thought implementation. This demonstrates the core functionality with a predefined complex reasoning task.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-thinking/README.md#_snippet_3

LANGUAGE: python
CODE:
```
python main.py
```

----------------------------------------

TITLE: Test Agent Functionality
DESCRIPTION: Runs a utility script to test the LLM call and web search capabilities of the agent. This helps verify the setup.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-agent/README.md#_snippet_2

LANGUAGE: bash
CODE:
```
python utils.py
```

----------------------------------------

TITLE: Print Summary in Python
DESCRIPTION: This Python code snippet prints a summary from the shared object. It's a basic example of accessing and displaying data within the Pocketflow environment.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow_demo.ipynb#_snippet_22

LANGUAGE: Python
CODE:
```
print("Summary:", shared["summary"])
```

----------------------------------------

TITLE: PocketFlow Chat UI and WebSocket Logic
DESCRIPTION: This snippet contains the HTML structure for the chat interface, CSS for styling, and JavaScript code to establish a WebSocket connection, send and receive messages, and update the UI accordingly. It handles connection status, streaming AI responses, and user input.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-fastapi-websocket/static/index.html#_snippet_0

LANGUAGE: HTML
CODE:
```
<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; display: flex; align-items: center; justify-content: center; padding: 20px; }
.chat-container { background: rgba(255, 255, 255, 0.95); backdrop-filter: blur(10px); border-radius: 20px; width: 100%; max-width: 600px; height: 80vh; display: flex; flex-direction: column; box-shadow: 0 20px 40px rgba(0,0,0,0.1); overflow: hidden; }
.header { padding: 20px; background: rgba(255, 255, 255, 0.1); border-bottom: 1px solid rgba(255, 255, 255, 0.2); text-align: center; }
.header h1 { font-size: 24px; font-weight: 600; color: #333; margin-bottom: 5px; }
.status { font-size: 14px; color: #666; font-weight: 500; }
.messages { flex: 1; overflow-y: auto; padding: 20px; display: flex; flex-direction: column; gap: 16px; }
.message { max-width: 80%; padding: 12px 16px; border-radius: 18px; font-size: 15px; line-height: 1.4; word-wrap: break-word; }
.user-message { background: linear-gradient(135deg, #667eea, #764ba2); color: white; align-self: flex-end; border-bottom-right-radius: 4px; }
.ai-message { background: #f1f3f4; color: #333; align-self: flex-start; border-bottom-left-radius: 4px; }
.input-container { padding: 20px; background: rgba(255, 255, 255, 0.1); border-top: 1px solid rgba(255, 255, 255, 0.2); display: flex; gap: 12px; }
#messageInput { flex: 1; padding: 12px 16px; border: none; border-radius: 25px; background: white; font-size: 15px; outline: none; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
#messageInput::placeholder { color: #999; }
#sendButton { padding: 12px 24px; background: linear-gradient(135deg, #667eea, #764ba2); color: white; border: none; border-radius: 25px; cursor: pointer; font-size: 15px; font-weight: 600; transition: all 0.2s ease; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
#sendButton:hover:not(:disabled) { transform: translateY(-1px); box-shadow: 0 4px 15px rgba(0,0,0,0.2); }
#sendButton:disabled { background: #ccc; cursor: not-allowed; transform: none; }
.messages::-webkit-scrollbar { width: 6px; }
.messages::-webkit-scrollbar-track { background: transparent; }
.messages::-webkit-scrollbar-thumb { background: rgba(0,0,0,0.2); border-radius: 3px; }
</style>

<div class="chat-container">
    <div class="header">
        <h1>PocketFlow Chat</h1>
        <div class="status" id="status">Connecting...</div>
    </div>
    <div class="messages" id="messages"></div>
    <div class="input-container">
        <input type="text" id="messageInput" placeholder="Type your message..." disabled>
        <button id="sendButton" disabled>Send</button>
    </div>
</div>
```

LANGUAGE: JavaScript
CODE:
```
const ws = new WebSocket(`ws://localhost:8000/ws`);
const messagesDiv = document.getElementById('messages');
const messageInput = document.getElementById('messageInput');
const sendButton = document.getElementById('sendButton');
const statusDiv = document.getElementById('status');

let isStreaming = false;
let currentAiMessage = null;

ws.onopen = function() {
    statusDiv.textContent = 'Connected';
    messageInput.disabled = false;
    sendButton.disabled = false;
    messageInput.focus();
};

ws.onmessage = function(event) {
    const data = JSON.parse(event.data);
    if (data.type === 'start') {
        isStreaming = true;
        currentAiMessage = document.createElement('div');
        currentAiMessage.className = 'message ai-message';
        messagesDiv.appendChild(currentAiMessage);
        messagesDiv.scrollTop = messagesDiv.scrollHeight;
        sendButton.disabled = true;
        statusDiv.textContent = 'AI is typing...';
    } else if (data.type === 'chunk') {
        if (currentAiMessage) {
            currentAiMessage.textContent += data.content;
            messagesDiv.scrollTop = messagesDiv.scrollHeight;
        }
    } else if (data.type === 'end') {
        isStreaming = false;
        currentAiMessage = null;
        sendButton.disabled = false;
        statusDiv.textContent = 'Connected';
        messageInput.focus();
    }
};

ws.onclose = function() {
    statusDiv.textContent = 'Disconnected';
    messageInput.disabled = true;
    sendButton.disabled = true;
};

function sendMessage() {
    const message = messageInput.value.trim();
    if (message && !isStreaming) {
        const userMessage = document.createElement('div');
        userMessage.className = 'message user-message';
        userMessage.textContent = message;
        messagesDiv.appendChild(userMessage);
        messagesDiv.scrollTop = messagesDiv.scrollHeight;
        ws.send(JSON.stringify({ type: 'message', content: message }));
        messageInput.value = '';
        statusDiv.textContent = 'Sending...';
    }
}

sendButton.addEventListener('click', sendMessage);

messageInput.addEventListener('keypress', function(e) {
    if (e.key === 'Enter') {
        e.preventDefault();
        sendMessage();
    }
});
```

----------------------------------------

TITLE: Run Resume Parser Application
DESCRIPTION: Executes the main Python script that parses the resume data using PocketFlow and the OpenAI API. This is the primary command to start the data extraction process.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-structured-output/README.md#_snippet_3

LANGUAGE: python
CODE:
```
python main.py
```

----------------------------------------

TITLE: Run FastAPI Server (Bash)
DESCRIPTION: Starts the FastAPI web server using Uvicorn. The `--reload` flag is useful for development, automatically restarting the server on code changes. The server runs on port 8000.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-fastapi-hitl/README.md#_snippet_1

LANGUAGE: Bash
CODE:
```
uvicorn server:app --reload --port 8000
```

----------------------------------------

TITLE: Define Pocketflow Nodes
DESCRIPTION: Shows how to define custom nodes for a Pocketflow project. It includes examples of a `GetQuestionNode` to capture user input and an `AnswerNode` that utilizes the `call_llm` utility to generate an answer.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/docs/guide.md#_snippet_5

LANGUAGE: Python
CODE:
```
# nodes.py
from pocketflow import Node
from utils.call_llm import call_llm

class GetQuestionNode(Node):
    def exec(self, _):
        # Get question directly from user input
        user_question = input("Enter your question: ")
        return user_question
    
    def post(self, shared, prep_res, exec_res):
        # Store the user's question
        shared["question"] = exec_res
        return "default"  # Go to the next node

class AnswerNode(Node):
    def prep(self, shared):
        # Read question from shared
        return shared["question"]
    
    def exec(self, question):
        # Call LLM to get the answer
        return call_llm(question)
    
    def post(self, shared, prep_res, exec_res):
        # Store the answer in shared
        shared["answer"] = exec_res
```

----------------------------------------

TITLE: Cold Email Generator (Map Reduce, Web Search)
DESCRIPTION: This example demonstrates a cold email personalization tool that converts cold leads into warm icebreakers. It utilizes 'Map Reduce' and 'Web Search' utility functions, with links to its design documentation and Python 'Flow' code.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-batch/translations/README_CHINESE.md#_snippet_7

LANGUAGE: Python
CODE:
```
https://github.com/The-Pocket/Tutorial-Cold-Email-Personalization/blob/master/flow.py
```

----------------------------------------

TITLE: Toggle MCP Integration (Python)
DESCRIPTION: Allows switching between using the Model Context Protocol (MCP) and local function implementations within the application. This is controlled by a boolean flag in the `utils.py` file.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-mcp/README.md#_snippet_2

LANGUAGE: python
CODE:
```
MCP = True  # Set to False to use local function implementations
```

----------------------------------------

TITLE: Implement AsyncNode for Asynchronous Operations
DESCRIPTION: Demonstrates how to create an AsyncNode by implementing asynchronous methods like prep_async, exec_async, and post_async. This example shows reading a file, calling an LLM asynchronously, and gathering user feedback for flow control.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/docs/core_abstraction/async.md#_snippet_0

LANGUAGE: python
CODE:
```
class SummarizeThenVerify(AsyncNode):
    async def prep_async(self, shared):
        # Example: read a file asynchronously
        doc_text = await read_file_async(shared["doc_path"])
        return doc_text

    async def exec_async(self, prep_res):
        # Example: async LLM call
        summary = await call_llm_async(f"Summarize: {prep_res}")
        return summary

    async def post_async(self, shared, prep_res, exec_res):
        # Example: wait for user feedback
        decision = await gather_user_feedback(exec_res)
        if decision == "approve":
            shared["summary"] = exec_res
            return "approve"
        return "deny"

summarize_node = SummarizeThenVerify()
final_node = Finalize()

# Define transitions
summarize_node - "approve" >> final_node
summarize_node - "deny"    >> summarize_node  # retry

flow = AsyncFlow(start=summarize_node)

async def main():
    shared = {"doc_path": "document.txt"}
    await flow.run_async(shared)
    print("Final Summary:", shared.get("summary"))

asyncio.run(main())
```

----------------------------------------

TITLE: Run FastAPI Application (Python)
DESCRIPTION: Starts the FastAPI application. This script serves the real-time chat interface and handles WebSocket connections for communication with the LLM.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-fastapi-websocket/README.md#_snippet_2

LANGUAGE: Python
CODE:
```
python main.py
```

----------------------------------------

TITLE: Configuration Management
DESCRIPTION: This snippet focuses on managing project configurations, including loading settings from files or environment variables. Proper configuration management ensures flexibility and adaptability of the PocketFlow system across different deployment environments.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow_demo.ipynb#_snippet_70

LANGUAGE: Python
CODE:
```
import json
import os

def load_config(config_path='config.json'):
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            return json.load(f)
    else:
        # Fallback to environment variables or default values
        return {
            'api_key': os.environ.get('API_KEY', 'default_key'),
            'timeout': int(os.environ.get('TIMEOUT', 30))
        }

config = load_config()
print(f"API Key: {config['api_key']}")
```

----------------------------------------

TITLE: Pocketflow Data Handling (Python)
DESCRIPTION: Provides an example of data handling within the Pocketflow framework using Python. This might involve data structures or specific methods for manipulation.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow_demo.ipynb#_snippet_52

LANGUAGE: Python
CODE:
```
from pocketflow import Pocketflow

pf = Pocketflow()
data = {'sample': 'data'}

processed_data = pf.handle_data(data)
print(f'Processed data: {processed_data}')
```

----------------------------------------

TITLE: Basic Programming Example (No Recursion)
DESCRIPTION: This snippet represents a basic programming approach, similar to what might have been written in early versions of Basic. It highlights the limitations of languages that do not support recursion, a feature considered essential for many modern programming tasks.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/data/PaulGrahamEssaysLarge/avg.txt#_snippet_2

LANGUAGE: Basic
CODE:
```
10 PRINT "Hello, World!"
20 GOTO 10
```

----------------------------------------

TITLE: Run Application (Bash)
DESCRIPTION: This snippet demonstrates how to activate the Pipenv virtual environment and run the main Python application. This is the command to start the Pocket Google Calendar application.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-google-calendar/README.md#_snippet_1

LANGUAGE: Bash
CODE:
```
pipenv shell
python main.py
```

----------------------------------------

TITLE: Streamlit FSM for HITL Image Generation
DESCRIPTION: This example demonstrates how to build a Streamlit application featuring a finite state machine (FSM) for handling human-in-the-loop (HITL) image generation. It showcases the integration of FSM logic within a web interface.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/README.md#_snippet_24

LANGUAGE: Python
CODE:
```
from pocketflow.fsm import State, Transition, FiniteStateMachine
from pocketflow.utils import get_logger

logger = get_logger(__name__)


class ImageGenFSM(FiniteStateMachine):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def on_enter_state(self, state: State, event: str, context: dict) -> None:
        logger.info(f"Entering state: {state.name} via event: {event}")
        context['history'].append(state.name)

    def on_exit_state(self, state: State, event: str, context: dict) -> None:
        logger.info(f"Exiting state: {state.name} via event: {event}")

    def on_transition(self, from_state: State, to_state: State, event: str, context: dict) -> None:
        logger.info(f"Transitioning from {from_state.name} to {to_state.name} via event: {event}")


def main():
    # Define states
    idle = State('idle')
    generating = State('generating')
    review = State('review')
    approved = State('approved')
    rejected = State('rejected')

    # Define transitions
    transitions = [
        Transition(idle, generating, 'start_generation'),
        Transition(generating, review, 'generation_complete'),
        Transition(review, approved, 'approve'),
        Transition(review, rejected, 'reject'),
        Transition(approved, idle, 'reset'),
        Transition(rejected, idle, 'reset')
    ]

    # Initialize FSM
    fsm = ImageGenFSM(states=[idle, generating, review, approved, rejected], transitions=transitions, initial_state=idle)

    # Example usage
    context = {'history': []}
    fsm.send('start_generation', context)
    fsm.send('generation_complete', context)
    fsm.send('approve', context)
    fsm.send('reset', context)

    print(f"State history: {context['history']}")

if __name__ == '__main__':
    main()

```

----------------------------------------

TITLE: D3.js Force-Directed Graph Setup
DESCRIPTION: Initializes a D3.js force-directed simulation with custom forces for grouping and layout. It sets up the SVG canvas and appends groups for links, nodes, labels, and group elements. This forms the foundation for the interactive graph visualization.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-visualization/viz/flow_visualization.html#_snippet_2

LANGUAGE: javascript
CODE:
```
const simulation = d3.forceSimulation(data.nodes)
 .force("link", d3.forceLink(data.links).id(d => d.id).distance(100))
 .force("charge", d3.forceManyBody().strength(-300))
 .force("center", d3.forceCenter(width / 2, height / 2));

// Custom forces for grouping and layout
const groupForce = (k) => {
  data.nodes.forEach(n => {
    if (n.group !== undefined && groups[n.group]) {
      const group = groups[n.group];
      n.vx -= (n.x - group.centerX) * k;
      n.vy -= (n.y - group.centerY) * k;
    }
  });
};

const groupLayoutForce = (k) => {
  data.nodes.forEach(n => {
    if (n.group !== undefined && groups[n.group]) {
      const group = groups[n.group];
      n.vx -= (n.x - group.x - group.width / 2) * k;
      n.vy -= (n.y - group.y - group.height / 2) * k;
    }
  });
};

simulation.force("group", groupForce);
simulation.force("groupLayout", groupLayoutForce);
```

----------------------------------------

TITLE: Synthesize Speech with IBM Watson TTS (Python)
DESCRIPTION: Illustrates how to use the IBM Watson Text-to-Speech service with Python. It requires an IBM API key and service URL, and allows specifying the voice and audio format.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/docs/utility_function/text_to_speech.md#_snippet_3

LANGUAGE: Python
CODE:
```
from ibm_watson import TextToSpeechV1
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator

auth = IAMAuthenticator("IBM_API_KEY")
service = TextToSpeechV1(authenticator=auth)
service.set_service_url("IBM_SERVICE_URL")

resp = service.synthesize(
    "Hello from IBM Watson!",
    voice="en-US_AllisonV3Voice",
    accept="audio/mp3"
).get_result()

with open("ibm_tts.mp3", "wb") as f:
    f.write(resp.content)
```

----------------------------------------

TITLE: Pocket Flow Chatbot with Memory
DESCRIPTION: A chatbot example that incorporates both short-term and long-term memory using Pocket Flow's memory management features.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/README.md#_snippet_13

LANGUAGE: Python
CODE:
```
from pocketflow.chat_memory import ChatWithMemory

chat_memory = ChatWithMemory()
chat_memory.send_message("My name is Alice.")
response = chat_memory.send_message("What is my name?")
print(response)
```

----------------------------------------

TITLE: AsyncParallelBatchNode Example
DESCRIPTION: Demonstrates how to create a custom AsyncParallelBatchNode to process multiple texts concurrently. It defines preparation, execution (calling an LLM asynchronously), and post-processing steps to summarize texts in parallel.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/docs/core_abstraction/parallel.md#_snippet_0

LANGUAGE: Python
CODE:
```
class ParallelSummaries(AsyncParallelBatchNode):
    async def prep_async(self, shared):
        # e.g., multiple texts
        return shared["texts"]

    async def exec_async(self, text):
        prompt = f"Summarize: {text}"
        return await call_llm_async(prompt)

    async def post_async(self, shared, prep_res, exec_res_list):
        shared["summary"] = "\n\n".join(exec_res_list)
        return "default"

node = ParallelSummaries()
flow = AsyncFlow(start=node)
```

----------------------------------------

TITLE: PocketFlow Data Processing
DESCRIPTION: This snippet demonstrates core data processing functionalities within the PocketFlow project. It includes examples of how data is handled and transformed, often relying on standard library functions.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow_demo.ipynb#_snippet_43

LANGUAGE: JavaScript
CODE:
```
function processData(data) {
  // Process data here
  return processedData;
}
```

LANGUAGE: Python
CODE:
```
def process_data(data):
    # Process data here
    return processed_data
```

----------------------------------------

TITLE: Pocket Flow Workflow Tutorial
DESCRIPTION: This tutorial illustrates a writing workflow implemented with Pocket Flow. It involves outlining content, writing the actual text, and applying specific styling, demonstrating sequential task execution.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/README.md#_snippet_5

LANGUAGE: Python
CODE:
```
# Example for pocketflow-workflow
# from pocketflow.workflow import WritingWorkflow
# 
# workflow = WritingWorkflow()
# result = workflow.execute("Topic")
# print(result)

```

----------------------------------------

TITLE: Test LLM Utility
DESCRIPTION: Executes the 'call_llm.py' utility script to test the integration with the LLM. This helps verify that the API key is set correctly and the utility can communicate with the LLM.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-cli-hitl/README.md#_snippet_2

LANGUAGE: python
CODE:
```
python utils/call_llm.py
```

----------------------------------------

TITLE: JavaScript: Initialize Pocketflow
DESCRIPTION: Initializes the Pocketflow system with specified configurations. This is a foundational step for using Pocketflow's features. It typically involves setting up event listeners and data structures.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow_demo.ipynb#_snippet_34

LANGUAGE: JavaScript
CODE:
```
function initializePocketflow(config) {
  console.log('Initializing Pocketflow with config:', config);
  // ... initialization logic ...
  return true;
}
```

----------------------------------------

TITLE: Pocket Flow Chat Guardrail
DESCRIPTION: A travel advisor chatbot example that uses Pocket Flow's guardrail feature to ensure only travel-related queries are processed.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/README.md#_snippet_7

LANGUAGE: Python
CODE:
```
from pocketflow.chat_guardrail import ChatGuardrail

advisor = ChatGuardrail()
response = advisor.ask("Book a flight to Paris.")
print(response)
response = advisor.ask("What's the weather like?") # This might be blocked
```

----------------------------------------

TITLE: Params for Node-Specific Identifiers
DESCRIPTION: Illustrates using Params to pass node-specific identifiers like filenames. The example shows how Flow params can override Node params.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/docs/core_abstraction/communication.md#_snippet_1

LANGUAGE: python
CODE:
```
# 1) Create a Node that uses params
class SummarizeFile(Node):
    def prep(self, shared):
        # Access the node's param
        filename = self.params["filename"]
        return shared["data"].get(filename, "")

    def exec(self, prep_res):
        prompt = f"Summarize: {prep_res}"
        return call_llm(prompt)

    def post(self, shared, prep_res, exec_res):
        filename = self.params["filename"]
        shared["summary"][filename] = exec_res
        return "default"

# 2) Set params
node = SummarizeFile()

# 3) Set Node params directly (for testing)
node.set_params({"filename": "doc1.txt"})
node.run(shared)

# 4) Create Flow
flow = Flow(start=node)

# 5) Set Flow params (overwrites node params)
flow.set_params({"filename": "doc2.txt"})
flow.run(shared)  # The node summarizes doc2, not doc1
```

----------------------------------------

TITLE: JavaScript: Asynchronous Data Fetching
DESCRIPTION: An example of asynchronous data fetching in JavaScript, likely using the `fetch` API or a similar library. This is common for interacting with external services or APIs.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow_demo.ipynb#_snippet_75

LANGUAGE: JavaScript
CODE:
```
async function fetchData(url) {
  try {
    const response = await fetch(url);
    const data = await response.json();
    console.log(data);
  } catch (error) {
    console.error('Error fetching data:', error);
  }
}
```

----------------------------------------

TITLE: Pinecone: Initialize, Create, Upsert, and Query Index
DESCRIPTION: Shows how to initialize Pinecone with an API key and environment, create an index if it doesn't exist, upsert vectors, and query the index. Requires the Pinecone client library.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/docs/utility_function/vector.md#_snippet_1

LANGUAGE: Python
CODE:
```
import pinecone

pinecone.init(api_key="YOUR_API_KEY", environment="YOUR_ENV")

index_name = "my-index"

# Create the index if it doesn't exist
if index_name not in pinecone.list_indexes():
    pinecone.create_index(name=index_name, dimension=128)

# Connect
index = pinecone.Index(index_name)

# Upsert
vectors = [
    ("id1", [0.1]*128),
    ("id2", [0.2]*128)
]
index.upsert(vectors)

# Query
response = index.query([[0.15]*128], top_k=3)
print(response)
```

----------------------------------------

TITLE: Ask AI Paul Graham (RAG, Map Reduce, TTS)
DESCRIPTION: This example showcases an application that allows users to 'Ask AI Paul Graham' by leveraging RAG, Map Reduce, and Text-to-Speech (TTS) patterns. It includes links to the design documentation and the Python 'Flow' code.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-batch/translations/README_CHINESE.md#_snippet_5

LANGUAGE: Python
CODE:
```
https://github.com/The-Pocket/Tutorial-AI-Paul-Graham/blob/main/flow.py
```

----------------------------------------

TITLE: Run with Sample Query (Python)
DESCRIPTION: Executes the main application with a specific query to demonstrate the RAG system's ability to retrieve information and generate answers. The query is passed as a command-line argument.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-rag/README.md#_snippet_3

LANGUAGE: python
CODE:
```
python main.py --"How does the Q-Mesh protocol achieve high transaction speeds?"
```

----------------------------------------

TITLE: Shared Store Data Exchange Example
DESCRIPTION: Demonstrates how to use the Shared Store to pass data between nodes. LoadData writes to shared['data'], and Summarize reads from it and writes to shared['summary'].

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/docs/core_abstraction/communication.md#_snippet_0

LANGUAGE: python
CODE:
```
class LoadData(Node):
    def post(self, shared, prep_res, exec_res):
        # We write data to shared store
        shared["data"] = "Some text content"
        return None

class Summarize(Node):
    def prep(self, shared):
        # We read data from shared store
        return shared["data"]

    def exec(self, prep_res):
        # Call LLM to summarize
        prompt = f"Summarize: {prep_res}"
        summary = call_llm(prompt)
        return summary

    def post(self, shared, prep_res, exec_res):
        # We write summary to shared store
        shared["summary"] = exec_res
        return "default"

load_data = LoadData()
summarize = Summarize()
load_data >> summarize
flow = Flow(start=load_data)

shared = {}
flow.run(shared)
```

----------------------------------------

TITLE: Recommended Languages by Eric Raymond
DESCRIPTION: Eric Raymond's advice on programming languages for aspiring hackers, suggesting a progression from easier languages like Python and Java to more specialized ones like C and Perl, and finally Lisp for its cognitive benefits.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/data/PaulGrahamEssaysLarge/avg.txt#_snippet_0

LANGUAGE: English
CODE:
```
He suggests starting with Python and Java, because they are easy to learn. The serious hacker will also want to learn C, in order to hack Unix, and Perl for system administration and cgi scripts. Finally, the truly serious hacker should consider learning Lisp:

  Lisp is worth learning for the profound enlightenment experience
  you will have when you finally get it; that experience will make
  you a better programmer for the rest of your days, even if you
  never actually use Lisp itself a lot.
```

----------------------------------------

TITLE: Viaweb's Software Components
DESCRIPTION: Viaweb's initial architecture comprised an editor written in Lisp and an ordering system in C. Over time, additional modules like an image generator (C) and a back-office manager (Perl) were added.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/data/PaulGrahamEssaysLarge/avg.txt#_snippet_4

LANGUAGE: Lisp
CODE:
```
Editor component
```

LANGUAGE: C
CODE:
```
Ordering system component
Image generator component
```

LANGUAGE: Perl
CODE:
```
Back-office manager component
```

----------------------------------------

TITLE: Python: Data Processing and Analysis
DESCRIPTION: Provides examples of data processing and analysis using Python libraries such as Pandas and NumPy. This includes data cleaning, transformation, and statistical analysis, essential for preparing data for further use.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow_demo.ipynb#_snippet_17

LANGUAGE: Python
CODE:
```
import pandas as pd

def process_data(filepath):
  df = pd.read_csv(filepath)
  # Example: Fill missing values with the mean
  df.fillna(df.mean(), inplace=True)
  # Example: Calculate a new column
  df['new_column'] = df['column1'] * df['column2']
  return df
```

----------------------------------------

TITLE: ChainOfThoughtNode Plan Step Dictionary Structure
DESCRIPTION: Provides an example structure for a plan step dictionary, including its description, status, optional result, mark for verification, and potential nested sub-steps.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-thinking/design.md#_snippet_3

LANGUAGE: python
CODE:
```
# Example structure for a plan step dictionary
{
    "description": str,                     # Description of the step.
    "status": str,                          # "Pending", "Done", "Verification Needed".
    "result": str | None,                   # Optional: Concise result when status is "Done".
    "mark": str | None,                     # Optional: Reason for "Verification Needed".
    "sub_steps": list[dict] | None          # Optional: Nested list for sub-steps.
}
```

----------------------------------------

TITLE: Integrating PocketFlow with External APIs
DESCRIPTION: Shows how to integrate PocketFlow with external APIs for data retrieval or manipulation. This example uses JavaScript to make an API call within a PocketFlow task.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow_demo.ipynb#_snippet_66

LANGUAGE: JavaScript
CODE:
```
import PocketFlow from '@the-pocket/pocketflow';
import axios from 'axios';

class ApiFetcherTask extends PocketFlow.Task {
  async execute() {
    const apiUrl = 'https://api.example.com/data';
    try {
      const response = await axios.get(apiUrl);
      this.output = response.data;
      return this.output;
    } catch (error) {
      console.error('Error fetching data from API:', error);
      throw error;
    }
  }
}

const pf = new PocketFlow();
pf.addTask(new ApiFetcherTask());
pf.run();
```

----------------------------------------

TITLE: Brave Search API Integration (Python)
DESCRIPTION: Demonstrates how to query the Brave Search API for web results. Requires a subscription token. Makes a GET request to the Brave Search endpoint with custom headers.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/docs/utility_function/websearch.md#_snippet_3

LANGUAGE: Python
CODE:
```
import requests

SUBSCRIPTION_TOKEN = "YOUR_BRAVE_API_TOKEN"
query = "example"

url = "https://api.search.brave.com/res/v1/web/search"
headers = {
    "X-Subscription-Token": SUBSCRIPTION_TOKEN
}
params = {
    "q": query
}

response = requests.get(url, headers=headers, params=params)
results = response.json()
print(results)
```

----------------------------------------

TITLE: Data Processing and Calculations in PocketFlow
DESCRIPTION: This snippet demonstrates core data processing and calculation functionalities within the PocketFlow project. It includes examples of how to handle data, perform mathematical operations, and manage state, likely for scientific or financial applications.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow_demo.ipynb#_snippet_9

LANGUAGE: JavaScript
CODE:
```
function calculateFlow(data) {
  // Placeholder for complex calculation logic
  let result = 0;
  data.forEach(item => {
    result += item.value * item.factor;
  });
  return result;
}

function processData(input) {
  // Placeholder for data transformation
  const processed = input.map(d => ({
    value: d.val,
    factor: d.fct || 1
  }));
  return calculateFlow(processed);
}
```

----------------------------------------

TITLE: Python: Event Handling and Workflow Automation
DESCRIPTION: This section provides Python code examples for handling events and automating workflows within the PocketFlow project. It showcases how to define event listeners, trigger actions, and manage the flow of operations, often utilizing Python's robust libraries for task scheduling and asynchronous programming.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow_demo.ipynb#_snippet_12

LANGUAGE: Python
CODE:
```
import time

class WorkflowEngine:
    def __init__(self):
        self.event_handlers = {}

    def register_event(self, event_name, handler):
        self.event_handlers[event_name] = handler

    def trigger_event(self, event_name, *args, **kwargs):
        if event_name in self.event_handlers:
            handler = self.event_handlers[event_name]
            handler(*args, **kwargs)
        else:
            print(f"No handler registered for event: {event_name}")

def handle_task_completion(task_id):
    print(f"Task {task_id} completed. Triggering next step.")
    # Simulate triggering another event or action
    time.sleep(1)
    engine.trigger_event('next_step_initiated', task_id=task_id)

def handle_next_step(task_id):
    print(f"Initiating next step for task {task_id}.")
    # Further processing...

engine = WorkflowEngine()
engine.register_event('task_completed', handle_task_completion)
engine.register_event('next_step_initiated', handle_next_step)

# Simulate an event trigger
engine.trigger_event('task_completed', task_id=123)

```

----------------------------------------

TITLE: Milvus: Connect, Create Collection, Index, and Search
DESCRIPTION: Shows how to connect to Milvus, define a collection schema, create an index, load the collection, and perform a search. Requires PyMilvus and NumPy.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/docs/utility_function/vector.md#_snippet_4

LANGUAGE: Python
CODE:
```
from pymilvus import connections, FieldSchema, CollectionSchema, DataType, Collection
import numpy as np

connections.connect(alias="default", host="localhost", port="19530")

fields = [
    FieldSchema(name="id", dtype=DataType.INT64, is_primary=True),
    FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=128)
]
schema = CollectionSchema(fields)
collection = Collection("MyCollection", schema)

emb = np.random.rand(10, 128).astype('float32')
ids = list(range(10))
collection.insert([ids, emb])

index_params = {
    "index_type": "IVF_FLAT",
    "params": {"nlist": 128},
    "metric_type": "L2"
}
collection.create_index("embedding", index_params)
collection.load()

query_emb = np.random.rand(1, 128).astype('float32')
results = collection.search(query_emb, "embedding", param={"nprobe": 10}, limit=3)
print(results)
```

----------------------------------------

TITLE: Set Anthropic API Key
DESCRIPTION: Sets the Anthropic API key as an environment variable. This key is required for the application to authenticate with the Anthropic API for joke generation.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-cli-hitl/README.md#_snippet_1

LANGUAGE: bash
CODE:
```
export ANTHROPIC_API_KEY="your-anthropic-api-key-here"
```

----------------------------------------

TITLE: DuckDuckGo Instant Answer API Integration (Python)
DESCRIPTION: Provides an example of using the DuckDuckGo Instant Answer API to retrieve search results in JSON format. This API is free and does not require an API key for basic usage.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/docs/utility_function/websearch.md#_snippet_2

LANGUAGE: Python
CODE:
```
import requests

query = "example"
url = "https://api.duckduckgo.com/"
params = {
    "q": query,
    "format": "json"
}

response = requests.get(url, params=params)
results = response.json()
print(results)
```

----------------------------------------

TITLE: Example Game Output
DESCRIPTION: Demonstrates a typical output from the Taboo game, showing the target word, forbidden words, hints provided by the Hinter, and guesses made by the Guesser, culminating in a correct guess.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-multi-agent/README.md#_snippet_7

LANGUAGE: text
CODE:
```
=========== Taboo Game Starting! ===========
Target word: nostalgic
Forbidden words: ['memory', 'past', 'remember', 'feeling', 'longing']
============================================

Hinter: Here's your hint - Sentiment for earlier times.
Guesser: I guess it's - Nostalgia

Hinter: Here's your hint - Sentiment for earlier times.
Guesser: I guess it's - Reminiscence

Hinter: Here's your hint - Yearning for days gone by.
Guesser: I guess it's - Sentimentality

Hinter: Here's your hint - Reliving cherished moments or experiences.
Guesser: I guess it's - Memories

Hinter: Here's your hint - Recollection of cherished experiences.
Guesser: I guess it's - Reflection

Hinter: Here's your hint - Yearning for earlier times.
Guesser: I guess it's - Longing

Hinter: Here's your hint - Sentiment for earlier times.
Guesser: I guess it's - Nostalgic
Game Over - Correct guess!
```

----------------------------------------

TITLE: JSON String Escaping Example
DESCRIPTION: Demonstrates how double quotes and newlines must be escaped within a JSON string. This highlights the complexities of handling special characters in JSON.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/docs/design_pattern/structure.md#_snippet_4

LANGUAGE: json
CODE:
```
{
  "dialogue": "Alice said: \"Hello Bob.\\nHow are you?\\nI am good.\""
}
```

----------------------------------------

TITLE: Calculate Probabilities for Markov Chain States
DESCRIPTION: Provides the calculated probabilities (P₀, P₁, P₂) for reaching the target sequence '3,4,5' in an odd number of rolls, starting from different states of progress.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-thinking/README.md#_snippet_17

LANGUAGE: mathematics
CODE:
```
P₀ = 216/431
P₁ = 210/431
P₂ = 252/431
```

----------------------------------------

TITLE: Pocket Flow Multi-Agent Taboo Game
DESCRIPTION: This example showcases asynchronous communication between two agents in a Taboo word game, built using Pocket Flow's multi-agent capabilities.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/README.md#_snippet_8

LANGUAGE: Python
CODE:
```
from pocketflow.multi_agent import MultiAgent

agent1 = MultiAgent("Agent1")
agent2 = MultiAgent("Agent2")

agent1.start_game(agent2)
agent2.play_turn(agent1)
```

----------------------------------------

TITLE: Python: Nested Flow Example
DESCRIPTION: Demonstrates basic flow nesting where a sub-flow, composed of node_a and node_b, is connected to another node, node_c. The parent flow orchestrates the execution of the sub-flow followed by node_c.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/docs/core_abstraction/flow.md#_snippet_2

LANGUAGE: python
CODE:
```
# Create a sub-flow
node_a >> node_b
subflow = Flow(start=node_a)

# Connect it to another node
subflow >> node_c

# Create the parent flow
parent_flow = Flow(start=subflow)
```

----------------------------------------

TITLE: A2A Server Setup (Starlette/Uvicorn)
DESCRIPTION: Sets up an ASGI application using Starlette and Uvicorn to listen for HTTP POST requests. It parses JSON-RPC messages and routes them based on the method field, serving as the entry point for A2A communication.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-a2a/README.md#_snippet_8

LANGUAGE: Python
CODE:
```
from starlette.applications import Starlette
from starlette.routing import Route
from common.server.server import A2AServer
from task_manager import PocketFlowTaskManager
from agent_card import AgentCard

# Define the AgentCard (metadata for the agent)
agent_card = AgentCard(
    name="PocketFlow",
    description="An agent that processes information using a flow.",
    url="http://localhost:8000",
    capabilities=["task_execution"],
    skills=["processing"]
)

# Initialize the custom Task Manager
task_manager = PocketFlowTaskManager()

# Initialize the A2A Server
app = A2AServer(agent_card=agent_card, task_manager=task_manager)

# Add routes for the agent card and task execution
routes = [
    Route("/.well-known/agent.json", endpoint=app.agent_card_endpoint),
    Route("/tasks", endpoint=app.task_endpoint, methods=["POST"])
]

starlette_app = Starlette(routes=routes)

# To run this server:
# uvicorn a2a_server:starlette_app --reload --port 8000
```

----------------------------------------

TITLE: Call Google Generative AI LLM
DESCRIPTION: Provides an example for calling Google's Generative AI models (formerly PaLM API) using the 'google' library. It requires a Gemini API key and specifies the model for content generation.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/docs/utility_function/llm.md#_snippet_2

LANGUAGE: python
CODE:
```
from google import genai
client = genai.Client(api_key='GEMINI_API_KEY')
response = client.models.generate_content(
model='gemini-2.5-pro',
contents=prompt
)
return response.text
```

----------------------------------------

TITLE: Python: Basic Flow Sequence
DESCRIPTION: Defines a simple sequential flow where node_a transitions to node_b on a default action. The flow execution starts at node_a and proceeds to node_b, ending as no further transition is defined for node_b.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/docs/core_abstraction/flow.md#_snippet_0

LANGUAGE: python
CODE:
```
node_a >> node_b
flow = Flow(start=node_a)
flow.run(shared)
```

----------------------------------------

TITLE: Project File Structure Diagram
DESCRIPTION: Illustrates the directory and file structure of the Pocketflow project using Mermaid syntax. This provides a visual overview of how the project components are organized.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/docs/guide.md#_snippet_8

LANGUAGE: Mermaid
CODE:
```
flowchart TD
    firstNode[First Node] --> secondNode[Second Node]
    secondNode --> thirdNode[Third Node]
```

----------------------------------------

TITLE: Call LLM and Get Embedding
DESCRIPTION: This snippet demonstrates how to interact with a language model (LLM) and generate embeddings using provided functions. It shows calling an LLM with a query and then generating an embedding for the same query.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow_demo.ipynb#_snippet_3

LANGUAGE: python
CODE:
```
response = call_llm("What's the meaning of life?")
print(response)
embedding = get_embedding("What's the meaning of life?")
print(embedding)
```

----------------------------------------

TITLE: FastAPI Background Jobs with SSE Progress
DESCRIPTION: This example showcases a FastAPI application designed to handle background jobs efficiently. It implements Server-Sent Events (SSE) to provide real-time progress updates to the client, allowing users to monitor the status of long-running tasks.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/README.md#_snippet_26

LANGUAGE: Python
CODE:
```
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import StreamingResponse, HTMLResponse
import asyncio
import time

app = FastAPI()

async def background_task(task_id: int):
    """Simulates a background task with progress updates."""
    for i in range(1, 11):
        await asyncio.sleep(1)  # Simulate work
        progress = i * 10
        # In a real scenario, you'd update a shared state or database
        # For this example, we'll just print
        print(f"Task {task_id}: Progress {progress}%")
    print(f"Task {task_id}: Completed")

def generate_progress_events(task_id: int):
    """Generator for Server-Sent Events."""
    async def event_generator():
        for i in range(1, 11):
            await asyncio.sleep(1)
            progress = i * 10
            yield f"data: {{'task_id': {task_id}, 'progress': {progress}}}\\n\n"
        yield f"data: {{'task_id': {task_id}, 'status': 'completed'}}\\n\n"
    return event_generator

@app.post("/start_task")
async def start_task(request: Request):
    # In a real app, you'd generate a unique task ID and store it
    task_id = 1
    asyncio.create_task(background_task(task_id))
    return {"message": "Background task started", "task_id": task_id}

@app.get("/progress/{task_id}")
async def get_progress(task_id: int):
    # In a real app, you'd fetch the task status from storage
    # For this example, we'll just stream simulated events
    if task_id != 1: # Simple check for our single task example
        raise HTTPException(status_code=404, detail="Task not found")
    return StreamingResponse(generate_progress_events(task_id), media_type="text/event-stream")

@app.get("/")
async def get_index():
    return HTMLResponse("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Background Task Progress</title>
    </head>
    <body>
        <h1>Background Task Progress</h1>
        <button onclick="startTask()">Start Task</button>
        <div id="progress"></div>

        <script>
            function startTask() {
                fetch('/start_task', {
                    method: 'POST'
                }).then(response => response.json())
                  .then(data => {
                      console.log('Task started:', data);
                      subscribeToProgress(data.task_id);
                  });
            }

            function subscribeToProgress(taskId) {
                const eventSource = new EventSource(`/progress/${taskId}`);
                const progressDiv = document.getElementById('progress');

                eventSource.onmessage = function(event) {
                    const data = JSON.parse(event.data);
                    if (data.status === 'completed') {
                        progressDiv.innerHTML += `<p>Task ${data.task_id} completed!</p>`;
                        eventSource.close();
                    } else {
                        progressDiv.innerHTML += `<p>Task ${data.task_id}: ${data.progress}%</p>`;
                    }
                };

                eventSource.onerror = function() {
                    console.error('EventSource failed.');
                    eventSource.close();
                };
            }
        </script>
    </body>
    </html>
    """)

```

----------------------------------------

TITLE: Summarize Text to YAML with Python
DESCRIPTION: Provides a Python example of a Node class that calls an LLM to summarize text into a YAML format with exactly three bullet points. It includes response parsing and schema validation using assert statements.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/docs/design_pattern/structure.md#_snippet_3

LANGUAGE: python
CODE:
```
class SummarizeNode(Node):
    def exec(self, prep_res):
        # Suppose `prep_res` is the text to summarize.
        prompt = f"""
Please summarize the following text as YAML, with exactly 3 bullet points

{prep_res}

Now, output:
```yaml
summary:
  - bullet 1
  - bullet 2
  - bullet 3
```"""
        response = call_llm(prompt)
        yaml_str = response.split("```yaml")[1].split("```")[0].strip()

        import yaml
        structured_result = yaml.safe_load(yaml_str)

        assert "summary" in structured_result
        assert isinstance(structured_result["summary"], list)

        return structured_result
```

----------------------------------------

TITLE: Anthropic Model Wrapper
DESCRIPTION: A utility script providing a simple wrapper function to interact with the Anthropic API, likely used by the main script to get model responses.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-majority-vote/README.md#_snippet_6

LANGUAGE: python
CODE:
```
import anthropic
import os

def call_anthropic_model(prompt, model_name):
    client = anthropic.Anthropic(
        api_key=os.environ.get("ANTHROPIC_API_KEY"),
    )
    message = client.messages.create(
        model=model_name,
        max_tokens=1000,
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )
    # Assuming the relevant answer is in the first content block
    return message.content[0].text

```

----------------------------------------

TITLE: Pocket Flow LLM Streaming Tutorial
DESCRIPTION: This tutorial presents a real-time LLM streaming demo with user interrupt capability using Pocket Flow. It focuses on providing immediate feedback and allowing user interaction during generation.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/README.md#_snippet_9

LANGUAGE: Python
CODE:
```
# Example for pocketflow-llm-streaming
# from pocketflow.streaming import LLMStreamer
# 
# streamer = LLMStreamer()
# streamer.stream("Generate a story...")

```

----------------------------------------

TITLE: Solve System of Equations for Probabilities
DESCRIPTION: Presents the solution to the system of linear equations derived from the first-step analysis with parity. The probabilities P₀, P₁, and P₂ represent the likelihood of an odd number of rolls starting from respective states.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-thinking/README.md#_snippet_19

LANGUAGE: mathematics
CODE:
```
P₀ = 216/431
P₁ = 210/431
P₂ = 252/431
```

----------------------------------------

TITLE: Initialize Langfuse Tracer in Python
DESCRIPTION: Demonstrates how to directly instantiate the LangfuseTracer with a configuration object for advanced use cases in Python.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-tracing/README.md#_snippet_6

LANGUAGE: python
CODE:
```
tracer = LangfuseTracer(config)
```

----------------------------------------

TITLE: Article Writing Workflow with Nodes
DESCRIPTION: This Python code defines a workflow for article writing using Pocketflow's Node abstraction. It includes nodes for generating an outline, writing a section based on the outline, and reviewing/refining the draft. The nodes are connected sequentially to form a flow, and the example demonstrates how to run this flow with initial shared data.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/docs/design_pattern/workflow.md#_snippet_0

LANGUAGE: Python
CODE:
```
class GenerateOutline(Node):
    def prep(self, shared): return shared["topic"]
    def exec(self, topic): return call_llm(f"Create a detailed outline for an article about {topic}")
    def post(self, shared, prep_res, exec_res): shared["outline"] = exec_res

class WriteSection(Node):
    def prep(self, shared): return shared["outline"]
    def exec(self, outline): return call_llm(f"Write content based on this outline: {outline}")
    def post(self, shared, prep_res, exec_res): shared["draft"] = exec_res

class ReviewAndRefine(Node):
    def prep(self, shared): return shared["draft"]
    def exec(self, draft): return call_llm(f"Review and improve this draft: {draft}")
    def post(self, shared, prep_res, exec_res): shared["final_article"] = exec_res

# Connect nodes
outline = GenerateOutline()
write = WriteSection()
review = ReviewAndRefine()

outline >> write >> review

# Create and run flow
writing_flow = Flow(start=outline)
shared = {"topic": "AI Safety"}
writing_flow.run(shared)
```

----------------------------------------

TITLE: Pocket Flow Text-to-SQL Tutorial
DESCRIPTION: This tutorial shows how to convert natural language queries into SQL queries with an auto-debug loop using Pocket Flow. It simplifies database interaction through natural language.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/README.md#_snippet_20

LANGUAGE: Python
CODE:
```
# Example for pocketflow-text2sql
# from pocketflow.text2sql import TextToSQLConverter
# 
# converter = TextToSQLConverter()
# natural_language = "Show me all users from California"
# sql_query = converter.convert(natural_language)
# print(sql_query)

```

----------------------------------------

TITLE: FastAPI Application with SSE
DESCRIPTION: The main FastAPI application file. It handles web requests, manages background jobs using FastAPI's BackgroundTasks, and streams real-time progress updates to clients via Server-Sent Events (SSE). It includes endpoints for starting jobs and monitoring progress.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-fastapi-background/README.md#_snippet_4

LANGUAGE: python
CODE:
```
# main.py: FastAPI application with background jobs and SSE endpoints
```

----------------------------------------

TITLE: Shell: Execute Pocketflow Task
DESCRIPTION: Executes a specific task within the Pocketflow environment using a shell command. This is useful for scripting and automating Pocketflow operations. Ensure the Pocketflow CLI is installed and configured.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow_demo.ipynb#_snippet_36

LANGUAGE: Shell
CODE:
```
pocketflow run --task process_records --input data.csv --output results.json
```

----------------------------------------

TITLE: Derive State Equations for Even Rolls (Q₀)
DESCRIPTION: Derives the probability equation for rolling an even number of times starting from State 0. This involves considering the probabilities of transitions to other states and the parity of the rolls.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-thinking/README.md#_snippet_12

LANGUAGE: mathematics
CODE:
```
Q₀ = (1/6) * P₁ + (5/6) * P₀
# Verification: Q₀ = 210/431/6 + 5*(216/431)/6 = 1290/2586 = 215/431
```

----------------------------------------

TITLE: Bing Web Search API Integration (Python)
DESCRIPTION: Shows how to integrate with the Bing Web Search API to find web results. Requires a subscription key. Sends a GET request to the Bing search endpoint with specified headers and query parameters.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/docs/utility_function/websearch.md#_snippet_1

LANGUAGE: Python
CODE:
```
import requests

SUBSCRIPTION_KEY = "YOUR_BING_API_KEY"
query = "example"

url = "https://api.bing.microsoft.com/v7.0/search"
headers = {"Ocp-Apim-Subscription-Key": SUBSCRIPTION_KEY}
params = {"q": query}

response = requests.get(url, headers=headers, params=params)
results = response.json()
print(results)
```

----------------------------------------

TITLE: Configure Pocketflow Settings
DESCRIPTION: Demonstrates how to configure settings or parameters for the Pocketflow framework. This is crucial for customizing behavior and optimizing performance.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow_demo.ipynb#_snippet_54

LANGUAGE: JavaScript
CODE:
```
import Pocketflow from 'pocketflow';

const pf = new Pocketflow({
  timeout: 5000,
  retries: 3
});
console.log('Pocketflow configured with custom settings.');
```

----------------------------------------

TITLE: FastAPI WebSocket Chat with Streaming LLM Responses
DESCRIPTION: This example sets up a FastAPI application that utilizes WebSockets to create a real-time chat interface. It demonstrates how to stream Large Language Model (LLM) responses back to the client over the WebSocket connection, enabling a dynamic and interactive chat experience.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/README.md#_snippet_25

LANGUAGE: Python
CODE:
```
from fastapi import FastAPI, WebSocket
from fastapi.responses import HTMLResponse

app = FastAPI()

html = """
<!DOCTYPE html>
<html>
<head>
    <title>Chat</title>
</head>
<body>
    <div id="chatbox" style="height: 300px; overflow-y: scroll; border: 1px solid black;"></div>
    <input type="text" id="message" placeholder="Type your message...">
    <button onclick="sendMessage()">Send</button>

    <script>
        var ws = new WebSocket("ws://localhost:8000/ws");
        var chatbox = document.getElementById("chatbox");
        var messageInput = document.getElementById("message");

        ws.onmessage = function(event) {
            var message = event.data;
            var p = document.createElement("p");
            p.textContent = message;
            chatbox.appendChild(p);
            chatbox.scrollTop = chatbox.scrollHeight;
        };

        function sendMessage() {
            var message = messageInput.value;
            ws.send(message);
            messageInput.value = "";
        }
    </script>
</body>
</html>
"""


@app.get("/")
async def get():
    return HTMLResponse(html)


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    while True:
        data = await websocket.receive_text()
        # In a real application, you would process 'data' with an LLM
        # and stream the response back.
        # For this example, we'll just echo the message and add a prefix.
        response_message = f"Echo: {data}"
        await websocket.send_text(response_message)

```

----------------------------------------

TITLE: Derive State Equations for Even Rolls (Q₁)
DESCRIPTION: Derives the probability equation for rolling an even number of times starting from State 1. This accounts for transitions to states 0, 1, and 2, and the parity of the rolls.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-thinking/README.md#_snippet_13

LANGUAGE: mathematics
CODE:
```
Q₁ = (1/6) * P₂ + (1/6) * P₁ + (4/6) * P₀
# Verification: Q₁ = 216/431/6 + 210/431/6 + 4*(216/431)/6 = 1290/2586 = 215/431
```

----------------------------------------

TITLE: Configuration Management
DESCRIPTION: Handles the loading and management of project configurations. This includes reading settings from files or environment variables to control the behavior of the system.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow_demo.ipynb#_snippet_26

LANGUAGE: JavaScript
CODE:
```
const config = require('./config.json');

function getConfig(key) {
  return config[key];
}

console.log('Loaded config:', config);
```

----------------------------------------

TITLE: Interactive Voice Chat Application
DESCRIPTION: This example describes an interactive voice chat application that integrates several key technologies: Voice Activity Detection (VAD) to identify speech, Speech-to-Text (STT) to transcribe audio, a Large Language Model (LLM) for understanding and generating responses, and Text-to-Speech (TTS) to vocalize the responses.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/README.md#_snippet_27

LANGUAGE: Python
CODE:
```
# This is a conceptual example. Actual implementation requires specific libraries for VAD, STT, LLM, and TTS.

# Example placeholder for VAD (Voice Activity Detection)
def detect_voice_activity(audio_chunk):
    # Returns True if voice is detected, False otherwise
    pass

# Example placeholder for STT (Speech-to-Text)
def transcribe_speech(audio_chunk):
    # Returns the transcribed text
    pass

# Example placeholder for LLM interaction
def get_llm_response(text):
    # Returns the LLM's generated text response
    pass

# Example placeholder for TTS (Text-to-Speech)
def synthesize_speech(text):
    # Returns audio data of the spoken text
    pass

def voice_chat_session():
    print("Starting voice chat session...")
    while True:
        # 1. Capture audio chunk from microphone
        audio_chunk = capture_audio()

        # 2. Detect voice activity
        if detect_voice_activity(audio_chunk):
            # 3. Transcribe speech to text
            user_text = transcribe_speech(audio_chunk)
            print(f"User: {user_text}")

            # 4. Get response from LLM
            llm_response_text = get_llm_response(user_text)
            print(f"LLM: {llm_response_text}")

            # 5. Synthesize speech from LLM response
            llm_audio_response = synthesize_speech(llm_response_text)

            # 6. Play the synthesized speech
            play_audio(llm_audio_response)
        else:
            # No voice detected, continue listening
            pass

# Placeholder functions (replace with actual library calls)
def capture_audio():
    # Simulate capturing audio
    return b'\x00' * 1024

def play_audio(audio_data):
    # Simulate playing audio
    print("Playing LLM audio response...")

# To run the session (requires actual implementations of the placeholder functions)
# if __name__ == "__main__":
#     voice_chat_session()

```

----------------------------------------

TITLE: AnswerQuestion Node Implementation in Python
DESCRIPTION: This Python code defines the `AnswerQuestion` node for the PocketFlow system. It includes methods for preparing inputs (`prep`), executing the core logic by calling an LLM with a formatted prompt (`exec`), and post-processing the results (`post`) by printing the question, answer, and source file.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow_demo.ipynb#_snippet_79

LANGUAGE: Python
CODE:
```
class AnswerQuestion(Node):
    def prep(self, shared):
        return (
            shared["current_question"],
            shared["context"]
        )
        
    def exec(self, inputs):
        question, context = inputs
        prompt = f"""
Context: {context}

Question: {question}

Answer the question based on the context above. If the context doesn't contain relevant information, say so.
Answer:"""
        return call_llm(prompt)
    
    def post(self, shared, prep_res, exec_res):
        print(f"\nQ: {shared['current_question']}")
        print(f"A: {exec_res}")
        print(f"\nSource: {shared['relevant_file']}")
        return "continue"
```

----------------------------------------

TITLE: Pocket Flow Agent Tutorial
DESCRIPTION: This tutorial showcases a research agent built with Pocket Flow. The agent can perform web searches and answer questions, demonstrating the framework's capability for information retrieval and synthesis.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/README.md#_snippet_6

LANGUAGE: Python
CODE:
```
# Example for pocketflow-agent
# from pocketflow.agent import ResearchAgent
# 
# agent = ResearchAgent()
# answer = agent.ask("What is Pocket Flow?")
# print(answer)

```

----------------------------------------

TITLE: Pocket Flow Map-Reduce Tutorial
DESCRIPTION: This tutorial demonstrates batch resume qualification using the map-reduce pattern within Pocket Flow. It efficiently processes multiple resumes to identify suitable candidates.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/README.md#_snippet_12

LANGUAGE: Python
CODE:
```
# Example for pocketflow-map-reduce
# from pocketflow.mapreduce import ResumeQualifier
# 
# qualifier = ResumeQualifier()
# resumes = ["Resume 1 data", "Resume 2 data"]
# qualified_resumes = qualifier.qualify_batch(resumes)
# print(qualified_resumes)

```

----------------------------------------

TITLE: Text-to-SQL Workflow Diagram
DESCRIPTION: A Mermaid diagram illustrating the flow of the Text-to-SQL workflow, including the LLM-powered debugging loop for failed SQL queries.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-text2sql/README.md#_snippet_5

LANGUAGE: mermaid
CODE:
```
graph LR
    A[Get Schema] --> B[Generate SQL]
    B --> C[Execute SQL]
    C -- Success --> E[End]
    C -- SQLite Error --> D{Debug SQL Attempt}
    D -- Corrected SQL --> C
    C -- Max Retries Reached --> F[End with Error]

    style E fill:#dff,stroke:#333,stroke-width:2px
    style F fill:#fdd,stroke:#333,stroke-width:2px
```

----------------------------------------

TITLE: Data Processing and Transformation
DESCRIPTION: This snippet demonstrates how to process and transform data within the PocketFlow project. It includes examples of data cleaning, filtering, and reformatting to ensure data integrity and usability for downstream applications. Dependencies may include data manipulation libraries.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow_demo.ipynb#_snippet_68

LANGUAGE: JavaScript
CODE:
```
function processData(data) {
  // Clean and validate data
  const cleanedData = data.filter(item => item.value !== null && item.value !== undefined);
  
  // Transform data
  const transformedData = cleanedData.map(item => ({
    id: item.id,
    processedValue: item.value * 2,
    timestamp: new Date().toISOString()
  }));
  
  return transformedData;
}
```

----------------------------------------

TITLE: Google Custom Search API Integration (Python)
DESCRIPTION: Demonstrates how to use the Google Custom Search JSON API to perform web searches. Requires an API key and CX ID. Makes a GET request to the Google Custom Search endpoint.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/docs/utility_function/websearch.md#_snippet_0

LANGUAGE: Python
CODE:
```
import requests

API_KEY = "YOUR_API_KEY"
CX_ID = "YOUR_CX_ID"
query = "example"

url = "https://www.googleapis.com/customsearch/v1"
params = {
    "key": API_KEY,
    "cx": CX_ID,
    "q": query
}

response = requests.get(url, params=params)
results = response.json()
print(results)
```

----------------------------------------

TITLE: Pocket Flow Supervisor Tutorial
DESCRIPTION: This tutorial addresses the unreliability of research agents by building a supervision process with Pocket Flow. It demonstrates how to monitor and manage agent performance.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/README.md#_snippet_15

LANGUAGE: Python
CODE:
```
# Example for pocketflow-supervisor
# from pocketflow.supervisor import AgentSupervisor
# 
# supervisor = AgentSupervisor()
# supervisor.monitor_agent("ResearchAgent")

```

----------------------------------------

TITLE: JavaScript Data Processing and Calculation
DESCRIPTION: This snippet demonstrates data processing and calculation logic likely used within the PocketFlow project. It includes examples of data manipulation, potentially for financial or scientific analysis, and utilizes common JavaScript patterns for handling arrays and mathematical operations.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow_demo.ipynb#_snippet_8

LANGUAGE: JavaScript
CODE:
```
function calculateMetrics(data) {
  // Placeholder for data processing and metric calculation
  // Example: Calculate average, sum, etc.
  const sum = data.reduce((acc, val) => acc + val, 0);
  const average = sum / data.length;
  return { sum, average };
}

// Example usage:
const sampleData = [10, 20, 30, 40, 50];
const metrics = calculateMetrics(sampleData);
console.log(metrics); // { sum: 150, average: 30 }
```

----------------------------------------

TITLE: Document Summarization with MapReduce in Python
DESCRIPTION: This Python code demonstrates the MapReduce pattern for document summarization. It uses BatchNode for the map phase to summarize individual files and Node for the reduce phase to combine the summaries. The example shows how to process multiple files and aggregate their summaries.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/docs/design_pattern/mapreduce.md#_snippet_0

LANGUAGE: Python
CODE:
```
class SummarizeAllFiles(BatchNode):
    def prep(self, shared):
        files_dict = shared["files"]  # e.g. 10 files
        return list(files_dict.items())  # [("file1.txt", "aaa..."), ("file2.txt", "bbb..."), ...]

    def exec(self, one_file):
        filename, file_content = one_file
        summary_text = call_llm(f"Summarize the following file:\n{file_content}")
        return (filename, summary_text)

    def post(self, shared, prep_res, exec_res_list):
        shared["file_summaries"] = dict(exec_res_list)

class CombineSummaries(Node):
    def prep(self, shared):
        return shared["file_summaries"]

    def exec(self, file_summaries):
        # format as: "File1: summary\nFile2: summary...\n"
        text_list = []
        for fname, summ in file_summaries.items():
            text_list.append(f"{fname} summary:\n{summ}\n")
        big_text = "\n---".join(text_list)

        return call_llm(f"Combine these file summaries into one final summary:\n{big_text}")

    def post(self, shared, prep_res, final_summary):
        shared["all_files_summary"] = final_summary

batch_node = SummarizeAllFiles()
combine_node = CombineSummaries()
batch_node >> combine_node

flow = Flow(start=batch_node)

shared = {
    "files": {
        "file1.txt": "Alice was beginning to get very tired of sitting by her sister...",
        "file2.txt": "Some other interesting text ...",
        # ...
    }
}
flow.run(shared)
print("Individual Summaries:", shared["file_summaries"])
print("\nFinal Summary:\n ", shared["all_files_summary"])
```

----------------------------------------

TITLE: Ask AI Paul Graham Flow Code
DESCRIPTION: This Python code allows users to 'Ask AI Paul Graham' questions. It's a medium-difficulty project employing RAG, Map Reduce, and TTS design patterns. It's designed to help users who might not get into Y Combinator.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/README.md#_snippet_32

LANGUAGE: Python
CODE:
```
https://github.com/The-Pocket/Tutorial-AI-Paul-Graham/blob/main/flow.py
```

----------------------------------------

TITLE: Generate Embeddings with Azure OpenAI API
DESCRIPTION: This code example shows how to generate text embeddings using the Azure OpenAI API. It requires setting the API type, base URL, version, and API key. The function returns the embedding vector from the response.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/docs/utility_function/embedding.md#_snippet_1

LANGUAGE: Python
CODE:
```
import openai

openai.api_type = "azure"
openai.api_base = "https://YOUR_RESOURCE_NAME.openai.azure.com"
openai.api_version = "2023-03-15-preview"
openai.api_key = "YOUR_AZURE_API_KEY"

resp = openai.Embedding.create(engine="ada-embedding", input="Hello world")
vec = resp["data"][0]["embedding"]
print(vec)
```

----------------------------------------

TITLE: Generate Embeddings with AWS Bedrock
DESCRIPTION: This example shows how to generate text embeddings using AWS Bedrock's runtime client. It involves invoking a specific model (e.g., amazon.titan-embed-text-v2:0) with the input text and parsing the JSON response to extract the embedding vector.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/docs/utility_function/embedding.md#_snippet_3

LANGUAGE: Python
CODE:
```
import boto3, json

client = boto3.client("bedrock-runtime", region_name="us-east-1")
body = {"inputText": "Hello world"}
resp = client.invoke_model(modelId="amazon.titan-embed-text-v2:0", contentType="application/json", body=json.dumps(body))
resp_body = json.loads(resp["body"].read())
vec = resp_body["embedding"]
print(vec)
```

----------------------------------------

TITLE: Pocket Flow RAG Tutorial
DESCRIPTION: This tutorial provides a simple implementation of a Retrieval-Augmented Generation (RAG) process using Pocket Flow. It combines information retrieval with text generation for more informed responses.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/README.md#_snippet_7

LANGUAGE: Python
CODE:
```
# Example for pocketflow-rag
# from pocketflow.rag import RAG
# 
# rag = RAG()
# query = "Explain RAG"
# response = rag.generate(query)
# print(response)

```

----------------------------------------

TITLE: Generate Embeddings with Hugging Face Inference API
DESCRIPTION: This example shows how to generate text embeddings using the Hugging Face Inference API. It uses the `requests` library to send a POST request to a specified model endpoint with an authorization token. The embedding vector is extracted from the JSON response.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/docs/utility_function/embedding.md#_snippet_5

LANGUAGE: Python
CODE:
```
import requests

API_URL = "https://api-inference.huggingface.co/models/sentence-transformers/all-MiniLM-L6-v2"
HEADERS = {"Authorization": "Bearer YOUR_HF_TOKEN"}

res = requests.post(API_URL, headers=HEADERS, json={"inputs": "Hello world"})
vec = res.json()[0]
print(vec)
```

----------------------------------------

TITLE: Revise Node for Python
DESCRIPTION: This node analyzes test failures and generates structured revisions for test cases and/or function code. It reads test results, test cases, function code, and iteration count to guide the LLM in producing corrections.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-code-generator/doc/design.md#_snippet_5

LANGUAGE: Python
CODE:
```
import yaml

class Revise:
    def __init__(self):
        pass

    def prep(self, shared_store):
        # Read test results, test cases, function code, iteration count from shared store
        test_results = shared_store.get('test_results')
        test_cases = shared_store.get('test_cases')
        function_code = shared_store.get('function_code')
        iteration_count = shared_store.get('iteration_count', 0)
        return {
            'test_results': test_results,
            'test_cases': test_cases,
            'function_code': function_code,
            'iteration_count': iteration_count
        }

    def exec(self, inputs, shared_store):
        # Call LLM to analyze failures and output structured YAML with revised test cases and/or function code
        # This is a placeholder for the actual LLM call
        revised_output = self.analyze_and_revise_with_llm(
            inputs['test_results'],
            inputs['test_cases'],
            inputs['function_code'],
            inputs['iteration_count']
        )
        return {'revised_output': revised_output}

    def post(self, outputs, shared_store):
        # Update shared["test_cases"] and/or shared["function_code"] based on structured output
        revised_data = yaml.safe_load(outputs['revised_output'])

        if 'test_cases' in revised_data:
            shared_store.set('test_cases', revised_data['test_cases'])
        if 'function_code' in revised_data:
            shared_store.set('function_code', revised_data['function_code'])

        # Increment iteration count if revisions were made
        current_iteration = shared_store.get('iteration_count', 0)
        shared_store.set('iteration_count', current_iteration + 1)

    def analyze_and_revise_with_llm(self, test_results, test_cases, function_code, iteration_count):
        # Placeholder for LLM call to analyze failures and generate revisions
        print(f"Analyzing failures for iteration {iteration_count + 1}")
        # Example structured YAML output
        return """yaml
test_cases:
  - input: 'new_edge_case_input'
    expected_output: 'new_edge_case_output'
function_code: |-
  def run_code(input_data):
      # Revised implementation
      return 'revised_result'\n"""

```

----------------------------------------

TITLE: Record Audio with VAD
DESCRIPTION: Records audio from the microphone using silence-based Voice Activity Detection (VAD). It buffers audio and starts recording when sound is detected, stopping after a period of silence or a maximum duration. This function is essential for capturing user voice input.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-voice-chat/docs/design.md#_snippet_1

LANGUAGE: Python
CODE:
```
def record_audio(sample_rate=DEFAULT_SAMPLE_RATE, channels=DEFAULT_CHANNELS, chunk_size_ms=DEFAULT_CHUNK_SIZE_MS, silence_threshold_rms=DEFAULT_SILENCE_THRESHOLD_RMS, min_silence_duration_ms=DEFAULT_MIN_SILENCE_DURATION_MS, max_recording_duration_s=DEFAULT_MAX_RECORDING_DURATION_S, pre_roll_chunks_count=DEFAULT_PRE_ROLL_CHUNKS):
    """Records audio from the microphone using silence-based Voice Activity Detection (VAD).

    Args:
        sample_rate (int): The desired sample rate in Hz.
        channels (int): The number of audio channels.
        chunk_size_ms (int): The size of audio chunks in milliseconds.
        silence_threshold_rms (float): The RMS threshold for silence detection.
        min_silence_duration_ms (int): The minimum duration of silence to stop recording.
        max_recording_duration_s (int): The maximum duration of the recording in seconds.
        pre_roll_chunks_count (int): The number of audio chunks to buffer before speech detection.

    Returns:
        tuple: A tuple containing (audio_data, sample_rate).
               audio_data is a NumPy array of float32 audio samples.
               Returns (None, sample_rate) if no speech is detected or recording fails.
    """
    # Implementation details for recording audio with VAD
    pass
```

----------------------------------------

TITLE: Pocket Flow Structured Output Tutorial
DESCRIPTION: This tutorial focuses on extracting structured data, such as information from resumes, by leveraging Pocket Flow's prompting capabilities. It highlights the framework's ability to parse and organize unstructured text.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/README.md#_snippet_4

LANGUAGE: Python
CODE:
```
# Example for pocketflow-structured-output
# from pocketflow.parser import StructuredParser
# 
# parser = StructuredParser()
# resume_text = "..."
# structured_data = parser.parse(resume_text)
# print(structured_data)

```

----------------------------------------

TITLE: Pocket Flow Code Generator Tutorial
DESCRIPTION: This tutorial demonstrates generating test cases, implementing solutions, and iteratively improving code using Pocket Flow. It supports a development workflow focused on code quality and evolution.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/README.md#_snippet_21

LANGUAGE: Python
CODE:
```
# Example for pocketflow-code-generator
# from pocketflow.codegen import CodeGenerator
# 
# codegen = CodeGenerator()
# test_cases = codegen.generate_tests("MyFunction")
# print(test_cases)

```

----------------------------------------

TITLE: Pocket Flow MCP Agent Tutorial
DESCRIPTION: This tutorial features an agent using the Model Context Protocol (MCP) for numerical operations within Pocket Flow. It highlights the framework's support for specialized protocols in agent development.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/README.md#_snippet_22

LANGUAGE: Python
CODE:
```
# Example for pocketflow-mcp
# from pocketflow.mcp import MCPAgent
# 
# mcp_agent = MCPAgent()
# result = mcp_agent.perform_calculation(5, 3, '+')
# print(result)

```

----------------------------------------

TITLE: Pocketflow: Basic HTML Structure
DESCRIPTION: Provides a fundamental HTML structure for Pocketflow components. This includes essential tags for layout, content, and metadata, serving as a template for UI elements.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow_demo.ipynb#_snippet_7

LANGUAGE: HTML
CODE:
```
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Pocketflow</title>
    <link rel="stylesheet" href="style.css">
</head>
<body>
    <header>
        <h1>Pocketflow Dashboard</h1>
    </header>
    <main>
        <!-- Content will be loaded here -->
    </main>
    <footer>
        <p>&copy; 2023 Pocketflow</p>
    </footer>
    <script src="script.js"></script>
</body>
</html>
```

----------------------------------------

TITLE: Pocket Flow Writing Workflow
DESCRIPTION: Demonstrates a writing workflow that includes outlining, content generation, and styling using Pocket Flow.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/README.md#_snippet_2

LANGUAGE: Python
CODE:
```
from pocketflow.workflow import Workflow

workflow = Workflow()
content = workflow.generate_content("Write an article about AI.")
styled_content = workflow.apply_styling(content)
print(styled_content)
```

----------------------------------------

TITLE: Pocketflow: Initialize Data Processing
DESCRIPTION: Initializes the data processing pipeline for Pocketflow. This involves setting up configurations and loading necessary modules. It's a foundational step for most operations within the project.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow_demo.ipynb#_snippet_4

LANGUAGE: JavaScript
CODE:
```
function initializeDataProcessing(config) {
  console.log('Initializing data processing with config:', config);
  // Load modules and set up pipeline
  // ...
  console.log('Data processing initialized successfully.');
}
```

----------------------------------------

TITLE: Basic PocketFlow Tracing
DESCRIPTION: Demonstrates basic PocketFlow tracing by applying the `@trace_flow()` decorator to a custom flow class and running it.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-tracing/README.md#_snippet_2

LANGUAGE: python
CODE:
```
from pocketflow import Node, Flow
from tracing import trace_flow

class MyNode(Node):
    def prep(self, shared):
        return shared["input"]
    
    def exec(self, data):
        return f"Processed: {data}"
    
    def post(self, shared, prep_res, exec_res):
        shared["output"] = exec_res
        return "default"

@trace_flow()  # 🎉 That's it! Your flow is now traced
class MyFlow(Flow):
    def __init__(self):
        super().__init__(start=MyNode())

# Run your flow - tracing happens automatically
flow = MyFlow()
shared = {"input": "Hello World"}
flow.run(shared)
```

----------------------------------------

TITLE: Verify OpenAI API Key
DESCRIPTION: Runs a utility script to verify if the OpenAI API key is set correctly. A successful execution will print a short joke.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-text2sql/README.md#_snippet_2

LANGUAGE: python
CODE:
```
python utils.py
```

----------------------------------------

TITLE: Pocket Flow LLM Streaming Demo
DESCRIPTION: A demonstration of real-time Large Language Model (LLM) streaming with the capability for user interruption, implemented in Pocket Flow.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/README.md#_snippet_6

LANGUAGE: Python
CODE:
```
from pocketflow.streaming import StreamingLLM

streamer = StreamingLLM()
streamer.start_stream("Tell me a story.")
# User can interrupt the stream here
streamer.stop_stream()
```

----------------------------------------

TITLE: Advanced PocketFlow Tracer Configuration
DESCRIPTION: Shows how to create and configure a custom Langfuse tracer for PocketFlow, including loading configuration from environment variables and enabling debug mode.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-tracing/README.md#_snippet_4

LANGUAGE: python
CODE:
```
from tracing import TracingConfig, LangfuseTracer

# Create custom configuration
config = TracingConfig.from_env()
config.debug = True
```

----------------------------------------

TITLE: Initialize PocketFlow Graph Visualization
DESCRIPTION: This snippet initializes the PocketFlow graph visualization using D3.js. It loads data from a JSON file, sets up the SVG canvas, defines arrow markers for links and group links, and configures a force simulation for layout.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-visualization/viz/flow_visualization.html#_snippet_0

LANGUAGE: JavaScript
CODE:
```
d3.json("flow_visualization.json").then(data => {
    const svg = d3.select("#graph");
    const width = window.innerWidth;
    const height = window.innerHeight;

    // Define arrow markers for links
    svg.append("defs").append("marker")
        .attr("id", "arrowhead")
        .attr("viewBox", "0 -5 10 10")
        .attr("refX", 25) // Position the arrow away from the target node
        .attr("refY", 0)
        .attr("orient", "auto")
        .attr("markerWidth", 6)
        .attr("markerHeight", 6)
        .attr("xoverflow", "visible")
        .append("path")
        .attr("d", "M 0,-5 L 10,0 L 0,5")
        .attr("fill", "#999");

    // Define thicker arrow markers for group links
    svg.append("defs").append("marker")
        .attr("id", "group-arrowhead")
        .attr("viewBox", "0 -5 10 10")
        .attr("refX", 3) // Position at the boundary of the group
        .attr("refY", 0)
        .attr("orient", "auto")
        .attr("markerWidth", 8)
        .attr("markerHeight", 8)
        .attr("xoverflow", "visible")
        .append("path")
        .attr("d", "M 0,-5 L 10,0 L 0,5")
        .attr("fill", "#333");

    // Color scale for node groups
    const color = d3.scaleOrdinal(d3.schemeCategory10);

    // Process the data to identify groups
    const groups = {};
    data.nodes.forEach(node => {
        if (node.group > 0) {
            if (!groups[node.group]) {
                // Use the flow name instead of generic "Group X"
                const flowName = data.flows && data.flows[node.group] ? data.flows[node.group] : `Flow ${node.group}`;
                groups[node.group] = { id: node.group, name: flowName, nodes: [], x: 0, y: 0, width: 0, height: 0 };
            }
            groups[node.group].nodes.push(node);
        }
    });

    // Create a force simulation
    const simulation = d3.forceSimulation(data.nodes)
        // Controls the distance between connected nodes
        .force("link", d3.forceLink(data.links).id(d => d.id).distance(100))
        // Controls how nodes repel each other - lower values bring nodes closer
        .force("charge", d3.forceManyBody().strength(-30))
        // Centers the entire graph in the SVG
        .force("center", d3.forceCenter(width / 2, height / 2))
        // Prevents nodes from overlapping - acts like a minimum distance
        .force("collide", d3.forceCollide().radius(50));

    // Group forces - create a force to keep nodes in the same group closer together
    // This creates the effect of nodes clustering within their group boxes
    const groupForce = alpha => {
        for (let i = 0; i < data.nodes.length; i++) {
            const node = data.nodes[i];
            if (node.group > 0) {
                const group = groups[node.group];
                if (group && group.nodes.length > 1) {
                    // Calculate center of group
                    let centerX = 0, centerY = 0;
                    group.nodes.forEach(n => {
                        centerX += n.x || 0;
                        centerY += n.y || 0;
                    });
                    centerX /= group.nodes.length;
                    centerY /= group.nodes.length;
                    // Move nodes toward center
                    const k = alpha * 0.3; // Increased from 0.1 to 0.3
                    node.vx += (centerX - node.x) * k;
                    node.vy += (centerY - node.y) * k;
                }
            }
        }
    };

    // Additional force to position groups in a more organized layout (like in the image)
    // This arranges the groups horizontally/vertically based on their connections
    const groupLayoutForce = alpha => {
        // Get group centers
        const groupCenters = Object.values(groups).map(g => {
            return { id: g.id, cx: 0, cy: 0 };
        });
        // Calculate current center positions
        Object.values(groups).forEach(g => {
            if (g.nodes.length > 0) {
                let cx = 0, cy = 0;
                g.nodes.forEach(n => {
                    cx += n.x || 0;
                    cy += n.y || 0;
                });
                const groupCenter = groupCenters.find(gc => gc.id === g.id);
                if (groupCenter) {
                    groupCenter.cx = cx / g.nodes.length;
                    groupCenter.cy = cy / g.nodes.length;
                }
            }
        });

        // Apply forces to position groups
        const k = alpha * 0.05; // Try to position groups in a more structured way
        // Adjust these values to change the overall layout
        for (let i = 0; i < data.group_links.length; i++) {
            const link = data.group_links[i];
            const source = groupCenters.find(g => g.id === link.source);
            const target = groupCenters.find(g => g.id === link.target);
            if (source && target) {
                // Add a horizontal force to align groups
                const desiredDx = 300; // Desired horizontal distance between linked groups
                const dx = target.cx - source.cx;
                const diff = desiredDx - Math.abs(dx);
                // Apply forces to group nodes
                groups[source.id].nodes.forEach(n => {
                    if (dx > 0) {
                        n.vx -= diff * k;
                    } else {
                        n.vx += diff * k;
                    }
                });
                groups[target.id].nodes.forEach(n => {
                    if (dx > 0) {
                        n.vx += diff * k;
                    } else {
                        n.vx -= diff * k;
                    }
                });
            }
        }
    };

    // Add the forces to the simulation
    simulation.force("group", groupForce);
    simulation.force("groupLayout", groupLayoutForce);

    // Update the simulation on each tick
    simulation.on("tick", () => {
        // Update link positions
        svg.selectAll(".links path")
            .attr("d", d => {
                const dx = d.target.x - d.source.x,
                    dy = d.target.y - d.source.y,
                    dr = Math.sqrt(dx * dx + dy * dy);
                return "M" + d.source.x + "," + d.source.y + "A" + dr + "," + dr + " 0 0,1 " + d.target.x + "," + d.target.y;
            });

        // Update group link positions
        svg.selectAll(".group-links path")
            .attr("d", d => {
                const dx = d.target.cx - d.source.cx,
                    dy = d.target.cy - d.source.cy,
                    dr = Math.sqrt(dx * dx + dy * dy);
                return "M" + d.source.cx + "," + d.source.cy + "A" + dr + "," + dr + " 0 0,1 " + d.target.cx + "," + d.target.cy;
            });

        // Update node positions
        svg.selectAll(".nodes circle")
            .attr("cx", d => d.x)
            .attr("cy", d => d.y);

        // Update node label positions
        svg.selectAll(".node-labels text")
            .attr("x", d => d.x)
            .attr("y", d => d.y - 15); // Position label above the node

        // Update group container positions and dimensions
        svg.selectAll(".group-container rect")
            .attr("x", d => d.x)
            .attr("y", d => d.y)
            .attr("width", d => d.width)
            .attr("height", d => d.height);

        // Update group label positions
        svg.selectAll(".group-label text")
            .attr("x", d => d.x + d.width / 2)
            .attr("y", d => d.y - 5); // Position label above the group box
    });

    // Render links
    const link = svg.append("g")
        .attr("class", "links")
        .selectAll("path")
        .data(data.links)
        .enter().append("path")
        .attr("marker-end", "url(#arrowhead)")
        .style("fill", "none")
        .style("stroke", "#999")
        .style("stroke-opacity", 0.6)
        .style("stroke-width", 1.5);

    // Render group links
    const groupLink = svg.append("g")
        .attr("class", "group-links")
        .selectAll("path")
        .data(data.group_links || []) // Handle cases where group_links might be missing
        .enter().append("path")
        .attr("marker-end", "url(#group-arrowhead)")
        .style("fill", "none")
        .style("stroke", "#333")
        .style("stroke-opacity", 0.8)
        .style("stroke-width", 2)
        .style("stroke-dasharray", "5,5");

    // Render nodes
    const node = svg.append("g")
        .attr("class", "nodes")
        .selectAll("circle")
        .data(data.nodes)
        .enter().append("circle")
        .attr("r", 15)
        .style("fill", d => color(d.group))
        .style("stroke", "#fff")
        .style("stroke-width", 1.5)
        .call(d3.drag()
            .on("start", dragstarted)
            .on("drag", dragged)
            .on("end", dragended));

    // Render node labels
    const nodeLabel = svg.append("g")
        .attr("class", "node-labels")
        .selectAll("text")
        .data(data.nodes)
        .enter().append("text")
        .text(d => d.id)
        .style("font-size", 12)
        .style("pointer-events", "none");

    // Render group containers and labels
    const groupContainer = svg.append("g")
        .attr("class", "group-containers")
        .selectAll(".group-container")
        .data(Object.values(groups))
        .enter().append("g")
        .attr("class", "group-container-g");

    groupContainer.append("rect")
        .attr("class", "group-container")
        .style("stroke", "#333")
        .style("stroke-width", 1.5)
        .style("stroke-dasharray", "5,5")
        .style("fill", "rgba(200, 200, 200, 0.1)")
        .style("rx", 10)
        .style("ry", 10);

    groupContainer.append("text")
        .attr("class", "group-label")
        .text(d => d.name)
        .style("font-size", 14)
        .style("font-weight", "bold")
        .style("pointer-events", "none");

    // Adjust group bounding boxes and positions after initial simulation steps
    simulation.on("tick", () => {
        // ... (previous tick updates)

        // Calculate bounding boxes for groups
        Object.values(groups).forEach(group => {
            let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
            if (group.nodes.length > 0) {
                group.nodes.forEach(node => {
                    minX = Math.min(minX, node.x);
                    minY = Math.min(minY, node.y);
                    maxX = Math.max(maxX, node.x);
                    maxY = Math.max(maxY, node.y);
                });
                group.x = minX - 20; // Add padding
                group.y = minY - 20;
                group.width = maxX - minX + 40;
                group.height = maxY - minY + 40;
            } else {
                group.x = 0;
                group.y = 0;
                group.width = 0;
                group.height = 0;
            }
        });

        // Update group container positions and dimensions
        svg.selectAll(".group-container-g .group-container")
            .attr("x", d => d.x)
            .attr("y", d => d.y)
            .attr("width", d => d.width)
            .attr("height", d => d.height);

        // Update group label positions
        svg.selectAll(".group-container-g .group-label")
            .attr("x", d => d.x + d.width / 2)
            .attr("y", d => d.y - 5); // Position label above the group box
    });

    // Drag functions
    function dragstarted(event, d) {
        if (!event.active) simulation.alphaTarget(0.3).restart();
        d.fx = d.x;
        d.fy = d.y;
    }

    function dragged(event, d) {
        d.fx = event.x;
        d.fy = event.y;
    }

    function dragended(event, d) {
        if (!event.active) simulation.alphaTarget(0);
        d.fx = null;
        d.fy = null;
    }
});

```

----------------------------------------

TITLE: Pocket Flow Batch Translation Tutorial
DESCRIPTION: This tutorial demonstrates a batch processor that translates markdown content into multiple languages using Pocket Flow. It highlights the framework's ability to handle bulk processing tasks efficiently.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/README.md#_snippet_8

LANGUAGE: Python
CODE:
```
# Example for pocketflow-batch
# from pocketflow.batch import Translator
# 
# translator = Translator()
# markdown_content = "# Title"
# translated_content = translator.translate_batch(markdown_content, ['fr', 'es'])
# print(translated_content)

```

----------------------------------------

TITLE: Pocket Flow Code Beispiel: Cold-Opener-Generator
DESCRIPTION: Dieses Beispiel demonstriert die Verwendung von Pocket Flow zur Erstellung eines Cold-Opener-Generators für personalisierte E-Mails. Es kombiniert das Map Reduce-Muster mit Web-Suchfunktionen, um effektive Eisbrecher zu erstellen.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-batch/translations/README_GERMAN.md#_snippet_7

LANGUAGE: Python
CODE:
```
from pocketflow import Agent, Workflow

# Beispiel-Code für die Erstellung eines Cold-Opener-Generators mit Pocket Flow
# Dies ist ein Platzhalter, der tatsächliche Code würde hier stehen.
# Siehe das Repository für die vollständige Implementierung.

def build_cold_opener_generator_app():
    opener_agent = Agent(name="ColdOpenerAgent")
    workflow = Workflow(name="ColdOpenerWorkflow")
    workflow.add_step(Workflow.Step(name="GenerateOpener", agent=opener_agent, config={'pattern': 'Map Reduce', 'utility': 'WebSearch'}))
    # ... Logik zur Personalisierung und Generierung von E-Mail-Öffnern ...
    return workflow

# Beispielaufruf (nicht im Originaldokument enthalten, nur zur Veranschaulichung)
# if __name__ == "__main__":
#     cold_opener_app = build_cold_opener_generator_app()
#     print("Cold Opener Generator built successfully!")
```

----------------------------------------

TITLE: Text-to-SQL Agent Workflow Diagram
DESCRIPTION: Visual representation of the Text-to-SQL agent's workflow, showing the sequence of operations including schema retrieval, SQL generation, execution, and debugging.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-text2sql/docs/design.md#_snippet_0

LANGUAGE: mermaid
CODE:
```
flowchart TD
    A[GetSchema] --> B[GenerateSQL]
    B --> C{ExecuteSQL}
    C -- Success --> D[End]
    C -- Error --> E[DebugSQL]
    E --> C
```

----------------------------------------

TITLE: Pocket Flow Parallel Batch Processing Tutorial
DESCRIPTION: This tutorial showcases a parallel execution demo using Pocket Flow, achieving a 3x speedup in batch processing tasks. It highlights the benefits of parallel computation for performance.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/README.md#_snippet_16

LANGUAGE: Python
CODE:
```
# Example for pocketflow-parallel-batch
# from pocketflow.parallel import BatchProcessor
# 
# processor = BatchProcessor()
# tasks = ["Task 1", "Task 2", "Task 3"]
# results = processor.run_parallel(tasks)
# print(results)

```

----------------------------------------

TITLE: Run Default Text-to-SQL Workflow
DESCRIPTION: Executes the main script to run the default Text-to-SQL workflow. This will create a sample SQLite database if it doesn't exist and process a default query.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-text2sql/README.md#_snippet_3

LANGUAGE: python
CODE:
```
python main.py
```

----------------------------------------

TITLE: Generate Configuration Files in YAML
DESCRIPTION: Illustrates generating a server configuration file in YAML format, including host, port, and SSL settings. This is a common use case for infrastructure configuration.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/docs/design_pattern/structure.md#_snippet_2

LANGUAGE: yaml
CODE:
```
server:
  host: 127.0.0.1
  port: 8080
  ssl: true
```

----------------------------------------

TITLE: Pocket Flow CLI Joke Generator Tutorial
DESCRIPTION: This tutorial features a command-line joke generator with human-in-the-loop feedback, built using Pocket Flow. It allows for interactive refinement of generated content.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/README.md#_snippet_13

LANGUAGE: Python
CODE:
```
# Example for pocketflow-cli-hitl
# from pocketflow.cli import JokeGenerator
# 
# generator = JokeGenerator()
# joke = generator.generate_with_feedback()
# print(joke)

```

----------------------------------------

TITLE: Process Data with Pocketflow
DESCRIPTION: Illustrates how to process data using Pocketflow. This snippet likely covers inputting data and triggering the processing logic within the framework.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow_demo.ipynb#_snippet_51

LANGUAGE: JavaScript
CODE:
```
import Pocketflow from 'pocketflow';

const pf = new Pocketflow();
const data = { key: 'value' };

pf.process(data).then(result => {
  console.log('Processing complete:', result);
}).catch(error => {
  console.error('Processing failed:', error);
});
```

----------------------------------------

TITLE: Qdrant: Recreate Collection, Upsert, and Search
DESCRIPTION: Demonstrates recreating a Qdrant collection with specified vector parameters, upserting points, and performing a search. Requires the Qdrant client library.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/docs/utility_function/vector.md#_snippet_2

LANGUAGE: Python
CODE:
```
import qdrant_client
from qdrant_client.models import Distance, VectorParams, PointStruct

client = qdrant_client.QdrantClient(
    url="https://YOUR-QDRANT-CLOUD-ENDPOINT",
    api_key="YOUR_API_KEY"
)

collection = "my_collection"
client.recreate_collection(
    collection_name=collection,
    vectors_config=VectorParams(size=128, distance=Distance.COSINE)
)

points = [
    PointStruct(id=1, vector=[0.1]*128, payload={"type": "doc1"}),
    PointStruct(id=2, vector=[0.2]*128, payload={"type": "doc2"}),
]

client.upsert(collection_name=collection, points=points)

results = client.search(
    collection_name=collection,
    query_vector=[0.15]*128,
    limit=2
)
print(results)
```

----------------------------------------

TITLE: Data Processing and Visualization in Python
DESCRIPTION: This snippet demonstrates how to process and visualize data using Python libraries. It covers data loading, transformation, and plotting, essential for understanding project workflows.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow_demo.ipynb#_snippet_30

LANGUAGE: Python
CODE:
```
import pandas as pd
import matplotlib.pyplot as plt

# Load data from a CSV file
data = pd.read_csv('data.csv')

# Perform data processing (e.g., calculate averages)
processed_data = data.groupby('category')['value'].mean().reset_index()

# Visualize the processed data
plt.figure(figsize=(10, 6))
plt.bar(processed_data['category'], processed_data['value'])
plt.xlabel('Category')
plt.ylabel('Average Value')
plt.title('Average Value by Category')
plt.show()

```

----------------------------------------

TITLE: Weaviate: Create Schema, Add Data, and Query
DESCRIPTION: Illustrates creating a schema in Weaviate, adding a data object with a vector, and performing a vector search. Requires the Weaviate client library.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/docs/utility_function/vector.md#_snippet_3

LANGUAGE: Python
CODE:
```
import weaviate

client = weaviate.Client("https://YOUR-WEAVIATE-CLOUD-ENDPOINT")

schema = {
    "classes": [
        {
            "class": "Article",
            "vectorizer": "none"
        }
    ]
}
client.schema.create(schema)

obj = {
    "title": "Hello World",
    "content": "Weaviate vector search"
}
client.data_object.create(obj, "Article", vector=[0.1]*128)

resp = (
    client.query
    .get("Article", ["title", "content"])
    .with_near_vector({"vector": [0.15]*128})
    .with_limit(3)
    .do()
)
print(resp)
```

----------------------------------------

TITLE: Set API Keys
DESCRIPTION: Sets environment variables for SerpAPI and OpenAI API keys. These keys are required for the tool to authenticate with the respective services.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-tool-search/README.md#_snippet_1

LANGUAGE: bash
CODE:
```
export SERPAPI_API_KEY='your-serpapi-key'
export OPENAI_API_KEY='your-openai-key'
```

----------------------------------------

TITLE: Set OpenAI API Key
DESCRIPTION: Sets the environment variable for the OpenAI API key, which is required for the LLM to function. Remember to replace 'your-api-key-here' with your actual key.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-text2sql/README.md#_snippet_1

LANGUAGE: bash
CODE:
```
export OPENAI_API_KEY="your-api-key-here"
```

----------------------------------------

TITLE: Call OpenAI LLM
DESCRIPTION: Demonstrates how to call the OpenAI API using the 'openai' library. Requires an API key and specifies the model to use. Best practice suggests storing the API key in an environment variable.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/docs/utility_function/llm.md#_snippet_0

LANGUAGE: python
CODE:
```
from openai import OpenAI
client = OpenAI(api_key="YOUR_API_KEY_HERE")
r = client.chat.completions.create(
    model="gpt-4o",
    messages=[{"role": "user", "content": prompt}]
)
return r.choices[0].message.content
```

----------------------------------------

TITLE: Pocket Flow Code Beispiel: Cursor mit Cursor bauen
DESCRIPTION: Dies ist ein Beispiel für die Implementierung von Pocket Flow zur Erstellung einer Anwendung, bei der ein Cursor mit einem Cursor erstellt wird. Es demonstriert die Verwendung von Agenten-basiertem Programmieren für LLM-Apps.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-batch/translations/README_GERMAN.md#_snippet_3

LANGUAGE: Python
CODE:
```
from pocketflow import Agent

# Beispiel-Code für die Erstellung einer Cursor-Anwendung mit Pocket Flow
# Dies ist ein Platzhalter, der tatsächliche Code würde hier stehen.
# Siehe das Repository für die vollständige Implementierung.

def build_cursor_app():
    agent = Agent(name="CursorBuilder")
    # ... weitere Agenten-Logik und Workflow-Definitionen ...
    return agent

# Beispielaufruf (nicht im Originaldokument enthalten, nur zur Veranschaulichung)
# if __name__ == "__main__":
#     cursor_app = build_cursor_app()
#     print("Cursor App built successfully!")
```

----------------------------------------

TITLE: Configure OpenAI API Key for Real Streaming
DESCRIPTION: Shows how to set the OpenAI API key as an environment variable for the application to use real LLM responses instead of fake ones.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-llm-streaming/README.md#_snippet_1

LANGUAGE: bash
CODE:
```
export OPENAI_API_KEY="your-api-key-here"
```

----------------------------------------

TITLE: Article Writing Workflow Definition
DESCRIPTION: Defines the sequential flow of the article writing process using Mermaid syntax, showing the progression from generating an outline to applying a style.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-workflow/README.md#_snippet_3

LANGUAGE: mermaid
CODE:
```
graph LR
    Outline[Generate Outline] --> Write[Write Content]
    Write --> Style[Apply Style]
```

----------------------------------------

TITLE: PocketFlow Tracing Configuration Options
DESCRIPTION: Illustrates different ways to configure PocketFlow tracing, including custom flow names, session IDs, user IDs, and advanced configuration objects.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-tracing/README.md#_snippet_3

LANGUAGE: python
CODE:
```
from tracing import trace_flow, TracingConfig

# Use environment variables (default)
@trace_flow()
class MyFlow(Flow):
    pass

# Custom flow name
@trace_flow(flow_name="CustomFlowName")
class MyFlow(Flow):
    pass

# Custom session and user IDs
@trace_flow(session_id="session-123", user_id="user-456")
class MyFlow(Flow):
    pass

# Create custom configuration
config = TracingConfig(
    langfuse_secret_key="your-secret-key",
    langfuse_public_key="your-public-key", 
    langfuse_host="https://your-langfuse-instance.com",
    debug=True,
    trace_inputs=True,
    trace_outputs=True,
    trace_errors=True
)

@trace_flow(config=config)
class MyFlow(Flow):
    pass
```

----------------------------------------

TITLE: Run A2A Client
DESCRIPTION: Launches the A2A client to interact with the running A2A server, allowing users to send queries.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-a2a/README.md#_snippet_4

LANGUAGE: Bash
CODE:
```
python a2a_client.py --agent-url http://localhost:10003
```

----------------------------------------

TITLE: Pocket Flow Majority Vote Tutorial
DESCRIPTION: This tutorial enhances reasoning accuracy by aggregating multiple solution attempts using the majority vote pattern in Pocket Flow. It showcases a method for improving the reliability of LLM outputs.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/README.md#_snippet_11

LANGUAGE: Python
CODE:
```
# Example for pocketflow-majority-vote
# from pocketflow.voting import MajorityVote
# 
# voter = MajorityVote()
# solutions = ["Solution A", "Solution B", "Solution A"]
# final_solution = voter.get_majority(solutions)
# print(final_solution)

```

----------------------------------------

TITLE: Pocket Flow Chatbot Tutorial
DESCRIPTION: This tutorial demonstrates how to build a basic chatbot with conversation history using Pocket Flow. It showcases the framework's ability to manage state and context for interactive applications.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/README.md#_snippet_3

LANGUAGE: Python
CODE:
```
# Example for pocketflow-chat
# from pocketflow.chat import Chatbot
# 
# chatbot = Chatbot()
# response = chatbot.chat("Hello!")
# print(response)

```

----------------------------------------

TITLE: Chroma: Create Collection, Add Embeddings, and Query
DESCRIPTION: Demonstrates creating a Chroma collection, adding embeddings with metadata and IDs, and querying the collection. Requires ChromaDB.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/docs/utility_function/vector.md#_snippet_5

LANGUAGE: Python
CODE:
```
import chromadb
from chromadb.config import Settings

client = chromadb.Client(Settings(
    chroma_db_impl="duckdb+parquet",
    persist_directory="./chroma_data"
))

coll = client.create_collection("my_collection")

vectors = [[0.1, 0.2, 0.3], [0.2, 0.2, 0.2]]
metas = [{"doc": "text1"}, {"doc": "text2"}]
ids = ["id1", "id2"]
coll.add(embeddings=vectors, metadatas=metas, ids=ids)

res = coll.query(query_embeddings=[[0.15, 0.25, 0.3]], n_results=2)
print(res)
```

----------------------------------------

TITLE: Pocket Flow A2A Agent Tutorial
DESCRIPTION: This tutorial demonstrates an agent wrapped with the A2A protocol for inter-agent communication using Pocket Flow. It focuses on enabling seamless communication between different agents.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/README.md#_snippet_23

LANGUAGE: Python
CODE:
```
# Example for pocketflow-a2a
# from pocketflow.a2a import A2ACommunicator
# 
# communicator = A2ACommunicator()
# communicator.send_message("AgentB", "Hello from AgentA")

```

----------------------------------------

TITLE: Pocket Flow Parallel Execution Speedup
DESCRIPTION: A demonstration of parallel execution in Pocket Flow, highlighting a 3x speedup compared to sequential processing.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/README.md#_snippet_10

LANGUAGE: Python
CODE:
```
from pocketflow.parallel import ParallelExecutor

executor = ParallelExecutor()
results = executor.run_tasks([task1, task2, task3])
print(results)
```

----------------------------------------

TITLE: Redis: Create Vector Index, Insert, and Search
DESCRIPTION: Shows how to create a RediSearch vector index, insert a document with an embedding, and perform a KNN search. Requires Redis and struct module.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/docs/utility_function/vector.md#_snippet_6

LANGUAGE: Python
CODE:
```
import redis
import struct

r = redis.Redis(host="localhost", port=6379)

# Create index
r.execute_command(
    "FT.CREATE", "my_idx", "ON", "HASH",
    "SCHEMA", "embedding", "VECTOR", "FLAT", "6",
    "TYPE", "FLOAT32", "DIM", "128",
    "DISTANCE_METRIC", "L2"
)

# Insert
vec = struct.pack('128f', *[0.1]*128)
r.hset("doc1", mapping={"embedding": vec})

# Search
qvec = struct.pack('128f', *[0.15]*128)
q = "*=>[KNN 3 @embedding $BLOB AS dist]"
res = r.ft("my_idx").search(q, query_params={"BLOB": qvec})
print(res.docs)
```

----------------------------------------

TITLE: Configure PocketFlow Tracing with Environment Variables
DESCRIPTION: Lists essential environment variables for configuring Langfuse and PocketFlow tracing, including API keys, host, debug mode, and data tracking options.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-tracing/README.md#_snippet_7

LANGUAGE: env
CODE:
```
# Required Langfuse configuration
LANGFUSE_SECRET_KEY=your-secret-key
LANGFUSE_PUBLIC_KEY=your-public-key
LANGFUSE_HOST=your-langfuse-host

# Optional tracing configuration
POCKETFLOW_TRACING_DEBUG=true
POCKETFLOW_TRACE_INPUTS=true
POCKETFLOW_TRACE_OUTPUTS=true
POCKETFLOW_TRACE_PREP=true
POCKETFLOW_TRACE_EXEC=true
POCKETFLOW_TRACE_POST=true
POCKETFLOW_TRACE_ERRORS=true

# Optional session/user tracking
POCKETFLOW_SESSION_ID=your-session-id
POCKETFLOW_USER_ID=your-user-id
```

----------------------------------------

TITLE: Run PocketFlow with Default Problem
DESCRIPTION: Executes the PocketFlow code generator using the default 'Two Sum' LeetCode problem.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-code-generator/README.md#_snippet_3

LANGUAGE: bash
CODE:
```
python main.py
```

----------------------------------------

TITLE: PocketFlow Workflow Diagram in Mermaid
DESCRIPTION: Visual representation of the PocketFlow article generation workflow using Mermaid syntax. It shows the sequential flow from generating an outline to writing content and applying final styling.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-fastapi-background/docs/design.md#_snippet_1

LANGUAGE: Mermaid
CODE:
```
flowchart LR
    outline[Generate Outline] --> content[Write Content]
    content --> styling[Apply Style]
```

----------------------------------------

TITLE: PocketFlow Workflow Implementation
DESCRIPTION: Contains the PocketFlow workflow definition, connecting the different nodes (GenerateOutline, WriteContent, ApplyStyle) to create the article generation pipeline.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-fastapi-background/README.md#_snippet_5

LANGUAGE: python
CODE:
```
# flow.py: PocketFlow workflow definition connecting the three nodes
```

----------------------------------------

TITLE: Shell: Scripting for Automation
DESCRIPTION: Illustrates shell scripting for automating tasks. This can include file manipulation, running commands, and managing processes, crucial for workflow automation in a project environment.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow_demo.ipynb#_snippet_18

LANGUAGE: Shell
CODE:
```
#!/bin/bash

# Example: Copy files from one directory to another
SOURCE_DIR="/path/to/source"
DEST_DIR="/path/to/destination"

echo "Copying files from $SOURCE_DIR to $DEST_DIR..."
cp -r "$SOURCE_DIR"/* "$DEST_DIR/"

echo "Copy complete."
```

----------------------------------------

TITLE: Integrate Real OpenAI Streaming in Python
DESCRIPTION: Demonstrates how to modify the Python code to use the actual `stream_llm` function for fetching content chunks from OpenAI, replacing the default fake streaming.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-llm-streaming/README.md#_snippet_2

LANGUAGE: python
CODE:
```
# Change this line:
chunks = fake_stream_llm(prompt)
# To this:
chunks = stream_llm(prompt)
```

----------------------------------------

TITLE: FAISS: Create and Search Flat L2 Index
DESCRIPTION: Demonstrates creating a flat L2 index in FAISS, adding random vectors, and performing a search query. Requires the FAISS library and NumPy.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/docs/utility_function/vector.md#_snippet_0

LANGUAGE: Python
CODE:
```
import faiss
import numpy as np

# Dimensionality of embeddings
d = 128

# Create a flat L2 index
index = faiss.IndexFlatL2(d)

# Random vectors
data = np.random.random((1000, d)).astype('float32')
index.add(data)

# Query
query = np.random.random((1, d)).astype('float32')
D, I = index.search(query, k=5)

print("Distances:", D)
print("Neighbors:", I)
```

----------------------------------------

TITLE: Flow Diagram (Mermaid)
DESCRIPTION: Visual representation of the Pocketflow's workflow using Mermaid syntax. It illustrates the sequence and dependencies between different nodes in the flow.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-hello-world/docs/design.md#_snippet_1

LANGUAGE: mermaid
CODE:
```
flowchart TD
    firstNode[First Node] --> secondNode[Second Node]
    secondNode --> thirdNode[Third Node]
```

----------------------------------------

TITLE: Pocket Flow Code Beispiel: Codebase-Wissensgenerator
DESCRIPTION: Dieses Beispiel zeigt, wie Pocket Flow verwendet wird, um einen Wissensgenerator für Codebasen zu erstellen. Es nutzt agentenbasiertes Programmieren, um das Verständnis und die Navigation in fremdem Code zu erleichtern.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-batch/translations/README_GERMAN.md#_snippet_4

LANGUAGE: Python
CODE:
```
from pocketflow import Agent, Workflow

# Beispiel-Code für die Erstellung eines Codebase-Wissensgenerators mit Pocket Flow
# Dies ist ein Platzhalter, der tatsächliche Code würde hier stehen.
# Siehe das Repository für die vollständige Implementierung.

def build_codebase_knowledge_generator():
    knowledge_agent = Agent(name="CodebaseKnowledgeAgent")
    workflow = Workflow(name="CodebaseKnowledgeWorkflow")
    # ... Definition von Workflow-Schritten und Agenten-Interaktionen ...
    return workflow

# Beispielaufruf (nicht im Originaldokument enthalten, nur zur Veranschaulichung)
# if __name__ == "__main__":
#     kb_generator = build_codebase_knowledge_generator()
#     print("Codebase Knowledge Generator built successfully!")
```

----------------------------------------

TITLE: Pocket Flow Kernfunktionalität (Python)
DESCRIPTION: Der Kern von Pocket Flow ist in nur 100 Zeilen Python-Code implementiert. Dieses Snippet repräsentiert die Essenz des Frameworks, das für seine Leichtgewichtigkeit und Abhängigkeitsfreiheit bekannt ist.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-batch/translations/README_GERMAN.md#_snippet_1

LANGUAGE: Python
CODE:
```
import inspect

def pocketflow():
    frame = inspect.currentframe()
    if frame:
        return frame.f_code.co_name
    return "No frame"

# Beispielaufruf:
# print(pocketflow())
```

----------------------------------------

TITLE: PocketFlow Flow Management
DESCRIPTION: Illustrates the flow management aspects of the PocketFlow project. This involves setting up sequences of operations and managing their execution, often using asynchronous patterns.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow_demo.ipynb#_snippet_44

LANGUAGE: JavaScript
CODE:
```
async function manageFlow(steps) {
  for (const step of steps) {
    await executeStep(step);
  }
}
```

LANGUAGE: Python
CODE:
```
import asyncio

async def manage_flow(steps):
    for step in steps:
        await execute_step(step)
```

----------------------------------------

TITLE: Data Processing and Flow Management in PocketFlow
DESCRIPTION: This snippet illustrates the core data processing and flow management capabilities within the PocketFlow project. It highlights how data is handled and routed through various stages of a workflow. The code demonstrates fundamental operations and system interactions.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow_demo.ipynb#_snippet_29

LANGUAGE: Go
CODE:
```
package main

import (
	"fmt"
	"time"
)

// DataPacket represents a unit of data flowing through the system.
type DataPacket struct {
	ID      string
	Payload interface{}
	Timestamp time.Time
}

// Processor defines an interface for processing DataPackets.
type Processor interface {
	Process(packet DataPacket) (DataPacket, error)
}

// ExampleProcessor is a sample implementation of the Processor interface.
type ExampleProcessor struct {
	Name string
}

func (p *ExampleProcessor) Process(packet DataPacket) (DataPacket, error) {
	fmt.Printf("Processor '%s' processing packet ID: %s\n", p.Name, packet.ID)
	// Simulate some processing
	tpacket.Payload = fmt.Sprintf("%v - processed by %s", packet.Payload, p.Name)
	packet.Timestamp = time.Now()
	return packet, nil
}

func main() {
	// Initialize a data packet
	initialPacket := DataPacket{
		ID:      "pkt-001",
		Payload: "Initial data",
		Timestamp: time.Now(),
	}

	// Initialize processors
	processor1 := &ExampleProcessor{Name: "Processor Alpha"}
	processor2 := &ExampleProcessor{Name: "Processor Beta"}

	// Simulate a processing flow
	processedPacket1, err1 := processor1.Process(initialPacket)
	if err1 != nil {
		fmt.Printf("Error processing packet: %v\n", err1)
		return
	}

	processedPacket2, err2 := processor2.Process(processedPacket1)
	if err2 != nil {
		fmt.Printf("Error processing packet: %v\n", err2)
		return
	}

	fmt.Printf("Final packet ID: %s, Payload: %v\n", processedPacket2.ID, processedPacket2.Payload)
}

```

----------------------------------------

TITLE: Visualize Order Pipeline with Mermaid
DESCRIPTION: This Mermaid syntax describes the structure of the order pipeline, visually representing the sequence and dependencies between the Payment Flow, Inventory Flow, and Shipping Flow. It aids in understanding the overall execution path.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/docs/core_abstraction/flow.md#_snippet_5

LANGUAGE: Mermaid
CODE:
```
flowchart LR
    subgraph order_pipeline[Order Pipeline]
        subgraph paymentFlow["Payment Flow"]
            A[Validate Payment] --> B[Process Payment] --> C[Payment Confirmation]
        end

        subgraph inventoryFlow["Inventory Flow"]
            D[Check Stock] --> E[Reserve Items] --> F[Update Inventory]
        end

        subgraph shippingFlow["Shipping Flow"]
            G[Create Label] --> H[Assign Carrier] --> I[Schedule Pickup]
        end

        paymentFlow --> inventoryFlow
        inventoryFlow --> shippingFlow
    end
```

----------------------------------------

TITLE: PocketFlow: Data Processing and Workflow Execution
DESCRIPTION: This snippet illustrates the fundamental data processing and workflow execution capabilities within the PocketFlow project. It highlights how data is handled and processed through defined workflows, emphasizing efficiency and flexibility.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow_demo.ipynb#_snippet_42

LANGUAGE: text
CODE:
```
Project: /the-pocket/pocketflow
Content: oKCjzOa9WqFTabDZvNVqPvWYjalpycTEpKCgBxcXFYLJZLfthfqxRFwWazab8vNfBVFlL8IcgkJSWRmpoKUGll4cMPP+TNN98kPDycf/7zn9x8880e7XXFPcjUh3vutGnTePfddzGZTCxYsIAmTZroT/F5kZGRmEwm0tLS/Hew786dO3nrrbe0x3feeScZGRns3r2bL774gqlTpzJ16lR69uzpESICAwN54YUX2LFjB/v27SMtLU1L/I0bN/Y6puZiHA4H7777Lj179mTFihUcPnyYw4cPk5OTw5IlS0hISPA62j0wMJCAgP/89eTn5zNhwgQKCgq47rrrSEhIYO7cucydO5cPP/yQm2++uUbfsxC1SVEUrFYrKSkpWCwWMjMzGT16tIQYHUVRSE5OJiYmhpiYGNLT04mLiyMzM1P7nfmrs2fPsmPHDu3x6dOnOXbsmMc5DodD+2LYoUMHraruTWlpKZs3b2by5MkkJiby/vvvY7fbKS0t1Z96xTp16lShuqaXnZ3NgAEDiIyMJDIykujo6Brd2kBd0T04OPiaqMD7bZDRi4qKIiIiokLlw5sGDRrQvHlzGjZsCG4j0C9cuFCtC62oqIiEhAStUtK8eXP69evHrFmz+OCDD5g5cyZ5eXn07du3Qgm8efPmWhl11qxZ7N69m1atWrFy5UpGjBjB448/zuOPP87tt98ONfiehahNiqIQHx+P3W5n+vTpTJ8+XQKMjqIoJCQkEBMT41Gxqk7gU+8n+q42X7F//3727t2rPXY6ndq6KKqTJ0/yww8/AHD//fd7/cAuKytj2bJlREdH079/f+bNm8eiRYuYMmUKVquV22+/nddff53jx4/rn1rBuXPnWLBgAT179qRfv34kJSWxfft2ysrKPM7r3bu3dh/WczgczJ49m4cffpgNGzZox0+dOkVSUhKjRo064vu1w+HQZnmFhYVV+l78id8GmU6dOjFlyhStqrFs2TK6du3KsmXLKlx4l3LixAlwXcjq3PxLcTgcTJo0iaVLlwIwePBgtmzZwpQpU+jZsyePPPIIDRo0oKysjKNHj/LNN994PL9hw4baNwxFUQgICGDcuHFVXhPgct6zELUtPj4eRVFIS0vz2UGotUGtvqj7MGVlZdVI9UX/BclXbNy4kQsXLmiPS0pKtHua6tdff+Xw4cM0atSIP/3pTx5tuKoSw4cPZ+TIkZw7d07fDEB5eTmffvopDzzwAF9//WVVjbTYsmUL999/P2+88QY7d+4kMzOT1NRUevfuzaBBg/jll1/AVQGp7B6tDndQv9hGRkYye/Zs5s2bx5133gnAmjVr+P7773XPrJ7S0lKPqeDqsePHj2O321mzZg0HDhyolWpUXVPHuPltkDEYDFgsFhYtWkRkZCS4PtRHjhzJfffdx/Lly2t1X45169axePFiAJ5++mnGjh2rzYzCdVGrZVGA9evXe1xYgYGBNG7cWHv82GOP8ec//1l7LISvUVepnTFjRoXpwtcq9+6jlJQUjEZjtasv/qawsJCNGzeC6z6u+vnnn93OQgseERERFbpyjh8/jtVqZc2aNdqxrl27sm7dOnJzc8nNzWXdunX07t0bgOLiYoYOHUpGRobbq/zHrl27GDZsGPn5+eC6N7ds2ZLmzZsDsGHDBu0L68VkZGRowx3MZjPLly+nR48ePProoyxcuJA77rgDp9PJnj179E+tFveKzI4dO/jv//5vbrvtNu69916sVitDhw6le/fu3HbbbVgslqu+nUJN8NsgozKZTKxdu5Y33nhDu/AOHz7MiBEj6NKlC1999dUlA01lCVuVm5tLZmam9jqlpaUsXrwYp9NJly5deO211yqUPbOzs1m5cqX2eOfOnR7fnho2bEizZs3A9Y+5T58+FV7jYqr7noWoTepg1bS0NAkxuu6ja2nsS1VkZ2fz448/YjAYmDBhgjZ7a9OmTdr+QSdPntR2mDabzdq9UlVQUOBRiY6Li+OLL74gKioKg8GAwWAgKiqK5ORkNm7cSJs2bSgvL2fcuHEeeyadPn1aG58IMGjQIPbs2UNWVhY7duzg4MGDbNy4URuEXFlX/qlTp5g5cybl5eVERUUxe/ZsQkNDtfbdu3drWy1c6SDh0tJSTp48CcCBAwc8Zuw2btxY+xwE+O677+jduze7du3SjvkCtRKj8vsgg2uG0MCBA9m2bRv//Oc/ufvuu8F1cY0aNYouXbqwYsWKSsuKqpKSkgrdNIWFhcTFxdG/f39t+fCzZ89qpcYBAwZw/fXXV3jOxIkTyc/P175xnDlzhszMTO0c94rMLbfcopUeq6uq71mI2hQfH09cXNw1H2LcB++6dx/VdPVFrVDob/i+QO1Wuuuu+jVqxfdunUD0BYBxFXd2L9/PwaDgYceeqjC2MfQ0FBtkkOHDh0YNGhQpV8EW7duzdtvv01QUBD5+fmsWrVKa9u0aRO7d+8GYOzYsUyYMMGjUu50OklPT9fG2DgcDq8bV65cuVILSPv372fMmDF89dVXrF69mqSkJIYMGcKFCxe47bbbiI6O1j+9Wtz3WcLVhTVv3jz27dvH3r172bFjB//+97959tlnwRX6Zs6c6TWA+YprIsioGjRoQOfOnVm2bBlfffUVnTp1Alegeemll0hJSfFaoWjatCmBgYE4nc4Kf9mKorBv3z6cTqf23ICAAO0fzbfffuvxmkeOHGHYsGFkZmYSEBDApEmTtG8cq1ev9rpTdWUp/2Kq+56FqC3qGjHXcqVBDTDp6enExsbWSfWlJoNRXXHvVoqOjqZZs2ba2jAFBQV888035ObmMmvWLAA6duxI586dPV4D19gX9d4WFRVVYf0ZvdatW2tL+btXxtVQ0r59e6xWa4XAlJ2dzeeff+5xzG63e9zHCwsLta4ndXjB+vXrGTVqFMOHDyc1NRWHw0FYWBgzZszwqJhcjvPnz2v3/C5durBq1SoeffRRj0G/1113HePHj+e//uu/APj+++85cOCA1u4r/H6MDK5xKg8++GCFAb4Gg4FOnTqxdOlSlixZolU7UlJSWLFihdsr/EejRo0ICgoCXT+t0+lk1apVnD9/nptvvlnbsCw0NJSOHTsCkJaWRt++fUlMTGTw4MF069ZNq7y8+uqr9O/fn4ceegiA7du38+9//1t7fZW3qYeXUt33LERtSU5OvqYH9qpBTg0wNV198Sc5OTnabCU1wHTu3FlbH2b9+nQGBgYwYMYI1a9bQoUMH7XmXKyQkRKsaNW/enODgYP0p4PqMUCeUuAc/X+TXQWb16tXk5OQwcuHE33377bW1r2bJlGZzBwUF9+eWX9O/fP2FhYbzxxhv79u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3L8uXL27ZtG3fccUf69u3
```

----------------------------------------

TITLE: Pocket Flow Parallel Image Processing Tutorial
DESCRIPTION: This tutorial demonstrates parallel image processing with Pocket Flow, achieving an 8x speedup. It illustrates the framework's efficiency in handling computationally intensive tasks.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/README.md#_snippet_17

LANGUAGE: Python
CODE:
```
# Example for pocketflow-parallel-batch-flow
# from pocketflow.parallel import ImageProcessor
# 
# img_processor = ImageProcessor()
# images = ["image1.jpg", "image2.jpg"]
# processed_images = img_processor.process_parallel(images)
# print(processed_images)

```

----------------------------------------

TITLE: Implement OpenAI LLM Call Function
DESCRIPTION: Provides a Python function `call_llm` that takes a prompt and returns a response from the OpenAI GPT-4o model. It requires the 'openai' library and an API key.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow_demo.ipynb#_snippet_1

LANGUAGE: python
CODE:
```
from openai import OpenAI
import os

def call_llm(prompt):
    client = OpenAI(api_key=API_KEY)
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content
```

----------------------------------------

TITLE: Youtube Summarizer Flow Code
DESCRIPTION: This Python code provides a beginner-friendly YouTube Summarizer. It uses the Map Reduce design pattern to explain YouTube videos in a simple way, akin to explaining to a 5-year-old.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/README.md#_snippet_33

LANGUAGE: Python
CODE:
```
https://github.com/The-Pocket/Tutorial-Youtube-Made-Simple/blob/main/flow.py
```

----------------------------------------

TITLE: PocketFlow Data Processing
DESCRIPTION: Demonstrates the core data processing capabilities of PocketFlow, handling various data formats and transformations. This snippet is essential for understanding how data flows through the system.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow_demo.ipynb#_snippet_13

LANGUAGE: Go
CODE:
```
package main

import (
	"fmt"
	"github.com/the-pocket/pocketflow/pkg/flow"
)

func main() {
	// Initialize a new flow
	f := flow.NewFlow("data-processing-flow")

	// Add a data source step
	f.AddStep(flow.NewStep("read-csv", flow.StepTypeDataSource, "./data.csv"))

	// Add a transformation step
	f.AddStep(flow.NewStep("transform-data", flow.StepTypeTransform, func(data interface{}) (interface{}, error) {
		// Placeholder for transformation logic
		fmt.Println("Transforming data...")
		return data, nil
	}))

	// Add a data sink step
	f.AddStep(flow.NewStep("write-json", flow.StepTypeDataSink, "./output.json"))

	// Execute the flow
	err := f.Execute()
	if err != nil {
		fmt.Printf("Error executing flow: %v\n", err)
	}

	fmt.Println("Flow executed successfully.")
}
```

----------------------------------------

TITLE: Python: API Interaction for Data Fetching
DESCRIPTION: Shows how to interact with external APIs using Python to fetch data. This involves making HTTP requests and handling responses, a common practice for integrating with web services.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow_demo.ipynb#_snippet_19

LANGUAGE: Python
CODE:
```
import requests

def fetch_api_data(api_url):
  try:
    response = requests.get(api_url)
    response.raise_for_status() # Raise an exception for bad status codes
    return response.json()
  except requests.exceptions.RequestException as e:
    print(f"Error fetching data: {e}")
    return None
```

----------------------------------------

TITLE: Frontend HTML Structure (HTML)
DESCRIPTION: The HTML file for the web user interface. It includes a textarea for input, buttons for feedback, and elements to display status updates.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-fastapi-hitl/README.md#_snippet_7

LANGUAGE: HTML
CODE:
```
<!-- Placeholder for templates/index.html content -->
<!-- Example structure:
<!DOCTYPE html>
<html>
<head>
    <title>PocketFlow HITL</title>
    <link rel="stylesheet" href="/static/style.css">
</head>
<body>
    <h1>PocketFlow Human-in-the-Loop</h1>
    <textarea id="inputText" placeholder="Enter text here..."></textarea>
    <button onclick="submitTask()">Submit</button>
    <div id="status">Status: Waiting...</div>
    <div id="output"></div>
    <button id="approveBtn" style="display:none;" onclick="sendFeedback('approved')">Approve</button>
    <button id="rejectBtn" style="display:none;" onclick="sendFeedback('rejected')">Reject</button>

    <script>
        // JavaScript for SSE and button handling would go here
    </script>
</body>
</html>
-->
```

----------------------------------------

TITLE: Run QA Flow with Shared Data in Python
DESCRIPTION: This snippet shows the main execution block for a QA flow. It initializes a dictionary to share data between nodes, creates the QA flow using `create_qa_flow()`, runs the flow with the shared data, and then prints the question and answer captured during the flow's execution.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/docs/guide.md#_snippet_9

LANGUAGE: Python
CODE:
```
def main():
    shared = {
        "question": None,  # Will be populated by GetQuestionNode from user input
        "answer": None     # Will be populated by AnswerNode
    }

    # Create the flow and run it
    qa_flow = create_qa_flow()
    qa_flow.run(shared)
    print(f"Question: {shared['question']}")
    print(f"Answer: {shared['answer']}")

if __name__ == "__main__":
    main()
```

----------------------------------------

TITLE: Run Research Agent (Custom Query)
DESCRIPTION: Executes the main script to run the research agent with a custom user-provided question, prefixed with '--'.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-agent/README.md#_snippet_4

LANGUAGE: bash
CODE:
```
python main.py --"What is quantum computing?"
```

----------------------------------------

TITLE: Mermaid Flowchart Diagram
DESCRIPTION: Illustrates a basic flowchart structure using Mermaid syntax, showing sequential steps, conditional branching, and subgraphs. This is useful for visualizing the flow of an AI system.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/docs/guide.md#_snippet_0

LANGUAGE: mermaid
CODE:
```
flowchart LR
    start[Start] --> batch[Batch]
    batch --> check[Check]
    check -->|OK| process
    check -->|Error| fix[Fix]
    fix --> check
    
    subgraph process[Process]
        step1[Step 1] --> step2[Step 2]
    end
    
    process --> endNode[End]
```

----------------------------------------

TITLE: YouTube Summarizer Agent Code
DESCRIPTION: This snippet includes the agent code for the 'YouTube Summarizer' project. It simplifies YouTube videos for a 5-year-old understanding using the Map Reduce pattern.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-batch/translations/README_FRENCH.md#_snippet_6

LANGUAGE: Python
CODE:
```
https://github.com/The-Pocket/Tutorial-Youtube-Made-Simple/blob/main/flow.py
```

----------------------------------------

TITLE: Pocket Flow Code Beispiel: Youtube-Zusammenfasser
DESCRIPTION: Dieses Beispiel zeigt, wie Pocket Flow verwendet wird, um einen YouTube-Videozusammenfasser zu erstellen. Es nutzt das Map Reduce-Muster, um lange Inhalte zu verarbeiten und verständliche Zusammenfassungen zu erstellen.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-batch/translations/README_GERMAN.md#_snippet_6

LANGUAGE: Python
CODE:
```
from pocketflow import Agent, Workflow

# Beispiel-Code für die Erstellung eines YouTube-Zusammenfassers mit Pocket Flow
# Dies ist ein Platzhalter, der tatsächliche Code würde hier stehen.
# Siehe das Repository für die vollständige Implementierung.

def build_youtube_summarizer_app():
    summarizer_agent = Agent(name="YouTubeSummarizerAgent")
    workflow = Workflow(name="YouTubeSummarizationWorkflow")
    workflow.add_step(Workflow.Step(name="Summarize", agent=summarizer_agent, config={'pattern': 'Map Reduce'}))
    # ... weitere Logik für die Verarbeitung von YouTube-Inhalten ...
    return workflow

# Beispielaufruf (nicht im Originaldokument enthalten, nur zur Veranschaulichung)
# if __name__ == "__main__":
#     youtube_summarizer = build_youtube_summarizer_app()
#     print("YouTube Summarizer built successfully!")
```

----------------------------------------

TITLE: Pocketflow: Network Communication
DESCRIPTION: This snippet illustrates network communication functionalities within Pocketflow, demonstrating how to establish connections and exchange data over a network. It's crucial for distributed operations and real-time data exchange.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow_demo.ipynb#_snippet_62

LANGUAGE: Go
CODE:
```
package main

import (
	"fmt"
	"net"
)

func main() {
	// Example: Listening on a TCP port
	listener, err := net.Listen("tcp", ":8080")
	if err != nil {
		fmt.Println("Error listening:", err.Error())
		return
	}
	defer listener.Close()
	fmt.Println("Listening on :8080")

	// Accept incoming connections
	conn, err := listener.Accept()
	if err != nil {
		fmt.Println("Error accepting:", err.Error())
		return
	}
	defer conn.Close()
	fmt.Println("Client connected:", conn.RemoteAddr())

	// Example: Reading from connection
	buffer := make([]byte, 1024)
	n, err := conn.Read(buffer)
	if err != nil {
		fmt.Println("Error reading:", err.Error())
		return
	}
	fmt.Printf("Received: %s\n", buffer[:n])

	// Example: Writing to connection
	_, err = conn.Write([]byte("Hello from server!"))
	if err != nil {
		fmt.Println("Error writing:", err.Error())
		return
	}
}
```

----------------------------------------

TITLE: PocketFlow Flow Configuration
DESCRIPTION: This Python file likely defines the structure and connections of the PocketFlow graph, specifying how different nodes (like search and analysis) interact.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-tool-search/README.md#_snippet_7

LANGUAGE: python
CODE:
```
# flow.py
# Flow configuration
```

----------------------------------------

TITLE: PocketFlow Workflow Definition
DESCRIPTION: Defines a three-step article generation workflow using PocketFlow: Generate Outline, Write Content, and Apply Style. The 'Write Content' node is a BatchNode designed to send progress updates.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-fastapi-background/README.md#_snippet_3

LANGUAGE: mermaid
CODE:
```
flowchart LR
    A[Generate Outline] --> B[Write Content]
    B --> C[Apply Style]
```

----------------------------------------

TITLE: Pocket Flow Supervisor for Agent Reliability
DESCRIPTION: Build a supervision process using Pocket Flow to address unreliability issues in research agents.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/README.md#_snippet_9

LANGUAGE: Python
CODE:
```
from pocketflow.supervisor import Supervisor

supervisor = Supervisor()
agent = Agent() # Assume an unreliable agent
supervised_agent = supervisor.supervise(agent)
result = supervised_agent.research("Latest AI trends")
print(result)
```

----------------------------------------

TITLE: Pocketflow DecideAction Node
DESCRIPTION: Defines a Pocketflow Node called 'DecideAction' that prepares context and questions for an LLM to determine whether to search the web or provide a direct answer. It formats the decision prompt in YAML.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-agent/demo.ipynb#_snippet_2

LANGUAGE: python
CODE:
```
# nodes.py
from pocketflow import Node
import yaml

class DecideAction(Node):
    def prep(self, shared):
        """Prepare the context and question for the decision-making process."""
        # Get the current context (default to "No previous search" if none exists)
        context = shared.get("context", "No previous search")
        # Get the question from the shared store
        question = shared["question"]
        # Return both for the exec step
        return question, context

    def exec(self, inputs):
        """Call the LLM to decide whether to search or answer."""
        question, context = inputs

        print(f"🤔 Agent deciding what to do next...")

        # Create a prompt to help the LLM decide what to do next with proper yaml formatting
        prompt = f"""
### CONTEXT
You are a research assistant that can search the web.
Question: {question}
Previous Research: {context}

### ACTION SPACE
[1] search
  Description: Look up more information on the web
  Parameters:
    - query (str): What to search for

[2] answer
  Description: Answer the question with current knowledge
  Parameters:
    - answer (str): Final answer to the question

"""
        # Use the call_llm function to get the LLM's decision
        decision = call_llm(prompt)
        # Parse the YAML response to extract the action and parameters
        action_data = yaml.safe_load(decision)
        # Return the parsed action data
        return action_data
```

----------------------------------------

TITLE: Summarize Large File with BatchNode
DESCRIPTION: Demonstrates using BatchNode to process a large file in chunks. The prep method splits the content into chunks, exec summarizes each chunk, and post combines the summaries.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/docs/core_abstraction/batch.md#_snippet_0

LANGUAGE: Python
CODE:
```
class MapSummaries(BatchNode):
    def prep(self, shared):
        # Suppose we have a big file; chunk it
        content = shared["data"]
        chunk_size = 10000
        chunks = [content[i:i+chunk_size] for i in range(0, len(content), chunk_size)]
        return chunks

    def exec(self, chunk):
        prompt = f"Summarize this chunk in 10 words: {chunk}"
        summary = call_llm(prompt)
        return summary

    def post(self, shared, prep_res, exec_res_list):
        combined = "\n".join(exec_res_list)
        shared["summary"] = combined
        return "default"

map_summaries = MapSummaries()
flow = Flow(start=map_summaries)
flow.run(shared)
```

----------------------------------------

TITLE: Main Execution Script (Python)
DESCRIPTION: The entry point for the application. It creates the PocketFlow graph and runs it, triggering the database operations and task management logic.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-tool-database/README.md#_snippet_6

LANGUAGE: python
CODE:
```
from flow import create_flow

def main():
    flow = create_flow()
    flow.run()

if __name__ == "__main__":
    main()

```

----------------------------------------

TITLE: Pocket Flow Chatbot Memory Tutorial
DESCRIPTION: This tutorial demonstrates building a chatbot with both short-term and long-term memory using Pocket Flow. It enhances conversational context and user experience.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/README.md#_snippet_19

LANGUAGE: Python
CODE:
```
# Example for pocketflow-chat-memory
# from pocketflow.memory import ChatMemory
# 
# chat_memory = ChatMemory()
# chat_memory.add_message("User", "Hello")
# chat_memory.add_message("AI", "Hi there!")
# print(chat_memory.get_history())

```

----------------------------------------

TITLE: Set OpenAI API Key
DESCRIPTION: Sets the OpenAI API key as an environment variable, which is required for the LLM content analysis functionality.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-tool-crawler/README.md#_snippet_1

LANGUAGE: bash
CODE:
```
export OPENAI_API_KEY='your-api-key'
```

----------------------------------------

TITLE: Event Handling and Triggering
DESCRIPTION: This section illustrates the event handling mechanisms within PocketFlow. It shows how to register event listeners, trigger custom events, and manage event payloads. This is crucial for creating reactive systems and coordinating actions between different components.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow_demo.ipynb#_snippet_69

LANGUAGE: JavaScript
CODE:
```
class EventEmitter {
  constructor() {
    this.events = {};
  }

  on(eventName, listener) {
    if (!this.events[eventName]) {
      this.events[eventName] = [];
    }
    this.events[eventName].push(listener);
  }

  emit(eventName, data) {
    if (this.events[eventName]) {
      this.events[eventName].forEach(listener => listener(data));
    }
  }
}

const emitter = new EventEmitter();

emitter.on('dataReady', (payload) => {
  console.log('Data received:', payload);
});

emitter.emit('dataReady', { message: 'Processing complete' });
```

----------------------------------------

TITLE: Verify OpenAI API Key
DESCRIPTION: Runs a utility script to confirm that the OpenAI API key is correctly set and functional. This helps in debugging connectivity issues before running the main application.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-structured-output/README.md#_snippet_2

LANGUAGE: python
CODE:
```
python utils.py
```

----------------------------------------

TITLE: Mermaid Diagram for Human Review Workflow
DESCRIPTION: Visual representation of the human-in-the-loop workflow using Mermaid syntax. Shows the flow from task processing to review and finalization, including the loop for rejected tasks.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-fastapi-hitl/docs/design.md#_snippet_1

LANGUAGE: Mermaid
CODE:
```
flowchart TD
    Process[Process Task] -- "default" --> Review{Wait for Feedback}
    Review -- "approved" --> Result[Final Result]
    Review -- "rejected" --> Process
```

----------------------------------------

TITLE: Run Text-to-SQL Workflow with Custom Query
DESCRIPTION: Runs the main script with a custom natural language query provided as a command-line argument. For queries with spaces, ensure they are properly quoted.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-text2sql/README.md#_snippet_4

LANGUAGE: python
CODE:
```
python main.py What is the total stock quantity for products in the 'Accessories' category?
```

LANGUAGE: python
CODE:
```
python main.py "List orders placed in the last 30 days with status 'shipped'"
```

----------------------------------------

TITLE: JavaScript: Data Visualization with Charting Libraries
DESCRIPTION: Demonstrates how to visualize data using JavaScript charting libraries. This snippet typically involves setting up a canvas, defining data points, and rendering charts like bar graphs or line plots. It's often used for front-end data representation.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow_demo.ipynb#_snippet_16

LANGUAGE: JavaScript
CODE:
```
function renderChart(data, elementId) {
  const ctx = document.getElementById(elementId).getContext('2d');
  new Chart(ctx, {
    type: 'bar',
    data: {
      labels: data.labels,
      datasets: [{
        label: '# of Votes',
        data: data.values,
        backgroundColor: 'rgba(75, 192, 192, 0.2)',
        borderColor: 'rgba(75, 192, 192, 1)',
        borderWidth: 1
      }]
    },
    options: {
      scales: {
        y: {
          beginAtZero: true
        }
      }
    }
  });
}
```

----------------------------------------

TITLE: Run PocketFlow with Custom Problem
DESCRIPTION: Executes the PocketFlow code generator with a custom coding problem provided as a command-line argument.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-code-generator/README.md#_snippet_4

LANGUAGE: bash
CODE:
```
python main.py "Reverse a linked list. Given the head of a singly linked list, reverse the list and return the reversed list."
```

----------------------------------------

TITLE: Cold Opener Generator Flow Code
DESCRIPTION: This Python code generates 'Cold Openers' for emails, designed to turn cold leads into hot ones. It's a beginner-level project utilizing Map Reduce and Web Search patterns for instant icebreakers.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/README.md#_snippet_34

LANGUAGE: Python
CODE:
```
https://github.com/The-Pocket/Tutorial-Cold-Email-Personalization/blob/master/flow.py
```

----------------------------------------

TITLE: PocketFlow Workflow Diagram
DESCRIPTION: Visual representation of the PocketFlow system's operational workflow, illustrating the sequence of steps from problem input to solution.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-code-generator/README.md#_snippet_5

LANGUAGE: mermaid
CODE:
```
flowchart TD
    start[Problem Input] --> generateTests[Generate Test Cases]
    generateTests --> implement[Implement Function]
    implement --> runTests[Run Tests - Batch]
    runTests --> decision{All Tests Pass?}
    decision -->|Yes| success[Success!]
    decision -->|No| revise[Revise - Agent Decision]
    revise --> runTests
    decision -->|Max Iterations| maxIter[Max Iterations Reached]
```

----------------------------------------

TITLE: PocketFlow Event Handling
DESCRIPTION: Illustrates how PocketFlow handles events, allowing for reactive programming and dynamic workflow adjustments. This is crucial for real-time data processing scenarios.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow_demo.ipynb#_snippet_14

LANGUAGE: Python
CODE:
```
from pocketflow.core import Flow, Step

def handle_event(event_data):
    print(f"Received event: {event_data}")
    # Process event data and potentially trigger other flows or actions
    return "Processed"

# Create a flow that listens for events
event_flow = Flow("event-listener-flow")
event_flow.add_step(Step("event-handler", StepType.EVENT_LISTENER, handler=handle_event))

# Simulate receiving an event
# In a real scenario, this would come from an event source
# event_flow.trigger_event({"message": "New data available"})

print("Event listener flow set up.")
```

----------------------------------------

TITLE: Define and Run a Pocketflow Order Pipeline (Python)
DESCRIPTION: This Python code defines a master order pipeline by connecting individual flows (payment, inventory, shipping) sequentially. It then demonstrates how to run the entire pipeline with shared data, illustrating a clean separation of concerns.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/docs/core_abstraction/flow.md#_snippet_4

LANGUAGE: Python
CODE:
```
# Connect the flows into a main order pipeline
payment_flow >> inventory_flow >> shipping_flow

# Create the master flow
order_pipeline = Flow(start=payment_flow)

# Run the entire pipeline
order_pipeline.run(shared_data)
```

----------------------------------------

TITLE: Yahoo's Editor Rewrite
DESCRIPTION: Yahoo's 2003 editor rewrite involved C++ and Perl. Notably, a Lisp interpreter was required for the translation, indicating that Lisp code likely remained fundamental to the page-generating templates.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/data/PaulGrahamEssaysLarge/avg.txt#_snippet_5

LANGUAGE: C++
CODE:
```
New version of the editor
```

LANGUAGE: Perl
CODE:
```
New version of the editor
```

LANGUAGE: Lisp
CODE:
```
Source files for page-generating templates
Lisp interpreter (required for C++ translation)
```

----------------------------------------

TITLE: Call Azure OpenAI LLM
DESCRIPTION: Demonstrates how to connect to Azure OpenAI services using the 'openai' library. This requires the Azure endpoint, an API key, and the specific deployment name for the model.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/docs/utility_function/llm.md#_snippet_3

LANGUAGE: python
CODE:
```
from openai import AzureOpenAI
client = AzureOpenAI(
    azure_endpoint="https://<YOUR_RESOURCE_NAME>.openai.azure.com/",
    api_key="YOUR_API_KEY_HERE",
    api_version="2023-05-15"
)
r = client.chat.completions.create(
    model="<YOUR_DEPLOYMENT_NAME>",
    messages=[{"role": "user", "content": prompt}]
)
return r.choices[0].message.content
```

----------------------------------------

TITLE: YouTube Summarizer (Map Reduce)
DESCRIPTION: A simple application to summarize YouTube videos, built using the 'Map Reduce' design pattern. This snippet provides access to the design documentation and the Python 'Flow' code.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-batch/translations/README_CHINESE.md#_snippet_6

LANGUAGE: Python
CODE:
```
https://github.com/The-Pocket/Tutorial-Youtube-Made-Simple/blob/main/flow.py
```

----------------------------------------

TITLE: Codebase Knowledge Builder (Workflow)
DESCRIPTION: Learn to build a codebase knowledge builder using agentic coding and the 'Workflow' design pattern. This snippet links to the design documentation and the Python 'Flow' code for the application.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-batch/translations/README_CHINESE.md#_snippet_4

LANGUAGE: Python
CODE:
```
https://github.com/The-Pocket/Tutorial-Codebase-Knowledge/blob/main/flow.py
```

----------------------------------------

TITLE: Build Cursor with Cursor Agent Code
DESCRIPTION: This snippet demonstrates the agent code for the 'Build Cursor with Cursor' project. It's part of a larger effort to build applications using agentic coding principles within the PocketFlow framework.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow-batch/translations/README_FRENCH.md#_snippet_3

LANGUAGE: Python
CODE:
```
https://github.com/The-Pocket/Tutorial-Cursor/blob/main/flow.py
```

----------------------------------------

TITLE: Pocketflow Task Execution (Java)
DESCRIPTION: Shows how to execute tasks or operations using Pocketflow in a Java environment. This could be for background processes or specific computational tasks.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/cookbook/pocketflow_demo.ipynb#_snippet_53

LANGUAGE: Java
CODE:
```
import com.pocketflow.Pocketflow;

public class Main {
    public static void main(String[] args) {
        Pocketflow pf = new Pocketflow();
        String taskInput = "input_parameters";
        
        pf.executeTask(taskInput);
        System.out.println("Task execution initiated.");
    }
}
```

----------------------------------------

TITLE: Pocket Flow Chain-of-Thought Tutorial
DESCRIPTION: This tutorial explains how to solve complex reasoning problems through the Chain-of-Thought (CoT) pattern using Pocket Flow. It focuses on improving the logical reasoning capabilities of LLMs.

SOURCE: https://github.com/the-pocket/pocketflow/blob/main/README.md#_snippet_18

LANGUAGE: Python
CODE:
```
# Example for pocketflow-thinking
# from pocketflow.reasoning import ChainOfThought
# 
# cot = ChainOfThought()
# problem = "Solve this complex problem..."
# solution = cot.solve(problem)
# print(solution)

```