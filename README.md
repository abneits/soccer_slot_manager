⚽ Indoor Soccer Slot Manager
A dedicated web application to manage weekly 5-a-side football sessions.

This project was built to streamline the organization of our weekly indoor soccer match (Wednesdays at 7:00 PM). It handles user accounts via a referral system, manages registrations for the upcoming slot, tracks match results, and generates player statistics.

Shutterstock

🚀 Features
🔐 User Management & Authentication
Secure Access: Individual accounts with login/password.

Referral System: Registration is invite-only. A new user must be sponsored/referred by an existing member to create an account.

Guest Management: Registered users can add an unlimited number of guests (non-members) to a session.

CRUD Rights: Users can modify or delete their own registrations (including their guests).

📅 Session Management
Weekly Slot: configured for Wednesdays at 19:00 (7 PM).

Dashboard: A clean, simple view showing who is registered for the next upcoming session.

Teams & Results: Post-match input for team compositions and final scores.

📊 Statistics & Gamification
Track performance and dedication with automated leaderboards:

Top Winner: User with the most matches won.

Most Reliable: User with the highest attendance rate.

Best Recruiter: User who has referred/invited the most people.

💾 Database Structure (MongoDB)
The application uses MongoDB for flexible data storage. Below is the schema design for the two main collections.

1. Collection: user
Stores profile information for registered members.

JSON

{
  "_id": "ObjectId",
  "firstName": "String",
  "lastName": "String",
  "displayName": "String", // Name shown on the scoreboard
  "registrationDate": "Date",
  "referredBy": "ObjectId" // Reference to the user who sponsored them
}
2. Collection: slot
Stores data for each weekly session (past and upcoming).

JSON

{
  "_id": "ObjectId",
  "date": "Date", // e.g., 2023-10-25T19:00:00
  "registrations": [
    {
      "userId": "ObjectId", // Null if guest
      "guestName": "String", // Null if registered user
      "addedBy": "ObjectId" // Who made the registration
    }
  ],
  "slotInfo": {
    "teamA": ["String/ObjectId"],
    "teamB": ["String/ObjectId"],
    "finalScore": "String", // e.g., "12-10"
    "winner": "String" // "TeamA", "TeamB", or "Draw"
  }
}
🛠️ Tech Stack
Database: MongoDB

Backend: [Insert your backend here, e.g., Node.js / Express / Python Flask]

Frontend: [Insert your frontend here, e.g., React / Vue.js / EJS]

Authentication: [e.g., JWT / Session based]

⚙️ Installation & Setup
Follow these steps to get a local copy up and running.

Prerequisites
Node.js (or your specific runtime)

MongoDB installed locally or a cloud instance (Atlas).

Steps
Clone the repository

Bash

git clone https://github.com/your-username/soccer-slot-manager.git
cd soccer-slot-manager
Install dependencies

Bash

npm install
# or pip install -r requirements.txt
Configure Environment Variables Create a .env file in the root directory and add your MongoDB connection string:

Code snippet

MONGO_URI=mongodb://localhost:27017/futsal_db
PORT=3000
JWT_SECRET=your_secret_key
Run the application

Bash

npm start
Access the App Open your browser and navigate to http://localhost:3000.

🤝 Contributing
Contributions are welcome! If you want to add a feature (e.g., automatic team balancing algorithm, payment integration), feel free to fork the repository and submit a pull request.

Fork the Project

Create your Feature Branch (git checkout -b feature/AmazingFeature)

Commit your Changes (git commit -m 'Add some AmazingFeature')

Push to the Branch (git push origin feature/AmazingFeature)

Open a Pull Request

📝 License
Distributed under the MIT License. See LICENSE for more information.
