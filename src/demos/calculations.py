# Import the required libraries
import os
import base64
import datetime
from pathlib import Path
import matplotlib.pyplot as plt
import streamlit as st
import pandas as pd
import plotly.express as px
from src.report.qu_audit import *
import uuid
import plotly
from src.s3.s3FileManager import S3FileManager
import datetime



class BiasAuditCalculations:
    """
    Class to perform bias audit calculations.
    """

    def main(self):
        """
        Main function to perform bias audit calculations.
        """

        if "fields_selected" not in st.session_state:
            st.session_state.fields_selected = False

        if "report_notes" not in st.session_state:
            st.session_state.report_notes = {}

        if "click_count" not in st.session_state:
            st.session_state.click_count = 0

        st.header("Bias Audit Reporting Tool", divider='blue')

        data = None

        # checkbox to upload data or use sample data
        use_sample_data = st.checkbox("Use Sample Data")
        st.write("OR")
        bin_file = 'data/AEDT/dataSchema.csv'
        with open(bin_file, 'rb') as f:
            sample_file_data = f.read()
        bin_str = base64.b64encode(sample_file_data).decode()
        href = f'<a href="data:application/octet-stream;base64,{bin_str}" download="{os.path.basename(bin_file)}">this sample file</a>'
        st.markdown(f"""Upload your own data to perform the audit. The data should at least contain these columns: Race, Gender, Disability, Protected Class and Selected. The last column indicates whether the applicant was selected or not. You can use {href} to format your data appropriately""", unsafe_allow_html=True)

        
        # upload data file
        uploaded_file = st.file_uploader("Upload your data file", type=["csv", "xlsx"])
        if uploaded_file:
            try:
                if uploaded_file.name.endswith('.csv'):
                    data = pd.read_csv(uploaded_file)
                else:
                    data = pd.read_excel(uploaded_file)
                st.success("Data successfully uploaded!")
                st.write("Preview:")
                st.dataframe(data.head())
            except Exception as e:
                st.error("Error uploading file. Please check the format and try again.")
                st.error(e)


        if use_sample_data:
            data = pd.read_csv("data/AEDT/data.csv")
            st.write("Sample Data Preview:")
            st.dataframe(data.head())

        def calculate_selection_rates(data, category_col, selected_col, selected_value):
            
            st.subheader(f"Selection Rates for {category_col}", divider='orange')
            st.write("The selection rates are calculated as follows:")
            st.latex(r"\text{Selection Rate} = \frac{\text{Number of Selected}}{\text{Total Applicants}}")
            
            # create a copy of the data
            data_copy = data.copy()

            # normalize the data by the selected value to be true and the other to be false
            data_copy[selected_col] = data_copy[selected_col].apply(lambda x: 1 if x == selected_value else 0)
            
            # calculate the selection rates
            selection_rates = data_copy.groupby(category_col)[selected_col].mean()
            # round it to four decimal places
            selection_rates = selection_rates.round(4)

            #  label the columns appropriately as the name of the category and the selected column
            selection_rates.index.name = category_col
            selection_rates.name = selected_col

            # add the total for the selection rates and the selected total per category
            total_by_category = data[category_col].value_counts()
            total_selected_by_category = data.groupby(category_col)[selected_col].value_counts().unstack().fillna(0)

            # reorder the rows so that the one with the 
            selection_rates = pd.concat([selection_rates, total_by_category, total_selected_by_category], axis=1)

            # label the columns appropriately
            selection_rates.columns = ["Selection Rate", "Total Applicants", selection_rates.columns[-2], selection_rates.columns[-1]]

            # reorder the columns in the following order: Yes, No, Total, selection_rate
            selection_rates = selection_rates[[selection_rates.columns[-2], selection_rates.columns[-1], "Total Applicants", "Selection Rate"]]

            # reset the index as a new column
            selection_rates.reset_index(inplace=True)
            
            return pd.DataFrame(selection_rates)


        def calculate_impact_ratios(selection_rates, category_col, selected_col, selected_value):
            st.subheader(f"Impact Ratios for {category_col}", divider='orange')
            st.write("The impact ratios are calculated as follows:")
            st.latex(r"\text{Impact Ratio} = \frac{\text{Selection Rate for a category}}{\text{Selection Rate for most selected category}}")
            
            # create a copy of the selection rates
            selection_rates = selection_rates.copy()
            
            # calculate the impact ratios
            selection_rates['Impact Ratio'] = selection_rates["Selection Rate"] / selection_rates["Selection Rate"].max()

            # round it to 4 decimals
            selection_rates['Impact Ratio'] = selection_rates['Impact Ratio'].round(4)

            return pd.DataFrame(selection_rates)


        def plot_graph(data, x_col, y_col):
            fig = px.bar(data, x=x_col, y=y_col, title=f"{y_col} by {x_col}", labels={y_col: y_col, x_col: x_col}, width=1000, height=700)
            # make each bar have diffferent color
            fig.update_traces(marker_color=px.colors.sequential.Plasma)
            st.plotly_chart(fig)
            return fig


        def validate_fields(form_data: dict):
            if not form_data['agree_terms']:
                return False, "Please agree to the terms and conditions."
            # check if all the fields are filled
            if not all(form_data.values()):
                return False, "Please fill in all the fields."
            elif not form_data["agree_terms"]:
                return False, "Please agree to the terms and conditions."
            # validate company email
            elif not form_data["company_email"].endswith(".com") or "@" not in form_data["company_email"]:
                return False, "Please enter a valid company email."
            # validate phone number
            elif not form_data["company_phone"].startswith("+") or not form_data["company_phone"].replace("+", "").isdigit():
                return False, "Please enter a valid company phone number. The number should start with +1 and not contain any spaces. (For example: +19877899876)"
            # validate auditor email
            elif not form_data["auditor_email"].endswith(".com") or "@" not in form_data["auditor_email"]:
                return False, "Please enter a valid auditor email."
            # validate phone number
            elif not form_data["auditor_phone"].startswith("+") or not form_data["auditor_phone"].replace("+", "").isdigit():
                return False, "Please enter a valid auditor phone number. The number should start with +1 and not contain any spaces. (For example: +19877899876)"
            return True, "All fields are valid."
            
            

        def category_expander(id, data):
            if data is not None:
                columns = list(data.columns)
                category_col = st.selectbox("Select the column to group by category (Race/Sex/Disability/Protected Class):", ["Select"] + columns, help="This column can be either the sex, race, disability status, or the protected class of the applicants.", key=f"{id}_category")
                selected_col = st.selectbox("Select the column in the data that indicates whether the applicant was selected or not:", ["Select"] + columns, help="This column should be the one that indicates whether the applicant was selected or not.", key=f"{id}_selected")
                if selected_col != "Select":
                    selected_value = st.selectbox("Select the value that indicates that the person was Selected (1/Yes/Y/Selected)", ["Select"] + list(data[selected_col].unique()), help="This is the value that indicates that the applicant was selected. Can be 1, 'Yes', 'Y', 'Selected' etc. Cannot be 0, 'No', 'N', 'Not Selected'.", key=f"{id}_selected_value")
                if category_col == selected_col:
                    st.session_state.fields_selected = False
                    st.info("Category and Selected columns cannot be the same. Please select different columns.")
                elif category_col not in data.columns or selected_col not in data.columns:
                    st.session_state.fields_selected = False
                    st.info("Choose the other column.")
                elif data[category_col].nunique() > 100:
                    st.session_state.fields_selected = False
                    st.warning("The number of categories is too high to generate a report. Please choose a column with fewer categories. Refer to the help text for more information.")
                elif data[selected_col].nunique() > 2:
                    st.session_state.fields_selected = False
                    st.warning("The selected column should have only two unique values indicating whether the applicant was selected or not. Please choose a different column. Please refer to the help text for more information.")
                elif selected_value == "Select":
                    st.session_state.fields_selected = False
                    st.info("Please select the value that indicates that the applicant was selected in the selected column.")
                else:
                    st.session_state.fields_selected = True  


                if st.session_state.fields_selected == True:
                    # calculate the selection rates
                    selection_rates = calculate_selection_rates(data, category_col, selected_col, selected_value)
                    st.write(f"Selection Rates for {category_col}:")
                    st.dataframe(selection_rates.style.text_gradient(subset=[
                                    "Selection Rate"], cmap="RdYlGn", 
                                    vmin=min(selection_rates["Selection Rate"]), 
                                    vmax=max(selection_rates["Selection Rate"])))     
                    

                    # plot the selection rates
                    plot = plot_graph(selection_rates, category_col, "Selection Rate")
                    # TODO st.session_state.report_notes.append(Note(category='plotly_chart', value=plot)) # not working because of internal server error for qu_audit
                    
                    # calculate the impact ratios
                    impact_ratios = calculate_impact_ratios(selection_rates, category_col, selected_col, selected_value)
                    st.write(f"Impact Ratios for {category_col}:")
                    
                    st.dataframe(impact_ratios.style.text_gradient(subset=[
                                        "Impact Ratio"], cmap="RdYlGn", 
                                        vmin=min(impact_ratios["Impact Ratio"]), 
                                        vmax=max(impact_ratios["Impact Ratio"])))
                    st.session_state.report_notes[f"audit_{id}_impact"] = Note(category='embed', title=f'Impact Ratios for {category_col}', value=impact_ratios.to_html(), description='Impact ratios for the categories in the dataset.')
                    
                    # plot the impact ratios
                    plot = plot_graph(impact_ratios, category_col, "Impact Ratio")
                    # TODO st.session_state.report_notes.append(Note(category='plotly_chart', value=plot))


        if data is not None:
            st.subheader("Audit Calculator", divider='orange')
            
            instruction_col, button_col = st.columns([3, 1])
            with instruction_col:
                st.write("Click on the \"Add New Category\" button to add a new category to audit. You can add multiple audits to compare the selection rates and impact ratios.")
            with button_col:
                add_audit_button = st.button("Add New Category", key="add_audit", use_container_width=True, type="primary")
            
            if add_audit_button:
                st.session_state.click_count += 1

            st.divider()

            for i in range(st.session_state.click_count):
            
                subheader_col, remove_button_col = st.columns([3, 1])
                with subheader_col:
                    st.subheader(f"Category {i+1}:")
                with remove_button_col:
                    remove_audit_button = st.button("Remove", key=f"remove_audit_{i}", use_container_width=True, type="secondary")
                if remove_audit_button:
                    st.session_state.click_count -= 1
                    st.session_state.fields_selected = False
                    st.rerun()
                category_expander(i, data)
                st.write("---")



            # Report
            if len(st.session_state.report_notes) > 0:
                st.subheader("Bias Audit Report", divider='orange')
                st.write("Enter the following information to generate the report:")

                form = st.form(key="report_form")

                form.write("Company Information")
                col1, col2 = form.columns(2)
                # company information
                company_name = col1.text_input("Enter the name of the company:", placeholder="XYZ Company")
                company_address = col2.text_input("Enter the address of the company:", placeholder="123 XYZ st, City, Country")
                company_website = col1.text_input("Enter the website of the company:", placeholder="www.xyzcompany.com")
                company_email = col2.text_input("Enter the email of the company:", placeholder="abx@xyz.com")
                company_phone = col1.text_input("Enter the phone number of the company:", placeholder="+1234567890")
                company_industry = col2.text_input("Enter the industry of the company:", placeholder="Technology")

                form.divider()
                form.write("Data Information")

                # data information
                data_source = form.text_input("Enter the source of the data:", placeholder="ATS of the XYZ Company")
                data_description = form.text_area("Enter a brief description of the data:", placeholder="This dataset contains information about the applicants for the XYZ Company.")
                data_remarks = form.text_area("Enter any remarks about the data:", placeholder="The data is collected from the ATS of the XYZ Company.")

                form.divider()
                form.write("Auditor Information")
                # auditor information
                col1, col2 = form.columns(2)
                auditor_name = col1.text_input("Enter the name of the auditor:", placeholder="John Doe")
                auditor_position = col2.text_input("Enter the position of the auditor:", placeholder="Data Analyst")
                auditor_email = col1.text_input("Enter the email of the auditor:", placeholder="abc@xyz.com")
                auditor_phone = col2.text_input("Enter the phone number of the auditor:", placeholder="+1234567890")

                form.divider()
                form.write("Tool Information")
                # Tool information
                col1, col2 = form.columns(2)
                tool_name = col1.text_input("Enter the name of the tool that is being audited:", placeholder="AEDT tool")
                tool_owner = col2.text_input("Enter the owner/vendor of the tool that is being audited:", placeholder="XYZ")
                tool_description = form.text_area("Enter a brief description of the tool:", placeholder="This tool is used to automate the hiring process for the XYZ Company.")


                form.divider()
                # terms and conditions checkbox
                agree_terms = form.checkbox("By clicking here, you agree that the audit was performed independently by the abovementioned individual with the help of QuantUniversity's AlgoAudit Tool.")

                form_data = {
                    "company_name": company_name,
                    "company_address": company_address,
                    "company_website": company_website,
                    "company_email": company_email,
                    "company_phone": company_phone,
                    "company_industry": company_industry,
                    "data_source": data_source,
                    "data_description": data_description,
                    "data_remarks": data_remarks,
                    "auditor_name": auditor_name,
                    "auditor_position": auditor_position,
                    "auditor_email": auditor_email,
                    "auditor_phone": auditor_phone,
                    "agree_terms": agree_terms,
                    "tool_name": tool_name,
                    "tool_owner": tool_owner,
                    "tool_description": tool_description
                }

                generate_report = form.form_submit_button("Generate Report")
                

                if generate_report:
                    valid_fields, response = validate_fields(form_data)
                    if not valid_fields:
                        form.warning(response)
                    else:
                        file_id = uuid.uuid4()
                        template_id = "ff14ff4225804f6f8f787f22460e1f63"
                        template_reader = TemplateReader(template_id)
                        template_reader.load()
                        # Calculate the date 1 year from today
                        audit_date = datetime.datetime.now().strftime("%Y-%m-%d")
                        one_year_from_now = (datetime.datetime.now() + datetime.timedelta(days=365)).strftime("%Y-%m-%d")

                        template_input = {
                            # "Introduction": f"This report presents the results of a \"Bias Audit\" by QuantUniversity, LLC conducted by {auditor_name} in accordance with the New York City's Automated Employment Decision Tools ordinance (Local Law 144, Int. 1894-2020) (herein \"New York City Ordinance\") of {company_name}'s use of the {tool_name}."
                            "Introduction": f"This report presents the findings from the bias audit conducted for {company_name}, as per the requirements of Local Law 144 of 2021 of New York City. This legislation necessitates that automated employment decision tools (AEDTs) used within New York City be subject to an annual bias audit. The law's primary goal is to ensure these tools do not perpetuate bias or discrimination in employment practices. The audit aims to evaluate the tool against rigorous standards to ensure it operates fairly and equitably. This is essential in maintaining the integrity of employment processes and protecting potential employees from discriminatory practices facilitated by automated tools. By adhering to the stipulations of Local Law 144, companies demonstrate their commitment to fair employment practices and ethical use of technology. This report details the process followed during the audit, the findings, and the conclusions drawn regarding the compliance of {company_name} with the specified legal requirements.",
                            "Analysis Information": f"The audit was performed by {auditor_name}, who holds the position of {auditor_position} at our firm. With extensive experience in conducting bias audits, {auditor_name} brings a depth of understanding and expertise to the evaluation process, ensuring thorough and accurate compliance checks are made against Local Law 144. Contact details for further communication regarding this audit are as follows: Email - {auditor_email}, Phone - {auditor_phone}. For any clarifications or additional information requests, please feel free to reach out to the auditor directly. The methodology adopted for the audit included a comprehensive analysis of the tool's design, deployment, and operational data. This process ensures that all aspects of the tool's impact on employment decisions are scrutinized and evaluated for any potential biases.",
                            "Audit Conducted on:": audit_date,
                            "Audit Distribution Range": f"The audit is valid from {audit_date} to {one_year_from_now}.",
                            "Purpose": f"The primary purpose of this audit is to assess the selection rates and impact ratios of the automated decision-making tool \"{tool_name}\" used by {company_name}. This assessment is critical in identifying any biases that could adversely affect candidates based on protected categories such as sex, race/ethnicity, or other intersectional factors. This audit also serves to verify that {company_name} is in full compliance with the applicable laws and ethical guidelines concerning the use of automated tools in employment decisions. By conducting this audit, the company aims to uphold its commitment to fair and equitable employment practices. The findings from this audit are intended to guide {company_name} in making informed decisions about the deployment and continued use of \"{tool_name}\". Recommendations for improvements or modifications to the tool may also be provided to ensure ongoing compliance and enhancement of fairness in its application.",
                            "Audit Information": f"The audit was conducted on {audit_date}, with the full cooperation of {company_name}. The process involved both quantitative analyses of the tool's output and qualitative assessments of its deployment environment and use cases. Audited by {auditor_name}, the audit strictly adhered to the guidelines and requirements set forth by Local Law 144 of 2021. The auditor's qualifications and position ensure a high standard of scrutiny and objectivity in the audit process. Documentation of the audit process, methodologies used, and criteria for evaluation are maintained meticulously. These documents are available for review upon request, providing transparency and accountability in the audit process.",
                            "About the Company": f"{company_name} is located at {company_address}, with a robust online presence indicated by their website: {company_website}. For direct inquiries, they can be contacted via email at {company_email} or by phone at {company_phone}. The company operates within the {company_industry} industry, where the use of automated tools for employment decisions is increasingly prevalent. As a participant in this industry, {company_name} recognizes the importance of maintaining fair employment practices and adheres to all relevant regulations and ethical standards. This commitment is reflected in their proactive approach to conducting annual bias audits. The information provided here outlines the company's dedication to transparency and compliance in all its operations, particularly in the utilization of technology within its hiring processes.",
                            "Tool being audited": f"The tool under audit, \"{tool_name}\", is owned by {tool_owner}. This tool is designed to assist in the automation of employment decisions, using sophisticated algorithms to analyze applicant data and make recommendations or decisions. \"{tool_name}\" is intended to streamline the hiring process while enhancing the objectivity and fairness of employment decisions. However, to ensure that the tool does not inadvertently introduce or perpetuate bias, it undergoes a rigorous audit process. The description provided helps stakeholders understand the tool's functionality and the significance of the audit in ensuring that its operations remain within the bounds of legal and ethical standards.",
                            "Tool Description": tool_description,
                            "Data Information": f"The audit examined data sourced from {data_source}, described in the following \"Data Description\" section. Remarks on the data, provided in the audit documentation, are included in the \"Remarks on Data Provided\", highlighting specific areas of focus or concern during the audit.This section of the report emphasizes the criticality of data quality and relevance in the operation of automated employment decision tools. The integrity and appropriateness of the data used directly influence the fairness and effectiveness of the tool. The thorough documentation of the data source, description, and any pertinent remarks ensure a transparent audit trail. This transparency is crucial in validating the audit findings and providing a foundation for any recommendations made.",
                            "Data Description": data_description,
                            "Remarks on Data Provided": data_remarks,
                        }
                        
                        
                        report_generator = ReportGenerator(name=f"Bias Audit for Client {company_name}.", version="1.0",
                                                            category="basic")
                        
                        report_generator.load(template_input)

                        for note in st.session_state.report_notes.values():
                            
                            report_generator.add_note(note)

                        
                        report_generator.generate()
                        Path(f"data/AEDT/reports").mkdir(parents=True, exist_ok=True)
                        report_generator.save(Path(f"data/AEDT/reports/{file_id}.html"))

                        st.success("The report has been generated and saved successfully.")

                        # put in s3
                        s3_file_manager = S3FileManager()

                        # TODO change email
                        s3_file_manager.upload_file(
                            open(Path(f"data/AEDT/reports/{file_id}.html"), "rb"), f"qu-aedt/test/reports/{st.session_state.user_info['email']}/{file_id}.html")

                        st.download_button("Download Report", open(Path(
                            f"data/AEDT/reports/{file_id}.html"), 'rb'), file_name="Bias Audit Report.html", mime='text/html', use_container_width=True)
