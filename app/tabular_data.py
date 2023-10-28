"""Provides functionality for working with tabular data."""

import logging
import os

from bq import generate_create_table_sql
from bq import run_query
from dotenv import load_dotenv
from llm import add_cap_ref
from llm import prompt_llm
from utils.file_utils import read_file_to_string


load_dotenv()

GOOGLE_CLOUD_BIGQUERY_TABLE = os.getenv("GOOGLE_CLOUD_BIGQUERY_TABLE")
NUMBER_OF_ATTEMPTS_TO_FIX_SQL_QUERY_ERRORS = os.getenv(
    "NUMBER_OF_ATTEMPTS_TO_FIX_SQL_QUERY_ERRORS",
)
CONTEXT_FOR_SQL_QUERY_PROMPT = read_file_to_string(
    "./prompt_pieces/prompt_for_sql_query/context.txt",
)
EXTRA_INSTRUCTIONS_FOR_SQL_QUERY_PROMPT = read_file_to_string(
    "./prompt_pieces/prompt_for_sql_query/extra_instructions.txt",
)
EXAMPLES_FOR_SQL_QUERY_PROMPT = read_file_to_string(
    "./prompt_pieces/prompt_for_sql_query/examples.txt",
)
CONTEXT_FOR_SQL_QUERY_EXPLANATION = read_file_to_string(
    "./prompt_pieces/prompt_for_sql_query_explanation/context.txt",
)
EXTRA_INSTRUCTIONS_FOR_SQL_QUERY_EXPLANATION = read_file_to_string(
    "./prompt_pieces/prompt_for_sql_query_explanation/extra_instructions.txt",
)
COLUMN_DESCRIPTION = read_file_to_string("./prompt_pieces/columns_description.txt")
TABLE_DEFINITIONS = generate_create_table_sql(GOOGLE_CLOUD_BIGQUERY_TABLE)


def get_tabular_data(question):
    # generating prompt to llm for geting sql query
    prompt_for_sql_query = prompt_for_sql_query_builder(question)
    logging.info("🗣️ user input:\n%s", prompt_for_sql_query)

    # sending prompt to llm expecting to get sql query in response
    sql_query = prompt_llm(prompt_for_sql_query)
    logging.info("🤖 llm answer SQL query:\n%s", sql_query)

    # running returned query on the database
    was_query_successfull, bq_answer = run_query(sql_query)

    # if there were errors when running the query, ask llm to fix it
    # giving it the entire context of previous attempts
    if not was_query_successfull:
        previous_fix_attempts_sql = [sql_query]
        previous_fix_attempts_db_error = [bq_answer]
        for _ in range(int(NUMBER_OF_ATTEMPTS_TO_FIX_SQL_QUERY_ERRORS)):
            # generating propmpt and sanding it to llm expecting to get
            # response form db after correctly executed
            (
                was_query_successfull,
                bq_answer,
                sql_query,
            ) = attempts_to_fix_sql_query_errors(
                question,
                bq_answer,
                sql_query,
                previous_fix_attempts_sql,
                previous_fix_attempts_db_error,
            )
            if was_query_successfull:
                break

            previous_fix_attempts_sql.append(sql_query)
            previous_fix_attempts_db_error.append(bq_answer)

    if not was_query_successfull:
        # if all attempts of rebuilding query faild sending appropriate response to user
        logging.info(
            "🗣️ user input:\n %s\n🤖 generated SQL query: %s",
            question,
            sql_query,
        )
        logging.info(
            "💔 Model faild to generate correct query in %s attempts",
            NUMBER_OF_ATTEMPTS_TO_FIX_SQL_QUERY_ERRORS,
        )
        return (
            False,
            "Przepraszam nie udało się utworzyć odpowiedniego zapytania SQL",
            bq_answer,
            sql_query,
        )

    # generating prompt and sanding it to llm for geting explenation of
    # what will be seen in final response table
    prompt_for_sql_query_explenation = prompt_for_sql_query_explenation_builder(
        sql_query,
        question,
    )
    logging.info(
        "🔄 sending prompt for generating sql query explanation:\n %s",
        prompt_for_sql_query_explenation,
    )
    llm_response_sql_query_explained = prompt_llm(prompt_for_sql_query_explenation)

    logging.info(
        "🗣️ user input:\n%s\n🤖 generated SQL query:%s",
        question,
        sql_query,
    )
    return True, llm_response_sql_query_explained, bq_answer, sql_query


def attempts_to_fix_sql_query_errors(
    question,
    error_message,
    sql_query,
    previous_fix_attempts_sql,
    previous_fix_attempts_db_error,
):
    # If there were errors in the query, we send a request to llm
    # to correct the error max NUMBER_OF_ATTEMPTS_TO_FIX_SQL_QUERY_ERRORS times.
    prompt = """
context: You are a reliable data science expert who corrects errors in
Google Cloud BigQuery queries.
"""
    if len(previous_fix_attempts_db_error) > 1:
        prompt += """\nYou already tried fixing SQL_QUERY but it didn't work.
        Very important! All queries below are wrong you can not write a query
        that is the same!
        """
        for sql, error in zip(
            previous_fix_attempts_sql[:-1],
            previous_fix_attempts_db_error[:-1],
        ):
            prompt = add_cap_ref(
                prompt,
                "",
                "your answer can not be the same as PREVIOUS_SQL_QUERY:",
                sql,
            )
            prompt = add_cap_ref(
                prompt,
                "",
                "PREVIOUS_ERROR:",
                error,
            )

    prompt = add_cap_ref(
        prompt,
        "Make sure the columns you are referencing exist in the TABLE_DEFINITIONS:",
        "TABLE_DEFINITIONS",
        TABLE_DEFINITIONS,
    )

    prompt = add_cap_ref(
        prompt,
        "Repair this query",
        "USER_REQUEST:",
        question,
    )
    prompt = add_cap_ref(
        prompt,
        """\nPlease correct the following query so that it meets the user's request
        and does not cause an error on BigQuery on Google Cloud Platform.
        It is very important that your answer, can be executed on the bigquery table!
        """,
        "SQL_QUERY:",
        sql_query,
    )
    prompt = add_cap_ref(
        prompt,
        "",
        "ERROR:",
        error_message,
    )
    prompt = add_cap_ref(
        prompt,
        """Now fix the SQL_QUERY for this purpose take into account all
        your PREVIOUS_ERROR Syntax errors and do NOT make any of these errors!
        """,
        "CORRECT_QUERY:",
        "",
    )

    log_messsage = ("🦺🚧 rebuilding sql query prompt:\n %s \n", prompt)
    logging.info(log_messsage)
    sql_query = prompt_llm(prompt)
    sql_query = sql_query.replace("```", "")
    sql_query = sql_query.replace("```sql", "")
    sql_query = sql_query.replace("sql", "")
    logging.info("🤖 query:\n %s \n", sql_query)
    was_query_successfull, bq_answer = run_query(sql_query)
    return was_query_successfull, bq_answer, sql_query


def prompt_for_sql_query_builder(question):
    prompt = CONTEXT_FOR_SQL_QUERY_PROMPT

    # Use database structure from CREATE TABLE statement
    prompt = add_cap_ref(
        prompt,
        "\n\nUse these TABLE_DEFINITIONS to satisfy the database query.:",
        "TABLE_DEFINITIONS",
        TABLE_DEFINITIONS,
    )

    prompt = add_cap_ref(
        prompt,
        "",
        "COLUMN_DESCRIPTION",
        COLUMN_DESCRIPTION,
    )

    # Extra instructions
    prompt = add_cap_ref(
        prompt,
        EXTRA_INSTRUCTIONS_FOR_SQL_QUERY_PROMPT,
        "",
        "",
    )

    # Examples
    prompt = add_cap_ref(
        prompt,
        EXAMPLES_FOR_SQL_QUERY_PROMPT,
        "",
        "",
    )

    # Prompt
    prompt = add_cap_ref(
        prompt,
        f"input: {question}\noutput: YOUR_ANSWER",
        "",
        "",
    )

    return prompt


def prompt_for_sql_query_explenation_builder(sql_query, question):
    prompt = CONTEXT_FOR_SQL_QUERY_EXPLANATION

    prompt = add_cap_ref(
        prompt,
        "",
        "Describe what can be seen in the result table based on the SQL_QUERY:",
        "",
    )

    prompt = add_cap_ref(
        prompt,
        "",
        "SQL_QUERY",
        sql_query,
    )

    prompt = add_cap_ref(
        prompt,
        "",
        "EMPLOYEE_QUESTION",
        f"The SQL_QUERY was created based on the employee's question '{question}'",
    )

    prompt = add_cap_ref(
        prompt,
        """For context this SQL query is executed on table with these
        TABLE_DEFINITIONS and COLUMN_DESCRIPTION:
        """,
        "TABLE_DEFINITIONS",
        TABLE_DEFINITIONS,
    )

    prompt = add_cap_ref(
        prompt,
        "",
        "COLUMN_DESCRIPTION",
        COLUMN_DESCRIPTION,
    )

    prompt = add_cap_ref(
        prompt,
        "",
        EXTRA_INSTRUCTIONS_FOR_SQL_QUERY_EXPLANATION,
        "",
    )

    return prompt
