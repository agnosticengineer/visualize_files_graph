# visualize_files_graph
Visualize how recursively different files in a directory are related in an interactive graph diagram. 

### How to use the Python script

#### How to Use the setup.sh Script and visualize_files_graph.py in a Python Virtual Environment on MacBook (follow similar steps for your OS): 
```

	1.	Save the setup.sh Script:
	•	Copy the content of the setup.sh script into a file named setup.sh.
	•	Save this file in the directory where you have or will place the visualize_files_graph.py script.
	
    2.	Make the setup.sh Script Executable:
	•	Open a terminal and navigate to the directory where you saved the setup.sh script.
	•	Run the following command to make the script executable:
    chmod +x setup.sh
    
    3.	Run the setup.sh Script:
	•	Execute the setup.sh script to set up the environment:
    ./setup.sh
    •	This will create a Python virtual environment, install the required dependencies, and then deactivate the environment when done.
    
    4.	Activate the Python Virtual Environment:
	•	After running the setup.sh, you need to activate the virtual environment to use the visualize_files_graph.py script:
    source yaml_view_env/bin/activate
    
    5.	Run the visualize_files_graph.py Script:
	•	Ensure that visualize_files_graph.py is in the same directory.
	•	You can now run the visualize_files_graph.py script within the virtual environment using the following command:
    python visualize_files_graph.py /path/to/parent_directory /path/to/output_graph.html
    
    6.	Deactivate the Virtual Environment:
	•	After you’re done using the script, you can deactivate the virtual environment by running:
    deactivate

```

