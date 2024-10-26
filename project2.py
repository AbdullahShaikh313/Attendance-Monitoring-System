import tkinter as tk
from tkinter import messagebox
import cv2
import face_recognition
import os
import numpy as np
from datetime import datetime, timedelta
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from PIL import Image, ImageTk


# Define global variables
running = False
status_text = None
path = r'C:\Users\dell\OneDrive\Desktop\PROJECT\images'
images = []
classNames = []
myList = os.listdir(path)

# Load student images and names
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

# Create attendance file if it doesn't exist
attendance_file = r'C:\Users\dell\OneDrive\Desktop\PROJECT\Attendance.csv'
if not os.path.exists(attendance_file):
    with open(attendance_file, 'w') as f:
        f.write('Name,Roll Number,Class,Time\n')

# Function to mark attendance
def markAttendance(name):
    student_roll, student_class = "Unknown", "Unknown"
    students_file = r'C:\Users\dell\OneDrive\Desktop\PROJECT\students.csv'

    # Fetch student info if available
    if os.path.exists(students_file):
        with open(students_file, 'r') as f:
            for line in f.readlines():
                data = line.strip().split(',')
                if data[0].upper() == name:
                    student_roll, student_class = data[1], data[2]
                    break

    # Log attendance if not yet recorded today
    today = datetime.now().strftime('%Y-%m-%d')
    with open(attendance_file, 'r+') as f:
        if not any(today in line and line.startswith(name) for line in f.readlines()):
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
                y1, x2, y2, x1 = [v * 4 for v in faceLoc]  # Scale back to original size
                cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)
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
    with open(attendance_file, 'r') as f:
        data = f.read()
    text_box.delete('1.0', tk.END)
    text_box.insert(tk.END, data)

def generate_pdf_report():
    one_month_ago = datetime.now() - timedelta(days=30)
    filtered_records = []

    # Filter records from the last month
    with open(attendance_file, 'r') as f:
        for line in f.readlines()[1:]:  # Skip the header
            # Split line and check for correct format
            data = line.strip().split(',')
            if len(data) != 4:
                print(f"Skipping malformed line: {line}")
                continue
            name, roll, cls, time_str = data
            try:
                date_obj = datetime.strptime(time_str, '%Y-%m-%d %H:%M:%S')
                if date_obj >= one_month_ago:
                    filtered_records.append((name, roll, cls, time_str))
            except ValueError:
                print(f"Skipping line with invalid date format: {line}")
                continue

    # Create the PDF
    pdf_path = r'C:\Users\dell\OneDrive\Desktop\PROJECT\Attendance_Report.pdf'
    c = canvas.Canvas(pdf_path, pagesize=A4)
    width, height = A4
    c.setFont("Helvetica", 12)
    c.drawString(50, height - 50, "Attendance Report - Last 30 Days")
    y_position = height - 80

    # Add attendance records to PDF
    for i, (name, roll, cls, time) in enumerate(filtered_records):
        if y_position < 50:  # Create a new page if needed
            c.showPage()
            c.setFont("Helvetica", 12)
            y_position = height - 50
        c.drawString(50, y_position, f"{i+1}. Name: {name}, Roll: {roll}, Class: {cls}, Time: {time}")
        y_position -= 20

    c.save()
    messagebox.showinfo("PDF Generated", f"Attendance PDF saved to {pdf_path}")

def register_new_student():
    cap = cv2.VideoCapture(0)
    success, img = cap.read()
    if success:
        student_name, student_roll, student_class = entry_name.get(), entry_roll.get(), entry_class.get()

        if student_name and student_roll and student_class:
            img_path = os.path.join(path, f"{student_name}.jpg")
            cv2.imwrite(img_path, img)
            images.append(img)
            classNames.append(student_name)
            encodeListKnown.append(face_recognition.face_encodings(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))[0])

            with open(r'C:\Users\dell\OneDrive\Desktop\PROJECT\students.csv', 'a') as f:
                f.write(f"{student_name},{student_roll},{student_class}\n")

            messagebox.showinfo("Success", f"Student {student_name} registered!")
        else:
            messagebox.showerror("Error", "Fill in all fields.")
    cap.release()

# Tkinter GUI setup
root = tk.Tk()
root.title("Face Recognition Attendance System")

# Set background color for the main window
root.configure(bg='#f0f0f0')  # Light grey background

frame_top = tk.Frame(root, bg='#f0f0f0')
frame_top.pack(pady=10)

frame_middle = tk.Frame(root, bg='#f0f0f0')
frame_middle.pack(pady=10)

frame_bottom = tk.Frame(root, bg='#f0f0f0')
frame_bottom.pack(pady=10)

button_font = ('Helvetica', 12)

status_text = tk.StringVar()
status_text.set("Welcome to the Attendance System")
status_label = tk.Label(frame_top, textvariable=status_text, font=('Helvetica', 14), fg='blue', bg='#f0f0f0')
status_label.pack(pady=10)

# Define font for labels and set increased width for Entry fields
label_font = ('Helvetica', 12, 'bold')
entry_width = 25  # Set desired width for entry fields
entry_font = ('Helvetica', 12)

tk.Label(frame_middle, text="New Student Name:", font=label_font, bg='#f0f0f0').grid(row=0, column=0, padx=10, pady=5)
entry_name = tk.Entry(frame_middle, width=entry_width, font=entry_font)
entry_name.grid(row=0, column=1, padx=10, pady=5)

tk.Label(frame_middle, text="Roll Number:", font=label_font, bg='#f0f0f0').grid(row=1, column=0, padx=10, pady=5)
entry_roll = tk.Entry(frame_middle, width=entry_width, font=entry_font)
entry_roll.grid(row=1, column=1, padx=10, pady=5)

tk.Label(frame_middle, text="Class:", font=label_font, bg='#f0f0f0').grid(row=2, column=0, padx=10, pady=5)
entry_class = tk.Entry(frame_middle, width=entry_width, font=entry_font)
entry_class.grid(row=2, column=1, padx=10, pady=5)

# Create buttons with custom background color
register_btn = tk.Button(frame_middle, text="Register Student", command=register_new_student, width=20, height=2, font=button_font, bg='#4CAF50', fg='white')
register_btn.grid(row=3, columnspan=2, pady=10)

start_btn = tk.Button(frame_bottom, text="Start Recognition", command=start_recognition, width=20, height=2, font=button_font, bg='#9C27B0', fg='white')
start_btn.grid(row=0, column=0, padx=20, pady=20)

stop_btn = tk.Button(frame_bottom, text="Stop Recognition", command=stop_recognition, width=20, height=2, font=button_font, bg='#9C27B0', fg='white')
stop_btn.grid(row=0, column=1, padx=10, pady=10)

show_btn = tk.Button(frame_bottom, text="Show Attendance", command=show_attendance, width=20, height=2, font=button_font, bg='#9C27B0', fg='white')
show_btn.grid(row=0, column=2, padx=10, pady=10)

pdf_btn = tk.Button(frame_bottom, text="Generate PDF Report", command=generate_pdf_report, width=20, height=2, font=button_font, bg='#9C27B0', fg='white')
pdf_btn.grid(row=0, column=3, padx=10, pady=10)

text_box = tk.Text(frame_bottom, height=10, width=50)
text_box.grid(row=1, columnspan=4, pady=10)

def update_status(message):
    status_text.set(message)

root.mainloop()
