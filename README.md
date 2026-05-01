Overview

This project implements a distributed IoT system using two separate databases (one per house) and TCP-based communication between servers. Each server stores its own IoT data and shares new data with its partner after a synchronization point.

When a query is made, the system:

checks if the local database has all required data,
requests missing historical data from the partner server if needed,
combines both datasets,
and returns a final, accurate result.

This demonstrates a distributed, partially replicated system, not a centralized database.

Architecture:
  Client
  Sends user queries to a server.
  Server A & Server B (server.py)
  Each server:
  connects to its own NeonDB database,
  processes queries,
  communicates with the partner server when data is incomplete.
  NeonDB (PostgreSQL)
  Stores IoT data processed through the clean_iot_data view.

Requirements
  Make sure you have the following installed:
  Python 3.10+
  psycopg2
  Access to your NeonDB database
  Google Cloud VM (or any machine with a public IP)

Install dependencies:
  pip install psycopg2-binary
  
Configuration
  Before running, update these values in server.py:
  
  DB_URL = "your_neon_db_connection_string"
  
  PARTNER_HOST = "your_partner_external_ip_from_google_cloud_vm"
  PARTNER_PORT = 6000  # or 5000 depending on setup

Typical setup:
  Machine	Port
  Server A	5000
  Server B	6000

Running the System
  Step 1 — Start both servers
  
  On your machine:
  
  python server.py
  
  Enter:
  
  5000
  
  On your partner’s machine:
  
  python server.py
  
  Enter:
  
  6000
  
  You should see:
  
  Server listening on 0.0.0.0:PORT
  
Step 2 — Start the client
  On either machine:
  
  python client.py
  
  Enter:
  
  Server IP: <server external IP>
  Port: 5000 (or 6000 depending on which server you connect to)
  
Step 3 — Run queries
  The client supports exactly three queries:
    - Average fridge moisture (hour/week/month)
    - Average dishwasher water consumption (hour/week/month)
    - Electricity usage comparison (last 24 hours)
