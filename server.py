import socket
import json
from datetime import datetime, timedelta
import psycopg2

# ---------------- CONFIG ----------------
DB_URL = "Connection_String" #Enter Connection String From NeonDB here

PARTNER_HOST = "12.34.56.78"   # partners external IP
PARTNER_PORT = 6000        # partners port

SHARING_START = datetime(2026, 4, 30, 0, 30)


#DB Connection

def get_connection():
    return psycopg2.connect(DB_URL)


def query_sum_count(metric, device, start_time, end_time=None):
    conn = get_connection()
    cur = conn.cursor()

    try:
        if end_time:
            query = """
                SELECT COALESCE(SUM(value),0), COUNT(*)
                FROM clean_iot_data
                WHERE metric = %s
                AND device_type = %s
                AND timestamp >= %s
                AND timestamp < %s
            """
            cur.execute(query, (metric, device, start_time, end_time))
        else:
            query = """
                SELECT COALESCE(SUM(value),0), COUNT(*)
                FROM clean_iot_data
                WHERE metric = %s
                AND device_type = %s
                AND timestamp >= %s
            """
            cur.execute(query, (metric, device, start_time))

        result = cur.fetchone()
        return result[0] or 0, result[1] or 0

    except Exception as e:
        print("DB ERROR:", e)
        return 0, 0

    finally:
        cur.close()
        conn.close()


#Fetching through partners DB by talking to their server

def fetch_partner(metric, device, start_time, end_time):
    payload = json.dumps({
        "type": "FETCH",
        "metric": metric,
        "device": device,
        "start": start_time.isoformat(),
        "end": end_time.isoformat()
    })

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((PARTNER_HOST, PARTNER_PORT))
            s.sendall(payload.encode())

            response = s.recv(4096).decode()

            if not response:
                print("Empty response from partner")
                return 0, 0

            data = json.loads(response)
            return data.get("sum", 0), data.get("count", 0)

    except Exception as e:
        print("Partner fetch failed:", e)
        return 0, 0


#Core Calculations

def compute_average(metric, device, start_time):
    local_sum, local_count = query_sum_count(metric, device, start_time)

    if start_time >= SHARING_START:
        print("Using local data only")
        if local_count == 0:
            return "No data"
        return local_sum / local_count

    else:
        print("Fetching from partner...")

        remote_sum, remote_count = fetch_partner(
            metric,
            device,
            start_time,
            SHARING_START
        )

        total_sum = local_sum + remote_sum
        total_count = local_count + remote_count

        if total_count == 0:
            return "No data"

        return total_sum / total_count



def compute_electricity():
    conn = get_connection()
    cur = conn.cursor()

    try:
        query = """
            SELECT house_id, SUM(value)
            FROM clean_iot_data
            WHERE metric = 'electricity'
            AND timestamp >= NOW() - INTERVAL '24 hours'
            GROUP BY house_id;
        """

        cur.execute(query)
        rows = cur.fetchall()

        totals = {row[0]: row[1] for row in rows}

        A = totals.get('A', 0)
        B = totals.get('B', 0)

        if A > B:
            return f"House A used more electricity by {A - B:.2f}"
        else:
            return f"House B used more electricity by {B - A:.2f}"

    except Exception as e:
        print("Electricity error:", e)
        return "Error computing electricity"

    finally:
        cur.close()
        conn.close()



def process_request(message):
    print("Incoming:", message)

    if message.startswith("{"):
        try:
            data = json.loads(message)

            if data.get("type") == "FETCH":
                metric = data["metric"]
                device = data["device"]
                start = datetime.fromisoformat(data["start"])
                end = datetime.fromisoformat(data["end"])

                sum_val, count_val = query_sum_count(metric, device, start, end)

                response = json.dumps({
                    "sum": sum_val,
                    "count": count_val
                })

                print("Sending:", response)
                return response

        except Exception as e:
            print("FETCH JSON ERROR:", e)
            return json.dumps({"sum": 0, "count": 0})

    now = datetime.now()

    try:
        if "moisture" in message:
            hour = compute_average("moisture", "fridge", now - timedelta(hours=1))
            week = compute_average("moisture", "fridge", now - timedelta(days=7))
            month = compute_average("moisture", "fridge", now - timedelta(days=30))

            return f"""
Average Fridge Moisture:
Hour: {hour:.2f}
Week: {week:.2f}
Month: {month:.2f}
"""

        elif "water consumption" in message:
            hour = compute_average("water", "dishwasher", now - timedelta(hours=1))
            week = compute_average("water", "dishwasher", now - timedelta(days=7))
            month = compute_average("water", "dishwasher", now - timedelta(days=30))

            return f"""
Average Dishwasher Water Consumption:
Hour: {hour:.2f}
Week: {week:.2f}
Month: {month:.2f}
"""

        elif "electricity" in message:
            return compute_electricity()

    except Exception as e:
        print("CLIENT REQUEST ERROR:", e)

    return "Invalid query"

#Starting Server
def start_server(host="0.0.0.0", port=5000):  #Make sure to create a firewall rule to allow port 5000 to allow incoming connections to your google cloud vm. 
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        server_socket.bind((host, port))
        server_socket.listen(5)
        print(f"Server listening on {host}:{port}")

        while True:
            conn, addr = server_socket.accept()
            print(f"Connected by {addr}")

            with conn:
                while True:
                    data = conn.recv(4096)
                    if not data:
                        break

                    message = data.decode().strip()
                    response = process_request(message)

                    conn.sendall(response.encode())

    except Exception as e:
        print("Server error:", e)

    finally:
        server_socket.close()


if __name__ == "__main__":
    port = int(input("Enter port: "))
    start_server(port=port)
