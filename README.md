# Procurement Management System

A web-based Procurement Management System built with Django and PostgreSQL to manage the purchasing process, from purchase requests to vendor selection, purchase orders, and goods receipt.

## Features

- **Purchase Request (PR):** Create, submit, and revise purchase requests.
- **PR Approval:** Approve, reject, or request revisions to purchase requests.
- **Vendor Selection:** Manage vendor selection and quotation comparison.
- **Purchase Order (PO):** Create and issue purchase orders based on approved vendor selections.
- **Goods Receipt (GR):** Record partial and complete deliveries and track received quantities.
- **Role-Based Access Control:** Restrict actions based on user roles.

## Technology Stack

- Python
- Django
- PostgreSQL
- HTML
- Bootstrap 5

## User Roles

- Requester
- Approver
- Procurement Officer
- Procurement Manager

## Requirements

- Python 3.11 or compatible version
- PostgreSQL
- Git

## Installation

1. Clone the repository:

   ```bash
   git clone <REPOSITORY_URL>
   cd procurement-system
   ```

2. Create a virtual environment:

   ```bash
   python -m venv .venv
   ```

3. Activate the virtual environment on Windows:

   ```powershell
   .venv\Scripts\Activate.ps1
   ```

4. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

5. Configure the environment variables and PostgreSQL database according to your local setup.

6. Apply database migrations:

   ```bash
   python manage.py migrate
   ```

7. Create an administrator account:

   ```bash
   python manage.py createsuperuser
   ```

8. Start the development server:

   ```bash
   python manage.py runserver
   ```

9. Open the application at `http://127.0.0.1:8000/`.

## Database Configuration

Configure the PostgreSQL connection and Django secret key using environment variables. Do not commit credentials or secret keys to the repository.

## Notes

This project is intended for development and evaluation purposes. Configure the database and required environment variables before running the application.
