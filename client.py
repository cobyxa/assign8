import socket

# -------- CONFIG --------
SERVER_HOST = input("Enter server IP: ").strip()
SERVER_PORT = int(input("Enter server port: ").strip())

# -------- VALID QUERIES --------
VALID_QUERIES = {
    "1": "What is the average moisture inside our kitchen fridges in the past hours, week and month?",
    "2": "What is the average water consumption per cycle across our smart dishwashers in the past hour, week and month?",
    "3": "Which house consumed more electricity in the past 24 hours?"
}

# -------- CLIENT --------
def start_client():
    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((SERVER_HOST, SERVER_PORT))

        print("\nConnected to server.\n")

        while True:
            print("Choose a query:")
            print("1) Average fridge moisture (hour/week/month)")
            print("2) Average dishwasher water consumption (hour/week/month)")
            print("3) Electricity usage comparison (last 24h)")
            print("4) Exit")

            choice = input("Enter choice: ").strip()

            if choice == "4":
                print("Closing connection.")
                break

            if choice not in VALID_QUERIES:
                print("\nSorry, this query cannot be processed. Please try one of the supported queries.\n")
                continue

            query = VALID_QUERIES[choice]

            # Send query
            client_socket.sendall(query.encode())

            # Receive response
            response = client_socket.recv(4096).decode()

            print("\n--- Server Response ---")
            print(response)
            print("-----------------------\n")

        client_socket.close()

    except ValueError:
        print("Error: Port must be a number.")
    except socket.gaierror:
        print("Error: Invalid server IP.")
    except ConnectionRefusedError:
        print("Error: Connection refused. Is the server running?")
    except TimeoutError:
        print("Error: Connection timed out.")
    except Exception as e:
        print(f"Unexpected error: {e}")


if __name__ == "__main__":
    start_client()