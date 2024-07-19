# Import the required libraries
import base64
import os
import streamlit as st
import pandas as pd
import plotly.graph_objects as graph_objects
from src.report.qu_audit import *
import uuid
from pathlib import Path
from src.common.logger import Logger
import plotly.express as px
from src.s3.s3FileManager import S3FileManager

# Create the Logger object
logger = Logger.get_logger()


class BiasAuditCalculations:
    """
    Class to perform bias audit calculations.
    """

    def __init__(self):
        """
        Constructor for the BiasAuditCalculations class.
        """
        self.df = pd.read_csv("./data/AEDT/data.csv", header=0)
        self.file_id = uuid.uuid4()

        template_id = "ff14ff4225804f6f8f787f22460e1f63"
        self.template_reader = TemplateReader(template_id)
        self.template_reader.load()
        self.template_input = {
            "Bias Audit Report": "This is the bias audit report for XYZ Corp."}
        self.report_generator = ReportGenerator(name="Bias Audit for Client XYZ Corp.", version="1.0",
                                                category="basic", owner='Sri Krishnamurthy', contact='info@qusandbox.com')
        self.report_generator.load(self.template_input)
        self.s3_file_manager = S3FileManager()

    def main(self):
        """
        Main function to perform bias audit calculations.
        """
        logger.info("Logged in to Bias Audit Calculations")
        if 'df_intersectional_counts' not in st.session_state:
            st.session_state.df_intersectional_counts = pd.DataFrame({'A': []})

        # Create a copy of the dataframe
        df_copy = self.df.copy()

        # Display the header
        st.header("Bias Audit Calculations ", divider="blue")
        st.subheader("Use the sample data or upload your data",
                     divider="orange")
        st.dataframe(self.df, hide_index=True)
        st.divider()

        # Display the sample data schema
        bin_file = 'data/AEDT/dataSchema.csv'
        with open(bin_file, 'rb') as f:
            data = f.read()
        bin_str = base64.b64encode(data).decode()
        href = f'<a href="data:application/octet-stream;base64,{bin_str}" download="{os.path.basename(bin_file)}">sample file.</a>'
        st.markdown(
            f"""<h6 style='text-align: center;'> Use the above sample dataset or upload your own data using the format in this {href}</h6>""", unsafe_allow_html=True)

        # Upload a file
        uploaded_file = st.file_uploader(
            "Choose a file", type=['csv'], key="fileUploader")

        if uploaded_file is not None:
            # Read the dataframe
            try:
                dataframe = pd.read_csv(uploaded_file, header=0)
            except Exception as e:
                st.error(
                    "You need to upload a CSV file following the data schema in the sample file. Please try again.")
            # Validate the uploaded data frame
            try:
                if not list[set(dataframe.columns)] == list[set(df_copy.columns)]:
                    st.error(
                        "Please submit valid data schema. Use the above data schema file link as reference")

                # check if the dataframe is empty or length of dataframe is 1
                elif dataframe.empty or len(dataframe) == 1:
                    st.error(
                        "The uploaded file is empty. Please upload a valid file with data.")
                else:
                    st.dataframe(dataframe)
                    df_copy = dataframe.copy()
                    self.file_id = uuid.uuid4()
                    st.session_state.report_generated = False

            except Exception as e:
                st.error(
                    "Please submit valid data schema. Use the above data schema file link as reference")

        st.divider()

        # Convert the 'IsSelected (Yes/No)' column to boolean
        df_copy['IsSelected (Yes/No)'] = df_copy['IsSelected (Yes/No)'].map(
            {'Yes': True, 'No': False})

        # Calculate the selection rate and impact ratio by Sex
        sex_categories = df_copy.groupby('Sex (Male/Female)').agg(Total=(
            'Sex (Male/Female)', 'size'), Selected=('IsSelected (Yes/No)', 'sum')).reset_index()
        # make sure there are two rows and if not enter zeros in the second row
        sex_categories["Selection_Rate"] = (
            sex_categories['Selected']/sex_categories['Total']).round(2)
        sex_categories['Impact_Ratio'] = (
            sex_categories['Selection_Rate']/max(sex_categories['Selection_Rate'])).round(3)

        embed_sex_table = Note(category='embed',
                               title='Audit metrics by category: Sex',
                               description='',
                               value=sex_categories.to_html())

        # Calculate the selection rate and impact ratio by Race/Ethnicity
        race_categories = df_copy.groupby('Race/Ethnicity').agg(Total=(
            'Race/Ethnicity', 'size'), Selected=('IsSelected (Yes/No)', 'sum')).reset_index()
        race_categories["Selection_Rate"] = (
            race_categories['Selected']/race_categories['Total']).round(2)
        race_categories['Impact_Ratio'] = (
            race_categories['Selection_Rate']/max(race_categories['Selection_Rate'])).round(3)

        embed_race_table = Note(category='embed',
                                title='Audit metrics by category: Race/Ethnicity',
                                description='',
                                value=race_categories.to_html())

        total_counts = df_copy.groupby(
            ['Sex (Male/Female)', 'Race/Ethnicity']).size().reset_index(name='Total Count')
        selected_df = df_copy[df_copy['IsSelected (Yes/No)']]
        total_selected = selected_df.groupby(
            ['Sex (Male/Female)', 'Race/Ethnicity']).size().reset_index(name='Total Selected')
        intersectional_counts = pd.merge(total_counts, total_selected, on=[
                                         'Sex (Male/Female)', 'Race/Ethnicity'], how='left')

        intersectional_counts["Selection Rate"] = (
            intersectional_counts['Total Selected']/intersectional_counts['Total Count']).round(2)
        intersectional_counts['Impact_Ratio'] = (
            intersectional_counts['Selection Rate']/max(intersectional_counts['Selection Rate'])).round(3)

        st.session_state.df_intersectional_counts = intersectional_counts.copy()

        # Calculating SELECTION RATE and IMPACT RATIO
        st.subheader("Calculating Selection Rate and Impact Ratio",
                     divider="orange")

        # Display the formulae for selection rate
        container = st.container(border=True)
        container.latex(
            r'''\text{SELECTION RATE} = \frac{Number\ of\ Selected}{Total\ Applicants}''')
        container.write(' \n')
        category = sex_categories.iloc[0, 0]
        container.markdown(
            f"<h5 style='text-align: center;'><u>For {category} applicants:</u></h5>", unsafe_allow_html=True)
        total_applicants = sex_categories.iloc[0, 1]
        sex_selected = sex_categories.iloc[0, 2]
        selection_rate = sex_categories.iloc[0, 3]
        latex_code = r'\text{SELECTION RATE} = \frac{Number\ of\ Selected\ }{Total\ Applicants} = \frac{' + \
            str(sex_selected) + \
            '}{' + str(total_applicants) + '} = ' + str(selection_rate)
        container.latex(latex_code)
        st.write(" ")

        # Display the formulae for impact ratio
        container = st.container(border=True)
        container.latex(
            r'''\text{IMPACT RATIO} = \frac{Selection\ Rate\ for\ a\ Category}{Selection\ Rate\ of\ the\ Most\ Selected\ Category}''')
        container.write(' \n')
        container.markdown(
            f"<h5 style='text-align: center;'><u>For {category} applicants:</u></h5>", unsafe_allow_html=True)
        impact_ratio = sex_categories.iloc[0, 4]
        max_selection_rate = max(sex_categories['Selection_Rate'])
        container.latex(r'\text{IMPACT RATIO} = \frac{Selection\ Rate\ for\ a\ Category}{Selection\ Rate\ of\ the\ Most\ Selected\ Category} = \frac{' +
                        str(selection_rate) + '}{' + str(max_selection_rate) + '}= '+str(impact_ratio))

        # Categories: SEX
        st.subheader("Audit metrics by category: Sex", divider="orange")

        sex_categories.fillna(0, inplace=True)
        race_categories.fillna(0, inplace=True)
        intersectional_counts.fillna(0, inplace=True)


        _, r, _ = st.columns([.4, .2, .4])
        # Display the table view
        st.write(" ")
        vmin = min(sex_categories["Impact_Ratio"])
        vmax = max(sex_categories["Impact_Ratio"])
        st.write(" ")
        st.dataframe(sex_categories.style.text_gradient(subset=[
                        "Impact_Ratio"], cmap="RdYlGn", vmin=vmin, vmax=vmax), width=700,  hide_index=True)

        # Race / Ethnicity Categories
        st.subheader("Audit metrics by category: Race/Ethnicity",
                     divider="orange")
        vmin = min(race_categories["Impact_Ratio"])
        vmax = max(race_categories["Impact_Ratio"])
        st.dataframe(race_categories.style.text_gradient(
            subset=["Impact_Ratio"], cmap="RdYlGn", vmin=vmin, vmax=vmax), hide_index=True)

        # Intersectional Categories
        st.subheader(
            "Audit metrics by category: Sex + Race/Ethnicity", divider="orange")

        vmin = min(intersectional_counts["Impact_Ratio"])
        vmax = max(intersectional_counts["Impact_Ratio"])
        st.dataframe(data=intersectional_counts.style.text_gradient(subset=[
                     "Impact_Ratio"], cmap="RdYlGn", vmin=vmin, vmax=vmax), hide_index=True)

        embed_sex_race_table = Note(category='embed',
                                    title='Audit metrics by category: Sex + Race/Ethnicity',
                                    description='',
                                    value=intersectional_counts.to_html())

        # Plot the impact ratio
        race_ethnicity = intersectional_counts['Race/Ethnicity'].unique()
        for i, race in enumerate(race_ethnicity):
            index = race.find('(')
            if i != -1:
                race_ethnicity[i] = race[:index]

        fig = px.histogram(intersectional_counts, x='Race/Ethnicity', y='Impact_Ratio',
                           color='Sex (Male/Female)', barmode='group', height=800)
        # embed_impact_ratio_chart = Note(category='plotly_chart', value=fig)

        st.markdown(
            f"<h4 style='text-align: center; text-shadow: 1px 1px 1px blue;'>Impact Ratio vs Race/Ethnicity</h4>", unsafe_allow_html=True)
        st.plotly_chart(fig, use_container_width=True)

        Path("data/AEDT/reports").mkdir(parents=True, exist_ok=True)

        generate_button, download_button, _, _ = st.columns([1, 1, 1, 2])
        generate_report_button = generate_button.button(
            "Generate Report", key="generate_report_button", use_container_width=True)


        if generate_report_button or ("report_generated" in st.session_state and st.session_state.report_generated == True):
            st.session_state.report_generated = True

            logger.info("Generating Bias Audit Report")
            
            self.report_generator = ReportGenerator(name="Bias Audit for Client XYZ Corp.", version="1.0",
                                        category="basic", owner='Sri Krishnamurthy', contact='info@qusandbox.com')
            self.report_generator.load(self.template_input)

            self.report_generator.add_note(embed_sex_table)
            self.report_generator.add_note(embed_race_table)
            self.report_generator.add_note(embed_sex_race_table)
            # self.report_generator.add_note(embed_impact_ratio_chart)

            self.report_generator.generate()
            self.report_generator.save(Path(f"data/AEDT/reports/{self.file_id}.html"))

            # put in s3
            self.s3_file_manager.upload_file(
                open(Path(f"data/AEDT/reports/{self.file_id}.html"), "rb"), f"qu-aedt/test/reports/{st.session_state.user_info['email']}/{self.file_id}.html")
            st.success("Report saved successfully")

            download_button.download_button("Download Report", open(Path(
                f"data/AEDT/reports/{self.file_id}.html"), 'rb'), file_name="Bias Audit Report.html", mime='text/html', use_container_width=True)
