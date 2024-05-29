import json
import sys
import tkinter as tk
from tkinter import messagebox, filedialog
from jinja2 import Template

class TrackEditor:
    def __init__(self, root, json_data, file_path, index_name):
        self.root = root
        self.json_data = json_data
        self.file_path = file_path
        self.index_name=index_name
        with open('./python/esrally_operations.json', 'r') as file:
            self.available_operations = json.load(file)
            
        self.init_ui()

    def init_ui(self):
        self.root.title("Track Editor")

        # Display current schedule
        self.schedule_frame = tk.LabelFrame(self.root, text="Current Schedule")
        self.schedule_frame.pack(fill="both", expand="yes", padx=10, pady=10)

        self.schedule_listbox = tk.Listbox(self.schedule_frame)
        self.schedule_listbox.pack(fill="both", expand="yes", padx=10, pady=10)
        self.update_schedule_listbox()

        # Display available operations
        self.operations_frame = tk.LabelFrame(self.root, text="Available Operations")
        self.operations_frame.pack(fill="both", expand="yes", padx=10, pady=10)

        self.operations_listbox = tk.Listbox(self.operations_frame)
        self.operations_listbox.pack(fill="both", expand="yes", padx=10, pady=10)
        for operation in self.available_operations:
            if "operation-type" in operation['operation']:
                self.operations_listbox.insert(tk.END, operation["operation"]["operation-type"])
            else: 
                self.operations_listbox.insert(tk.END, operation["operation"])

        # Add button
        self.add_button = tk.Button(self.root, text="Add Operation", command=self.add_operation)
        self.add_button.pack(pady=10)

        # Save button
        self.save_button = tk.Button(self.root, text="Save JSON", command=self.save_json)
        self.save_button.pack(pady=10)

    def update_schedule_listbox(self):
        self.schedule_listbox.delete(0, tk.END)
        for item in self.json_data["schedule"]:
            operation_type = item["operation"]["operation-type"] if isinstance(item["operation"], dict) else item["operation"]
            self.schedule_listbox.insert(tk.END, operation_type)

    def add_operation(self):
        selected_index = self.operations_listbox.curselection()
        if not selected_index:
            messagebox.showwarning("Warning", "No operation selected")
            return
            
        selected_operation = self.available_operations[selected_index[0]]
        self.json_data["schedule"].append(selected_operation)
        self.update_schedule_listbox()

    def save_json(self):
        file_path = filedialog.asksaveasfilename(initialfile='track.json', defaultextension=".json", filetypes=[("JSON files", "*.json"), ("All files", "*.*")])

        if file_path:
            seen=set()
            final_schedule=[]
            for i in self.json_data['schedule']:
                if 'operation-type' in i['operation']:
                    op_type=i['operation']['operation-type']
                    if 'index' in i['operation']:
                        i['operation'].update({'index':self.index_name})
                else: 
                    op_type=i['operation']

                
                if op_type not in seen:
                    seen.add(op_type)
                    final_schedule.append(i) 
            self.json_data['schedule']=final_schedule
                
            with open(file_path, "w") as f:
                json.dump(self.json_data, f, indent=2)
            messagebox.showinfo("Success", f"JSON saved to {file_path}")


def process_json_file(file_path):
    try:
        with open(f'{file_path}/track.json', 'r') as file:
            json_obj=json.loads(file)
            if "schedule" in json_obj:
                del json_obj["schedule"]
            return json_obj
    except Exception as e:
        with open(f'{file_path}/track.json', 'r') as file:
            lines = file.readlines()
        # Remove the top line
        content = ''.join(lines[1:])
        '''
        THIS IS JANK AS HELL 
        '''
        content=content.split('"schedule"')[0].strip()[:-1]+'\n}'
        json_obj = json.loads(content)
        
        json_obj.update({
            "schedule":[]
        })
        index_name=json_obj['indices'][0]['name']
        
        return json_obj, index_name

def main():
    if len(sys.argv) < 2:
        print("Usage: python script.py <path_to_track.json>")
        sys.exit(1)

    file_path = sys.argv[1]
    initial_data, index_name=process_json_file(file_path)

    root = tk.Tk()
    app = TrackEditor(root, initial_data, file_path, index_name)
    root.mainloop()

if __name__ == "__main__":
    main()
