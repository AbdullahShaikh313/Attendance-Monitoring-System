import tkinter as tk
from tkinter import messagebox
import cv2
import face_recognition
import os
import numpy as np
from datetime import datetime

running = False
status_text = None
path = r'C:\Users\dell\OneDrive\Desktop\PROJECT\images'
images = []
classNames = []
myList = os.listdir(path)

for cl in myList:
    curImg = cv2.imread(f'{path}/{cl}')
    images.append(curImg)
    classNames.append(os.path.splitext(cl)[0])

def findEncodings(images):
    encodeList = []
    for img in images:
        try:
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            encode = face_recognition.face_encodings(img)[0]
            encodeList.append(encode)
        except IndexError:
            print("Face not found, skipping.")
    return encodeList

encodeListKnown = findEncodings(images)

if not os.path.exists(r'C:\Users\dell\OneDrive\Desktop\PROJECT\Attendance.csv'):
    with open(r'C:\Users\dell\OneDrive\Desktop\PROJECT\Attendance.csv', 'w') as f:
        f.write('Name,Roll Number,Class,Time\n')

def markAttendance(name):
    student_roll = "Unknown"
    student_class = "Unknown"
    
    # Check the student information in 'students.csv'
    if os.path.exists(r'C:\Users\dell\OneDrive\Desktop\PROJECT\students.csv'):
        with open(r'C:\Users\dell\OneDrive\Desktop\PROJECT\students.csv', 'r') as f:
            lines = f.readlines()
            for line in lines:
                data = line.strip().split(',')
                if data[0].upper() == name:
                    student_roll = data[1]
                    student_class = data[2]
                    break
    else:
        print("students.csv file not found.")

    # Open the Attendance file and check for today’s attendance
    today = datetime.now().strftime('%Y-%m-%d')
    with open(r'C:\Users\dell\OneDrive\Desktop\PROJECT\Attendance.csv', 'r+') as f:
        myDataList = f.readlines()
        attendance_today = [line for line in myDataList if line.startswith(name) and today in line]

        if not attendance_today:
            dtString = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            f.write(f'{name},{student_roll},{student_class},{dtString}\n')
            print(f"Attendance marked for {name}")


def start_recognition():
    global running
    running = True
    cap = cv2.VideoCapture(0)

    while running:
        success, img = cap.read()
        imgS = cv2.resize(img, (0, 0), None, 0.25, 0.25)
        imgS = cv2.cvtColor(imgS, cv2.COLOR_BGR2RGB)

        facesCurFrame = face_recognition.face_locations(imgS)
        encodesCurFrame = face_recognition.face_encodings(imgS, facesCurFrame)

        for encodeFace, faceLoc in zip(encodesCurFrame, facesCurFrame):
            matches = face_recognition.compare_faces(encodeListKnown, encodeFace)
            faceDis = face_recognition.face_distance(encodeListKnown, encodeFace)
            matchIndex = np.argmin(faceDis)

            if matches[matchIndex]:
                name = classNames[matchIndex].upper()
                y1, x2, y2, x1 = faceLoc
                y1, x2, y2, x1 = y1 * 4, x2 * 4, y2 * 4, x1 * 4
                cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.rectangle(img, (x1, y2 - 35), (x2, y2), (0, 255, 0), cv2.FILLED)
                cv2.putText(img, name, (x1 + 6, y2 - 6), cv2.FONT_HERSHEY_COMPLEX, 1, (255, 255, 255), 2)
                markAttendance(name)
                update_status(f"Recognized: {name}")
            else:
                update_status("No match found.")

        cv2.imshow('Webcam', img)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
def stop_recognition():
    global running
    running = False
    messagebox.showinfo("Info", "Recognition stopped.")
    
def show_attendance():
    with open(r'C:\Users\dell\OneDrive\Desktop\PROJECT\Attendance.csv', 'r') as f:
        data = f.read()
    text_box.delete('1.0', tk.END)  # Clear the text box
    text_box.insert(tk.END, data)
def register_new_student():
    cap = cv2.VideoCapture(0)
    success, img = cap.read()
    if success:
        student_name = entry_name.get()
        student_roll = entry_roll.get()
        student_class = entry_class.get()

        if student_name and student_roll and student_class:
            img_path = os.path.join(path, student_name + ".jpg")
            cv2.imwrite(img_path, img)
            images.append(img)
            classNames.append(student_name)
            encodeListKnown.append(face_recognition.face_encodings(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))[0])
            with open(r'C:\Users\dell\OneDrive\Desktop\PROJECT\students.csv', 'a') as f:
                f.write(f'{student_name},{student_roll},{student_class}\n')
            messagebox.showinfo("Success", f"Student {student_name} registered!")
        else:
            messagebox.showerror("Error", "Fill in all fields.")
    cap.release()

# Tkinter GUI code continues...
# Tkinter GUI Setup
root = tk.Tk()
root.title("Face Recognition Attendance System")

# Create frames for better layout
frame_top = tk.Frame(root)
frame_top.pack(pady=10)

frame_middle = tk.Frame(root)
frame_middle.pack(pady=10)

frame_bottom = tk.Frame(root)
frame_bottom.pack(pady=10)

# Status label
status_text = tk.StringVar()
status_text.set("Welcome to the Attendance System")
status_label = tk.Label(frame_top, textvariable=status_text, font=('Helvetica', 14), fg='blue')
status_label.pack(pady=10)

# Entry for student name, roll number, and class
tk.Label(frame_middle, text="New Student Name:").grid(row=0, column=0, padx=10, pady=5)
entry_name = tk.Entry(frame_middle)
entry_name.grid(row=0, column=1, padx=10, pady=5)

tk.Label(frame_middle, text="Roll Number:").grid(row=1, column=0, padx=10, pady=5)
entry_roll = tk.Entry(frame_middle)
entry_roll.grid(row=1, column=1, padx=10, pady=5)

tk.Label(frame_middle, text="Class:").grid(row=2, column=0, padx=10, pady=5)
entry_class = tk.Entry(frame_middle)
entry_class.grid(row=2, column=1, padx=10, pady=5)

# Button to register new student
register_btn = tk.Button(frame_middle, text="Register Student", command=register_new_student)
register_btn.grid(row=3, columnspan=2, pady=10)

# Buttons for recognition
start_btn = tk.Button(frame_bottom, text="Start Recognition", command=start_recognition)
start_btn.grid(row=0, column=0, padx=10, pady=10)

stop_btn = tk.Button(frame_bottom, text="Stop Recognition", command=stop_recognition)
stop_btn.grid(row=0, column=1, padx=10, pady=10)

show_btn = tk.Button(frame_bottom, text="Show Attendance", command=show_attendance)
show_btn.grid(row=0, column=2, padx=10, pady=10)

# Create a text box to display attendance records
text_box = tk.Text(frame_bottom, height=10, width=50)
text_box.grid(row=1, columnspan=3, pady=10)

# Function to update status label
def update_status(message):
    status_text.set(message)

# Start the Tkinter event loop
root.mainloop()
