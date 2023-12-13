# tseapy: Time Series Explorative Analysis Python

**tseapy** is an innovative open-source Python application designed for comprehensive and intuitive analysis of time series data. Leveraging the power of Python, it offers a user-friendly web interface that enables users to interact with their data dynamically, facilitating various time series analysis tasks. Whether you're a data scientist, researcher, or enthusiast, tseapy makes it easier to explore and understand time series data.

## Getting Started

Follow these instructions to set up tseapy on your local machine for development and testing purposes.

### Prerequisites

Before you begin, ensure you have the following installed:
- Python 3.6 or higher
- pip

### Installation

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/mrkshdt/tseapy.git
   ```

2. **Navigate to the Project Directory**:
   ```bash
   cd tseapy
   ```

3. **Create a Virtual Environment**:
   ```bash
   python3 -m venv tseapy-venv
   ```

4. **Activate the Virtual Environment**:
   - On Windows:
     ```bash
     tseapy-venv\Scripts\activate
     ```
   - On Unix or MacOS:
     ```bash
     source tseapy-venv/bin/activate
     ```

5. **Install Required Packages**:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

To launch tseapy:
1. Start the application:
   ```bash
   python app.py
   ```
2. Open your web browser and navigate to: `http://localhost:5000`.

## Project Structure

- **app.py**: The entry point of the application.
- **tseapy/**: The heart of the application, containing core functionalities such as data processing (`tseapy/data/`), task management (`tseapy/tasks/`), and web view (`tseapy/view/`).
- **templates/**: Houses HTML templates for the web interface.
- **static/**: Contains static files like CSS for styling.
- **tests/**: Includes unit tests to ensure the reliability and efficiency of the application.

Embark on your time series analysis journey with **tseapy** – your go-to tool for insightful and interactive data exploration!