import streamlit as st
from src.s3.s3FileManager import S3FileManager
import datetime


class MyReports:
    def __init__(self):
        self.s3_file_manager = S3FileManager()

    def display_report(self, report):
        name_col, date_col, size_col, delete_button_col, download_button_col = st.columns([
                                                                                          4, 2, 2, 1, 1])
        file_name = report[0][report[0].rindex('/')+1:]
        date = report[1]
        # convert time to day, month, date, time
        date = date.strftime("%d-%m-%Y %H:%M")

        size = report[2]
        size = size/1024
        size = str(round(size, 2)) + " KB"
        name_col.write(file_name)
        date_col.write(date)
        size_col.write(size)
        if delete_button_col.button("Delete", key=f"{file_name}_delete_button", type="primary", use_container_width=True):
            self.s3_file_manager.delete_report(
                report[0], st.session_state.user_info['email'])
            st.rerun()
        temp_dir = self.s3_file_manager.download_file_in_temp(
            f"{report[0]}")
        download_button_col.download_button(label="Download", data=open(
            f"{temp_dir}/{file_name}", 'rb').read(), file_name=file_name, key=f"{file_name}_download_button", use_container_width=True)
        st.divider()

    def main(self):
        # fetch reports
        # display reports - delete , rename, download report, view report in new tab.
        st.header("My Reports", divider='blue')
        reports = self.s3_file_manager.get_reports_list(
            st.session_state.user_info['email'])
        reports.sort(key=lambda x: x[1], reverse=True)
        if len(reports) == 0:
            st.write("No reports available.")
        else:
            name_col, date_col, size_col, delete_button_col, download_button_col = st.columns([
                4, 2, 2, 1, 1])
            name_col.markdown("**Name**", )
            date_col.markdown("**Created at**")
            size_col.markdown("**Size**")
            delete_button_col.markdown("**Delete**")
            download_button_col.markdown("**Download**")
            st.divider()
            for report in reports:
                self.display_report(report)
