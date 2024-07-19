# Import the required libraries
import requests
import json
from types import SimpleNamespace

SERVER_URL = "https://api.quantuniversity.com"

class ReportGenerator:
    """
    This class is used to generate reports for the experiments.
    
    Attributes:
    name (str): The name of the report.
    version (str): The version of the report.
    category (str): The category of the report.
    notes (list): The list of notes for the report.
    references (str): The references for the report.
    owner (str): The owner of the report.
    contact (str): The contact for the report.
    parameters (dict): The parameters for the report.
    detail (dict): The details for the report.
    """

    def __init__(self, name="test", version="1.0", category="basic", notes=[], references="", owner='Sri Krishnamurthy', contact='info@qusandbox.com'):
        """
        The constructor for the ReportGenerator class.
        
        Parameters:
        name (str): The name of the report.
        version (str): The version of the report.
        category (str): The category of the report.
        notes (list): The list of notes for the report.
        references (str): The references for the report.
        owner (str): The owner of the report.
        contact (str): The contact for the report.
        """
        self.parameters = {}
        self.parameters['name']= name
        self.parameters['version']= version
        if references:
          self.parameters['references']= references
        self.parameters['owner'] = owner
        self.parameters['contact'] = contact
        self.category = category
        self.detail = {}
        self.notes = []
        for note in notes:
            self.notes.append(note.__dict__)
        
    def load(self, value={}):
        """
        This function is used to load the report details.
        
        Parameters:
        value (dict): The details for the report.
        """
        if isinstance(value, (dict, str)):
            self.detail = value
        else:
            # self.detail = json.loads(json.dumps(value, default=lambda o: o.__dict__))
            self.detail = value.value
            
    def add_note(self, note):
        """
        This function is used to add a note to the report.
        
        Parameters:
        note (Note): The note to be added to the report.
        """
        self.notes.append(note.__dict__)
    
    def generate(self):
        """
        This function is used to generate the report.
        
        Returns:
        str: The generated report.
        """
        url = SERVER_URL + "/experiment/public/stage/" + self.category + "/artifact/"
        body = {
            "report_parameters": self.parameters,
            "report_details": self.detail,
            "notes": self.notes
        }
        response = requests.post(url, json.dumps(body))
        if response.status_code != 200:
            raise ValueError('Unexpected happened.')
        self.report = response.json()['HTML']
        return self.report
    
    def save(self, path="audit.html"):
        """
        This function is used to save the report to a file.
        
        Parameters:
        path (str): The path to save the report.
        """
        file = open(path, "w")
        file.write(self.report)
        
    def publish(self, APIkey="", experiment="", stage=""):
        """
        This function is used to publish the report.
        
        Parameters:
        APIkey (str): The API key for the report.
        experiment (str): The experiment for the report.
        stage (str): The stage for the report.
        """
        print("Publish reports to QuSandbox available with prime version, contact info@qusandbox.com for more infomation")
    
    
class TemplateReader:
    """
    This class is used to read the template.
    
    Attributes:
    template_id (str): The id of the template.
    template (dict): The template details.
    """
    
    def __init__(self, template_id="7acd5c69079946b199c8bab692512f27"):
        """
        The constructor for the TemplateReader class.
        
        Parameters:
        template_id (str): The id of the template.
        """
        self.template_id = template_id
        
    def load(self):
        """
        This function is used to load the template.
        """
        url = SERVER_URL + "/template/" + self.template_id
        response = requests.get(url)
        self.template = response.json()['Items'][0]
        
    def get_raw_json(self):
        """
        This function is used to get the raw json of the template.
        
        Returns:
        dict: The raw json of the template.
        """
        return json.loads(self.template['templateValue'])
    
    def get_sample_input(self):
        """
        This function is used to get the sample input for the template.
        
        Returns:
        TemplateValue: The sample input for the template.
        """
        survey_json = json.loads(self.template['templateValue'])
        sample_input = {}
        for page in survey_json['pages']:
            for element in page['elements']:
                if element['type'] == 'panel':
                    for question in element['elements']:
                        if question["type"] == "rating":
                            sample_input[question['name']] = 4
                        elif question["type"] == "text":
                            sample_input[question['name']] = question['defaultValue']
                        else:
                            sample_input[question['name']] = "TBD"
                else:
                    sample_input[element['name']] = "TBD"
        # return json.loads(json.dumps(sample_input), object_hook=lambda d: SimpleNamespace(**d))
        return TemplateValue(sample_input)
    
class Note:
    """
    This class is used to create a note for the report.
    
    Attributes:
    Artifact (str): The artifact for the note.
    ArtifactType (str): The artifact type for the note.
    Title (str): The title for the note.
    Content (str): The content for the note.
    """

    categories = ['plotly_json', 'plotly_chart', 'embed', 'link', 'base64', 'file']

    def __init__(self, category="base64", value="", title="", description=""):
        """
        The constructor for the Note class.
        
        Parameters:
        category (str): The category of the note.
        value (str): The value of the note.
        title (str): The title of the note.
        description (str): The description of the note.
        """
        self.Title = title
        self.Content = description
        if category not in self.categories:
            print('Support categories are ' + str(self.categories))
            raise ValueError('Not a support note category')
        else:
            if category in ['link', 'base64', 'file']:
                self.ArtifactType = 'base64'
                if category == 'file':
                    import base64
                    data = open(value, "r").read()
                    self.Artifact = "data:image/jpeg;base64," + base64.b64encode(data).decode('utf-8')
                else:
                    self.Artifact = "data:image/jpeg;base64," + value
            elif category == 'embed':
                self.ArtifactType = 'embed'
                self.Artifact = value
            elif category in ['plotly_json', 'plotly_chart']:
                import plotly
                self.ArtifactType = 'plotly'
                if category == 'plotly_chart':
                    self.Artifact = plotly.io.to_json(value)
                else:
                    self.Artifact = value

class TemplateValue:
    """
    This class is used to create a template value.
    
    Attributes:
    value (dict): The value for the template.
    """
    
    def __init__(self, input={}):
        """
        The constructor for the TemplateValue class.
        
        Parameters:
        input (dict): The input for the template.
        """
        self.value = input

    def set_value(self, key, value):
        """
        This function is used to set the value for the template.
        
        Parameters:
        key (str): The key for the value.
        value (str): The value for the key.
        """
        self.value[key] = value

    def delete_value(self, key):
        """
        This function is used to delete the value for the template.
        
        Parameters:
        key (str): The key for the value.
        """
        if key in self.value:
          del self.value[key]

    def __repr__(self):
        """
        This function is used to represent the template value.
        
        Returns:
        str: The template value.
        """
        return json.dumps(self.value)

    def __str__(self):
        """
        This function is used to represent the template value.
        
        Returns:
        str: The template value.
        """
        return json.dumps(self.value)

def browse_all_templates():
    """
    This function is used to browse all the templates.
    
    Returns:
    list: The list of templates.
    """
    url = SERVER_URL + "/template/"
    response = requests.get(url)
    results = response.json()['Items']
    templates = []
    for result in results:
        templates.append({
            "id":result["SK"].split('#')[1],
            "name":result["templateName"],
            "sample":result["templateSample"],
            "category":result["templateType"]
        })
    return templates

def get_sample(url):
    """
    This function is used to get the sample from the url.
    
    Parameters:
    url (str): The url to get the sample.
    
    Returns:
    str: The sample from the url.
    """
    return requests.get(url).text

def show_report(html):
    """
    This function is used to show the report.
    
    Parameters:
    html (str): The html of the report.
    """
    try:
        from IPython.core.display import HTML
        display(HTML(html))
    except:
        print('Not in notebook environment, please copy the html string to a file manually')