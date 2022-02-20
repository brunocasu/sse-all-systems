import preparation_system as ps


if __name__ == '__main__':
    #1) We need to start the rest_api.py
    #2) Start the send_raw_session_test.py to simulate the send of the raw_session
    #3) Now we can start the main.py that will create the preparation_system class and execute the method
    #   "execute_preparation_system"
    cl = ps.Preparation_system()
    cl.execute_preparation_system()

