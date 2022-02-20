HOW TO RUN DEVELOPMENT SYSTEM:
    1) Configure starting network params in conf_files/initial_network_params.json
    2) Configure servers url in conf_files/application_settings.json
    3) Run the servers
    
MANUAL TESTING:
    - The graphs with the intermediate and final results are in graph/
    - The json reports (params of 5 best networks + final test report) are in json_report_files/
    4) Configure as follow the file for manual execution in conf_files/execution_flow.json
    
    1) To start and get the data 
        {
            "start": true,
              "training": false,
              "success_training": false,
              "chosen_network_index": null,
              "testing": false,
              "retraining": false,
              "accept_final_report_step": false,
              "accept_network": false
        }
    2) Retrain the network (curve not flat enough):
        - change number of iteration in initial_network_params.json
        {
            "start": false,
              "training": true,
              "success_training": false,
              "chosen_network_index": null,
              "testing": false,
              "retraining": false,
              "accept_final_report_step": false,
              "accept_network": false
        }
    3) GridSearch + Validation:
        {
            "start": false,
              "training": false,
              "success_training": true,
              "chosen_network_index": null,
              "testing": false,
              "retraining": false,
              "accept_final_report_step": false,
              "accept_network": false
        }
    4) Retrain the network:
        {
            "start": false,
              "training": true,
              "success_training": false,
              "chosen_network_index": null,
              "testing": false,
              "retraining": true,
              "accept_final_report_step": false,
              "accept_network": false
        }
    
    5) Choose network + Testing:
            - "chosen_network_index": insert a number [0-4] based on validation_report.json content
           {
            "start": false,
              "training": false,
              "success_training": false,
              "chosen_network_index": 1,
              "testing": true,
              "retraining": false,
              "accept_final_report_step": false,
              "accept_network": false
        } 
    6) Accept or reject final report
            -"accept_final_report_step": true
            -"accept_network": true/false
            {
            "start": false,
              "training": false,
              "success_training": false,
              "chosen_network_index": null,
              "testing": false,
              "retraining": false,
              "accept_final_report_step": true,
              "accept_network": false
        } 

AUTOMATIC TESTING:
    4) Configure accuracy thresholds in conf_files/application_settings.json
    
