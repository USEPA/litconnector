## LitConnector

Analysis of literature traditionally involves labor-intensive searches and reviews to identify connections, weigh evidence, and generate hypotheses. To address these challenges, we developed LitConnector, an open-source application that uses semantic relationships from annotated literature to provide an interactive way of reviewing literature collections. This tool enables investigators to focus on relevant subsets and uncover complex thematic connections that might be overlooked through conventional literature search methods. 


### Running LitConnector

To start the app using Docker, run:
`docker-compose up -d`

Next, navigate to http://localhost:8501/

### Development

#### Requirements
- Python 3.9+

#### Setup

1. Create and activate a Python virtual environment

2. Install dependencies

`pip install -e ".[dev]"`

3. Run the app

`streamlit run src/app.py`


### Disclaimer

The United States Environmental Protection Agency (EPA) GitHub project
code is provided on an "as is" basis and the user assumes responsibility for its use. EPA
has relinquished control of the information and no longer has responsibility to protect
the integrity, confidentiality, or availability of the information. Any reference to specific
commercial products, processes, or services by service mark, trademark, manufacturer, or
otherwise, does not constitute or imply their endorsement, recommendation or favoring
by EPA. The EPA seal and logo shall not be used in any manner to imply endorsement of
any commercial product or activity by EPA or the United States Government.

### Contact

If you have any questions, please reach out to Scott Lynn at <Lynn.Scott@epa.gov>