[![License: LGPL v3](https://img.shields.io/badge/License-LGPL%20v3-blue.svg)](https://www.gnu.org/licenses/lgpl-3.0)

# Supplies (Procurement Management System)

This Odoo project implements an Odoo 17 solution for supplier registration, RFP creation, and quotation management. It is designed as a containerized application for ease of development and production deployment. This repository includes all necessary Docker, Nginx, and configuration files.

## Table of Contents

- [Supplies (Procurement Management System)](#supplies-procurement-management-system)
  - [Table of Contents](#table-of-contents)
  - [Overview](#overview)
  - [Dependencies](#dependencies)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
    - [Method 1: Simple Run](#method-1-simple-run)
    - [Method 2: Build the Image](#method-2-build-the-image)
  - [Odoo Setup](#odoo-setup)
  - [Customization](#customization)
  - [Additional Notes](#additional-notes)
  - [Release Notes](#release-notes)
    - [v1.0.0 (Initial Release) - 2025-02-25](#v100-initial-release---2025-02-25)

## Overview

This project is built on Odoo 17 and is containerized using Docker. It integrates with Nginx as a reverse proxy to ensure smooth request handling and security. The solution leverages additional Python libraries, including Pydantic 2 and the Pydantic email validator, and depends on the wkhtml2pdf binary. The project is intended to run on Ubuntu 24.

## Dependencies

- **Odoo 18**
- **wkhtml2pdf Binary**
- **Ubuntu 24**
- **Additional Python Libraries:**
  - Pydantic 2
  - Pydantic email validator

## Prerequisites

- [Docker](https://www.docker.com/get-started)
- [Docker Compose](https://docs.docker.com/compose/install/)
- Git for cloning repositories

## Installation

### Method 1: Simple Run

1. **Clone the Supplies Repository:**

   ```bash
   git clone --branch main --single-branch https://github.com/rnium/supplies.git supplies
   ```

2. **Pull the Prebuilt Image:**

   ```bash
   docker-compose pull
   ```

3. **Run the Containers in Detached Mode:**

   ```bash
   docker-compose up -d
   ```

### Method 2: Build the Image

1. **Clone the Docker Branch:**

   ```bash
   git clone --branch supplies-docker --single-branch https://github.com/rnium/supplies.git supplies-docker
   ```

2. **Enter the Directory:**

   ```bash
   cd supplies-docker
   ```

3. **Clone the Supplies Repository:**

   Inside the `supplies-docker` directory, run:

   ```bash
   git clone --branch rony_30207_final_project --single-branch https://github.com/rnium/supplies.git supplies
   ```

4. **Prepare the Enterprise Code:**

   Copy your Odoo 17 enterprise code into the current folder and rename the folder to `enterprise` (as expected by the Dockerfile).

5. **Build the Docker Image:**

   ```bash
   docker-compose build
   ```

6. **Start the Containers:**

   ```bash
   docker-compose up
   ```

## Odoo Setup

After the containers are running, follow these steps to complete the Odoo configuration:

1. **Create a New Database:**
   - Open your web browser and navigate to your Odoo instance (usually at `http://localhost:80`).
   - On the database management screen, click **"Create Database"**.
   - Fill in the required details such as the master password, database name, email, password, and company information.
   - Click **"Create Database"** to proceed.

2. **Install the 'Supplies' Module:**
   - Once logged into Odoo, navigate to the **Apps** menu.
   - If you don’t see the Supplies module, click on **"Update Apps List"** to refresh the available modules.
   - Search for **"Supplies"**.
   - Click **"Install"** next to the Supplies module.

3. **User Management:**
   - Navigate to **Settings > Users & Companies > Users**.
   - Create new user accounts as needed.
   - Assign appropriate groups to each user:
     - **Reviewer:** For users responsible for reviewing supplier registrations and quotations.
     - **Approver:** For users with final approval rights over supplier registrations and RFPs.
   - Configure additional user settings and access rights as required.

## Customization

- **Nginx Configuration:**  
  You can customize the `nginx.conf` file to meet your requirements. For production deployment, ensure you configure the server hostname and implement other necessary security optimizations.

- **Odoo Configuration:**  
  The `odoodocker.conf` file is available for adjustments. Modify it according to your deployment environment or performance needs.

- **Docker Compose:**  
  Feel free to edit the `docker-compose.yml` file to change service configurations, add volumes, or update environment variables.

## Additional Notes

- **Production Deployment:**  
  When deploying to production, it is recommended to review and adjust the Nginx settings for SSL termination, load balancing, and other security measures.

- **Further Customizations:**  
  Users can extend and customize other configuration files and services (such as the Odoo enterprise code and additional libraries) based on their project needs.

## Release Notes

### v1.0.0 (Initial Release) - 2025-02-25
- Released the initial version of the Supplies (Procurement Management System).
- Implemented supplier registration with email OTP verification.
- Developed the two-step verification process for supplier account creation.
- Introduced RFP creation, publication, and quotation management features.
- Configured Docker containerization, Nginx reverse proxy, and Odoo 17 integration.
- Provided basic user management with roles for Reviewer and Approver.
- Established core dependencies including wkhtml2pdf, Pydantic 2, and Pydantic email validator.
- Licensed under GNU LGPL-3.0.
