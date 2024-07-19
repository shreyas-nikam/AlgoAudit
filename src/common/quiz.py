# Import the required libraries
import uuid
from datetime import date
import pandas as pd
import json
import random
import streamlit as st
import cv2
import base64
import os


class Quiz:
    """
    This class is used to display the quiz in the Streamlit app.

    Attributes:
    questions (dict): The dictionary of questions.
    """

    def __init__(self):
        """
        The constructor for the Quiz class.
        """
        self.questions = json.load(
            open(st.session_state.config_param["QUESTIONS_FILE"]))
        self.NUM_QUESTIONS_TO_SOLVE = int(
            st.session_state.config_param["QUIZ_TOTAL_QUES"])
        self.interaction_table_name: str = st.session_state.config_param[
            "USER_QUIZ_INTERACTION_TABLE_NAME"]
        self.results_table_name: str = st.session_state.config_param["QUIZ_RESULT_TABLE_NAME"]

    def main(self):
        """
        The main function to display the quiz in the Streamlit app.
        """

        def get_binary_file_downloader_html(bin_file, file_label='File'):
            """
            Function to download the binary file.
            """
            with open(bin_file, 'rb') as f:
                data = f.read()
            bin_str = base64.b64encode(data).decode()
            href = f'<a href="data:application/octet-stream;base64,{bin_str}" download="{os.path.basename(bin_file)}"> Download {file_label}</a>'
            return href

        def get_question():
            """
            Function to get the question.
            """
            curr_module = st.session_state.curr_module
            st.session_state.ques_per_module

            if sum(st.session_state.ques_count_per_module) != 0:
                for _ in range(len(st.session_state.ques_count_per_module)):
                    curr_module = (
                        curr_module + 1) % len(st.session_state.ques_count_per_module)
                    if st.session_state.ques_count_per_module[curr_module] != 0:
                        break
                ques = st.session_state.ques_per_module[curr_module].pop(
                    random.randrange(len(st.session_state.ques_per_module[curr_module])))
                st.session_state.ques_count_per_module[curr_module] -= 1
                st.session_state.curr_module = curr_module
            return ques

        # Initialize session state variables if they don't exist yet
        if "ques_count_per_module" not in st.session_state:
            st.session_state.ques_count_per_module = []
            st.session_state.ques_per_module = []
            st.session_state.module_history = []
            for key in self.questions.keys():
                st.session_state.ques_per_module.append(
                    self.questions[key].copy())
                st.session_state.ques_count_per_module.append(
                    len(self.questions[key]))
                st.session_state.module_history.append([key, 0, 0])

        # Initialize the current question
        if "current_question" not in st.session_state:
            st.session_state.answers = {}
            st.session_state.current_question = 0
            st.session_state.questions = []
            st.session_state.right_answers = 0
            st.session_state.wrong_answers = 0
            st.session_state.done_with_quiz = False
            st.session_state.name = ""
            st.session_state.curr_module = -1

        if "show_explanation" not in st.session_state:
            st.session_state.show_explanation = False

        # Define a function to go to the next question
        def next_question():
            # Move to the next question in the questions list
            st.session_state.current_question += 1

            # If we've reached the end of the questions list, get a new question
            if st.session_state.current_question > len(st.session_state.questions) - 1:
                next_question = get_question()
                st.session_state.questions.append(next_question)
            st.rerun()

        # Display the summary of the performance
        def display_summary():
            df = pd.DataFrame(st.session_state.module_history)
            df.columns = ["Module Name", "Correct", "Total"]

            df["Percentage"] = round((df["Correct"]/df["Total"])*100, 2)

            def categorize_percent(percent):
                if percent > 75:
                    return 'Good'
                elif percent < 25:
                    return 'Bad'
                else:
                    return 'Moderate'

            df["Comment"] = ((df["Correct"]/df["Total"]) *
                             100).apply(lambda x: categorize_percent(x))

            _, tbl, _ = st.columns([.1, .8, .1])
            tbl.dataframe(df, use_container_width=True, hide_index=True)

        st.header("Quiz", divider="blue")

        # Check if the user exists using the id and the app code
        exists = st.session_state.supabaseDB.table(
            self.results_table_name).select("*").eq('user_id', st.session_state.user_info['id']).eq('app_code', st.session_state.config_param["APP_CODE"]).execute()
        if len(exists.data) != 0:
            st.subheader("Here is your certificate:", divider="grey")
            certi = cv2.imread(
                st.session_state.config_param["CERTIFICATE_PATH"])
            font = cv2.FONT_HERSHEY_COMPLEX
            fontScale = 2
            original = cv2.putText(certi, st.session_state.user_info['name'], (
                50, 380), font, fontScale, (0, 0, 0), thickness=2)

            original = cv2.putText(original, "Recorded on: "+date.today().strftime(
                '%B %d, %Y'), (850, 680), font, 0.7, (0, 0, 0), thickness=1)
            cv2.imwrite("Certificate.jpg", original)
            st.image("Certificate.jpg", use_column_width=True)
            st.markdown(get_binary_file_downloader_html(
                'Certificate.jpg', 'Certificate'), unsafe_allow_html=True)
            st.session_state.done_with_quiz = True
        else:

            # After getting 68% questions correct and attempting at least 20 questions, display a certificate
            if st.session_state.current_question >= st.session_state.config_param["QUIZ_TOTAL_QUES"] and st.session_state.right_answers/st.session_state.current_question >= 0.68:
                st.balloons()
                st.success("Congratulations! You have passed the quiz.")
                st.subheader("Summary", divider="grey")
                display_summary()

                result_data = {
                    'app_code': st.session_state.config_param["APP_CODE"],
                    'user_id': st.session_state.user_info['id'],
                    'right_answer': st.session_state.right_answers,
                    'total_attempted': st.session_state.current_question
                }
                st.session_state.supabaseDB.table(
                    self.results_table_name).insert(result_data).execute()

                st.subheader("Here is your certificate:", divider="grey")
                certi = cv2.imread(
                    st.session_state.config_param["CERTIFICATE_PATH"])
                font = cv2.FONT_HERSHEY_COMPLEX
                fontScale = 2
                original = cv2.putText(certi, st.session_state.user_info['name'], (
                    50, 380), font, fontScale, (0, 0, 0), thickness=2)

                original = cv2.putText(original, "Recorded on: "+date.today().strftime(
                    '%B %d, %Y'), (850, 680), font, 0.7, (0, 0, 0), thickness=1)
                cv2.imwrite("Certificate.jpg", original)
                st.image("Certificate.jpg", use_column_width=True)
                st.markdown(get_binary_file_downloader_html(
                    'Certificate.jpg', 'Certificate'), unsafe_allow_html=True)
                st.session_state.done_with_quiz = True

            # If the user has not yet completed the quiz, display the next question
            else:
                # display_question()
                if len(st.session_state.questions) == 0:
                    question = get_question()
                    st.session_state.questions.append(question)

                # Disable the submit button if the user has already answered this question
                submit_button_disabled = st.session_state.current_question in st.session_state.answers

                # Get the current question from the questions list
                question = st.session_state.questions[st.session_state.current_question]

                # Get Module name
                module_name = st.session_state.module_history[st.session_state.curr_module][0]

                # Display the question prompt
                st.write(
                    f"{st.session_state.current_question + 1}. {question['question']} [Module: {module_name}]")

                # Use an empty placeholder to display the radio button options
                # options = st.empty()

                # Display the radio button options and wait for the user to select an answer
                user_answer = st.radio(
                    "Your answer:", question["options"], key=st.session_state.current_question, disabled=submit_button_disabled)
                selected_index = question["options"].index(user_answer)
                col1, _, col2 = st.columns([1, 3, 1])

                with col1:
                    # Display the submit button and disable it if necessary
                    submit_button = st.button(
                        "Submit Answer", type="primary", disabled=submit_button_disabled, use_container_width=True)

                with col2:
                    # Skip Question
                    if st.button("Next Question", type="primary", disabled=st.session_state.done_with_quiz or not submit_button_disabled, use_container_width=True):
                        st.session_state.show_explanation = False
                        next_question()

                results_placeholder = st.empty()
                # If the user clicks the submit button, check their answer and show the explanation
                answer_option = {0: 'a', 1: 'b', 2: 'c', 3: 'd'}
                if submit_button:
                    # Record the user's answer in the session state
                    st.session_state.answers[st.session_state.current_question] = question["options"].index(
                        user_answer)
                    if answer_option[selected_index] == question["answer_option"]:
                        st.session_state.right_answers += 1
                        st.session_state.module_history[st.session_state.curr_module][1] += 1
                        st.session_state.module_history[st.session_state.curr_module][2] += 1
                    else:

                        st.session_state.wrong_answers += 1
                        st.session_state.module_history[st.session_state.curr_module][2] += 1
                    db_data = {
                        'user_id': st.session_state.user_info['id'],
                        'question_id': question['uuid'],
                        'user_response': answer_option[selected_index],
                        'result': "Correct" if answer_option[selected_index] == question["answer_option"] else "Incorrect",
                        'app_code': st.session_state.config_param["APP_CODE"]
                    }
                    st.session_state.supabaseDB.table(
                        self.interaction_table_name).insert(db_data).execute()
                    st.session_state.show_explanation = True
                    st.rerun()

                    # Show an expander with the explanation of the correct answer
                if st.session_state.show_explanation:
                    with st.expander("Explanation"):
                        # Check if the user's answer is correct and update the score
                        if answer_option[selected_index] == question["answer_option"]:
                            results_placeholder.subheader("Correct!")
                        else:
                            results_placeholder.subheader("Incorrect!")
                            st.markdown(
                                f":blue-background[Sorry, the correct answer was \n {question['answer_option']}.]")
                        st.write(question["explanation"])
                    st.header(
                        f"Score: {st.session_state.right_answers} / {st.session_state.current_question + 1}")

                # Display the current score at the bottom of the page
                st.success(f"Correct answers: {st.session_state.right_answers}")
                st.error(f"Wrong answers: {st.session_state.wrong_answers}")
