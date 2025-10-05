# PretLoc

## Overview

PretLoc is a comprehensive rental management platform designed for organizations that lend equipment, tools, or other
assets. It provides a simple yet powerful interface for managing customers, inventories, reservations, and donations.

The application allows you to track customer information, manage equipment availability, process reservations, and
handle donation payments - all in one integrated system. PretLoc is particularly suitable for non-profit organizations,
tool libraries, community centers, and similar establishments that offer lending services.

## Key Features

* Customer management with customizable customer types
* Inventory tracking with categories and availability status
* Reservation system with calendar view and PDF export
* Donation tracking and management
* Dashboard with key metrics and upcoming activities
* User management with different permission levels

## Getting Started with Docker Compose

### Prerequisites

* Docker and Docker Compose installed on your system
* Git (to clone the repository)

### Installation

1. Clone the repository:
    ```bash
    git clone https://github.com/yourusername/pretloc.git
    cd pretloc
    ```
2. Create a .env file in the project root with the following variables (adjust as needed):
    ```env
    # Running user
    PUID=1001
    PGID=1002
    # Django settings
    DJANGO_DEBUG=True
    DJANGO_SECRET=votre_cle_secrete
    # Database settings
    DB_NAME=gestion_materiel
    DB_USER=postgres
    DB_PASSWORD=postgres
    DB_HOST=db
    DB_PORT=5432
    # admin credentials
    ADMIN_LOGIN=admin
    ADMIN_PASSWD=admin
    ADMIN_EMAIL=admin@example.com
    ```
3. Build and start the containers:

    ```bash
    docker-compose up -d
    ```

4. Access the application:

    * Web interface: http://localhost:8000
    * Admin interface: http://localhost:8000/admin

### Docker Compose Commands

* Start the application: `docker-compose up -d`
* Stop the application: `docker-compose down`
* View logs: `docker-compose logs -f`
* Execute commands in the container: `docker-compose exec web python manage.py [command]`
* Rebuild containers after code changes: `docker-compose build`

## Configuration

PretLoc can be configured through environment variables or by editing the `.env` file:

* Container settings:
    * `PUID`, `PGID`: User and group IDs for file permissions
* Database settings:
    * `DB_HOST`, `DB_PORT`: Database connection settings
    * `DB_NAME`: Name of the PostgreSQL database
    * `DB_USER`, `DB_PASSWORD`: PostgreSQL user credentials
* Django settings:
    * `DJANGO_SECRET_KEY`: Security key for Django (keep this secret)
    * `DJANGO_DEBUG`: Set to True for development, False for production
* Superuser credentials:
    * `ADMIN_LOGIN`, `ADMIN_PASSWD`, `ADMIN_EMAIL`: Credentials for the initial admin user

## Usage

1. Log in with your admin credentials
2. Set up customer types under the administration section
3. Add inventory items and categorize them
4. Create customer profiles
5. Start managing reservations and tracking donations

## Requests

* Customer management
    * Customer types
        * [X] Allow defining customer types (member, non-member, external)
        * [X] Allow defining benefits for each customer type
            * [X] Exemption from donation
            * [X] Extended reservation period
            * [x] Donation calculation coefficient (e.g., double donation for external customers)
    * Customer
        * [ ] Allow archiving customers (no longer suggest them in searches)
        * [X] In Customer view, display customer type
            * [X] In Customer view, display if the customer has a donation exemption
        * [ ] Add a field in customers to know if they have already made a donation this year (membership fee)
* Reservation management
    * [X] Display customer type in reservation view
        * [X] Display if the customer has a donation exemption
        * [ ] Display if the customer has already made a donation this year
            * [ ] Display suggested donation amount deducing the membership fee if already paid this year
    * [ ] Display asset availability in reservation view line
        * [ ] (optional) deduce of the availability the current reservation
            * [ ] Have the same search for customer in reservation and customer list
        * [ ] (optional) display customer type icon in search bar
    * [ ] Allow generating PDFs of all reservations due next Friday or Monday.
    * [ ] Allow customers to renew their reservation (same items, different date)
    * [ ] In return view, display the articles
        * [ ] Allow inputs of how many items are returned (in case of partial return or damaged)
            * [ ] Compute donation based on the number of items returned (even exempt customers must pay for
              non-returned items)
* Donation management
    * [ ] Allow recording a donation for a customer
    * [ ] Allow indicating if the donation is for the annual membership (exemption)
    * [ ] Allow indicating the amount of the donation
    * [ ] Allow indicating the date of the donation
    * [ ] Display donations in the customer view
    * [ ] Display donations in the home view (total number and total amount this year)
* Miscellaneous
    * [ ] In home page, display the number of reservation in progress or to come.
    * [ ] In home page, display the number of reservations due next Friday or Monday.
    * [ ] In home page, display the amount of donations made this year
    * [ ] Timing management for reservations
        * [ ] Allow members and ganathans to reserve 12 months in advance
        * [ ] Allow external customers to reserve 1 month in advance
            * [ ] Prevent validation if this limit is exceeded