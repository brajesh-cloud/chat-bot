import os
import pymysql
from dotenv import load_dotenv
from openai import OpenAI
import json
import sys
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any

load_dotenv()

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
MYSQL_HOST = os.getenv('MYSQL_HOST', 'localhost')
MYSQL_USER = os.getenv('MYSQL_USER')
MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD')
MYSQL_DBNAME = os.getenv('MYSQL_DBNAME')

if not OPENAI_API_KEY or not MYSQL_USER or not MYSQL_PASSWORD or not MYSQL_DBNAME:
    print("Error: Missing required env vars. Copy .env.example to .env and fill it.")
    sys.exit(1)

client = OpenAI(api_key=OPENAI_API_KEY)

app = FastAPI(
    root_path="/api",
    title="IMCS DB Bot API")

class QuestionRequest(BaseModel):
    question: str

TABLE_DESCS = """
Tables:
- employees: id (BIGINT), created_by(VARCHAR), creation_date (DATETIME), modified_by (VARCHAR), modified_date (DATETIME) first_name (VARCHAR), middle_name (VARCHAR), last_name (VARCHAR), birth_date (DATE), gender (VARCHAR), marital_status (VARCHAR), primary_email (VARCHAR), _other_emails (TEXT), primary_contact_phone (VARCHAR), _other_phones (VARCHAR), permanent_address_1 (VARCHAR), permanent_address_2  (VARCHAR), permanent_city (VARCHAR), permanent_zip (VARCHAR), permanent_state (VARCHAR), permanent_country (VARCHAR), current_address_1 (VARCHAR), current_address_2 (VARCHAR), current_city (VARCHAR), current_zip (VARCHAR), current_state (VARCHAR), current_country (VARCHAR), _other_emergencycontacts (TEXT), education_level (VARCHAR), education_specialization (VARCHAR), education_university_name (VARCHAR), education_city (VARCHAR), education_state (VARCHAR), education_country (VARCHAR), education_passing_year (VARCHAR), education_gcpa (VARCHAR), _other_education (TEXT), employmentid (VARCHAR), employment_type (VARCHAR), employment_start_date (DATE), employment_end_date (DATE), employment_current_title (VARCHAR), employment_position_start_date (DATE) employment_position_end_date (DATE), employment_department (VARCHAR), employment_offer_letter_document_ (VARCHAR), employment_drivers_lincense_document_ (VARCHAR), employment_everify_document_ (VARCHAR), employment_i9_document_ (VARCHAR), employment_ssn_document_ (VARCHAR), employment_i94_document_ (VARCHAR), employment_i94_expiration_date (DATE), employment_passport_number (VARCHAR), employment_passport_issue_date (DATE), employment_passport_expiration_date (DATE), employment_passport_issuance_contry (VARCHAR), employment_skills (VARCHAR), _other_certificates (TEXT), employment_end_employment (BIT), employment_end_type (VARCHAR), employment_end_reason (TEXT), offerletter_date (DATE), employment_miscellaneous_document_ (VARCHAR), onboarding_w4 (VARCHAR), onboarding_direct_deposit_details (VARCHAR), onboarding_university_contact (VARCHAR), onboarding_medical_insurance_form (VARCHAR), visa (VARCHAR), medical_insurance (VARCHAR), immigration_expiry_duration (VARCHAR), company_insurance_document (VARCHAR), insurance_waiver_form (VARCHAR), notes (TEXT), rehire (BIT), candidate_name (VARCHAR), employment_job_title (VARCHAR), healthcare_it (VARCHAR), sector (VARCHAR), termination_email (BIT), billing_status (VARCHAR), billing_start_date (DATE), is_exception (SMALLINT), note_for_exception (TEXT), hospital_system (VARCHAR), _other_currentaddress (TEXT), hospital_name (VARCHAR), relationship_id_healthcare_placement (BIGINT), placement_details (TEXT), recruiter (VARCHAR), relationship_id_users_recruiter (VARCHAR), recruiting_lead (VARCHAR), relationship_id_users_recruiting_lead (VARCHAR), recruiting_manager (VARCHAR),relationship_id_users_recruiting_manager (VARCHAR), delivery_manager (VARCHAR), relationship_id_users_delivery_manager (VARCHAR), account_manager (VARCHAR), relationship_id_users_account_manager (VARCHAR), relationship_id_preboarding (INT), payroll_type (VARCHAR), delivery_head (VARCHAR), is_healthcare (BIT), is_healthcare_employee (VARCHAR)

- employees_canada: id (INT), created_by (VARCHAR), creation_date (DATETIME), modified_by (VARCHAR), modified_date (DATETIME), first_name (VARCHAR), last_name (VARCHAR), birth_date (DATE), personal_email (VARCHAR), personal_contact (VARCHAR), company_email (VARCHAR), citizenship_status (VARCHAR), address_1 (VARCHAR), address_2 (VARCHAR), city (VARCHAR), zip (VARCHAR), state (VARCHAR), country (VARCHAR), job_title (VARCHAR), pay_rate (DECIMAL), client_name (VARCHAR), work_authorization (VARCHAR), work_authorization_end_date (DATE), insurance_taken (BIT), documents (VARCHAR), relationship_id_clients (INT), employment_start_date (DATE), offerletter_date (DATE), employment_end_employment (BIT), employment_end_type (VARCHAR), employment_end_date (DATE), employment_offer_letter_document_ (VARCHAR), employment_drivers_lincense_document_ (VARCHAR), employment_sin_document_ (VARCHAR), immigration_document_ (VARCHAR)

- preboarding: id (BIGINT), created_by (VARCHAR), creation_date (DATETIME), modified_by (VARCHAR), modified_date (DATETIME), entry_date (DATE), first_name (VARCHAR), middle_name (VARCHAR), last_name (VARCHAR), tel_no (VARCHAR), email_id (VARCHAR), visa_type (VARCHAR), employment_category (VARCHAR), projected_start_date (DATE), bdm (VARCHAR), vendor (VARCHAR), onboarding_date (DATE), client (VARCHAR), communication_address_1 (VARCHAR), communication_address_2 (VARCHAR), communication_city (VARCHAR),communication_zip (VARCHAR), communication_state (VARCHAR), communication_country (VARCHAR), onboarding_package (VARCHAR), tracking_number (VARCHAR), status (VARCHAR), actual_date (DATE), notes (TEXT), gift (VARCHAR), account_manager (VARCHAR), recruiter (VARCHAR), recruiting_manager (VARCHAR), delivery_manager (VARCHAR), manager (VARCHAR), sector (VARCHAR), delivery_head (VARCHAR), relationship_id_user_account_manager (VARCHAR), relationship_id_user_recruiter (VARCHAR),relationship_id_user_recruiting_manager (VARCHAR), relationship_id_user_delivery_manager (VARCHAR), relationship_id_user_delivery_head (VARCHAR), onboarding_status (VARCHAR), end_client (VARCHAR), relationship_id_clients (INT), eta_date (DATE), relationship_id_user_bdm (VARCHAR), end_client_address_1 (VARCHAR), end_client_address_2 (VARCHAR), end_client_city (VARCHAR), end_client_zip (VARCHAR), end_client_state (VARCHAR), end_client_country (VARCHAR), mode_of_work (VARCHAR), job_duties (TEXT), referral_source (VARCHAR), other_referral_source (VARCHAR), relationship_id_healthcare_placement (BIGINT), fdi_sent_to_er (BIT)

- contractors: id (BIGINT), created_by (VARCHAR), creation_date (DATETIME), modified_by (VARCHAR), modified_date (DATETIME), first_name (VARCHAR), middle_name (VARCHAR), last_name (VARCHAR), client (VARCHAR), sub_vendor (VARCHAR), start_date (DATE), is_end_contractor (SMALLINT), exit_date (DATE), exit_reason (TEXT), bdm (VARCHAR), notes (TEXT), purchase_order (VARCHAR), purchase_order_client (VARCHAR), bill_rate (DOUBLE), pay_rate (DOUBLE), primary_email (VARCHAR), coi_expiry_date (DATE), coi_files (VARCHAR), submission_rate (VARCHAR), discounted_bill_rate (VARCHAR), recruiter_name (VARCHAR), relationship_id_clients (BIGINT), relationship_id_vendors (INT),i9e_verify (VARCHAR), payslips (VARCHAR), country (VARCHAR), relationship_id_preboarding (INT), sector (VARCHAR), delivery_head (VARCHAR), relationship_id_users_recruiter (VARCHAR)

- projects: id (BIGINT), created_by (VARCHAR), creation_date (DATETIME), modified_by (VARCHAR), modified_date (DATETIME), candidate_name (VARCHAR), relationship_id_employees (BIGINT), client_name (VARCHAR), relationship_id_clients (BIGINT), candidate_email (VARCHAR), contract_start_date (DATE), contract_end_date (DATE), employment_type (VARCHAR), client_location (VARCHAR), job_location (VARCHAR), invoice_term (VARCHAR), invoice_term_custom_date (DATE), payment_terms (VARCHAR), documents (VARCHAR), payment_time_periods (VARCHAR), end_client_address_1 (VARCHAR), end_client_address_2 (VARCHAR), end_client_city (VARCHAR), end_client_zip (VARCHAR), end_client_state (VARCHAR), end_client_country (VARCHAR), end_client_name (VARCHAR), first_ren_end_date (DATE), second_ren_end_date (DATE), ongoing (VARCHAR), project_end_date (DATE), bdm (VARCHAR), client_email (VARCHAR), client_contact_number (VARCHAR), client_contact_name (VARCHAR), industry_type (VARCHAR), submission_rate (DOUBLE), discounted_bill_rate (DOUBLE), overtime_rate (DOUBLE), sector (VARCHAR), hospital_system (VARCHAR), multiple_projects (BIT), _multiple_other_projects (TEXT), hospital_name (VARCHAR), recruiter (VARCHAR), relationship_id_users_recruiter (VARCHAR), recruiting_lead (VARCHAR), relationship_id_users_recruiting_lead (VARCHAR), recruiting_manager (VARCHAR), relationship_id_users_recruiting_manager (VARCHAR), delivery_manager (VARCHAR), relationship_id_users_delivery_manager (VARCHAR), account_manager (VARCHAR), relationship_id_users_account_manager (VARCHAR), orientation_pay_rate (DECIMAL), regular_pay_rate (DECIMAL), new_regular_pay_rate_1 (DECIMAL), effective_date_1 (DATE), new_regular_pay_rate_2 (DECIMAL), effective_date_2 (DATE), new_bill_rate_1 (DOUBLE), new_bill_rate_2 (DOUBLE), new_discounted_rate_1 (DOUBLE), new_discounted_rate_2 (DOUBLE), new_bill_rate_1_date (DATE), new_bill_rate_2_date (DATE), new_discounted_rate_1_date (DATE), new_discounted_rate_2_date (DATE), new_bill_rate_1_effective_date (DATE), new_bill_rate_2_effective_date (DATE), new_discounted_rate_1_effective_date (DATE), new_discounted_rate_2_effective_date (DATE), pay_rate (DOUBLE), bill_rate (DOUBLE), relationship_id_projects (INT)

- healthcare_placement: id (BIGINT), created_by (VARCHAR), creation_date (DATETIME), modified_by (VARCHAR), modified_date (DATETIME), first_name (VARCHAR), last_name (VARCHAR), email (VARCHAR), contact_phone (VARCHAR), msp (VARCHAR), hospital (VARCHAR), required_start_date (DATE), recruiter (VARCHAR), account_manager (VARCHAR), offer_date (DATE), offer_letter (VARCHAR), placement_status (VARCHAR), healthcare_notes (TEXT), relationship_id_india_recruiter (INT), relationship_id_usa_recruiter (INT), relationship_id_mexico_recruiter (INT), relationship_id_canada_recruiter (INT), recruiting_lead (VARCHAR), relationship_id_india_recruiting_lead (INT), relationship_id_usa_recruiting_lead (INT), relationship_id_mexico_recruiting_lead (INT), relationship_id_canada_recruiting_lead (INT), recruiting_manager (VARCHAR), relationship_id_india_recruiting_manager (INT), relationship_id_usa_recruiting_manager (INT), relationship_id_mexico_recruiting_manager (INT), relationship_id_canada_recruiting_manager (INT), relationship_id_india_account_manager (INT), relationship_id_usa_account_manager (INT), relationship_id_mexico_account_manager (INT), relationship_id_canada_account_manager (INT), hospital_system (VARCHAR), hospital_name (VARCHAR), relationship_id_users_recruiter (VARCHAR), relationship_id_users_recruiting_lead (VARCHAR), relationship_id_users_recruiting_manager (VARCHAR), relationship_id_users_account_manager (VARCHAR), delivery_manager (VARCHAR), relationship_id_users_delivery_manager (VARCHAR), referred_by (VARCHAR), referral_amount (DOUBLE), referral_paid_on (VARCHAR), resume_upload (VARCHAR), upload_date (DATE), orientation_pay_rate (DOUBLE), regular_pay_rate (DOUBLE), new_regular_pay_rate_1 (DOUBLE), effective_date_1 (DATE), new_regular_pay_rate_2 (DOUBLE), effective_date_2 (DATE), bonus_amount (DOUBLE), bonus_paid_on (DATE), bgc_vendor (VARCHAR), bgc_start_date (DATE), bgc_end_date (DATE), medical_vendor (VARCHAR), medical_start_date (DATE), medical_end_date (DATE), offer_accepted_date (DATE), relationship_id_checklist_users (INT), preboarding_date (DATE), revised_start_date (DATE), relationship_id_employees (INT), confirmed_start_date (DATE), joining_date (DATE), work_state (VARCHAR), first_required_start_datename (DATETIME), contract_end_date (DATE), abandoned_date (DATE), guaranteed_hours_per_week (DECIMAL), housing_reimbursement_weekly (DECIMAL), mi_reimbursement_weekly (DECIMAL), non_taxable_amount_per_hour (DECIMAL), non_taxable_amount_total (DECIMAL), reason_for_bad_delivery (VARCHAR), delivery_head (VARCHAR), relationship_id_users_delivery_head (VARCHAR), client_offer_date (DATE), employee_type (VARCHAR), required_end_date (DATE), revised_end_date (DATE), account_coordinator (VARCHAR), relationship_id_users_account_coordinator (VARCHAR), bill_rate (DOUBLE), pay_rate (DOUBLE), job_category (VARCHAR), job_title (VARCHAR)

Use only SELECT queries.
"""

def get_db_connection():
    return pymysql.connect(
        host=MYSQL_HOST,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        database=MYSQL_DBNAME,
        cursorclass=pymysql.cursors.DictCursor
    )

def generate_sql(question):
    prompt = f"""You are a MySQL expert. Convert this question to a safe SELECT-only SQL query.

CRITICAL RULES:
1. Only use columns that are EXPLICITLY listed in the table schema below. Do NOT assume or invent columns.
2. If a table does not have the required column, do NOT include it in the query (skip it entirely).
3. Before writing a UNION, verify EACH table actually has ALL columns referenced in that branch.
4. Output only the raw SQL query — no markdown, no explanation.

Schema:
{TABLE_DESCS}

Question: {question}"""
    
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1
    )
    # client.responses.create(
    #     model="gpt-4o",
    #     input="Hello",
    #     metadata={
    #         "user": "imcs-system"
    #     }
    # )
    sql = response.choices[0].message.content.strip()
    if sql.lower().startswith('```sql'):
        sql = sql.split('```sql')[1].split('```')[0].strip()
    elif sql.lower().startswith('```'):
        sql = sql.split('```')[1].strip()
    return sql

def execute_query(sql):
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(sql)
            return cursor.fetchall()
    finally:
        conn.close()

def format_results(question, results):
    if not results:
        return f"No results found for '{question}'."
    
    try:
        results_json = json.dumps(results[:10], indent=2)
        prompt = f"""Question: {question}

DB Results:
{results_json}

Summarize these results in clear, natural human language directly answering the question. Be concise. If multiple rows, highlight key patterns or list briefly."""
        
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )
        natural_answer = response.choices[0].message.content.strip()
        if len(results) > 10:
            natural_answer += f"\n(... and {len(results) - 10} more rows.)"
        return natural_answer
    except Exception:
        lines = ["Results:"]
        for row in results[:10]:
            lines.append(str(row))
        if len(results) > 10:
            lines.append(f"... and {len(results) - 10} more rows.")
        return "\n".join(lines)

# def main():
#     print("IMCS DB Bot ready! Ask questions about employees, etc. Type 'quit' to exit.")
#     while True:
#         question = input("\nYou: ").strip()
#         if question.lower() in ['quit', 'exit', 'bye']:
#             print("Bye!")
#             break
        
#         print("Bot: Generating SQL...")
#         sql = generate_sql(question)
#         print(f"Generated SQL: {sql}")
        
#         print("Executing...")
#         try:
#             results = execute_query(sql)
#             answer = format_results(question, results)
#         except Exception as e:
#             answer = f"Error: {str(e)} (Check SQL/safety)"
        
#         print(f"Bot: {answer}")

# if __name__ == "__main__":
#     main()


@app.post("/ask")
def ask_question(data: QuestionRequest):

    try:
        question = data.question

        sql = generate_sql(question)

        # Safety check
        if not sql.lower().startswith("select"):
            raise HTTPException(
                status_code=400,
                detail="Only SELECT queries allowed"
            )

        results = execute_query(sql)

        answer = format_results(question, results)

        return {
            "question": question,
            "sql": sql,
            "results": results,
            "answer": answer
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/")
def home():
    print(os.getenv("OPENAI_API_KEY"))
    return {"message": "IMCS DB Bot API Running"}

